"""astra.physics — bridge to the verified C++ physics core.

Implements spec v0.129 §3 (Time Architecture) and §6 (Unified Sampler) by
querying `proto/astra_nexus` via JSON-over-stdio. No physics math implemented
here — this is the thin adapter that respects the Calculator-bound LLM Agency
primitive (§15.6): every LLM that needs a number routes through this module.

Day 2 lands `nexus_bridge` + `observation_calc`. Subsequent days add
composition_rule, kepler, and tools wrappers that all sit on top of the
same bridge.
"""

from astra.physics.nexus_bridge import (
    NexusBridge,
    NexusBridgeError,
    NexusResponse,
    compute_apparent_rate,
)
from astra.physics.observation_calc import (
    ObservableState,
    RegimeLabel,
    composition_rule_evaluate,
    kepler_at,
    observe,
    retarded_time_solve,
)

__all__ = [
    "NexusBridge",
    "NexusBridgeError",
    "NexusResponse",
    "ObservableState",
    "RegimeLabel",
    "composition_rule_evaluate",
    "compute_apparent_rate",
    "kepler_at",
    "observe",
    "retarded_time_solve",
]
