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

from astra.grammar.strip_rules import count_think_open_close, find_speech_start
from astra.llm.client import LLMClient, SamplingParams, build_thinking_payload
from astra.llm.validator import (
    CalculatorBoundValidator,
    ValidationReport,
)

# --- Narrator inference budget (6e; F-LIVE-19 closure) -------------------
#
# Run #8 measured a 0.506 fallback rate at the 9B floor, and every fallback
# reason read 0-ungrounded: the class was ALL-COGNITION emission. The narrator
# reasoned past its token budget inside <think>, the unclosed tag failed
# CLOSED by design, and the template path took over on half of all turns.
#
# The root cause was config, not contract. The narrator path had:
#   - no compose budget of its own (max_tokens silently inherited the 2048
#     SamplingParams default, which is ASTRA's SPEECH budget), and
#   - no reasoning control (extra_payload was never passed, so thinking ran
#     at whatever the server's chat template defaults to: on).
#
# Both are fixed here with named values instead of inherited ones. The
# structural argument for thinking="off": the Narrator is a RENDERER. Its
# sysprompt's own summary is "you take structured world state and render it
# as in-register prose", and §15.6 makes it calculator-bound — it may only
# transcribe numerics it was given, never derive them. There is no decision
# for cognition to make, so cognition is pure cost. This is the F-LIVE-11 /
# F-LIVE-16 lesson one seam deeper: not "strip the cognition" but "do not
# generate it."
NARRATOR_COMPOSE_MAX_TOKENS = 1024
NARRATOR_TEMPERATURE = 0.4
NARRATOR_TOP_P = 0.85
NARRATOR_THINKING = "off"


def _strip_reasoning(raw: str) -> str:
    """Surface-4 discipline at the narrator seam (6c live catch,
    run #7): the Narrator is a reasoning model too, and its cognition
    must never enter ASTRA's perception. Live, the un-stripped path
    delivered the narrator's whole chain-of-thought as the bundle head —
    meta-vocabulary (`wall-clock`, `LLM`, `system prompt`) straight into
    the leak scanner, the `<state>` section displaced (state_coherent
    0.18), and think-side numerics (`-5`) tripping the calculator-bound
    validator into retry loops.

    Same rules as the ASTRA path: everything before the LAST `</think>`
    is cognition (v0.128 strip rule); an UNCLOSED `<think>` fails CLOSED
    (the whole emission is cognition; an empty delivery is a failed
    attempt, never a delivered bundle).
    """
    opens, closes = count_think_open_close(raw)
    if opens > closes:
        return ""
    return raw[find_speech_start(raw):].strip()


class NarratorValidationError(RuntimeError):
    """Raised when Narrator output fails calculator-bound validation past retry budget.

    Carries the final ValidationReport so the orchestrator can surface
    forensic detail (which numeric tokens went ungrounded) without
    re-running.
    """

    def __init__(
        self, report: ValidationReport, attempts: int, note: str = "",
    ) -> None:
        ungrounded = ", ".join(u.token for u in report.ungrounded[:5])
        message = (
            f"Narrator output failed calculator-bound validation after "
            f"{attempts} attempt(s); {len(report.ungrounded)} ungrounded "
            f"numeric token(s): [{ungrounded}{'...' if len(report.ungrounded) > 5 else ''}]"
        )
        if note:
            # Distinct failure classes keep gun R-4's channel legible:
            # "ungrounded numerics" and "nothing deliverable" are different
            # narrator problems with different levers (run #8 finding: the
            # dominant live class at the 9B floor is all-cognition /
            # reasoning-truncation, not invention).
            message = f"{message}; {note}"
        super().__init__(message)
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
        thinking: str = NARRATOR_THINKING,
    ) -> None:
        if sysprompt is None:
            sysprompt = load_narrator_sysprompt(prompts_dir or _default_prompts_dir())
        # Reasoning control composes UNDER any caller-supplied extra_payload:
        # an explicit chat_template_kwargs from the caller wins, so the
        # thinking default never silently overrides a deliberate override.
        merged_payload: dict[str, object] = {}
        thinking_payload = build_thinking_payload(thinking)
        if thinking_payload:
            merged_payload.update(thinking_payload)
        if extra_payload:
            merged_payload.update(extra_payload)
        self.thinking = thinking
        self.client = LLMClient(
            base_url=base_url,
            sysprompt=sysprompt,
            model_name=model_name,
            api_key=api_key,
            extra_payload=merged_payload or None,
        )
        # Lower temperature: Narrator renders facts, not character. Explicit
        # compose budget: never inherit ASTRA's speech-sized default (F-LIVE-19).
        self.sampling = sampling or SamplingParams(
            temperature=NARRATOR_TEMPERATURE,
            top_p=NARRATOR_TOP_P,
            max_tokens=NARRATOR_COMPOSE_MAX_TOKENS,
        )
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
            return _strip_reasoning(
                await self.client.chat_complete(composition_request, self.sampling),
            )

        pool_list = list(trace_pool)
        current_sampling = self.sampling
        max_attempts = max(1, self.validator.max_retries + 1)
        last_report: ValidationReport | None = None
        for attempt in range(max_attempts):
            raw = await self.client.chat_complete(composition_request, current_sampling)
            # Strip BEFORE validation: cognition is never delivered and its
            # numerics are not the bundle's numerics (6c: think-side "-5"s
            # were driving spurious retry loops). Empty delivery (all
            # cognition / unclosed think) is a failed attempt.
            delivered = _strip_reasoning(raw)
            if delivered:
                last_report = self.validator.validate(delivered, pool_list)
                if last_report.passed:
                    return delivered
                if self.validator.severity == "soft":
                    # Soft: log drift via the report; return the output.
                    return delivered
            # Hard + failed (or nothing deliverable): retry with reduced
            # temperature if attempts remain.
            if attempt + 1 < max_attempts:
                next_temp = self.validator.next_temperature(
                    current_sampling.temperature, attempt + 1,
                )
                current_sampling = current_sampling.model_copy(
                    update={"temperature": next_temp},
                )
        if last_report is None:
            # Every attempt was all-cognition: nothing was ever deliverable.
            # Report over the empty delivery, with the distinct class named
            # (unclosed/never-exited reasoning — typically the model running
            # past its token budget inside <think>; fails CLOSED by design).
            last_report = self.validator.validate("", pool_list)
            raise NarratorValidationError(
                last_report,
                attempts=max_attempts,
                note=(
                    "no deliverable bundle: every attempt was cognition-only "
                    "(unclosed or all-<think> emission; reasoning likely "
                    "truncated by the token budget)"
                ),
            )
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
