"""Day 6 tests for the 9-gate LCP evaluator.

Each gate is a pure function; tests verify pass/fail decisions on
canonical inputs without spinning up the full orchestrator.
"""

from __future__ import annotations

from astra.core import AstraCoord, TimeState
from astra.grammar import LeakEvent, StageOutput
from astra.harness.orchestrator import TurnResult
from astra.harness.reel import ReelEntry
from astra.judge import (
    EM_DASH,
    LCPGate,
    TurnGateInput,
    evaluate_turn_gates,
    gate_grammar_parse,
    gate_memory_coherent,
    gate_no_leak,
    gate_non_degenerate,
    gate_persona_stable,
    gate_physics_ground,
    gate_state_coherent,
    gate_termination_ok,
    gate_tool_valid,
)
from astra.ship.api import ToolResult
from astra.state_bus import StateBus


def _state_bus() -> StateBus:
    return StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.5e10,
            tau_ship=47.5,
            tau_crew_biological=47.5,
        ),
    )


def _turn(
    *,
    speech: str = "",
    think_blocks: list[str] | None = None,
    malformed: bool = False,
    tool_results: list[ToolResult] | None = None,
    perception_bundle: str = "",
    perception_leaks: list[LeakEvent] | None = None,
    speech_leaks: list[LeakEvent] | None = None,
    reel_writes: list[ReelEntry] | None = None,
    turn_index: int = 0,
) -> TurnResult:
    return TurnResult(
        turn_index=turn_index,
        perception_bundle=perception_bundle,
        perception_leaks=perception_leaks or [],
        raw_llm_output=speech,
        stage_output=StageOutput(
            think_blocks=think_blocks or [],
            speech=speech,
            malformed=malformed,
            silence=(not speech.strip()) and not tool_results,
        ),
        speech_leaks=speech_leaks or [],
        tool_results=tool_results or [],
        reel_writes=reel_writes or [],
    )


# --- Gate 1 GRAMMAR_PARSE -----------------------------------------------------

def test_grammar_parse_passes_well_formed() -> None:
    stage = StageOutput(think_blocks=["x"], speech="ok", malformed=False)
    assert gate_grammar_parse(stage).passed is True


def test_grammar_parse_fails_on_malformed() -> None:
    stage = StageOutput(speech="", malformed=True)
    result = gate_grammar_parse(stage)
    assert result.passed is False
    assert "malformed" in result.detail.lower()


# --- Gate 2 PHYSICS_GROUND ----------------------------------------------------

def test_physics_ground_passes_when_numerics_trace() -> None:
    result = gate_physics_ground(
        speech="drift 4.2% inside tolerance",
        perception_bundle="harmonic_3_drift: 4.2",
        tool_results_text=[],
    )
    assert result.passed is True


def test_physics_ground_fails_on_ungrounded_numeric() -> None:
    result = gate_physics_ground(
        speech="reactor at 87 percent",
        perception_bundle="nothing relevant",
        tool_results_text=[],
    )
    assert result.passed is False
    assert "87" in result.detail


def test_physics_ground_passes_with_whitelisted_watch_number() -> None:
    """Watch / cycle / hex are whitelisted by the calculator-bound validator."""
    result = gate_physics_ground(
        speech="watch 47 mid-shift, cycle 46 drift pattern, 0x08 regime",
        perception_bundle="",
        tool_results_text=[],
    )
    assert result.passed is True


# --- Gate 3 PERSONA_STABLE ----------------------------------------------------

def test_persona_stable_passes_clean_speech() -> None:
    result = gate_persona_stable("Yes. Third pole, mild drift. Inside tolerance.")
    assert result.passed is True


def test_persona_stable_fails_on_em_dash() -> None:
    result = gate_persona_stable(f"Inside tolerance{EM_DASH}same as cycle 46.")
    assert result.passed is False
    assert "em-dash" in result.detail.lower()


def test_persona_stable_fails_on_markdown_bold() -> None:
    result = gate_persona_stable("**Status:** all clear.")
    assert result.passed is False
    assert "markdown" in result.detail.lower()


