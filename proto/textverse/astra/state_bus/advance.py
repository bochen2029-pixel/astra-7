"""Time-only StateBus advance — the scheduling substrate for §4.3.1.

`advance_state_bus` produces a NEW frozen snapshot with the clocks moved
forward by a τ_ship delta (the scenario-scripted unit per the schema's
`tau_ship_delta_s`), honoring the §3.2 composition:

    dτ_ship = dilation_ratio · dt_cosmic   ⇒   dt_cosmic = dτ / dilation

with the dilation ratio taken from the snapshot's own derived kinematic
view (`ship_kinematics`, QCR-6) — so STL γ, warp f_warp, and the grav
factor all shape how much cosmic time a scripted τ interval costs, for
free. τ_crew_biological advances with τ_ship except under cryosleep,
where it runs at the metabolic rate ε (§1.2).

Scope (v0, honest): clocks only. Position advance, regime transitions
driven by propulsion, and the full physics tick remain the deferred
Day-6+ physics driver; heartbeat scheduling needs time, not trajectories.
The §4.2 epoch bound (QCR-3) composes automatically: an advance that
would push t_cosmic past 2^39 s fails at TimeState construction rather
than silently degrading.
"""

from __future__ import annotations

from astra.core.time_state import TimeState
from astra.state_bus.schema import StateBus

# Metabolic rate under cryosleep, spec §1.2: τ_crew "pauses (or advances
# at metabolic-rate ε ~ 10⁻⁴)". [chosen]
METABOLIC_EPSILON: float = 1.0e-4


def advance_state_bus(sb: StateBus, delta_tau_s: float) -> StateBus:
    """Return a new snapshot with clocks advanced by `delta_tau_s` of τ_ship."""
    if delta_tau_s < 0.0:
        raise ValueError(f"delta_tau_s must be >= 0, got {delta_tau_s}")
    if delta_tau_s == 0.0:
        return sb

    dilation = sb.ship_kinematics.dilation_ratio
    dt_cosmic = delta_tau_s / dilation
    crew_rate = METABOLIC_EPSILON if sb.cryosleep_active else 1.0

    new_time = TimeState(
        t_cosmic=sb.time.t_cosmic + dt_cosmic,
        tau_ship=sb.time.tau_ship + delta_tau_s,
        tau_crew_biological=sb.time.tau_crew_biological + delta_tau_s * crew_rate,
        rapidity_zeta=sb.time.rapidity_zeta,
        a_proper=sb.time.a_proper,
    )
    return sb.model_copy(update={"time": new_time})
