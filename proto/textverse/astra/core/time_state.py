"""TimeState — two-clock split + rapidity + regime per spec v0.128 §1.2, §3, §4.4.

- t_cosmic drives Kepler solver, stellar evolution, distant-body AstraCoord
  updates, cryosleep advance, "how old is the universe" queries.
- τ_ship is ASTRA's experiential clock; drives REEL timestamps, audio synth
  rate, conversation history, drift-detector cadence.
- τ_crew_biological derives from τ_ship; pauses on CRYOSLEEP at metabolic ε.

The composition rule (§3.2) is enforced inside proto/astra_nexus — this
module carries the state shape and the rapidity clamp from §3.7.

Frozen per §1.5: each turn produces a new immutable TimeState snapshot.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from astra.core.rapidity import OMEGA_MAX, rapidity_magnitude
from astra.core.regime import Regime


class TimeState(BaseModel):
    """Per spec v0.128 §4.4 Time Contract `state` block.

    Day 1 enforces shape and the static rapidity clamp. Composition-rule
    invariants (dτ/dt ∈ (0,1], γ stable to 4 sig figs, |v⃗| < c, γ ≡ 1 in
    WARP regime) are math invariants enforced by proto/astra_nexus and
    verified via nexus_bridge roundtrip in Day 2.
    """

    model_config = ConfigDict(frozen=True)

    t_cosmic: float = Field(ge=0.0)                          # seconds since epoch zero
    tau_ship: float = Field(ge=0.0)                          # ship proper time
    tau_crew_biological: float = Field(ge=0.0)               # pauses on cryosleep
    rapidity_zeta: tuple[float, float, float] = (0.0, 0.0, 0.0)
    a_proper: tuple[float, float, float] = (0.0, 0.0, 0.0)   # ship-frame, m/s²
    regime: Regime = Regime.REST

    @model_validator(mode="after")
    def _rapidity_clamp(self) -> Self:
        omega = rapidity_magnitude(self.rapidity_zeta)
        if omega > OMEGA_MAX:
            raise ValueError(
                f"Rapidity |ζ⃗| = {omega:.6f} exceeds clamp ω_max ≈ {OMEGA_MAX} "
                f"(spec v0.128 §3.7)"
            )
        return self