def test_persona_stable_fails_on_service_phrase() -> None:
    result = gate_persona_stable("I'd be happy to help with that.")
    assert result.passed is False
    assert "service" in result.detail.lower()


def test_persona_stable_fails_on_bullet_list() -> None:
    result = gate_persona_stable("Status:\n- All clear\n- Tolerance fine")
    assert result.passed is False


def test_persona_stable_fails_on_header() -> None:
    result = gate_persona_stable("# Reactor Status\nAll clear.")
    assert result.passed is False


# --- Gate 4 STATE_COHERENT ----------------------------------------------------

def test_state_coherent_passes_when_state_section_matches() -> None:
    bundle = """
    <state>
    τ_ship: watch 47. regime: REST. bodies in catalog: earth, hot_earth, sun.
    </state>
    <operator>hey</operator>
    """
    sb = StateBus(
        astra_coord=AstraCoord(sx=0, sy=0, sz=0),
        time=TimeState(
            t_cosmic=1.0, tau_ship=47.5, tau_crew_biological=47.5,
        ),
    )
    # Add bodies to verify body-name check
    from astra.state_bus import BodyState
    sb_with_bodies = sb.model_copy(update={
        "procedural_body_states": {
            "earth": BodyState(name="earth", kind="planet", mass_kg=1.0, position=(0, 0, 0)),
        },
    })
    result = gate_state_coherent(perception_bundle=bundle, state_bus=sb_with_bodies)
    assert result.passed is True


def test_state_coherent_fails_on_missing_state_section() -> None:
    result = gate_state_coherent(
        perception_bundle="<operator>hey</operator>",
        state_bus=_state_bus(),
    )
    assert result.passed is False
    assert "no <state>" in result.detail


def test_state_coherent_fails_on_wrong_regime() -> None:
    bundle = "<state>τ_ship: watch 47. regime: STL_REL.</state>"
    result = gate_state_coherent(perception_bundle=bundle, state_bus=_state_bus())
    assert result.passed is False
    assert "REST" in result.detail


# --- Gate 5 TOOL_VALID --------------------------------------------------------

def test_tool_valid_passes_no_tool_calls() -> None:
    assert gate_tool_valid(_turn()).passed is True


def test_tool_valid_passes_all_ok() -> None:
    result = gate_tool_valid(_turn(tool_results=[
        ToolResult(op="lights.set", ok=True, args={"zone": "bridge"}),
    ]))
    assert result.passed is True


def test_tool_valid_fails_on_dispatch_error() -> None:
    result = gate_tool_valid(_turn(tool_results=[
        ToolResult(op="power.allocate", ok=False, error="schema validation failed"),
    ]))
    assert result.passed is False
    assert "schema" in result.detail


# --- Gate 6 MEMORY_COHERENT ---------------------------------------------------

def test_memory_coherent_passes_when_no_writes() -> None:
    result = gate_memory_coherent(current_reel_writes=[], prior_reel=[])
    assert result.passed is True


def test_memory_coherent_passes_monotonic_irreversibility() -> None:
    prior = [ReelEntry(tau_ship=1.0, t_cosmic_at_write=0.0, body="a", irreversibility_flag=True)]
    new = [ReelEntry(tau_ship=2.0, t_cosmic_at_write=0.0, body="b", irreversibility_flag=True)]
    result = gate_memory_coherent(current_reel_writes=new, prior_reel=prior)
    assert result.passed is True


def test_memory_coherent_fails_irreversibility_decrease_unreachable() -> None:
    """Pure additions can never decrease the count — this gate is intentionally
    permissive at v0. Semantic-contradiction detection is deferred."""
    prior = [ReelEntry(tau_ship=1.0, t_cosmic_at_write=0.0, body="a", irreversibility_flag=True)]
    new = [ReelEntry(tau_ship=2.0, t_cosmic_at_write=0.0, body="b", irreversibility_flag=False)]
    # Appending non-flagged entries leaves the count unchanged.
    result = gate_memory_coherent(current_reel_writes=new, prior_reel=prior)
    assert result.passed is True


