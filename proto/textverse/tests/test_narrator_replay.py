"""Narrator-path trace + Model-Off Replay (6c — closes the replay
module's named v0 scope limit: "replaying the Narrator's internal retry
loop is future work").

Every narrator completion — retry attempts included — is an oracle event
receipted via TracingLLMClient; replay reconstructs a NarratorBundle
answering from the trace. The retry loop replays deterministically
because the calculator-bound validator is a pure function of
(output, pool). Planted witnesses: tampered narrator context hash and
the fallback path both reproduce.
"""

from __future__ import annotations

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import SessionTrace, TurnOrchestrator
from astra.harness.replay import (
    ReplayDivergenceError,
    declared_state_digest,
    replay_narrator_bundle_from_trace,
    run_model_off_replay,
)
from astra.judge import build_turn_record
from astra.judge.lcp import LCPRunner
from astra.llm import AstraBundle, NarratorBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.state_bus import StateBus

# A numeric-free narrator bundle: passes hard calculator-bound validation
# against any pool (no numeric tokens to ground).
CLEAN_BUNDLE = (
    "<state>\nquiet watch. regime REST near origin.\n</state>\n\n"
    "<somatic>\nthird harmonic warm.\n</somatic>\n\n"
    "<recent>\n</recent>\n\n"
    "<operator>\nhow does it look?\n</operator>"
)
# An ungrounded numeric ("7734" appears in no pool text) forces a hard
# validator failure → retry (or fallback when every attempt fails).
DIRTY_BUNDLE = CLEAN_BUNDLE.replace("quiet watch.", "quiet watch. drift 7734.")


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


def _bus() -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(t_cosmic=1.5e10, tau_ship=684_000.0,
                       tau_crew_biological=684_000.0),
    )


def _bundles(
    astra_responses: list[str],
    narrator_responses: list[str],
) -> tuple[AstraBundle, NarratorBundle]:
    astra = AstraBundle(base_url="http://stub", sysprompt="stub")
    astra.client = _ScriptedClient(astra_responses)  # type: ignore[assignment]
    narrator = NarratorBundle(base_url="http://stub", sysprompt="stub")
    narrator.client = _ScriptedClient(narrator_responses)  # type: ignore[assignment]
    return astra, narrator


async def _record_session(
    narrator_responses: list[str],
    turns: int = 2,
) -> tuple[SessionTrace, str]:
    """Run a narrator-wired session; return (trace, declared digest)."""
    astra, narrator = _bundles(
        ["Quiet up here.", "Still quiet.", "Holding."], narrator_responses,
    )
    trace = SessionTrace()
    orch = TurnOrchestrator(
        state_bus=_bus(), astra_bundle=astra,
        narrator_bundle=narrator, trace=trace,
    )
    lcp = LCPRunner("narrator_replay_test")
    records = []
    for i in range(turns):
        result = await orch.run_turn(f"turn {i} check.")
        lcp_turn = lcp.evaluate_turn(
            turn=result, state_bus=orch.state_bus, operator_text=f"turn {i} check.",
        )
        records.append(
            build_turn_record(turn=result, lcp_turn=lcp_turn,
                              operator_text=f"turn {i} check."),
        )
    return trace, declared_state_digest(records)


@pytest.mark.asyncio
async def test_narrator_utterances_are_receipted() -> None:
    trace, _ = await _record_session([CLEAN_BUNDLE])
    narrator_utts = trace.utterances("narrator")
    assert len(narrator_utts) == 2  # one compose per turn, no retries
    assert all(u.context_sha256 for u in narrator_utts)
    # model_id propagates from the INNER client (the stub's default name);
    # a real NarratorBundle client carries "narrator" here.
    assert all(u.model_id == "default" for u in narrator_utts)
    assert len(trace.utterances("astra")) == 2


@pytest.mark.asyncio
async def test_retry_attempts_are_receipted_too() -> None:
    """Attempt 1 fails hard validation (ungrounded numeric) → retry;
    BOTH utterances must be in the trace or replay cannot reproduce."""
    trace, _ = await _record_session([DIRTY_BUNDLE, CLEAN_BUNDLE], turns=1)
    narrator_utts = trace.utterances("narrator")
    assert len(narrator_utts) == 2
    assert "7734" in narrator_utts[0].payload
    assert "7734" not in narrator_utts[1].payload


def test_replay_narrator_bundle_none_without_narrator_records() -> None:
    assert replay_narrator_bundle_from_trace(SessionTrace()) is None


class _StubTurnHarness:
    """Minimal record→replay comparison via the orchestrator directly
    (scenario-file-free): replays with trace-backed bundles and compares
    the declared digest."""


