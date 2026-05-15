"""ShipKinematicState — derived kinematic state per spec v0.128 §4.2.

State Bus exposes derived kinematic fields computed from rapidity + a_proper
+ gravitational sources. The math lives in proto/astra_nexus; this module
carries the shape that flows back from nexus_bridge into the State Bus.

Day 1 carries the type. Day 2 nexus_bridge wires the computation roundtrip.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from astra.core.regime import Regime


class ShipKinematicState(BaseModel):
    """Derived kinematic state. Computed per turn by proto/astra_nexus."""

    model_config = ConfigDict(frozen=True)

    v_local_cmb: tuple[float, float, float] = (0.0, 0.0, 0.0)
    gamma: float = Field(ge=1.0, default=1.0)               # γ = cosh(|ζ⃗|)
    grav_factor: float = Field(ge=0.0, le=1.0, default=1.0)  # √(1 − r_s/r) · √(1 + 2Φ/c²)
    dilation_ratio: float = Field(gt=0.0, le=1.0, default=1.0)  # dτ_ship/dt_cosmic
    regime: Regime = Regime.REST
