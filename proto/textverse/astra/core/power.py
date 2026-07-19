"""Power network — locked subsystem list per spec v0.129 §1.4.

Reactor produces finite power. Every consumer draws from it. Allocation is
zero-sum. The cognitive_cores slot binds to substrate envelope (reduced
power → smaller LLM, paused ephemeral instances). The warp-coupled Reflex
sub-bus receives guaranteed minimum when warp is active (operator cannot
suicide-route the stabilizer).

New subsystems require contract amendment — adding here breaks save-file
portability.
"""

from __future__ import annotations

from typing import Final

SUBSYSTEMS: Final[tuple[str, ...]] = (
    "warp",
    "life_support",
    "hydroponics",
    "sensors",
    "lights",
    "comms",
    "cognitive_cores",
)
