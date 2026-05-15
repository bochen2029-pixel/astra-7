"""astra.ship — ship state + tool API surface.

Implements Surface 1 (Ship envelope) and Surface 3 (Tool API) of the five
shared surfaces from spec v0.128 §15.7.

Files:
- spec.py:        4-deck constants per memory/hull_design_v0.md and book/CANON.md
                  (280m × 78m × 22m blended-wing-body slab, subsystem list)
- api.py:         Tool function definitions — locked names, locked Pydantic
                  schemas, locked semantics. v0 minimum: 6 operations
                  (warp.engage, warp.disengage, nav.heading_set, sensors.scan,
                  power.allocate, log.write).
- subsystems.py:  Subsystem state machines (reactor harmonics, power, etc.)
- dispatcher.py:  Validates tool calls + executes against State Bus

Expansion of the tool surface requires explicit contract amendment, not
implementer convenience.

Implementation: Day 5.
"""
