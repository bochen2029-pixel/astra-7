"""astra.harness — the Harness Contract surface.

Implements spec v0.128 §4.9 Harness Contract.

Day 5 lands:
- orchestrator.py:          TurnOrchestrator + TurnResult
- perception_assembler.py:  template-based four-section bundle composition
- reel.py:                  in-memory REEL with keyword/recency retrieval

Day N+ will land ephemeral instances (consolidator, journal_generator,
drift_detector) as scenarios surface the need.
"""

from astra.harness.orchestrator import TurnOrchestrator, TurnResult
from astra.harness.perception_assembler import assemble_perception_bundle
from astra.harness.reel import Reel, ReelEntry

__all__ = [
    "Reel",
    "ReelEntry",
    "TurnOrchestrator",
    "TurnResult",
    "assemble_perception_bundle",
]
