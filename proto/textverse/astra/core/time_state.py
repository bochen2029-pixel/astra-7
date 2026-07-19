"""TimeState — two-clock split + rapidity + kinematic-regime projection
per spec v0.129 §1.2, §3, §4.4.

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

# Epoch bound (spec-v0.130-DRAFT §2.1, QCR-3). t_cosmic is float64 seconds
# since EPOCH ZERO (voyage-anchored) — never "since Big Bang": at the
# cosmological epoch (~4.35e17 s) float64 ULP is 64 s, which violates the
# §5.3 replay tolerance (ε < 1e-4 s) by six orders of magnitude before any
# code runs. Below 2^39 s (≈17,400 years) ULP ≤ 6.1e-5 s < ε across the
# whole legal domain. The first mechanic that needs t_cosmic beyond this
# bound (deep-time arcs at γ ≈ 1e7) triggers the TimeCoord
# {int64 sec; double frac} representation + SaveFile v4 rather than a
# silent precision collapse. Forbidden-path KAT: tests/test_time_epoch_kat.py.
T_COSMIC_MAX: float = 2.0**39


class TimeState(BaseModel):
    """Per spec v0.129 §4.4 Time Contract `state` block.

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
                f"(spec v0.129 §3.7)"
            )
        return self

    @model_validator(mode="after")
    def _epoch_bound(self) -> Self:
        if self.t_cosmic >= T_COSMIC_MAX:
            raise ValueError(
                f"t_cosmic = {self.t_cosmic:.6g} s exceeds the epoch-zero domain "
                f"bound T_COSMIC_MAX = 2^39 s (~17,400 yr). float64 ULP beyond "
                f"this bound breaks the §5.3 replay tolerance; deep-time "
                f"mechanics require the TimeCoord representation "
                f"(spec-v0.130-DRAFT §2.1, QCR-3)."
            )
        return self
