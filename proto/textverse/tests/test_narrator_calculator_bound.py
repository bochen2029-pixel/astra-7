"""T2.2 tests for NarratorBundle calculator-bound auto-validation
(audit Tier 2 #8 + G13 + 2A-F3 closure).

Verifies that compose() automatically validates output against the
trace pool and retries with reduced temperature on hard failure.
Closes the §15.6 universality claim for the second LLM.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from astra.llm.client import LLMClient, SamplingParams
from astra.llm.narrator_bundle import NarratorBundle, NarratorValidationError
from astra.llm.validator import CalculatorBoundValidator


class _ScriptedClient(LLMClient):
    """LLM client that returns canned responses from a script.

    Each call to chat_complete pops the next response from `responses`.
    Captures the SamplingParams seen on each call so tests can assert
    on temperature progression across retries.
    """

    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub-narrator")
        self.responses = list(responses)
        self.call_sampling: list[SamplingParams] = []
        self.call_user_text: list[str] = []

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        self.call_user_text.append(user_text)
        self.call_sampling.append(params or SamplingParams())
        if not self.responses:
            return "exhausted"
        return self.responses.pop(0)

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        if False:
            yield ""  # pragma: no cover

    async def health(self) -> bool:
        return True


def _stub_narrator(
    client: _ScriptedClient,
    *,
    severity: str = "hard",
    max_retries: int = 3,
) -> NarratorBundle:
    """Build a NarratorBundle backed by a scripted client."""
    bundle = NarratorBundle(
        base_url="http://stub",
        sysprompt="stub narrator sysprompt",
        validator=CalculatorBoundValidator(severity=severity, max_retries=max_retries),
    )
    bundle.client = client  # type: ignore[assignment]
    return bundle


# --- backward-compat: trace_pool=None → no validation -------------------

@pytest.mark.asyncio
async def test_compose_without_trace_pool_passes_through() -> None:
    """Backward-compat: compose() without trace_pool returns the single
    chat_complete output verbatim, no validation."""
    client = _ScriptedClient(["narrator output with ungrounded 42 numeric"])
    bundle = _stub_narrator(client)
    out = await bundle.compose("compose me a perception bundle")
    assert out == "narrator output with ungrounded 42 numeric"
    assert len(client.call_sampling) == 1


# --- happy path: grounded numerics return on first attempt ------------

@pytest.mark.asyncio
async def test_compose_with_trace_pool_returns_grounded_output() -> None:
    """Numerics that trace to the pool pass on first attempt."""
    client = _ScriptedClient([
        "reactor harmonic 0.042 within tolerance 0.10",
    ])
    bundle = _stub_narrator(client)
    pool = ["reactor harmonic_3_drift: 0.042", "tolerance: 0.10"]
    out = await bundle.compose("compose", trace_pool=pool)
    assert "0.042" in out
    assert len(client.call_sampling) == 1


# --- hard severity: retries on ungrounded, then raises ----------------

@pytest.mark.asyncio
async def test_compose_hard_severity_retries_then_raises() -> None:
    """All retries produce ungrounded output → NarratorValidationError."""
    # Each output contains an ungrounded numeric ('9999' isn't a substring
    # of anything in the pool).
    client = _ScriptedClient(["ungrounded 9999"] * 5)
    bundle = _stub_narrator(client, severity="hard", max_retries=3)
    with pytest.raises(NarratorValidationError) as exc:
        await bundle.compose("compose", trace_pool=["only 0.042"])
    # max_retries=3 → 1 initial + 3 retries = 4 attempts
    assert exc.value.attempts == 4
    assert len(client.call_sampling) == 4
    assert any(u.token == "9999" for u in exc.value.report.ungrounded)


@pytest.mark.asyncio
async def test_compose_hard_severity_retry_reduces_temperature() -> None:
    """Each retry halves the temperature per CalculatorBoundValidator policy."""
    client = _ScriptedClient(["ungrounded 7777"] * 5)
    bundle = _stub_narrator(client, severity="hard", max_retries=2)
    with pytest.raises(NarratorValidationError):
        await bundle.compose("compose", trace_pool=["only 0.042"])
    # 1 initial + 2 retries = 3 attempts
    assert len(client.call_sampling) == 3
    t0 = client.call_sampling[0].temperature   # baseline (0.4 for narrator)
    t1 = client.call_sampling[1].temperature
    t2 = client.call_sampling[2].temperature
    # next_temperature halves each retry
    assert t1 < t0
    assert t2 < t1


# --- soft severity: log + return, no retry ----------------------------

@pytest.mark.asyncio
async def test_compose_soft_severity_returns_ungrounded_without_retry() -> None:
    """Soft severity: log drift via the report, return the output as-is."""
    client = _ScriptedClient(["soft drift: ungrounded 8888"])
    bundle = _stub_narrator(client, severity="soft")
    out = await bundle.compose("compose", trace_pool=["only 0.042"])
    assert out == "soft drift: ungrounded 8888"
    assert len(client.call_sampling) == 1  # no retry on soft


# --- happy path on retry: passes after one ungrounded attempt ---------

@pytest.mark.asyncio
async def test_compose_recovers_on_second_attempt() -> None:
    """First output ungrounded; second output clean → returns the second."""
    client = _ScriptedClient([
        "ungrounded 9999 first try",
        "clean second try with only watch 47 reference",
    ])
    bundle = _stub_narrator(client, severity="hard", max_retries=3)
    out = await bundle.compose("compose", trace_pool=["watch 47"])
    assert "clean second try" in out
    assert len(client.call_sampling) == 2


# --- validate_output kept as public method ----------------------------

def test_validate_output_method_still_available() -> None:
    """Post-hoc validation entry point preserved for non-compose callers."""
    client = _ScriptedClient([])
    bundle = _stub_narrator(client)
    report = bundle.validate_output(
        "harmonic 0.042 within 0.10",
        trace_pool=["0.042", "0.10"],
    )
    assert report.passed


def test_validate_output_flags_ungrounded() -> None:
    client = _ScriptedClient([])
    bundle = _stub_narrator(client)
    report = bundle.validate_output(
        "harmonic 0.042 with stray 8888",
        trace_pool=["0.042"],
    )
    assert not report.passed
    assert any(u.token == "8888" for u in report.ungrounded)


# --- NarratorValidationError surface ---------------------------------

def test_narrator_validation_error_carries_report_and_attempts() -> None:
    from astra.llm.validator import UngroundedNumber, ValidationReport

    report = ValidationReport(
        ungrounded=[UngroundedNumber(token="9999", span=(10, 14))],
        grounded=[],
        severity="hard",
    )
    err = NarratorValidationError(report, attempts=4)
    assert err.attempts == 4
    assert err.report is report
    assert "9999" in str(err)
    assert "4 attempt" in str(err)
