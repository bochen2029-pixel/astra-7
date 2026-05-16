"""Day 6 tests for LCPRunner aggregation + LCPSessionResult shape."""

from __future__ import annotations

from astra.core import AstraCoord, TimeState
from astra.grammar import StageOutput
from astra.harness.orchestrator import TurnResult
from astra.judge import PER_TURN_GATES, LCPGate, LCPRunner, build_turn_record
from astra.state_bus import StateBus


def _state_bus() -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.0, tau_ship=47.5, tau_crew_biological=47.5,
        ),
    )


def _good_turn(idx: int = 0, speech: str = "Yes.") -> TurnResult:
    return TurnResult(
        turn_index=idx,
        perception_bundle="<state>τ_ship watch 47. regime: REST.</state>",
        perception_leaks=[],
        raw_llm_output=speech,
        stage_output=StageOutput(speech=speech, malformed=False),
        speech_leaks=[],
    )


# --- Single turn -------------------------------------------------------------

def test_runner_evaluates_one_turn() -> None:
    runner = LCPRunner("test_scenario")
    result = runner.evaluate_turn(
        turn=_good_turn(),
        state_bus=_state_bus(),
    )
    assert result.turn_index == 0
    assert set(result.gates.keys()) == set(PER_TURN_GATES)
    assert result.passed is True


def test_runner_passed_property_per_turn() -> None:
    runner = LCPRunner("x")
    turn_result = runner.evaluate_turn(turn=_good_turn(), state_bus=_state_bus())
    assert turn_result.passed is True
    assert turn_result.failed_gates == []


# --- Multi-turn aggregation --------------------------------------------------

def test_runner_aggregates_multiple_turns() -> None:
    runner = LCPRunner("multi")
    for i in range(3):
        runner.evaluate_turn(
            turn=_good_turn(i, f"Yes turn {i}."),
            state_bus=_state_bus(),
        )
    session = runner.finalize(after_turns_budget=3, session_per_turn_assertions_passed=True)
    assert session.turn_count == 3
    assert session.scenario_name == "multi"
    assert session.termination_gate is not None
    assert session.termination_gate.passed is True


def test_session_aggregate_pass_rate() -> None:
    runner = LCPRunner("rates")
    runner.evaluate_turn(turn=_good_turn(0, speech="Yes turn zero."), state_bus=_state_bus())
    runner.evaluate_turn(turn=_good_turn(1, speech="Yes turn one."), state_bus=_state_bus())
    session = runner.finalize(after_turns_budget=2, session_per_turn_assertions_passed=True)
    rates = session.aggregate_pass_rate
    # Pass rate should be 1.0 across the board for two clean turns.
    for gate in PER_TURN_GATES:
        assert rates[gate] == 1.0


def test_session_overall_passed_when_all_pass() -> None:
    runner = LCPRunner("clean")
    runner.evaluate_turn(turn=_good_turn(0), state_bus=_state_bus())
    session = runner.finalize(after_turns_budget=1, session_per_turn_assertions_passed=True)
    assert session.overall_passed is True


def test_session_overall_fails_when_termination_fails() -> None:
    runner = LCPRunner("early_term")
    runner.evaluate_turn(turn=_good_turn(0), state_bus=_state_bus())
    # Budget was 3, we only ran 1 → termination gate fails
    session = runner.finalize(after_turns_budget=3, session_per_turn_assertions_passed=True)
    assert session.overall_passed is False
    assert session.termination_gate is not None
    assert session.termination_gate.passed is False


def test_session_failed_gate_counts() -> None:
    bad_speech = "**Status:** I'd be happy to help."
    runner = LCPRunner("bad")
    bad_turn = _good_turn(0, speech=bad_speech)
    runner.evaluate_turn(turn=bad_turn, state_bus=_state_bus())
    session = runner.finalize(after_turns_budget=1, session_per_turn_assertions_passed=False)
    counts = session.failed_gate_counts
    assert counts[LCPGate.PERSONA_STABLE] == 1


# --- TurnRecord builder ------------------------------------------------------

def test_build_turn_record_includes_all_gate_results() -> None:
    runner = LCPRunner("rec")
    turn = _good_turn(0)
    lcp_turn = runner.evaluate_turn(turn=turn, state_bus=_state_bus())
    record = build_turn_record(
        turn=turn,
        lcp_turn=lcp_turn,
        operator_text="hey",
        latency_s=0.123,
    )
    assert record.turn_index == 0
    assert record.operator_text == "hey"
    assert record.latency_s == 0.123
    assert record.speech == "Yes."
    # Every per-turn gate appears in the lcp_gates dict
    for gate in PER_TURN_GATES:
        assert gate.value in record.lcp_gates
