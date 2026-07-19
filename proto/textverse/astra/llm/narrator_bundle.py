"""Narrator-LLM bundle — calculator-bound perception renderer.

spec v0.129 §6.4: the Narrator turns State Bus + operator input into the
four-section perception bundle ASTRA reads. Every numeric in its output
must trace to a tool result observed in its input (calculator-bound).

**T2.2 (2026-05-16, audit Tier 2 #8 + G13 closure):** compose() now
auto-validates against the trace pool when one is provided. On hard-
severity failure, retries with halved temperature up to
validator.max_retries times before raising NarratorValidationError.
This closes §15.6 universality — both LLMs (ASTRA + Narrator) are now
calculator-bound by construction, not by caller convention.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from astra.llm.client import LLMClient, SamplingParams
from astra.llm.validator import (
    CalculatorBoundValidator,
    ValidationReport,
)


class NarratorValidationError(RuntimeError):
    """Raised when Narrator output fails calculator-bound validation past retry budget.

    Carries the final ValidationReport so the orchestrator can surface
    forensic detail (which numeric tokens went ungrounded) without
    re-running.
    """

    def __init__(self, report: ValidationReport, attempts: int) -> None:
        ungrounded = ", ".join(u.token for u in report.ungrounded[:5])
        super().__init__(
            f"Narrator output failed calculator-bound validation after "
            f"{attempts} attempt(s); {len(report.ungrounded)} ungrounded "
            f"numeric token(s): [{ungrounded}{'...' if len(report.ungrounded) > 5 else ''}]",
        )
        self.report = report
        self.attempts = attempts


def load_narrator_sysprompt(prompts_dir: Path) -> str:
    return (prompts_dir / "narrator_sysprompt.md").read_text(encoding="utf-8")


def _default_prompts_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "prompts"


class NarratorBundle:
    """Narrator-LLM bundle: client + sysprompt + calculator-bound validator.

    Lower temperature default (0.4) — Narrator is rendering, not improvising.
    Hard severity by default — Narrator output is the trace pool ASTRA reads;
    ungrounded numerics here are the worst kind of leak.
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
        api_key: str | None = None,
        extra_payload: dict[str, object] | None = None,
    ) -> None:
        if sysprompt is None:
            sysprompt = load_narrator_sysprompt(prompts_dir or _default_prompts_dir())
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        # Lower temperature: Narrator renders facts, not character.
        self.sampling = sampling or SamplingParams(temperature=0.4, top_p=0.85)
        # Hard severity: Narrator output is the trace pool ASTRA reads;
        # ungrounded numerics here are the worst kind of leak.
        self.validator = validator or CalculatorBoundValidator(severity="hard")

    async def compose(
        self,
        composition_request: str,
        trace_pool: Iterable[str] | None = None,
    ) -> str:
        """Generate one perception bundle.

        When `trace_pool` is provided, output is auto-validated against the
        calculator-bound discipline (§15.6 / §15.7 Surface 2). On hard
        validator severity, ungrounded output triggers a retry with halved
        temperature; max_retries attempts before raising
        NarratorValidationError. Soft severity logs drift and returns.

        When `trace_pool` is None (backward-compat), behaves as before —
        single chat completion, no validation. Caller is responsible for
        calling validate_output() separately if needed.
        """
        if trace_pool is None:
            return await self.client.chat_complete(composition_request, self.sampling)

        pool_list = list(trace_pool)
        current_sampling = self.sampling
        max_attempts = max(1, self.validator.max_retries + 1)
        last_output = ""
        last_report: ValidationReport | None = None
        for attempt in range(max_attempts):
            last_output = await self.client.chat_complete(composition_request, current_sampling)
            last_report = self.validator.validate(last_output, pool_list)
            if last_report.passed:
                return last_output
            if self.validator.severity == "soft":
                # Soft: log drift via the report; return the output.
                return last_output
            # Hard + failed: retry with reduced temperature if attempts remain.
            if attempt + 1 < max_attempts:
                next_temp = self.validator.next_temperature(
                    current_sampling.temperature, attempt + 1,
                )
                current_sampling = current_sampling.model_copy(
                    update={"temperature": next_temp},
                )
        # Exhausted retries; raise with the final report.
        assert last_report is not None  # by loop construction
        raise NarratorValidationError(last_report, attempts=max_attempts)

    def validate_output(
        self,
        narrator_output: str,
        trace_pool: list[str],
    ) -> ValidationReport:
        """Validate that the Narrator's numerics all trace to tool results.

        Kept as a public method for callers that want to validate
        post-hoc on text produced elsewhere. Auto-validation via
        compose(trace_pool=...) is the preferred path.
        """
        return self.validator.validate(narrator_output, trace_pool)
