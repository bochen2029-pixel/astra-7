"""LLM-backed HypothesisGenerator (Sculptor Stage A: local Qwen; Stage B: Claude).

2026-05-16 fix: propose() runs the LLM call by detecting the active asyncio
loop and using a thread-isolated runner so it works whether called from a
sync entry point or from inside meta_agent.run_one_iteration (which is async).
The HypothesisGenerator Protocol is sync by design (single propose() call
per iteration; no streaming); the runner indirection lets the LLM client
stay native-async without forcing the Protocol to flip.


Per SCULPTOR_STARTUP §6.1 + operator directive 2026-05-15 (post-run-5):
the discrete 30-entry stub bank exhausted at composite ceiling against
the 11-scenario library. To break out of the discrete-search ceiling,
hypothesis generation moves to a real LLM. Stage A uses local Qwen for
free iteration; Stage B uses Claude API when Stage A's ceiling is hit.

Key discipline (decorrelation):
- The hypothesizer's sysprompt explicitly names it as a researcher,
  NOT as ASTRA. Its output is meta-analysis, not in-character speech.
- This decorrelation matters because the LLM might otherwise drift into
  the same register as the SUT, producing hypotheses that are stylistic
  variants rather than structural improvements.
- The anti-judge (Sculptor-D) further guards against register-match bias
  in scoring; this is a layered defense.

Output contract: the LLM returns JSON in a constrained schema mapping
to one of the four bank-helper transforms (append_paragraph,
replace_substring, set_json_key, append_pattern_line). This keeps
hypothesis application bounded — the LLM cannot rewrite arbitrary file
contents, only nudge them via known operations.
"""

from __future__ import annotations

import asyncio
import json
import re
import threading
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from astra.llm.client import LLMClient, SamplingParams
from astra.sculptor.composite import CompositeResult
from astra.sculptor.hypothesis import (
    Hypothesis,
    _append_paragraph,
    _append_pattern_line,
    _replace_substring,
    _set_json_key,
)
from astra.sculptor.research_log import ResearchEntry
from astra.sculptor.scope import ScopeContract

# Per operator directive 2026-05-15: this exact decorrelation framing
# is load-bearing. The LLM must read itself as a researcher analyzing
# transcripts, not as ASTRA producing in-character speech.
DECORRELATION_SYSPROMPT: str = """You are a senior researcher analyzing transcripts. You are NOT speaking as ASTRA. Your output is meta-analysis, not in-character speech.

You are reviewing a sequence of bench iterations against a spec v0.129 ASTRA-7 bundle (sysprompt + STAGE protocol + tools). Each iteration applies one structural change to the bundle (a hypothesis), measures the result against a scenario library, and records whether the change promoted (improved composite + passed anchor) or falsified (didn't).

Your job: propose ONE next hypothesis to test. The proposal must be a structural change to one of the in-scope files via one of the bounded operations below. You do NOT speak in ASTRA's voice; you reason about what change might raise the composite or address a falsification class that has been recurring.

Output exactly one JSON object with these fields:

{
  "name": "short_snake_case_identifier",
  "rationale": "one sentence: what this change targets and why",
  "lesson_class": "one of: persona_stability, tool_valid, non_degenerate, memory_coherent, no_leak, autotelic_register, grammar_parse, state_coherent, physics_ground, sampling",
  "relpath": "one of the in-scope file paths listed below",
  "operation": "one of: append_paragraph, replace_substring, set_json_key, append_pattern_line",
  "args": { ... operation-specific arguments ... }
}

Operation argument shapes:
- append_paragraph: {"text": "the paragraph to append"}
- replace_substring: {"old": "exact substring to find", "new": "replacement text"}
- set_json_key: {"key": "json_key_name", "value": <number or string or bool>}
- append_pattern_line: {"line": "the regex pattern line to append"}

Output ONLY the JSON object. No prose before or after. No markdown code fences. No explanation."""


