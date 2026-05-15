"""Mini-universe catalog — Sun + Earth + Hot-Earth for v0 scenarios.

Per ARCHITECTURE.md §8 and the watch_47_morning fixture: a tiny 3-body
catalog sufficient to exercise retarded-time observation, Kepler solver,
and multi-body perception in early scenarios. Day N+ extends.

The orbital math itself lives in proto/astra_nexus (queried via
nexus_bridge); this module just owns the body definitions.
"""

from __future__ import annotations

from astra.state_bus.schema import BodyState, KeplerianElements

# Standard astronomy constants used as canonical orbit inputs.
AU_M: float = 1.495_978_707e11        # 1 astronomical unit in meters
EARTH_PERIOD_S: float = 3.155_692_5e7  # sidereal year in seconds


SUN: BodyState = BodyState(
    name="sun",
    kind="star",
    mass_kg=1.989e30,
    position=(0.0, 0.0, -AU_M),        # 1 AU below ship origin (scenario default)
)


EARTH: BodyState = BodyState(
    name="earth",
    kind="planet",
    mass_kg=5.972e24,
    kepler=KeplerianElements(
        a=AU_M,
        e=0.0167,
        period_s=EARTH_PERIOD_S,
        parent="sun",
    ),
)


HOT_EARTH: BodyState = BodyState(
    name="hot_earth",
    kind="planet",
    mass_kg=5.972e24,
    kepler=KeplerianElements(
        a=1.0e10,                       # close-in, 1-day period
        e=0.0,
        period_s=86_400.0,              # 1 day — visible retarded-time effect
        parent="sun",
    ),
)


# Canonical v0 catalog (used by scenarios that don't specify their own).
V0_CATALOG: dict[str, BodyState] = {
    "sun": SUN,
    "earth": EARTH,
    "hot_earth": HOT_EARTH,
}


def lookup_body(name: str) -> BodyState | None:
    """Resolve a body name → BodyState. None for unknown."""
    return V0_CATALOG.get(name)


def all_names() -> tuple[str, ...]:
    """Names of every body in the v0 catalog."""
    return tuple(V0_CATALOG.keys())
