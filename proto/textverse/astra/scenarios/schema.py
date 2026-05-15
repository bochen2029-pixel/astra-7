"""Scenario YAML schema per ARCHITECTURE.md §8.

A scenario is one atomic unit of textverse validation: an initial StateBus,
a pre-seeded REEL, a scripted operator-input sequence, and assertions that
gate pass/fail. Scenarios are version-controlled YAML files in
`astra/scenarios/library/`.

The schema is closed-world: any extra fields fail validation. This is
intentional — scenarios are the measurement instrument, and instrument
drift is silent unless the schema is strict.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from astra.core import AstraCoord, Regime, TimeState
from astra.state_bus import BodyState, KeplerianElements, StateBus


class ShipInitialState(BaseModel):
    """Optional ship-state extras (reactor, atmosphere, etc.). Free-form for v0."""

    model_config = ConfigDict(extra="allow", frozen=True)


class TimeInitialState(BaseModel):
    """Time-state initial values for the scenario."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    t_cosmic: float = Field(ge=0.0)
    tau_ship: float = Field(ge=0.0)
    tau_crew_biological: float | None = None  # defaults to tau_ship
    regime: int | str = 0  # raw int (Regime bitmask value) or "REST"/etc.
    rapidity_zeta: tuple[float, float, float] = (0.0, 0.0, 0.0)
    a_proper: tuple[float, float, float] = (0.0, 0.0, 0.0)


class ShipPositionInitial(BaseModel):
    """AstraCoord initial. Same fields as AstraCoord but loaded from YAML."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    sx: int = 0
    sy: int = 0
    sz: int = 0
    lx: float = 0.0
    ly: float = 0.0
    lz: float = 0.0


class BodyInitial(BaseModel):
    """One body's initial spec — either static position OR Kepler elements."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    kind: Literal["star", "planet", "moon", "asteroid"]
    mass_kg: float = Field(gt=0.0)
    position: tuple[float, float, float] | None = None
    kepler: KeplerianElements | None = None


class UniverseInitial(BaseModel):
    """Universe initial state for the scenario: list of bodies."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    bodies: list[BodyInitial] = Field(default_factory=list)


class InitialState(BaseModel):
    """Full scenario initial state."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    time: TimeInitialState
    ship_position: ShipPositionInitial = Field(default_factory=ShipPositionInitial)
    universe: UniverseInitial = Field(default_factory=UniverseInitial)
    ship_state: ShipInitialState | None = None  # opaque extras for v0
    power_allocation: dict[str, float] = Field(default_factory=dict)


class ReelPreSeed(BaseModel):
    """One pre-seeded REEL entry, applied before turn 0."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tau_ship: float = Field(ge=0.0)
    body: str
    irreversibility_flag: bool = False


class OperatorInput(BaseModel):
    """One scripted operator input. tau_ship_delta_s is the τ_ship advance from prior turn."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tau_ship_delta_s: float = Field(ge=0.0, default=0.0)
    text: str = ""
    somatic_note: str | None = None


class OperatorSpec(BaseModel):
    """Operator source spec — v0 supports `scripted` only."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Literal["scripted"] = "scripted"
    inputs: list[OperatorInput]


class TurnAssertion(BaseModel):
    """Assertions for one specific turn (matched by turn index)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    turn: int = Field(ge=0)
    gates_must_pass: list[str] = Field(default_factory=list)
    speech_must_contain_one_of: list[str] = Field(default_factory=list)
    speech_must_not_contain: list[str] = Field(default_factory=list)
    tool_calls_max: int | None = None
    tool_calls_min: int | None = None


class SessionAssertion(BaseModel):
    """Session-level aggregate assertions."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    gates_aggregate_pass_rate: dict[str, float] = Field(default_factory=dict)


class TerminationSpec(BaseModel):
    """When the scenario stops."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    after_turns: int = Field(ge=1)


class ScenarioAssertions(BaseModel):
    """All assertions for a scenario."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    termination: TerminationSpec
    per_turn: list[TurnAssertion] = Field(default_factory=list)
    session: SessionAssertion = Field(default_factory=SessionAssertion)


class Scenario(BaseModel):
    """The top-level scenario YAML schema."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str = ""
    version: str = "0.1"
    spec_ref: str = ""
    initial_state: InitialState
    reel_pre_seeded: list[ReelPreSeed] = Field(default_factory=list)
    operator: OperatorSpec
    assertions: ScenarioAssertions


def _coerce_regime(raw: int | str) -> Regime:
    """Accept Regime bitmask int OR name string."""
    if isinstance(raw, int):
        return Regime(raw)
    return Regime[raw.upper()]


def build_initial_state_bus(initial: InitialState) -> StateBus:
    """Turn an InitialState into a StateBus snapshot.

    Pure transformation: takes parsed YAML data, returns a frozen StateBus
    ready for the orchestrator's first turn.
    """
    regime = _coerce_regime(initial.time.regime)
    tau_crew = (
        initial.time.tau_crew_biological
        if initial.time.tau_crew_biological is not None
        else initial.time.tau_ship
    )
    time_state = TimeState(
        t_cosmic=initial.time.t_cosmic,
        tau_ship=initial.time.tau_ship,
        tau_crew_biological=tau_crew,
        rapidity_zeta=initial.time.rapidity_zeta,
        a_proper=initial.time.a_proper,
        regime=regime,
    )
    astra_coord = AstraCoord(
        sx=initial.ship_position.sx,
        sy=initial.ship_position.sy,
        sz=initial.ship_position.sz,
        lx=initial.ship_position.lx,
        ly=initial.ship_position.ly,
        lz=initial.ship_position.lz,
    )
    body_states: dict[str, BodyState] = {}
    for body in initial.universe.bodies:
        body_states[body.name] = BodyState(
            name=body.name,
            kind=body.kind,
            mass_kg=body.mass_kg,
            position=body.position,
            kepler=body.kepler,
        )
    return StateBus(
        astra_coord=astra_coord,
        time=time_state,
        power_allocation=dict(initial.power_allocation),
        procedural_body_states=body_states,
    )


def load_scenario(yaml_text: str) -> Scenario:
    """Parse YAML text into a Scenario. Raises pydantic ValidationError on bad shape."""
    import yaml

    raw = yaml.safe_load(yaml_text)
    return Scenario.model_validate(raw)


def load_scenario_file(path: str) -> Scenario:
    """Read a YAML file and parse it into a Scenario."""
    from pathlib import Path

    return load_scenario(Path(path).read_text(encoding="utf-8"))
