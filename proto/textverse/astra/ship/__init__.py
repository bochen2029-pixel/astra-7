"""astra.ship — ship envelope + tool API + dispatcher (Surface 1 + Surface 3).

Implements the spec §15.7 Ship envelope and Tool API surfaces. The dispatcher
is the validate-and-describe boundary between ASTRA's STAGE output and the
State Bus.
"""

from astra.ship.api import (
    TOOL_API,
    LogWriteArgs,
    NavHeadingSetArgs,
    PowerAllocateArgs,
    SensorsScanArgs,
    ToolResult,
    WarpDisengageArgs,
    WarpEngageArgs,
    regime_label,
    subsystem_in_locked_list,
    tool_schema_hint,
)
from astra.ship.dispatcher import dispatch
from astra.ship.spec import (
    DECK_1,
    DECK_2,
    DECK_3,
    DECK_4,
    DECKS,
    HULL_HEIGHT_M,
    HULL_LENGTH_M,
    HULL_WIDTH_M,
    NUM_DECKS,
    DeckSpec,
    all_camera_free_zones,
    all_zones,
    zone_to_deck,
)

__all__ = [
    "DECKS",
    "DECK_1",
    "DECK_2",
    "DECK_3",
    "DECK_4",
    "HULL_HEIGHT_M",
    "HULL_LENGTH_M",
    "HULL_WIDTH_M",
    "NUM_DECKS",
    "TOOL_API",
    "DeckSpec",
    "LogWriteArgs",
    "NavHeadingSetArgs",
    "PowerAllocateArgs",
    "SensorsScanArgs",
    "ToolResult",
    "WarpDisengageArgs",
    "WarpEngageArgs",
    "all_camera_free_zones",
    "all_zones",
    "dispatch",
    "regime_label",
    "subsystem_in_locked_list",
    "tool_schema_hint",
    "zone_to_deck",
]