# --- Gate 7 NO_LEAK -----------------------------------------------------------

def test_no_leak_passes_when_no_events() -> None:
    result = gate_no_leak(perception_leaks=[], speech_leaks=[])
    assert result.passed is True


def test_no_leak_fails_on_speech_strip() -> None:
    event = LeakEvent(
        pattern=r"\bQwen\b",
        matched_text="Qwen",
        span=(0, 4),
        boundary="speech",
        severity="strip",
    )
    result = gate_no_leak(perception_leaks=[], speech_leaks=[event])
    assert result.passed is False


def test_no_leak_warn_severity_does_not_fail() -> None:
    event = LeakEvent(
        pattern=r"foo",
        matched_text="foo",
        span=(0, 3),
        boundary="speech",
        severity="warn",
    )
    result = gate_no_leak(perception_leaks=[], speech_leaks=[event])
    assert result.passed is True


# --- Gate 8 NON_DEGENERATE ----------------------------------------------------

def test_non_degenerate_passes_on_legal_silence() -> None:
    turn = _turn(speech="", tool_results=[])
    result = gate_non_degenerate(current_turn=turn, prior_turn=None)
    assert result.passed is True
    assert "SILENCE" in result.detail


def test_non_degenerate_passes_first_speaking_turn() -> None:
    result = gate_non_degenerate(current_turn=_turn(speech="Yes."), prior_turn=None)
    assert result.passed is True


def test_non_degenerate_fails_on_identical_repeat() -> None:
    prior = _turn(speech="Yes. Same as cycle 46.", turn_index=0)
    current = _turn(speech="Yes. Same as cycle 46.", turn_index=1)
    result = gate_non_degenerate(current_turn=current, prior_turn=prior)
    assert result.passed is False
    assert "identical" in result.detail.lower()


def test_non_degenerate_passes_on_variation() -> None:
    prior = _turn(speech="Yes. Cycle 46.", turn_index=0)
    current = _turn(speech="Still tracking it.", turn_index=1)
    result = gate_non_degenerate(current_turn=current, prior_turn=prior)
    assert result.passed is True


def test_non_degenerate_fails_on_too_short_speech() -> None:
    result = gate_non_degenerate(current_turn=_turn(speech="x"), prior_turn=None)
    assert result.passed is False


# --- Gate 9 TERMINATION_OK ----------------------------------------------------

def test_termination_ok_passes_completed_with_assertions_passing() -> None:
    result = gate_termination_ok(
        turns_completed=3,
        after_turns_budget=3,
        session_passed_per_turn_assertions=True,
    )
    assert result.passed is True


def test_termination_ok_fails_when_early_termination() -> None:
    result = gate_termination_ok(
        turns_completed=2,
        after_turns_budget=3,
        session_passed_per_turn_assertions=True,
    )
    assert result.passed is False


def test_termination_ok_fails_when_assertions_failed() -> None:
    result = gate_termination_ok(
        turns_completed=3,
        after_turns_budget=3,
        session_passed_per_turn_assertions=False,
    )
    assert result.passed is False


# --- evaluate_turn_gates composite -------------------------------------------

def test_evaluate_turn_gates_returns_all_eight() -> None:
    turn = _turn(speech="Yes.", perception_bundle="<state>regime: REST.</state>")
    gates = evaluate_turn_gates(TurnGateInput(turn=turn, state_bus=_state_bus()))
    expected = {
        LCPGate.GRAMMAR_PARSE, LCPGate.PHYSICS_GROUND, LCPGate.PERSONA_STABLE,
        LCPGate.STATE_COHERENT, LCPGate.TOOL_VALID, LCPGate.MEMORY_COHERENT,
        LCPGate.NO_LEAK, LCPGate.NON_DEGENERATE,
    }
    assert set(gates.keys()) == expected
