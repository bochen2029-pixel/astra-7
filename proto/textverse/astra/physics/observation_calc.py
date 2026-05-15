"""Observation Calculator — spec v0.128 §6.3 wrapper.

Every render-path body query routes through this module. No other module
computes `body_state(t_cosmic)` for rendering. The Time Contract evolves
on `t_cosmic`; observation is a derived query, not a state mutation.

The math lives in proto/astra_nexus; this module is the Python entry point
that the perception assembler (Day 5) and the narrator-LLM input pipeline
(Day 4) both call through. Routing every numeric through here gives the
calculator-bound LLM agency (§15.6) its enforcement point.

Day 2 surface:
- `compute_apparent_rate` — regime-dispatched dt_emit/dt_recv from §3.11.

Day 3+ adds: body_state_at_t_emit, redshift composition, multi-body
observe() wrapping the full Observable struct from the C++ side.
"""

from __future__ import annotations

from astra.physics.nexus_bridge import (
    NexusBridge,
    NexusBridgeError,
    NexusResponse,
    compute_apparent_rate,
)

__all__ = [
    "NexusBridge",
    "NexusBridgeError",
    "NexusResponse",
    "compute_apparent_rate",
]
