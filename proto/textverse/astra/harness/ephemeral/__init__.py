"""astra.harness.ephemeral — background instances spawned during maintenance.

Implements spec v0.128 §4.9 ephemeral instance roles:
- consolidator: reviews recent conversation, scores salience, produces clean
                long-term REEL entries (calculator-bound for any numerics)
- journal_generator: §3.9 dual-clock journal output during cryosleep regimes
                     (output subject to leak detector before REEL commit)
- drift_detector: scans recent turns for register drift; emits corrections
                  via REEL entry (audit register)

Each ephemeral is an LLM bundle in its own right — calculator-bound, with
its own sysprompt. They write to the State Bus and REEL; they do NOT emit
to the operator directly (§4.9 invariant: ephemeral instances don't interact
with each other or with the operator; only the State Bus and REEL).

Implementation status (2026-06-10): all three §4.9 roles landed
(deterministic paths; LLM-voiced paths later behind the same signatures).
Orchestrator maintenance-window wiring follows when scenarios exercise it.
"""

from astra.harness.ephemeral.base import (
    EphemeralRole,
    EphemeralRunStatus,
    EphemeralStatus,
)
from astra.harness.ephemeral.consolidator import (
    MAX_CONSOLIDATED_ENTRIES,
    ConsolidationResult,
    QC3Matcher,
    consolidate_reel,
)
from astra.harness.ephemeral.drift_detector import (
    CorrectionArtifact,
    DriftFinding,
    detect_drift,
)
from astra.harness.ephemeral.journal_generator import (
    MAX_JOURNAL_ENTRIES,
    JournalResult,
    generate_journal,
)

__all__ = [
    "MAX_CONSOLIDATED_ENTRIES",
    "MAX_JOURNAL_ENTRIES",
    "ConsolidationResult",
    "CorrectionArtifact",
    "DriftFinding",
    "EphemeralRole",
    "EphemeralRunStatus",
    "EphemeralStatus",
    "JournalResult",
    "QC3Matcher",
    "consolidate_reel",
    "detect_drift",
    "generate_journal",
]
