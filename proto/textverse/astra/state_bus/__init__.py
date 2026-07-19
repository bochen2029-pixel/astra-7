"""astra.state_bus — single source of truth, double-buffered conceptually.

Implements spec v0.129 §4.2 State Bus Contract:
- Frame-coherent reads (a turn's snapshot is the read)
- Layer 0 schema (Pydantic models, all frozen)
- Save-seeds-not-state persistence (SaveFile v3; Day 5+)

The "double-buffered" property from §1.5 is enforced via immutable Pydantic
snapshots: a turn produces a new StateBus, never mutates the prior one.

Day 1 lands the schema. Day 5 wires the orchestrator's `snapshot()` /
`commit()` semantics and frame-boundary swap.
"""

from astra.state_bus.schema import (
    BHRecord,
    BodyState,
    ChaosFieldSummary,
    CosmologicalParams,
    KeplerianElements,
    StateBus,
    WarpState,
)

__all__ = [
    "BHRecord",
    "BodyState",
    "ChaosFieldSummary",
    "CosmologicalParams",
    "KeplerianElements",
    "StateBus",
    "WarpState",
]
