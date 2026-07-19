"""astra.core — Five Invariants as data types.

Implements spec v0.129 §1:
- AstraCoord (§1.1): 128-bit hierarchical floating origin
- TimeState (§1.2, §4.4): two-clock split, regime bitmask, rapidity
- RapidityVector helpers (§3.7): ω clamp, magnitude
- ShipKinematicState (§4.2): derived view (v⃗_cmb, γ, β, grav, dτ/dt)
- grav helpers (§3.2): Schwarzschild-dominant composition mirror
- Regime (§3.3): canonical bitmask hex values
- Power (§1.4): locked subsystem list
- HullSDF (§1.3): stub at v0; full SDF deferred to Implementation B

Pure data types. Physics math lives in proto/astra_nexus and is queried via
astra.physics.nexus_bridge (Day 2).
"""

from astra.core.astra_coord import (
    LOCAL_OFFSET_MAX_M,
    SECTOR_SIZE_M,
    AstraCoord,
    astra_distance,
)
from astra.core.detect_regime import detect_regime, kinematic_regime_from_rapidity
from astra.core.grav import compute_grav_factor, schwarzschild_radius_m
from astra.core.hull_sdf import PROVISIONAL_ZONES
from astra.core.power import SUBSYSTEMS
from astra.core.rapidity import OMEGA_MAX, rapidity_magnitude
from astra.core.regime import Regime
from astra.core.ship_kinematic import ShipKinematicState, derive_ship_kinematics
from astra.core.time_state import T_COSMIC_MAX, TimeState

__all__ = [
    "LOCAL_OFFSET_MAX_M",
    "OMEGA_MAX",
    "PROVISIONAL_ZONES",
    "SECTOR_SIZE_M",
    "SUBSYSTEMS",
    "T_COSMIC_MAX",
    "AstraCoord",
    "Regime",
    "ShipKinematicState",
    "TimeState",
    "astra_distance",
    "compute_grav_factor",
    "derive_ship_kinematics",
    "detect_regime",
    "kinematic_regime_from_rapidity",
    "rapidity_magnitude",
    "schwarzschild_radius_m",
]