@pytest.mark.asyncio
async def test_narrator_session_replays_byte_identically() -> None:
    trace, live_digest = await _record_session([CLEAN_BUNDLE])

    # Replay: both bundles answer from the trace; no transport anywhere.
    from astra.harness.replay import replay_bundle_from_trace

    orch = TurnOrchestrator(
        state_bus=_bus(),
        astra_bundle=replay_bundle_from_trace(trace),
        narrator_bundle=replay_narrator_bundle_from_trace(trace),
    )
    lcp = LCPRunner("narrator_replay_test")
    records = []
    for i in range(2):
        result = await orch.run_turn(f"turn {i} check.")
        lcp_turn = lcp.evaluate_turn(
            turn=result, state_bus=orch.state_bus, operator_text=f"turn {i} check.",
        )
        records.append(
            build_turn_record(turn=result, lcp_turn=lcp_turn,
                              operator_text=f"turn {i} check."),
        )
    assert declared_state_digest(records) == live_digest


@pytest.mark.asyncio
async def test_retry_loop_replays_deterministically() -> None:
    """The killer case: live session retried (dirty → clean). Replay
    re-runs the validator on the recorded dirty output, fails identically,
    consumes the clean one, and lands on the same digest."""
    trace, live_digest = await _record_session([DIRTY_BUNDLE, CLEAN_BUNDLE], turns=1)

    from astra.harness.replay import replay_bundle_from_trace

    orch = TurnOrchestrator(
        state_bus=_bus(),
        astra_bundle=replay_bundle_from_trace(trace),
        narrator_bundle=replay_narrator_bundle_from_trace(trace),
    )
    lcp = LCPRunner("narrator_replay_test")
    result = await orch.run_turn("turn 0 check.")
    lcp_turn = lcp.evaluate_turn(
        turn=result, state_bus=orch.state_bus, operator_text="turn 0 check.",
    )
    record = build_turn_record(turn=result, lcp_turn=lcp_turn,
                               operator_text="turn 0 check.")
    assert declared_state_digest([record]) == live_digest


@pytest.mark.asyncio
async def test_fallback_path_replays_and_is_recorded() -> None:
    """Every attempt ungrounded → exhausted retries → template fallback.
    The fallback reason is a declared column and the replay reproduces it."""
    trace, live_digest = await _record_session(
        [DIRTY_BUNDLE, DIRTY_BUNDLE, DIRTY_BUNDLE, DIRTY_BUNDLE], turns=1,
    )
    narrator_utts = trace.utterances("narrator")
    assert len(narrator_utts) >= 2  # every attempt receipted

    from astra.harness.replay import replay_bundle_from_trace

    orch = TurnOrchestrator(
        state_bus=_bus(),
        astra_bundle=replay_bundle_from_trace(trace),
        narrator_bundle=replay_narrator_bundle_from_trace(trace),
    )
    lcp = LCPRunner("narrator_replay_test")
    result = await orch.run_turn("turn 0 check.")
    assert result.narrator_fallback_reason  # fell back live AND on replay
    lcp_turn = lcp.evaluate_turn(
        turn=result, state_bus=orch.state_bus, operator_text="turn 0 check.",
    )
    record = build_turn_record(turn=result, lcp_turn=lcp_turn,
                               operator_text="turn 0 check.")
    assert record.narrator_fallback_reason
    assert declared_state_digest([record]) == live_digest


@pytest.mark.asyncio
async def test_tampered_narrator_context_hash_diverges() -> None:
    """Planted witness: a tampered narrator utterance context hash raises
    ReplayDivergenceError at the exact call."""
    trace, _ = await _record_session([CLEAN_BUNDLE], turns=1)
    tampered_records = []
    for r in trace.records:
        if r.kind == "llm_utterance" and r.role == "narrator":
            tampered_records.append(
                r.model_copy(update={"context_sha256": "0" * 64}),
            )
        else:
            tampered_records.append(r)
    tampered = SessionTrace(tampered_records)

    from astra.harness.replay import replay_bundle_from_trace

    orch = TurnOrchestrator(
        state_bus=_bus(),
        astra_bundle=replay_bundle_from_trace(tampered),
        narrator_bundle=replay_narrator_bundle_from_trace(tampered),
    )
    with pytest.raises(ReplayDivergenceError, match="context divergence"):
        await orch.run_turn("turn 0 check.")


@pytest.mark.asyncio
async def test_run_model_off_replay_accepts_narratorless_trace() -> None:
    """Template-path recordings replay exactly as before through the
    public entry point (narrator bundle resolves to None)."""
    from astra.scenarios import load_scenario_file

    # Cheapest end-to-end check: the public helper still constructs and
    # runs with narrator_bundle=None for a trace with no narrator records.
    scenario = load_scenario_file(
        str(
            __import__("pathlib").Path(__file__).resolve().parents[1]
            / "astra" / "scenarios" / "library" / "silence_operator_murmur.yaml",
        ),
    )
    astra = AstraBundle(base_url="http://stub", sysprompt="stub")
    astra.client = _ScriptedClient(["<think>quiet.</think>"])  # type: ignore[assignment]
    trace = SessionTrace()
    from astra.scenarios import ScenarioRunner

    runner = ScenarioRunner(
        scenario=scenario, astra_bundle=astra,
        write_artifacts=False, session_trace=trace,
    )
    live = await runner.run()
    replayed = await run_model_off_replay(scenario, trace)
    assert declared_state_digest(replayed.turn_records) == declared_state_digest(
        live.turn_records,
    )
