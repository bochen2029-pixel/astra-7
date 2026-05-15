"""Regime bitmask — canonical hex values per spec v0.128 §3.3.

The propulsion regime is a composable bitmask. GRAVITY_WELL composes with any
propulsion regime; WARP and STL_REL are mutually exclusive at the physics
level. All other combinations are valid bit-OR compositions.

Canonical hex values are part of the SaveFile wire format (§4.6) and replay
format (§5.3); they are locked across implementation builds.
"""

from __future__ import annotations

from enum import IntFlag


class Regime(IntFlag):
    """Propulsion regime per spec v0.128 §3.3."""

    REST          = 0x00
    STL_NONREL    = 0x01
    STL_REL       = 0x02
    WARP_CHARGE   = 0x04
    WARP_CRUISE   = 0x08
    WARP_SHUTDOWN = 0x10
    GRAVITY_WELL  = 0x20  # composable flag; multiplies into composition rule
    CRYOSLEEP     = 0x40
