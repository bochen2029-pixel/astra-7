"""§4.3.1 Turn-Scheduling — spec-v0.130-DRAFT §2.6 (heartbeat /
interruption / initiative) + the QCR-14 closure (ephemeral maintenance
windows riding the heartbeat) + the time-advance substrate.

Gun R-5's witness runs alongside this file: the pre-asynchrony scenario
suite executes unchanged through the whole landing (full `uv run pytest`),
so a scheduling regression in the existing 20 scenarios cannot land
silently.
"""

from __future__ import annotations

from math import cosh
from pathlib import Path

import pytest

from astra.core import AstraCoord, TimeState
from astra.harness import SessionTrace, TurnOrchestrator
from astra.harness.replay import declared_state_digest, run_model_off_replay
from astra.llm import AstraBundle, SamplingParams
from astra.llm.client import LLMClient
from astra.scenarios import ScenarioRunner, load_scenario_file
from astra.state_bus import StateBus, WarpState
from astra.state_bus.advance import METABOLIC_EPSILON, advance_state_bus

LIBRARY = Path(__file__).parent.parent / "astra" / "scenarios" / "library"

SILENT = "<think>quiet. nothing needs saying.</think>"
BRIEF_NOTE = (
    "<think>third harmonic warmed a half-step. worth one line.</think>\n"
    "Third harmonic came up a half-step. Watching it."
)


class _SeqClient(LLMClient):
    """Stub returning scripted responses in order (house pattern)."""

    def __init__(self, responses: list[str]) -> None:
        super().__init__(base_url="http://stub", sysprompt="stub")
        self.responses = responses
        self.call_index = 0

    async def chat_complete(
        self,
        user_text: str,
        params: SamplingParams | None = None,
    ) -> str:
        idx = min(self.call_index, len(self.responses) - 1)
        self.call_index += 1
        return self.responses[idx]

    async def health(self) -> bool:
        return True


def _bundle(responses: list[str]) -> AstraBundle:
    bundle = AstraBundle(base_url="http://stub", sysprompt="stub")
    bundle.client = _SeqClient(responses)  # type: ignore[assignment]
    return bundle


def _bus(
    *,
    zeta: tuple[float, float, float] = (0.0, 0.0, 0.0),
    warp: WarpState | None = None,
    cryosleep: bool = False,
) -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=100.0,
            tau_crew_biological=100.0,
            rapidity_zeta=zeta,
        ),
        warp=warp,
        cryosleep_active=cryosleep,
    )


def _orch(responses: list[str], **bus_kwargs: object) -> TurnOrchestrator:
    return TurnOrchestrator(
        state_bus=_bus(**bus_kwargs),  # type: ignore[arg-type]
        astra_bundle=_bundle(responses),
    )


# --- advance_state_bus (the scheduling substrate) ----------------------------


def test_advance_rest_cosmic_equals_tau() -> None:
    sb = advance_state_bus(_bus(), 600.0)
    assert sb.time.tau_ship == 700.0
    assert sb.time.t_cosmic == 1.5e10 + 600.0
    assert sb.time.tau_crew_biological == 700.0


def test_advance_stl_dilation_shapes_cosmic() -> None:
    """ω=1: dτ = dt_cosmic/γ ⇒ dt_cosmic = dτ·cosh(1)."""
    sb = advance_state_bus(_bus(zeta=(0.0, 0.0, 1.0)), 600.0)
    assert abs((sb.time.t_cosmic - 1.5e10) - 600.0 * cosh(1.0)) < 1e-6


def test_advance_warp_dilation() -> None:
    """W=1 cruising: dilation 0.5 ⇒ a τ interval costs 2× cosmic time."""
    sb = advance_state_bus(_bus(warp=WarpState(W=1.0, phase="cruising")), 600.0)
    assert abs((sb.time.t_cosmic - 1.5e10) - 1200.0) < 1e-9


def test_advance_cryosleep_metabolic_crew_clock() -> None:
    sb = advance_state_bus(_bus(cryosleep=True), 600.0)
    assert sb.time.tau_ship == 700.0
    assert sb.time.tau_crew_biological == 100.0 + 600.0 * METABOLIC_EPSILON


def test_advance_rejects_negative_and_zero_is_identity() -> None:
    base = _bus()
    with pytest.raises(ValueError, match=">= 0"):
        advance_state_bus(base, -1.0)
    assert advance_state_bus(base, 0.0) is base


# --- heartbeat turns ---------------------------------------------------------


@pytest.mark.asyncio
async def test_heartbeat_rejects_operator_text() -> None:
    orch = _orch([SILENT])
    with pytest.raises(ValueError, match="heartbeat"):
        await orch.run_turn("hello", turn_kind="heartbeat")


@pytest.mark.asyncio
async def test_heartbeat_silence_is_not_initiative() -> None:
    orch = _orch([SILENT])
    result = await orch.run_turn(turn_kind="heartbeat")
    assert result.turn_kind == "heartbeat"
    assert result.stage_output.silence
    assert result.initiative is False
    assert result.reel_writes == []


@pytest.mark.asyncio
async def test_initiative_flag_and_budget() -> None:
    """Speech on a heartbeat = initiation; the third within the window
    exceeds the budget (max 2) and is FLAGGED, never suppressed."""
    orch = _orch([BRIEF_NOTE, BRIEF_NOTE, BRIEF_NOTE])
    r1 = await orch.run_turn(turn_kind="heartbeat")
    orch.advance_time(300.0)
    r2 = await orch.run_turn(turn_kind="heartbeat")
    orch.advance_time(300.0)
    r3 = await orch.run_turn(turn_kind="heartbeat")

    assert r1.initiative and not r1.initiative_budget_exceeded
    assert r2.initiative and not r2.initiative_budget_exceeded
    assert r3.initiative and r3.initiative_budget_exceeded
    assert r3.stage_output.speech  # flagged, not suppressed


