"""astra.state_bus — single source of truth, double-buffered conceptually.

Implements spec v0.128 §4.2 State Bus Contract:
- Frame-coherent reads (snapshot at turn start; no mid-turn mutations leak)
- Layer 0 schema (Pydantic models)
- Save-seeds-not-state persistence (SaveFile v3)

The "double-buffered" property from §1.5 is enforced via immutable Pydantic
snapshots: a turn produces a new StateBus, never mutates the prior one.

Implementation: Day 1 (schema), Day 5 (orchestrator integration).
"""
