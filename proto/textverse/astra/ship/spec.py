"""Ship envelope constants per memory/hull_design_v0.md + spec §15.7 Surface 1.

The ship is hand-designed, canon-locked, 4 decks, 280m × 78m × 22m. These
constants are part of Surface 1 (Ship envelope) — both textverse and UE5
will conform to the same dimensions, deck count, and camera-free zones.

Locked v0 (provisional pending Day 7 first-scenario findings):
- Hull dimensions and deck count
- Camera-free zone list
- Subsystem-to-deck mapping

Day 5 ships the constants. Day 5+ extends with hull SDF (when UE5 lands)
and per-deck volume budgets (when life-support scenarios surface).
"""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

# Hull envelope (meters)
HULL_LENGTH_M: Final[float] = 280.0
HULL_WIDTH_M: Final[float] = 78.0
HULL_HEIGHT_M: Final[float] = 22.0

NUM_DECKS: Final[int] = 4


class DeckSpec(BaseModel):
    """One deck's static spec."""

    model_config = ConfigDict(frozen=True)

    index: int = Field(ge=1, le=4)            # 1=top (bridge), 4=bottom (engineering)
    height_m: float = Field(gt=0.0)
    function: str
    zones: tuple[str, ...]
    camera_free_zones: tuple[str, ...]


# Deck 1 (top): Bridge + observation
DECK_1: Final[DeckSpec] = DeckSpec(
    index=1,
    height_m=3.0,
    function="bridge_and_observation",
    zones=("bridge", "observation_lounge", "star_sighting_nook"),
    camera_free_zones=("observation_lounge",),
)

# Deck 2: Habitat + centrifuge ring
DECK_2: Final[DeckSpec] = DeckSpec(
    index=2,
    height_m=3.0,
    function="habitat",
    zones=(
        "quarters",
        "galley",
        "common",
        "library",
        "exercise",
        "hygiene",
        "guest_cabin",
        "centrifuge_ring",
    ),
    camera_free_zones=("quarters", "hygiene"),
)

# Deck 3: Operations + medical + hydroponics
DECK_3: Final[DeckSpec] = DeckSpec(
    index=3,
    height_m=4.5,
    function="operations",
    zones=(
        "medical",
        "cryosleep",
        "pharmacy",
        "isolation",
        "hydroponics",
        "atmosphere_regen",
        "water_reclamation",
        "sensor_ops",
        "comm_relay",
    ),
    camera_free_zones=("hydroponics_greenhouse",),
)

# Deck 4 (bottom): Engineering + cognitive cores
DECK_4: Final[DeckSpec] = DeckSpec(
    index=4,
    height_m=5.5,
    function="engineering",
    zones=(
        "reactor",
        "coolant_loop",
        "warp_drive",
        "stl_nozzles",
        "power_distribution",
        "cognitive_cores",
        "cargo",
        "fab",
        "eva_prep",
    ),
    camera_free_zones=(),
)


DECKS: Final[tuple[DeckSpec, ...]] = (DECK_1, DECK_2, DECK_3, DECK_4)


def all_camera_free_zones() -> tuple[str, ...]:
    """Flat tuple of every camera-free zone across all decks (spec §4.8)."""
    return tuple(zone for d in DECKS for zone in d.camera_free_zones)


def all_zones() -> tuple[str, ...]:
    """Flat tuple of every zone on every deck."""
    return tuple(zone for d in DECKS for zone in d.zones)


def zone_to_deck() -> dict[str, int]:
    """Map zone name → deck index."""
    return {zone: d.index for d in DECKS for zone in d.zones}