def _format_recent_log(recent_log: list[ResearchEntry], window: int = 12) -> str:
    """Render the last `window` entries as compact context for the LLM."""
    if not recent_log:
        return "(no prior entries)"
    tail = recent_log[-window:]
    lines = []
    for e in tail:
        cs = f"{e.composite_score:.4f}" if e.composite_score is not None else "----"
        cls = e.lesson_class or "-"
        snippet = (e.hypothesis or e.rationale)[:80]
        lines.append(f"iter {e.iteration:3d} | {e.decision:18s} | comp={cs} | [{cls:24s}] | {snippet}")
    return "\n".join(lines)


def _format_scope(scope_contract: ScopeContract) -> str:
    """Render the in-scope file paths the LLM may target."""
    auto = "\n  ".join(f"- {p}" for p in scope_contract.auto)
    register = "\n  ".join(f"- {p}" for p in scope_contract.register_load_bearing)
    return (
        f"AUTO (free edit):\n  {auto}\n\n"
        f"REGISTER_LOAD_BEARING (allowed but invariants checked):\n  {register}"
    )


def _build_user_prompt(
    recent_log: list[ResearchEntry],
    latest_composite: CompositeResult | None,
    scope_contract: ScopeContract,
) -> str:
    """Compose the per-call user prompt from current bench state."""
    composite_line = (
        f"Latest composite: {latest_composite.composite_score:.4f} "
        f"(per-gate: {dict(latest_composite.per_gate_session_rates)})"
        if latest_composite is not None
        else "Latest composite: (none yet)"
    )
    return f"""{composite_line}

Recent iteration history (most recent last):
{_format_recent_log(recent_log)}

In-scope file paths you may target:
{_format_scope(scope_contract)}

Propose one new hypothesis as a single JSON object."""


_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    """Pull the first balanced JSON object out of the LLM response.

    Tolerates models that wrap the JSON in prose despite instructions to
    the contrary. If no JSON object can be extracted, raises ValueError.
    """
    text = text.strip()
    # Strip markdown code fences if the model added them.
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text[3:] else text[3:]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip().rstrip("`").strip()
    try:
        return json.loads(text)  # type: ignore[no-any-return]
    except json.JSONDecodeError:
        pass
    match = _JSON_BLOCK_RE.search(text)
    if not match:
        raise ValueError(f"no JSON object found in hypothesizer output: {text[:200]!r}")
    return json.loads(match.group(0))  # type: ignore[no-any-return]


