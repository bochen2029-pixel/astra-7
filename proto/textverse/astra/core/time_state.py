"""TimeState — two-clock split + rapidity + kinematic-regime projection
per spec v0.128 §1.2, §3, §4.4.

- t_cosmic drives Kepler solver, stellar evolution, distant-body AstraCoord
  updates, cryosleep advance, "how old is the universe" queries.
- τ_ship is ASTRA's experiential clock; drives REEL timestamps, audio synth
  rate, conversation history, drift-detector cadence.
- τ_crew_biological derives from τ_ship; pauses on CRYOSLEEP at metabolic ε.

**Regime placement (audit R1, 2026-05-16):** the *composite* Regime
(propulsion base + CRYOSLEEP + GRAVITY_WELL flags) lives on StateBus
root as a `@computed_field` derived from `warp`, `cryosleep_active`,
`time.rapidity_zeta`, and grav factor. TimeState only exposes the
*kinematic projection* (REST / STL_NONREL / STL_REL from rapidity
alone) via `kinematic_regime`. This resolves the §4.2 vs §4.4 spec
ambiguity in favor of computed-from-truth: regime is never a settable
field anywhere — it is always derived from the underlying state.

The composition rule (§3.2) is enforced inside proto/astra_nexus — this
module carries the state shape and the rapidity clamp from §3.7.

Frozen per §1.5: each turn produces a new immutable TimeState snapshot.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from astra.core.detect_regime import kinematic_regime_from_rapidity
from astra.core.rapidity import OMEGA_MAX, rapidity_magnitude
from astra.core.regime import Regime


class TimeState(BaseModel):
    """Per spec v0.128 §4.4 Time Contract `state` block.

    Day 1 enforces shape and the static rapidity clamp. Composition-rule
    invariants (dτ/dt ∈ (0,1], γ stable to 4 sig figs, |v⃗| < c, γ ≡ 1 in
    WARP regime) are math invariants enforced by proto/astra_nexus and
    verified via nexus_bridge roundtrip in Day 2.

    `kinematic_regime` is a velocity-only projection (REST / STL_NONREL /
    STL_REL). The composite regime (which adds WARP_*, CRYOSLEEP,
    GRAVITY_WELL flags) lives on StateBus.regime and is computed from
    the full state context — see `astra.core.detect_regime.detect_regime`.
    """

    model_config = ConfigDict(frozen=True)

    t_cosmic: float = Field(ge=0.0)                          # seconds since epoch zero
    tau_ship: float = Field(ge=0.0)                          # ship proper time
    tau_crew_biological: float = Field(ge=0.0)               # pauses on cryosleep
    rapidity_zeta: tuple[float, float, float] = (0.0, 0.0, 0.0)
    a_proper: tuple[float, float, float] = (0.0, 0.0, 0.0)   # ship-frame, m/s²

    @computed_field  # type: ignore[prop-decorator]
    @property
    def kinematic_regime(self) -> Regime:
        """Velocity-only regime projection — REST / STL_NONREL / STL_REL
        derived from `rapidity_zeta` alone. Does NOT include WARP_*,
        CRYOSLEEP, or GRAVITY_WELL bits — those live on StateBus.regime.
        """
        return kinematic_regime_from_rapidity(self.rapidity_zeta)

    @model_validator(mode="after")
    def _rapidity_clamp(self) -> Self:
        omega = rapidity_magnitude(self.rapidity_zeta)
        if omega > OMEGA_MAX:
            raise ValueError(
                f"Rapidity |ζ⃗| = {omega:.6f} exceeds clamp ω_max ≈ {OMEGA_MAX} "
                f"(spec v0.128 §3.7)"
            )
        return self
