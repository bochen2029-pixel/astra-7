"""astra — ASTRA-7 closed-loop verification bench.

Top-level package. See ARCHITECTURE.md §5 for the full module layout.

Implementation status: scaffolded; Day 1 (Pydantic types in `core/` + `state_bus/`)
is the first actual code work. Until Day 1 lands, all submodules are empty.

This package implements:
- The harness contract (spec v0.128 §4.9)
- The STAGE grammar (§4.3)
- The Observation Calculator (§6.3)
- The Narrator-LLM bundle (§6.4)
- Calculator-bound LLM agency (§15.6)
- Loop Closure Property gates (§10)
- The scenario runner against the 9-gate LCP suite

It does NOT implement the physics math (that's `proto/astra_nexus`, locked).
It does NOT implement UE5 visuals (that's Implementation B per §15.7).

Per §15.5: lock envelope, sculpt within bounds, never violate prior commitments.
"""

__version__ = "0.1.0"
