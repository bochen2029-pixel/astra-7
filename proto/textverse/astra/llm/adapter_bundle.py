"""Adapter-LLM bundle — loose-form TOOL normalizer.

spec v0.129 §4.9: the Adapter takes ASTRA's `<tool>` body (which may be
JSON, key=value, or natural language) and emits a single JSON object the
dispatcher can execute. v0 may use a rules-based parser instead of an
actual LLM if scenarios don't surface need for ML flexibility.

Day 4 lands BOTH paths:
- AdapterBundle (LLM-backed): wraps an LLMClient + adapter sysprompt.
- RulesBasedAdapter: pure-Python JSON / regex parser, no LLM dependency.

The orchestrator (Day 5) chooses based on hardware tier and scenario need.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astra.llm.client import LLMClient, SamplingParams


def load_adapter_sysprompt(prompts_dir: Path) -> str:
    return (prompts_dir / "adapter_sysprompt.md").read_text(encoding="utf-8")


def _default_prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class AdapterResult(BaseModel):
    """Adapter output. `ok=True` ⇒ args is the validated dict; else error set."""

    model_config = ConfigDict(frozen=True)

    ok: bool
    args: dict[str, Any] = Field(default_factory=dict)
    error: str = ""


_KV_PAIR_RE: re.Pattern[str] = re.compile(
    r"""(\w+)\s*[:=]\s*("([^"]*)"|'([^']*)'|([^,\s]+))""",
)


class RulesBasedAdapter:
    """Pure-Python adapter for the v0 minimum case.

    Order of attempts on each loose body:
    1. Try `json.loads(body)`; if it returns a dict, use it.
    2. Try `key=value` / `key: value` pair extraction (quoted or bare).
    3. Return ok=False with a parse-failure error.

    No schema validation beyond shape — the dispatcher's Pydantic models
    in `astra/ship/api.py` enforce schema. The adapter's job is parsing.
    """

    def normalize(self, op_name: str, raw_body: str) -> AdapterResult:
        body = raw_body.strip()
        if not body:
            return AdapterResult(ok=False, error="empty body")

        # Attempt 1: pure JSON
        try:
            parsed = json.loads(body)
        except (json.JSONDecodeError, ValueError):
            parsed = None
        if isinstance(parsed, dict):
            return AdapterResult(ok=True, args=parsed)

        # Attempt 2: key=value pairs
        kv_args: dict[str, Any] = {}
        for match in _KV_PAIR_RE.finditer(body):
            key = match.group(1)
            value_str = (
                match.group(3)
                if match.group(3) is not None
                else match.group(4)
                if match.group(4) is not None
                else match.group(5)
            )
            kv_args[key] = self._coerce_value(value_str)
        if kv_args:
            return AdapterResult(ok=True, args=kv_args)

        return AdapterResult(
            ok=False,
            error=f"could not parse '{op_name}' body as JSON or key=value pairs",
        )

    @staticmethod
    def _coerce_value(s: str) -> Any:
        """Coerce a bare value string to bool/int/float when unambiguous."""
        if s.lower() == "true":
            return True
        if s.lower() == "false":
            return False
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        return s


class AdapterBundle:
    """LLM-backed adapter. Used when the rules-based path is insufficient."""

    def __init__(
        self,
        *,
        base_url: str,
        sysprompt: str | None = None,
        prompts_dir: Path | None = None,
        sampling: SamplingParams | None = None,
        model_name: str = "adapter",
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
    ) -> None:
        if sysprompt is None:
            sysprompt = load_adapter_sysprompt(prompts_dir or _default_prompts_dir())
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        # Very low temperature: Adapter is deterministic-ish JSON emission.
        self.sampling = sampling or SamplingParams(temperature=0.1, top_p=0.5)

    async def normalize(self, op_name: str, raw_body: str, schema_hint: str = "") -> AdapterResult:
        """Ask the Adapter LLM to normalize the body. Returns AdapterResult."""
        prompt = self._build_prompt(op_name, raw_body, schema_hint)
        text = (await self.client.chat_complete(prompt, self.sampling)).strip()
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError) as e:
            return AdapterResult(
                ok=False,
                error=f"adapter emitted non-JSON: {e}",
            )
        if not isinstance(parsed, dict):
            return AdapterResult(ok=False, error="adapter returned non-object")
        ok = bool(parsed.get("ok", False))
        if not ok:
            return AdapterResult(
                ok=False,
                error=str(parsed.get("error", "unspecified rejection")),
            )
        args = parsed.get("args", {})
        if not isinstance(args, dict):
            return AdapterResult(ok=False, error="adapter args not an object")
        return AdapterResult(ok=True, args=args)

    @staticmethod
    def _build_prompt(op_name: str, raw_body: str, schema_hint: str) -> str:
        parts = [
            f"operation: {op_name}",
        ]
        if schema_hint:
            parts.append(f"schema: {schema_hint}")
        parts.append("body:")
        parts.append(raw_body)
        return "\n".join(parts)
