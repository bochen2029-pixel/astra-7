"""Ephemeral instance shared surface per spec v0.129 §4.9 Harness Contract.

The HarnessState schema (§4.9) tracks ephemeral instances as
`{role, status, work_queue, last_artifact}` records. This module carries
that record shape plus the role vocabulary. The instances themselves are
pure functions over (StateBus, REEL) inputs in v0 — LLM-backed paths
arrive later behind the same signatures.

§4.9 invariants honored across this package:
- Ephemeral instances do not interact with each other directly; only with
  the State Bus and the Mind Kernel's REEL.
- Failure of one instance degrades coverage; it never stops the others
  (orchestrator-level concern; each instance reports via EphemeralStatus
  rather than raising on content-level problems).
- Outputs destined for REEL pass the leak gates before commit
  (journal: `LeakDetector.scan_journal_output` per §5.7).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

EphemeralRole = Literal["consolidator", "journal_generator", "drift_detector"]
EphemeralRunStatus = Literal["idle", "running", "completed", "failed"]


class EphemeralStatus(BaseModel):
    """One ephemeral instance record per §4.9 HarnessState schema."""

    model_config = ConfigDict(frozen=True)

    role: EphemeralRole
    status: EphemeralRunStatus = "idle"
    work_queue: list[str] = Field(default_factory=list)
    last_artifact: str = ""
