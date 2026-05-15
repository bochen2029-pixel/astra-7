"""Narrator-LLM bundle — calculator-bound perception renderer.

Spec v0.128 §6.4: the Narrator turns State Bus + operator input into the
four-section perception bundle ASTRA reads. Every numeric in its output
must trace to a tool result observed in its input (calculator-bound).

Day 4 lands the bundle surface. The Narrator's actual rendering logic
lives in `astra/harness/perception_assembler.py` (Day 5) which calls this
bundle's `compose()` method.
"""

from __future__ import annotations

from pathlib import Path

from astra.llm.client import LLMClient, SamplingParams
from astra.llm.validator import CalculatorBoundValidator, ValidationReport


def load_narrator_sysprompt(prompts_dir: Path) -> str:
    return (prompts_dir / "narrator_sysprompt.md").read_text(encoding="utf-8")


def _default_prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class NarratorBundle:
    """Narrator-LLM bundle: client + sysprompt + calculator-bound validator.

    Lower temperature default (0.4) — Narrator is rendering, not improvising.
    """

    def __init__(
        self,
        *,
        base_url: str,
        sysprompt: str | None = None,
        prompts_dir: Path | None = None,
        sampling: SamplingParams | None = None,
        validator: CalculatorBoundValidator | None = None,
        model_name: str = "narrator",
    ) -> None:
        if sysprompt is None:
            sysprompt = load_narrator_sysprompt(prompts_dir or _default_prompts_dir())
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
        )
        # Lower temperature: Narrator renders facts, not character.
        self.sampling = sampling or SamplingParams(temperature=0.4, top_p=0.85)
        # Hard severity: Narrator output is the trace pool ASTRA reads;
        # ungrounded numerics here are the worst kind of leak.
        self.validator = validator or CalculatorBoundValidator(severity="hard")

    async def compose(
        self,
        composition_request: str,
    ) -> str:
        """Generate one perception bundle. Returns the raw text."""
        return await self.client.chat_complete(composition_request, self.sampling)

    def validate_output(
        self,
        narrator_output: str,
        trace_pool: list[str],
    ) -> ValidationReport:
        """Validate that the Narrator's numerics all trace to tool results."""
        return self.validator.validate(narrator_output, trace_pool)
