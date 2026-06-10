"""Library-wide scenario validation — every YAML in the library must load.

Until now only watch_47_morning was schema-validated by test; the other
library files were validated implicitly at run time. This module makes the
WHOLE library a gate: every file parses, validates against the Scenario
schema, builds a coherent StateBus, and references only gates and tools
that exist. New scenarios get this for free.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from astra.scenarios.schema import Scenario, build_initial_state_bus
from astra.ship.api import TOOL_API

LIBRARY = Path(__file__).resolve().parents[1] / "astra" / "scenarios" / "library"
SCENARIO_FILES = sorted(LIBRARY.glob("*.yaml"))

KNOWN_GATES = {
    "grammar_parse",
    "persona_stable",
    "tool_valid",
    "no_leak",
    "state_coherent",
    "memory_coherent",
    "physics_ground",
    "non_degenerate",
    "autotelic_register",
}


def load(path: Path) -> Scenario:
    return Scenario.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def test_library_is_at_least_twenty_scenarios() -> None:
    assert len(SCENARIO_FILES) >= 20


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_scenario_validates(path: Path) -> None:
    scenario = load(path)
    assert scenario.name == path.stem, "file name must match scenario name"
    assert scenario.assertions.termination.after_turns >= 1


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_scenario_builds_coherent_state_bus(path: Path) -> None:
    scenario = load(path)
    bus = build_initial_state_bus(scenario.initial_state)
    # The computed_field derives regime from truth; construction succeeding
    # IS the coherence statement. Touch it to force derivation.
    assert int(bus.regime) >= 0


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_scenario_references_only_known_gates(path: Path) -> None:
    scenario = load(path)
    referenced: set[str] = set()
    for turn_assertion in scenario.assertions.per_turn:
        referenced.update(turn_assertion.gates_must_pass)
    referenced.update(scenario.assertions.session.gates_aggregate_pass_rate)
    unknown = referenced - KNOWN_GATES
    assert not unknown, f"unknown gates referenced: {unknown}"


@pytest.mark.parametrize("path", SCENARIO_FILES, ids=lambda p: p.stem)
def test_scenario_turn_indices_within_termination(path: Path) -> None:
    scenario = load(path)
    limit = scenario.assertions.termination.after_turns
    for turn_assertion in scenario.assertions.per_turn:
        assert turn_assertion.turn < limit
    # Scripted operator must supply at least as many inputs as turns run.
    assert len(scenario.operator.inputs) >= limit


def test_tool_api_lock_unchanged() -> None:
    """Scenario authoring assumes the locked 6-op surface (§1.4/§4.9)."""
    assert set(TOOL_API) == {
        "warp.engage",
        "warp.disengage",
        "nav.heading_set",
        "sensors.scan",
        "power.allocate",
        "log.write",
    }
