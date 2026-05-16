"""detect_regime — composite Regime computation per spec §3.3.

Pure-Python implementation of the regime composition algorithm. The
C++ astra_nexus exposes the same algorithm via the `detect_regime`
stdio op for cross-substrate verification; both implementations must
agree across the canonical state grid (enforced by
`tests/test_detect_regime.py::test_python_matches_cpp_across_grid`).

Composition rules (spec §3.3):
- Propulsion regimes are mutually exclusive at the physics level:
  WARP_* wins over STL_*; only one of {REST, STL_NONREL, STL_REL,
  WARP_CHARGE, WARP_CRUISE, WARP_SHUTDOWN} is set as the base.
- CRYOSLEEP is a compositional flag (bit 0x40): bit-OR'd in when active.
- GRAVITY_WELL is a compositional flag (bit 0x20): bit-OR'd in when
  the Schwarzschild composition has dropped the lapse factor below
  threshold (default 0.99 — within ~1% of unity counts as gravitational
  influence).

This module is closed-form: no I/O, no Pydantic models, no cross-module
state. The inputs are the StateBus.warp / StateBus.cryosleep_active /
TimeState.rapidity_zeta / grav_factor scalars and nothing else.
"""

from __future__ import annotations

from math import tanh
from typing import TYPE_CHECKING

from astra.core.rapidity import rapidity_magnitude
from astra.core.regime import Regime

if TYPE_CHECKING:
    from astra.state_bus.schema import WarpState


# Below this fraction of unity for the Schwarzschild lapse, GRAVITY_WELL fires.
# Provisional per spec §3.3 — "near a gravitational well." 0.99 means the
# composition rule has dropped τ_ship rate by 1% or more.
GRAV_WELL_THRESHOLD: float = 0.99

# Kinematic-regime boundary: |β| < 0.1 → STL_NONREL; |β| ≥ 0.1 → STL_REL.
# Per spec §3.3: "relativistic when γ > 1.005" ⇒ β > ~0.1.
STL_REL_BETA_THRESHOLD: float = 0.1


def kinematic_regime_from_rapidity(
    rapidity_zeta: tuple[float, float, float],
) -> Regime:
    """Velocity-only regime projection (REST / STL_NONREL / STL_REL).

    Ignores warp, cryosleep, and gravity — this is the kinematic
    component alone, used as a base for composition or as the
    `kinematic_regime` projection on TimeState.
    """
    omega = rapidity_magnitude(rapidity_zeta)
    if omega == 0.0:
        return Regime.REST
    beta = tanh(omega)
    if beta < STL_REL_BETA_THRESHOLD:
        return Regime.STL_NONREL
    return Regime.STL_REL


def detect_regime(
    *,
    rapidity_zeta: tuple[float, float, float] = (0.0, 0.0, 0.0),
    warp: WarpState | None = None,
    cryosleep_active: bool = False,
    grav_factor: float = 1.0,
) -> Regime:
    """Composite regime per spec §3.3.

    Returns the bit-OR composition: one base (REST/STL_*/WARP_*) plus
    optional CRYOSLEEP and GRAVITY_WELL flags.
    """
    if warp is not None:
        if warp.phase == "charging":
            base = Regime.WARP_CHARGE
        elif warp.phase == "cruising":
            base = Regime.WARP_CRUISE
        else:
            base = Regime.WARP_SHUTDOWN
    else:
        base = kinematic_regime_from_rapidity(rapidity_zeta)

    composite = base
    if cryosleep_active:
        composite |= Regime.CRYOSLEEP
    if grav_factor < GRAV_WELL_THRESHOLD:
        composite |= Regime.GRAVITY_WELL
    return composite
