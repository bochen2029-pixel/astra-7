"""ASTRA-LLM bundle — in-character cognition + STAGE emission.

Spec v0.128 §4.9 + §6.4: the bundle is the composition of substrate
(LLM client) + persona (sysprompt + STAGE addendum) + discipline
(CalculatorBoundValidator). The bundle is what the orchestrator talks to.

Day 4: surface only. Day 5 wires it into the turn loop. The smoke test
verifies one perception bundle → one STAGE output round-trip with no
substrate setup beyond a running llama-server.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from astra.grammar import StageOutput, StageParser
from astra.llm.client import LLMClient, SamplingParams
from astra.llm.validator import CalculatorBoundValidator, ValidationReport


def _read_prompt_file(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_astra_sysprompt(prompts_dir: Path) -> str:
    """Read the canonical sysprompt + STAGE addendum from the prompts dir.

    Concatenates with a blank line between, matching the manual-scenario
    setup in proto/textverse/scenarios/watch_47_morning.md.
    """
    sys_path = prompts_dir / "astra_sysprompt.md"
    addendum_path = prompts_dir / "astra_stage_addendum.md"
    sys_text = _read_prompt_file(sys_path)
    addendum_text = _read_prompt_file(addendum_path)
    return sys_text.rstrip() + "\n\n" + addendum_text.lstrip()


def default_prompts_dir() -> Path:
    """Path to proto/textverse/prompts/ relative to this file."""
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class AstraBundle:
    """ASTRA-LLM bundle: client + sysprompt + STAGE parser + validator."""

    def __init__(
        self,
        *,
        base_url: str,
        sysprompt: str | None = None,
        prompts_dir: Path | None = None,
        sampling: SamplingParams | None = None,
        validator: CalculatorBoundValidator | None = None,
        model_name: str = "astra",
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
    ) -> None:
        if sysprompt is None:
            sysprompt = load_astra_sysprompt(prompts_dir or default_prompts_dir())
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        self.sampling = sampling or SamplingParams()
        self.validator = validator or CalculatorBoundValidator(severity="soft")

    async def turn(self, perception_bundle: str) -> StageOutput:
        """One turn: perception in, parsed STAGE output out (non-streaming)."""
        raw = await self.client.chat_complete(perception_bundle, self.sampling)
        parser = StageParser()
        parser.push(raw)
        return parser.finalize()

    async def turn_stream(
        self,
        perception_bundle: str,
    ) -> AsyncIterator[str]:
        """Streaming turn: yields raw token deltas (caller parses on close)."""
        async for token in self.client.chat_stream(perception_bundle, self.sampling):
            yield token

    def validate_speech(
        self,
        speech: str,
        trace_pool: list[str],
    ) -> ValidationReport:
        """Run calculator-bound validation on a parsed speech string."""
        return self.validator.validate(speech, trace_pool)
