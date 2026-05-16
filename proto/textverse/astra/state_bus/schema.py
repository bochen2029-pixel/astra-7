"""StateBus Layer 0 schema per spec v0.128 §4.2.

The State Bus is the world's truth. Frame-coherent reads, atomic writes at
frame boundary, double-buffered conceptually (textverse implements this as
immutable Pydantic snapshots; each turn produces a new StateBus).

Layout follows ARCHITECTURE.md §6.1 with one correction: `bh_list` lives at
StateBus root level per v0.128 §4.2 (the §6.1 sketch nested it inside
TimeState). This is a sketch/spec divergence resolved in favor of v0.128 §4.2.

**State coherence type system (2026-05-16, audit D3+D4+G4+G5 closure):**
- `WarpState` is a first-class Pydantic model at StateBus root.
- `cryosleep_active` is a root bool.
- `regime` is a `@computed_field` on StateBus — never a settable field.
  Algorithm in `astra.core.detect_regime.detect_regime`.
- This resolves audit R1 ambiguity (§4.2 vs §4.4) in favor of
  computed-from-truth: the schema cannot construct an incoherent
  state (e.g. WARP_CRUISE bit with zero rapidity) because the bit is
  always derived from the underlying fields.

All sub-models are frozen. A turn produces a new StateBus; no mutation of
prior snapshots leaks.
"""

from __future__ import annotations

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from astra.core.astra_coord import AstraCoord
from astra.core.detect_regime import detect_regime
from astra.core.regime import Regime
from astra.core.time_state import TimeState


class BHRecord(BaseModel):
    """Black hole record. Schwarzschild only in v0.1; Kerr J=0 by design."""

    model_config = ConfigDict(frozen=True)

    mass_kg: float = Field(gt=0.0)
    position: AstraCoord
    j_angular_momentum: float = 0.0  # Kerr deferred to Phase 5+ per spec §7.5


class WarpState(BaseModel):
    """Warp drive state per spec v0.128 §4.2 / §4.6 (audit D3 closure).

    `W` is the warp coil intensity (0.0 = inactive, 1.0 = max cruise).
    `phase` selects which WARP_* bit composes into Regime:
        charging → WARP_CHARGE
        cruising → WARP_CRUISE
        dropping → WARP_SHUTDOWN
        shutdown → WARP_SHUTDOWN (post-jump cooldown)
    `charge_progress` (0.0-1.0) tracks pre-engagement coil charge state
    during the `charging` phase. Ignored in other phases (informational only).
    """

    model_config = ConfigDict(frozen=True)

    W: float = Field(ge=0.0, le=1.0)
    phase: Literal["charging", "cruising", "dropping", "shutdown"]
    charge_progress: float = Field(ge=0.0, le=1.0, default=0.0)


class CosmologicalParams(BaseModel):
    """Cosmological constants per spec v0.128 §4.2 (NEW v0.127).

    Flat ΛCDM: Ω_m + Ω_Λ ≡ 1. Default values are provisional.
    """

    model_config = ConfigDict(frozen=True)

    c: float = 299_792_458.0    # m/s, exact by SI definition
    h0_kms_mpc: float = 70.0    # km/s/Mpc, provisional
    omega_m: float = 0.3        # matter density parameter, provisional
    omega_lambda: float = 0.7   # dark energy density parameter, provisional

    @model_validator(mode="after")
    def _flat_lambda_cdm(self) -> Self:
        if abs((self.omega_m + self.omega_lambda) - 1.0) > 1e-9:
            raise ValueError(
                f"Flat ΛCDM violated: Ω_m + Ω_Λ = "
                f"{self.omega_m + self.omega_lambda}, expected 1.0 "
                f"(spec v0.128 §4.2)"
            )
        return self


class ChaosFieldSummary(BaseModel):
    """v0 placeholder summary of the chaos field χ(x,t).

    Full PDE state lives in proto/astra_nexus (Rig 1) and is not mirrored
    in textverse. This summary carries scalars sufficient for perception
    bundle assembly and audio extraction.
    """

    model_config = ConfigDict(frozen=True)

    mean_amplitude: float = 0.0
    max_amplitude: float = 0.0
    energy_density: float = 0.0


class KeplerianElements(BaseModel):
    """Two-body orbital elements. Solved on t_cosmic by proto/astra_nexus."""

    model_config = ConfigDict(frozen=True)

    a: float = Field(gt=0.0)            # semi-major axis (m)
    e: float = Field(ge=0.0, lt=1.0)    # eccentricity (bound orbits only in v0)
    period_s: float = Field(gt=0.0)     # orbital period (s)
    parent: str                          # name of parent body in StateBus


class BodyState(BaseModel):
    """Procedural body record per StateBus.procedural_body_states[name].

    Exactly one of `position` (static, meters in macro-grid frame) or
    `kepler` (orbiting). Day 5 universe loader resolves these to AstraCoord
    at query time; Day 1 carries the source-of-truth shape.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    kind: Literal["star", "planet", "moon", "asteroid"]
    mass_kg: float = Field(gt=0.0)
    position: tuple[float, float, float] | None = None
    kepler: KeplerianElements | None = None

    @model_validator(mode="after")
    def _exactly_one_position_source(self) -> Self:
        if (self.position is None) == (self.kepler is None):
            raise ValueError(
                f"BodyState '{self.name}' must have exactly one of "
                f"`position` or `kepler` (not both, not neither)"
            )
        return self


class StateBus(BaseModel):
    """Layer 0 single source of truth per spec v0.128 §4.2.

    Frozen per spec §1.5: each turn produces a new snapshot; no mutation
    of a prior frame is possible. Reads at turn start are frame-coherent
    by construction (the snapshot is the read).

    `regime` is a computed_field — never appears in `model_fields`,
    only in `model_computed_fields`. The schema cannot construct
    incoherent state because regime is always derived from the
    underlying `warp` / `cryosleep_active` / `time.rapidity_zeta`
    fields. grav_factor defaults to 1.0; will be computed from
    `bh_list` + `astra_coord` in a follow-up commit per audit Tier 2.
    """

    model_config = ConfigDict(frozen=True)

    astra_coord: AstraCoord
    time: TimeState
    warp: WarpState | None = None
    cryosleep_active: bool = False
    hull_damage: dict[str, float] = Field(default_factory=dict)
    chaos_field_summary: ChaosFieldSummary = Field(default_factory=ChaosFieldSummary)
    power_allocation: dict[str, float] = Field(default_factory=dict)
    procedural_body_states: dict[str, BodyState] = Field(default_factory=dict)
    bh_list: list[BHRecord] = Field(default_factory=list)
    cosmo_params: CosmologicalParams = Field(default_factory=CosmologicalParams)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def regime(self) -> Regime:
        """Composite Regime per spec §3.3, derived from underlying state.

        Algorithm in `astra.core.detect_regime.detect_regime`. Never
        settable — the schema cannot construct an incoherent state.
        """
        # grav_factor defaults to 1.0 here; the bh_list + position →
        # Schwarzschild composition is computed by C++ astra_nexus.
        # Follow-up commit will plumb the computed grav_factor through.
        return detect_regime(
            rapidity_zeta=self.time.rapidity_zeta,
            warp=self.warp,
            cryosleep_active=self.cryosleep_active,
        )