# --- interruption (fail-closed) ----------------------------------------------


@pytest.mark.asyncio
async def test_interruption_is_fail_closed() -> None:
    """The cancelled turn delivers nothing, dispatches nothing, writes no
    REEL; forensics retain the raw output; the next turn's perception
    carries the cut-off as state."""
    long_report_with_tool = (
        "<think>full rundown requested.</think>\n"
        '<tool name="sensors.scan">{"region": "all"}</tool>\n'
        "Reactor first. All four poles nominal, third carrying its usual"
    )
    followup = (
        "<think>deck two thump. check it.</think>\nChecking deck two now."
    )
    orch = _orch([long_report_with_tool, followup])

    cancelled = await orch.run_turn(
        "run me through full reactor status.", interrupted=True,
    )
    assert cancelled.interrupted
    assert cancelled.tool_results == []          # nothing dispatched
    assert cancelled.reel_writes == []           # nothing remembered as done
    assert cancelled.stage_output.silence        # nothing delivered
    assert "All four poles" in cancelled.interrupted_forensics
    assert len(orch.reel) == 0

    nxt = await orch.run_turn("what was that sound on deck two?")
    assert not nxt.interrupted
    assert "interrupted mid-emission" in nxt.perception_bundle
    assert "Checking deck two" in nxt.stage_output.speech


# --- §4.9 maintenance windows ride the heartbeat (QCR-14) --------------------


@pytest.mark.asyncio
async def test_consolidator_rides_heartbeat() -> None:
    reply = "<think>ack.</think>\nHolding steady."
    orch = _orch([reply, reply, reply, SILENT])
    for text in ("status?", "still fine?", "good. carry on."):
        await orch.run_turn(text)
    # 3 exchanges = 6 conversation turns >= CONSOLIDATE_MIN_WINDOW_TURNS
    hb = await orch.run_turn(turn_kind="heartbeat")

    assert any(run.startswith("consolidator:") for run in hb.ephemeral_runs)
    assert any(
        e.author_instance_id == "consolidator" for e in orch.reel.entries
    )
    assert any(
        e.author_instance_id == "consolidator" for e in hb.reel_writes
    )


@pytest.mark.asyncio
async def test_drift_detector_rides_heartbeat_on_leaks() -> None:
    leaky = "<think>slip.</think>\nDiagnostics again on Tuesday."
    orch = _orch([leaky, SILENT, SILENT])
    first = await orch.run_turn("when do you run diagnostics?")
    assert first.speech_leaks  # the planted weekday fired the detector

    hb = await orch.run_turn(turn_kind="heartbeat")
    assert any(run.startswith("drift_detector:") for run in hb.ephemeral_runs)

    # Counter reset: a clean follow-up heartbeat runs no drift check.
    hb2 = await orch.run_turn(turn_kind="heartbeat")
    assert not any(r.startswith("drift_detector:") for r in hb2.ephemeral_runs)


# --- runner integration + replay across scheduling ---------------------------


@pytest.mark.asyncio
async def test_heartbeat_scenario_runs_and_advances_time() -> None:
    scenario = load_scenario_file(str(LIBRARY / "heartbeat_quiet_watch.yaml"))
    responses = [
        "<think>he's settling in. no reply needed beyond presence.</think>\nCarrying on.",
        SILENT,
        SILENT,
        SILENT,
    ]
    runner = ScenarioRunner(
        scenario=scenario, astra_bundle=_bundle(responses), write_artifacts=False,
    )
    report = await runner.run()
    assert report.passed, [a.failures for a in report.turn_assertions if not a.passed]
    assert report.turn_records[1].turn_kind == "heartbeat"
    assert report.turn_records[1].operator_text == ""


@pytest.mark.asyncio
async def test_interruption_scenario_fail_closed_end_to_end() -> None:
    scenario = load_scenario_file(str(LIBRARY / "interruption_mid_report.yaml"))
    responses = [
        (
            "<think>full rundown.</think>\n"
            '<tool name="sensors.scan">{"region": "all"}</tool>\n'
            "Reactor first. All four poles nominal"
        ),
        "<think>thump on deck two.</think>\nChecking deck two now. Transient, low amplitude.",
    ]
    runner = ScenarioRunner(
        scenario=scenario, astra_bundle=_bundle(responses), write_artifacts=False,
    )
    report = await runner.run()
    assert report.passed, [a.failures for a in report.turn_assertions if not a.passed]
    assert report.turn_records[0].interrupted
    assert report.turn_records[0].tool_calls == []
    assert "deck two" in report.turn_records[1].speech.lower()


@pytest.mark.asyncio
async def test_model_off_replay_covers_scheduling() -> None:
    """Item-1 × item-2 composition: a session with heartbeats, an advance
    ladder, and maintenance work replays byte-identically from its trace."""
    scenario = load_scenario_file(str(LIBRARY / "heartbeat_quiet_watch.yaml"))
    responses = [
        "<think>settling.</think>\nCarrying on.",
        BRIEF_NOTE,
        SILENT,
        SILENT,
    ]
    trace = SessionTrace()
    live = await ScenarioRunner(
        scenario=scenario,
        astra_bundle=_bundle(responses),
        write_artifacts=False,
        session_trace=trace,
    ).run()

    replay = await run_model_off_replay(scenario, trace)
    assert declared_state_digest(replay.turn_records) == declared_state_digest(
        live.turn_records,
    )
