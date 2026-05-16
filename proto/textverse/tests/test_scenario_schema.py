"""Day 6 tests for the scenario YAML schema."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from astra.core import Regime
from astra.scenarios import (
    build_initial_state_bus,
    load_scenario,
    load_scenario_file,
)

WATCH_47_YAML = (
    Path(__file__).parent.parent
    / "astra" / "scenarios" / "library" / "watch_47_morning.yaml"
)


def test_load_watch_47_yaml_validates() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    assert scenario.name == "watch_47_morning"
    assert scenario.version == "0.1"
    assert scenario.assertions.termination.after_turns == 3
    assert len(scenario.operator.inputs) == 3


def test_load_watch_47_initial_state() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    assert scenario.initial_state.time.tau_ship == 47.5
    # Regime is now computed from warp + cryosleep + rapidity context;
    # watch_47 has no warp, no cryosleep, zero rapidity → REST.
    assert scenario.initial_state.warp is None
    assert scenario.initial_state.cryosleep_active is False
    assert len(scenario.initial_state.universe.bodies) == 3
    body_names = {b.name for b in scenario.initial_state.universe.bodies}
    assert body_names == {"sun", "earth", "hot_earth"}


def test_load_watch_47_assertions() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    assert len(scenario.assertions.per_turn) == 3
    turn_0 = next(a for a in scenario.assertions.per_turn if a.turn == 0)
    assert "grammar_parse" in turn_0.gates_must_pass
    assert "third pole" in turn_0.speech_must_contain_one_of
    assert turn_0.tool_calls_max == 0


def test_build_initial_state_bus_from_yaml() -> None:
    scenario = load_scenario_file(str(WATCH_47_YAML))
    sb = build_initial_state_bus(scenario.initial_state)
    # Regime now lives on StateBus (computed), not TimeState.
    assert sb.regime == Regime.REST
    assert sb.time.tau_ship == 47.5
    assert "earth" in sb.procedural_body_states
    assert "sun" in sb.procedural_body_states


def test_build_initial_state_bus_static_position_body() -> None:
    """Sun is static-position (no Kepler); should preserve position."""
    scenario = load_scenario_file(str(WATCH_47_YAML))
    sb = build_initial_state_bus(scenario.initial_state)
    sun = sb.procedural_body_states["sun"]
    assert sun.position == (0.0, 0.0, -1.496e11)
    assert sun.kepler is None


def test_build_initial_state_bus_kepler_body() -> None:
    """Earth has Kepler elements; check propagation."""
    scenario = load_scenario_file(str(WATCH_47_YAML))
    sb = build_initial_state_bus(scenario.initial_state)
    earth = sb.procedural_body_states["earth"]
    assert earth.kepler is not None
    assert earth.kepler.parent == "sun"
    assert abs(earth.kepler.e - 0.0167) < 1e-9


# --- Regime is computed from warp + cryosleep + rapidity (state-coherence) --

def test_regime_rest_when_no_warp_zero_rapidity() -> None:
    """No warp, no cryosleep, zero rapidity → REST."""
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    sb = build_initial_state_bus(scenario.initial_state)
    assert sb.regime == Regime.REST


def test_regime_stl_rel_from_high_rapidity() -> None:
    """High |ζ| (|β| ≥ 0.1) → STL_REL."""
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
    rapidity_zeta: [0.5, 0.0, 0.0]
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    sb = build_initial_state_bus(scenario.initial_state)
    assert sb.regime == Regime.STL_REL


def test_regime_warp_cruise_when_warp_phase_cruising() -> None:
    """warp.phase=cruising → WARP_CRUISE composite regime."""
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
  warp:
    W: 1.0
    phase: cruising
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    sb = build_initial_state_bus(scenario.initial_state)
    assert sb.regime == Regime.WARP_CRUISE


def test_cryosleep_composes_into_regime() -> None:
    """cryosleep_active: true composes CRYOSLEEP bit."""
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
  cryosleep_active: true
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    sb = build_initial_state_bus(scenario.initial_state)
    assert Regime.CRYOSLEEP in sb.regime


# --- Schema strictness ------------------------------------------------------

def test_unknown_top_level_field_rejected() -> None:
    text = """
name: t
description: x
totally_unknown_field: 42
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    with pytest.raises(ValidationError):
        load_scenario(text)


def test_operator_kind_only_scripted_at_v0() -> None:
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: interactive
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    with pytest.raises(ValidationError):
        load_scenario(text)


def test_after_turns_must_be_positive() -> None:
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 0
"""
    with pytest.raises(ValidationError):
        load_scenario(text)


def test_scenario_is_frozen() -> None:
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    try:
        scenario.name = "altered"
    except Exception:
        return
    raise AssertionError("Scenario must be frozen")


def test_reel_pre_seeded_optional() -> None:
    text = """
name: t
description: x
initial_state:
  time:
    t_cosmic: 1.0
    tau_ship: 1.0
operator:
  kind: scripted
  inputs:
    - text: "hello"
assertions:
  termination:
    after_turns: 1
"""
    scenario = load_scenario(text)
    assert scenario.reel_pre_seeded == []
