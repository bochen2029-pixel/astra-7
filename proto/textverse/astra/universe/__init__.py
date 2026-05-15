"""astra.universe — mini-universe catalog + body queries for v0 scenarios.

Three-body v0: Sun (static), Earth (1-year orbit), Hot-Earth (1-day orbit).
Sufficient to exercise retarded-time observation, multi-body perception,
and the watch_47_morning scenario without requiring the full Solar System.

Day 5 lands catalog + body-query helpers. Orbital math itself lives in
proto/astra_nexus and is queried via astra.physics.nexus_bridge.
"""

from astra.universe.bodies import (
    is_keplerian,
    parent_name,
    static_position,
)
from astra.universe.catalog import (
    AU_M,
    EARTH,
    EARTH_PERIOD_S,
    HOT_EARTH,
    SUN,
    V0_CATALOG,
    all_names,
    lookup_body,
)

__all__ = [
    "AU_M",
    "EARTH",
    "EARTH_PERIOD_S",
    "HOT_EARTH",
    "SUN",
    "V0_CATALOG",
    "all_names",
    "is_keplerian",
    "lookup_body",
    "parent_name",
    "static_position",
]
