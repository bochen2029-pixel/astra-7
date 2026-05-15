"""Tool API surface — locked v0 6-operation set per ARCHITECTURE §6.7 + spec §15.7 Surface 3.

The locked operation names, argument schemas, and return shapes. ASTRA can
invoke these from her STAGE output's `<tool>` channel; the dispatcher
validates each invocation against these Pydantic schemas before executing.

Expansion requires explicit contract amendment (a Day N+ revision with
findings justification). The 6 v0 ops are intentionally minimal — they
cover the watch_47_morning scenario's plausible action surface plus the
universal-utility ops every scenario needs.

Phase 0.x adds: cryosleep.enter, reel.recall, comms.send, hull.diagnostic,
doors.set, lights.set, atmosphere.adjust. Total ~15 operations for V1.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from astra.core import Regime
from astra.core.astra_coord import AstraCoord
from astra.core.power import SUBSYSTEMS

# --- Argument schemas (frozen Pydantic models) -------------------------------

class WarpEngageArgs(BaseModel):
    """warp.engage — set warp factor target (and optionally heading)."""

    model_config = ConfigDict(frozen=True)

    target_factor: float = Field(ge=0.0, le=1.0)
    target_coords: AstraCoord | None = None    # None = continue current heading


class WarpDisengageArgs(BaseModel):
    """warp.disengage — drop out of warp, controlled or emergency."""

    model_config = ConfigDict(frozen=True)

    mode: Literal["controlled", "emergency"] = "controlled"


class NavHeadingSetArgs(BaseModel):
    """nav.heading_set — set navigation heading (named body or coords)."""

    model_config = ConfigDict(frozen=True)

    target: AstraCoord | str   # AstraCoord OR named body ("earth", "hot_earth")


class SensorsScanArgs(BaseModel):
    """sensors.scan — perform a sensor sweep of a region at given sensitivity."""

    model_config = ConfigDict(frozen=True)

    region: Literal["forward", "aft", "all"] = "forward"
    sensitivity: float = Field(ge=0.0, le=1.0, default=0.5)


class PowerAllocateArgs(BaseModel):
    """power.allocate — set a subsystem's power fraction."""

    model_config = ConfigDict(frozen=True)

    subsystem: Literal[
        "warp",
        "life_support",
        "hydroponics",
        "sensors",
        "lights",
        "comms",
        "cognitive_cores",
    ]
    fraction: float = Field(ge=0.0, le=1.0)


class LogWriteArgs(BaseModel):
    """log.write — write an entry to a log channel."""

    model_config = ConfigDict(frozen=True)

    channel: Literal["watch", "ops", "private"]
    text: str = Field(min_length=1, max_length=2000)


# --- The locked dispatch table ----------------------------------------------

TOOL_API: dict[str, type[BaseModel]] = {
    "warp.engage":     WarpEngageArgs,
    "warp.disengage":  WarpDisengageArgs,
    "nav.heading_set": NavHeadingSetArgs,
    "sensors.scan":    SensorsScanArgs,
    "power.allocate":  PowerAllocateArgs,
    "log.write":       LogWriteArgs,
}


def tool_schema_hint(op_name: str) -> str:
    """One-line schema hint for the AdapterBundle's prompt construction."""
    schema_cls = TOOL_API.get(op_name)
    if schema_cls is None:
        return f"unknown op: {op_name}"
    fields = []
    for name, field in schema_cls.model_fields.items():
        annotation = field.annotation
        fields.append(f"{name}: {annotation}")
    return f"{op_name}({', '.join(fields)})"


# --- Result shape (returned by dispatcher to State Bus) ---------------------

class ToolResult(BaseModel):
    """The dispatcher's result for one invocation. Always frozen.

    `ok=True` → the call executed; `state_diff` describes what changed.
    `ok=False` → call rejected (schema validation failed or precondition
    not met); `error` describes why. ASTRA reads this back as part of next
    turn's perception bundle.
    """

    model_config = ConfigDict(frozen=True)

    op: str
    ok: bool
    args: dict[str, object] = Field(default_factory=dict)
    state_diff: dict[str, object] = Field(default_factory=dict)
    error: str = ""


# Sanity-check helpers for cross-referencing other modules.
def regime_label(r: Regime) -> str:
    """Human-readable propulsion-regime label (with composed flags)."""
    parts = []
    for name in ("STL_NONREL", "STL_REL", "WARP_CHARGE", "WARP_CRUISE", "WARP_SHUTDOWN"):
        flag = Regime[name]
        if flag in r and r != Regime.REST:
            parts.append(name)
    if Regime.GRAVITY_WELL in r:
        parts.append("GRAVITY_WELL")
    if Regime.CRYOSLEEP in r:
        parts.append("CRYOSLEEP")
    return "|".join(parts) if parts else "REST"


def subsystem_in_locked_list(name: str) -> bool:
    """True iff the subsystem name is in the locked SUBSYSTEMS list (§1.4)."""
    return name in SUBSYSTEMS