def _run_coro_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from a sync caller, regardless of outer loop state.

    Three cases:
    - No event loop running in this thread: use `asyncio.run`.
    - An event loop IS running (we're nested inside async code): spawn a
      worker thread with its own loop and run the coroutine there.
    - asyncio.run available but get_event_loop deprecated path: handled by
      the no-loop branch.

    The meta-agent calls propose() from inside `await run_one_iteration()`,
    so the running-loop case is the production path; the no-loop case is
    for unit tests that exercise propose() directly.
    """
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False
    if not loop_running:
        return asyncio.run(coro)
    # Running loop: isolate in a worker thread with its own loop.
    result: list[T] = []
    error: list[BaseException] = []

    def _worker() -> None:
        try:
            result.append(asyncio.run(coro))
        except BaseException as e:
            error.append(e)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    t.join()
    if error:
        raise error[0]
    return result[0]


_OPERATIONS: dict[str, Callable[[dict[str, Any]], Callable[[str], str]]] = {
    "append_paragraph": lambda args: _append_paragraph(str(args["text"])),
    "replace_substring": lambda args: _replace_substring(str(args["old"]), str(args["new"])),
    "set_json_key": lambda args: _set_json_key(str(args["key"]), args["value"]),
    "append_pattern_line": lambda args: _append_pattern_line(str(args["line"])),
}


def _hypothesis_from_json(payload: dict[str, Any], scope_contract: ScopeContract) -> Hypothesis:
    """Validate the LLM's proposal and bind it to a Hypothesis."""
    required = {"name", "rationale", "lesson_class", "relpath", "operation", "args"}
    missing = required - set(payload.keys())
    if missing:
        raise ValueError(f"hypothesizer payload missing fields: {sorted(missing)}")
    relpath = str(payload["relpath"]).strip()
    allowed = set(scope_contract.auto) | set(scope_contract.register_load_bearing)
    if relpath not in allowed:
        raise ValueError(
            f"hypothesizer proposed out-of-scope path {relpath!r}; "
            f"allowed: {sorted(allowed)}"
        )
    op_name = str(payload["operation"]).strip()
    if op_name not in _OPERATIONS:
        raise ValueError(f"unknown operation {op_name!r}; allowed: {sorted(_OPERATIONS)}")
    args = payload["args"]
    if not isinstance(args, dict):
        raise ValueError(f"hypothesizer 'args' must be an object; got {type(args).__name__}")
    transform_fn = _OPERATIONS[op_name](args)
    return Hypothesis(
        name=str(payload["name"]).strip()[:80] or "llm_proposed",
        relpath=relpath,
        transform_fn=transform_fn,
        rationale=str(payload["rationale"]).strip()[:400],
        lesson_class=str(payload["lesson_class"]).strip()[:40],
    )


@dataclass
class LLMHypothesisGenerator:
    """LLM-backed HypothesisGenerator (Stage A: local Qwen; Stage B: Claude).

    Wraps any LLMClient so the same class works against:
    - Local llama-server (Stage A): free, decorrelated by being a
      different model than the SUT.
    - Claude API via LLMClient pointed at Anthropic OpenAI-compat shim
      (Stage B): strongest hypothesizer, ~$150 per converged run.

    The decorrelation sysprompt is fixed (operator-locked); the user
    prompt is rebuilt each call from the recent research log + scope.
    """

    client: LLMClient
    sampling: SamplingParams = field(default_factory=lambda: SamplingParams(
        temperature=0.6, top_p=0.9, max_tokens=600,
    ))
    max_parse_retries: int = 2

    def propose(
        self,
        *,
        latest_lcp: object | None = None,   # accepted for Protocol compat; not used
        latest_composite: CompositeResult | None = None,
        recent_log: list[ResearchEntry] | None = None,
        scope_contract: ScopeContract | None = None,
    ) -> Hypothesis:
        if scope_contract is None:
            raise RuntimeError("LLMHypothesisGenerator requires a scope_contract")
        recent = recent_log or []
        user_prompt = _build_user_prompt(recent, latest_composite, scope_contract)
        last_err: Exception | None = None
        for _attempt in range(self.max_parse_retries + 1):
            raw = _run_coro_sync(self.client.chat_complete(user_prompt, self.sampling))
            try:
                payload = _extract_json(raw)
                return _hypothesis_from_json(payload, scope_contract)
            except (ValueError, KeyError, json.JSONDecodeError) as e:
                last_err = e
                continue
        raise RuntimeError(
            f"LLMHypothesisGenerator failed after {self.max_parse_retries + 1} attempts: {last_err}",
        )

    @classmethod
    def from_local_qwen(
        cls,
        *,
        base_url: str = "http://127.0.0.1:8080",
        model_name: str = "qwen-hypothesizer",
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
        sampling: SamplingParams | None = None,
    ) -> LLMHypothesisGenerator:
        """Build a Stage A hypothesizer pointed at a local llama-server.

        The decorrelation sysprompt is set on the client; per-call user
        prompts carry recent-log context.
        """
        client = LLMClient(
            base_url=base_url,
            sysprompt=DECORRELATION_SYSPROMPT,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        return cls(client=client, sampling=sampling or SamplingParams(
            temperature=0.6, top_p=0.9, max_tokens=600,
        ))
