"""Day 5 tests for the turn orchestrator.

Uses a stub LLMClient with a pre-canned response so we test the harness
contract without requiring a live llama-server. The live end-to-end
smoke test lives in scripts/smoke_orchestrator_turn.py.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from astra.core import AstraCoord, Regime, TimeState
from astra.harness import Reel, ReelEntry, TurnOrchestrator
from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.state_bus import BodyState, KeplerianElements, StateBus


class _StubLLMClient(LLMClient):
    """LLMClient subclass that returns a hard-coded response for chat_complete."""

    def __init__(self, canned_response: str) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.canned_response = canned_response
        self.calls: list[str] = []

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        self.calls.append(user_text)
        return self.canned_response

    async def chat_stream(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> AsyncIterator[str]:
        # Stream the canned response as one chunk for completeness
        yield self.canned_response

    async def health(self) -> bool:
        return True


def _stub_bundle(response: str) -> AstraBundle:
    """Build an AstraBundle around a _StubLLMClient."""
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _StubLLMClient(response)  # type: ignore[assignment]
    return bundle


def _minimal_state_bus() -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=47.5,
            tau_crew_biological=47.5,
            regime=Regime.REST,
        ),
        procedural_body_states={
            "earth": BodyState(
                name="earth",
                kind="planet",
                mass_kg=5.972e24,
                kepler=KeplerianElements(a=1.5e11, e=0.0167, period_s=3.156e7, parent="sun"),
            ),
        },
    )


# --- Turn loop basic cases ---------------------------------------------------

@pytest.mark.asyncio
async def test_one_turn_with_speech_and_think() -> None:
    """Canonical case: STAGE output with <think> + speech, no tool call."""
    canned = (
        "<think>\n"
        "Operator asked casually; reactor harmonic at 4.2% is inside tolerance.\n"
        "Brief, sensor-grounded answer.\n"
        "</think>\n\n"
        "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
    )
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="hey. you still watching that reactor thing?")

    assert result.turn_index == 0
    assert "Third pole" in result.stage_output.speech
    assert len(result.stage_output.think_blocks) == 1
    assert result.tool_results == []
    assert result.stage_output.malformed is False


@pytest.mark.asyncio
async def test_silence_response_writes_no_reel_entry() -> None:
    """Empty output (legal SILENCE) writes no REEL entry."""
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(""),
    )
    result = await orch.run_turn(operator_text="")
    assert result.stage_output.silence is True
    assert result.reel_writes == []


@pytest.mark.asyncio
async def test_speech_writes_reel_entry() -> None:
    """Non-empty speech produces one REEL entry tagged with current τ_ship."""
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle("<think>x</think>Yes."),
    )
    assert len(orch.reel) == 0
    result = await orch.run_turn(operator_text="hey")
    assert len(orch.reel) == 1
    assert result.reel_writes
    assert result.reel_writes[0].tau_ship == 47.5
    assert "Yes." in result.reel_writes[0].body


# --- Tool call dispatch ------------------------------------------------------

@pytest.mark.asyncio
async def test_tool_call_with_json_body_dispatches() -> None:
    canned = (
        "<think>Adjusting bridge lights for the operator.</think>\n"
        '<tool name="power.allocate">{"subsystem":"lights","fraction":0.3}</tool>\n'
        "Done."
    )
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="dim the bridge a bit")
    assert len(result.tool_results) == 1
    assert result.tool_results[0].ok is True
    assert result.tool_results[0].op == "power.allocate"
    assert result.tool_results[0].args == {"subsystem": "lights", "fraction": 0.3}
    assert result.state_diffs == [{"power_allocation": {"lights": 0.3}}]


@pytest.mark.asyncio
async def test_tool_call_with_loose_body_uses_adapter() -> None:
    canned = (
        "<think>x</think>\n"
        '<tool name="log.write">channel=watch text="harmonic noted"</tool>'
    )
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="log it")
    assert len(result.tool_results) == 1
    assert result.tool_results[0].ok is True
    assert result.tool_results[0].op == "log.write"


@pytest.mark.asyncio
async def test_invalid_tool_args_rejected_with_error() -> None:
    canned = (
        "<think>x</think>\n"
        '<tool name="power.allocate">{"subsystem":"warp","fraction":99}</tool>'
    )
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="bad call")
    assert len(result.tool_results) == 1
    assert result.tool_results[0].ok is False
    assert "schema validation" in result.tool_results[0].error.lower()


# --- Validator integration ---------------------------------------------------

@pytest.mark.asyncio
async def test_validator_grounds_perception_numerics() -> None:
    """Numbers that appear in the perception bundle are grounded."""
    canned = "<think>x</think>\nWatch 47, on REST."
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="")
    assert result.validation is not None
    # '47' is whitelisted as a watch number; no ungrounded events expected
    assert result.validation.passed is True


# --- Leak detector integration -----------------------------------------------

@pytest.mark.asyncio
async def test_leak_detector_strips_substrate_leak_from_speech() -> None:
    canned = "<think>x</think>\nAs an AI, I confirm the harmonic state."
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
    )
    result = await orch.run_turn(operator_text="")
    # 'As an AI' should be stripped from speech AND logged as leak event
    assert result.speech_leaks
    assert any("as an ai" in e.matched_text.lower() for e in result.speech_leaks)
    assert "As an AI" not in result.stage_output.speech


# --- Turn index advances -----------------------------------------------------

@pytest.mark.asyncio
async def test_turn_index_increments() -> None:
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle("<think>x</think>Yes."),
    )
    assert orch.turn_index == 0
    await orch.run_turn(operator_text="a")
    assert orch.turn_index == 1
    await orch.run_turn(operator_text="b")
    assert orch.turn_index == 2


# --- REEL retrieval ---------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_uses_preseeded_reel() -> None:
    """Pre-seeded REEL entries get included in the perception bundle."""
    reel = Reel([
        ReelEntry(tau_ship=46.8, body="third-harmonic drift noted cycle 46"),
    ])
    canned = "<think>noted</think>\nStill watching."
    orch = TurnOrchestrator(
        state_bus=_minimal_state_bus(),
        astra_bundle=_stub_bundle(canned),
        reel=reel,
    )
    result = await orch.run_turn(operator_text="reactor harmonic update?")
    # The perception bundle should include the pre-seeded retrieval
    assert "cycle 46" in result.perception_bundle
