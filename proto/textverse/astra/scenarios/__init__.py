"""astra.scenarios — scenario YAML schema + runner.

A scenario is the atomic unit of LCP validation. Each scenario is a YAML
file defining initial_state, reel_pre_seeded, operator inputs, and
assertions. The runner loads, executes against the harness, and produces
a RunReport.

Day 6 lands:
- schema.py:   Pydantic scenario schema + build_initial_state_bus helper
- runner.py:   ScenarioRunner + per-turn assertion checking + RunReport
- library/:    First canonical scenario, watch_47_morning.yaml
"""

from astra.scenarios.runner import (
    RunReport,
    ScenarioRunner,
    TurnAssertionResult,
    summary_for_operator,
)
from astra.scenarios.schema import (
    BodyInitial,
    InitialState,
    OperatorInput,
    OperatorSpec,
    ReelPreSeed,
    Scenario,
    ScenarioAssertions,
    SessionAssertion,
    ShipPositionInitial,
    TerminationSpec,
    TimeInitialState,
    TurnAssertion,
    UniverseInitial,
    build_initial_state_bus,
    load_scenario,
    load_scenario_file,
)

__all__ = [
    "BodyInitial",
    "InitialState",
    "OperatorInput",
    "OperatorSpec",
    "ReelPreSeed",
    "RunReport",
    "Scenario",
    "ScenarioAssertions",
    "ScenarioRunner",
    "SessionAssertion",
    "ShipPositionInitial",
    "TerminationSpec",
    "TimeInitialState",
    "TurnAssertion",
    "TurnAssertionResult",
    "UniverseInitial",
    "build_initial_state_bus",
    "load_scenario",
    "load_scenario_file",
    "summary_for_operator",
]
