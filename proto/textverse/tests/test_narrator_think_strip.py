"""Narrator think-strip — the 6c run-#7 live catch as permanent regression.

The Narrator is a reasoning model; un-stripped, its chain-of-thought was
delivered as the head of ASTRA's perception bundle: meta-vocabulary
(`wall-clock`, `LLM`) into the leak scanner (no_leak 0.105 that run),
`<state>` displaced (state_coherent 0.182), think-side numerics (`-5`)
tripping the calculator-bound validator into 4-attempt retry loops
(fallback rate 0.129). Closed at the narrator seam with the same rules
the ASTRA path uses: last-`</think>` strip; unclosed fails CLOSED.
"""

from __future__ import annotations

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import SessionTrace, TurnOrchestrator
from astra.harness.replay import (
    replay_bundle_from_trace,
    replay_narrator_bundle_from_trace,
)
from astra.judge import build_turn_record
from astra.judge.lcp import LCPRunner
from astra.llm import AstraBundle, NarratorBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.llm.narrator_bundle import NarratorValidationError, _strip_reasoning
from astra.state_bus import StateBus

# The observed live emission shape (run #7, watch_47_morning turn 1),
# abbreviated: cognition first — with constraint vocabulary and numerics —
# then the actual bundle.
LIVE_SHAPE = (
    "<think>\nThinking Process:\n"
    "1. **Analyze the Request:** Role: Narrator (not ASTRA). "
    "Constraints: no wall-clock, calculator-bound, LLM output rules, "
    "metabolic epsilon 1e-5, so -5 in the exponent.\n</think>\n\n"
    "<state>\nquiet watch. regime REST near origin.\n</state>\n\n"
    "<somatic>\nthird harmonic warm.\n</somatic>\n\n"
    "<recent>\n</recent>\n\n"
    "<operator>\nmorning.\n</operator>"
)

UNCLOSED = "<think>\nall cognition, tag never closes. drift -5."


def test_strip_delivers_bundle_only() -> None:
    delivered = _strip_reasoning(LIVE_SHAPE)
    assert delivered.startswith("<state>")
    assert "wall-clock" not in delivered
    assert "LLM" not in delivered
    assert "-5" not in delivered


def test_unclosed_think_fails_closed() -> None:
    assert _strip_reasoning(UNCLOSED) == ""


class _ScriptedClient(LLMClient):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = responses
        self.calls = 0

    async def chat_complete(
        self, user_text: str, params: SamplingParams | None = None,
    ) -> str:
        self.calls += 1
        return self.responses[min(self.calls, len(self.responses)) - 1]

    async def health(self) -> bool:
        return True


def _narrator(responses: list[str]) -> NarratorBundle:
    nb = NarratorBundle(base_url="http://stub", sysprompt="stub")
    nb.client = _ScriptedClient(responses)  # type: ignore[assignment]
    return nb


@pytest.mark.asyncio
async def test_think_numerics_do_not_trigger_retry() -> None:
    """The spurious-retry driver from run #7: `-5` lives in cognition, the
    delivered bundle is numeric-free — ONE call suffices."""
    nb = _narrator([LIVE_SHAPE])
    out = await nb.compose("compose.", trace_pool=["state json here"])
    client = nb.client
    assert isinstance(client, _ScriptedClient)
    assert client.calls == 1
    assert out.startswith("<state>")


@pytest.mark.asyncio
async def test_all_cognition_attempts_raise_and_fall_back() -> None:
    """Unclosed think on every attempt: nothing deliverable → error → the
    orchestrator falls back to the template path with the reason recorded."""
    nb = _narrator([UNCLOSED])
    with pytest.raises(NarratorValidationError):
        await nb.compose("compose.", trace_pool=["pool"])

    astra = AstraBundle(base_url="http://stub", sysprompt="stub")
    astra.client = _ScriptedClient(["Quiet."])  # type: ignore[assignment]
    orch = TurnOrchestrator(
        state_bus=StateBus(
            astra_coord=AstraCoord(sx=0, sy=0, sz=0),
            time=TimeState(t_cosmic=1.5e10, tau_ship=684_000.0,
                           tau_crew_biological=684_000.0),
        ),
        astra_bundle=astra,
        narrator_bundle=_narrator([UNCLOSED]),
    )
    result = await orch.run_turn("morning.")
    assert result.narrator_fallback_reason
    assert "<state>" in result.perception_bundle  # template took over


@pytest.mark.asyncio
async def test_stripped_narrator_session_still_replays() -> None:
    """The trace stores RAW narrator utterances (think included); replay
    re-strips deterministically and lands on the same digest."""
    astra = AstraBundle(base_url="http://stub", sysprompt="stub")
    astra.client = _ScriptedClient(["Quiet up here."])  # type: ignore[assignment]
    trace = SessionTrace()
    orch = TurnOrchestrator(
        state_bus=StateBus(
            astra_coord=AstraCoord(sx=0, sy=0, sz=0),
            time=TimeState(t_cosmic=1.5e10, tau_ship=684_000.0,
                           tau_crew_biological=684_000.0),
        ),
        astra_bundle=astra,
        narrator_bundle=_narrator([LIVE_SHAPE]),
        trace=trace,
    )
    lcp = LCPRunner("strip_replay")
    result = await orch.run_turn("morning.")
    record = build_turn_record(
        turn=result,
        lcp_turn=lcp.evaluate_turn(
            turn=result, state_bus=orch.state_bus, operator_text="morning.",
        ),
        operator_text="morning.",
    )
    # Raw (un-stripped) utterance is what the trace receipts:
    assert "-5" in trace.utterances("narrator")[0].payload

    from astra.harness.replay import declared_state_digest

    live_digest = declared_state_digest([record])

    orch2 = TurnOrchestrator(
        state_bus=StateBus(
            astra_coord=AstraCoord(sx=0, sy=0, sz=0),
            time=TimeState(t_cosmic=1.5e10, tau_ship=684_000.0,
                           tau_crew_biological=684_000.0),
        ),
        astra_bundle=replay_bundle_from_trace(trace),
        narrator_bundle=replay_narrator_bundle_from_trace(trace),
    )
    lcp2 = LCPRunner("strip_replay")
    result2 = await orch2.run_turn("morning.")
    record2 = build_turn_record(
        turn=result2,
        lcp_turn=lcp2.evaluate_turn(
            turn=result2, state_bus=orch2.state_bus, operator_text="morning.",
        ),
        operator_text="morning.",
    )
    assert declared_state_digest([record2]) == live_digest
