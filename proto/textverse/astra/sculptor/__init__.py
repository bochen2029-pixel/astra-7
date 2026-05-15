"""astra.sculptor — autonomous self-tuning pipeline over the textverse bench.

Sculptor is the bounded-sculpting agent per spec §15.4 ("lock envelope,
sculpt within bounds; revise only on adversarial-finding-justified loop
measurement"). It sits on top of the Phase 1 bench: textverse provides
the measurement (LCP gates + scenarios), Sculptor provides the
hypothesis-driven optimization.

The deliverable is durable knowledge: a research log of what was tried,
what worked, what didn't, why. The optimized bundle is a snapshot; the
log outlives any specific model.

Modules:
- config.py:       ConfigSnapshot (immutable bundle identifier)
- scope.py:        ScopeContract + ScopeEnforcer (the contract guard)
- research_log.py: append-only research log + findings.md + daily_report.md

Sculptor-B (auto-runner), Sculptor-C (meta-agent), Sculptor-D
(dual-judge), Sculptor-E (convergence) land subsequently.
"""

from astra.sculptor.config import (
    TRACKED_FILES,
    ConfigSnapshot,
    SnapshotFile,
    snapshot_from_disk,
    snapshot_from_json,
    snapshot_to_json,
)
from astra.sculptor.research_log import (
    Decision,
    ResearchEntry,
    append_entry,
    append_proposal,
    build_bench_regression_entry,
    build_falsified_entry,
    build_promote_entry,
    build_scope_refused_entry,
    latest_entry,
    latest_promote,
    read_entries,
    render_daily_report,
    render_findings_md,
    write_daily_report,
    write_findings_md,
)
from astra.sculptor.scope import (
    ChangeRequest,
    InvariantSpec,
    ScopeContract,
    ScopeDecision,
    ScopeEnforcer,
    load_scope_contract,
)

__all__ = [
    "TRACKED_FILES",
    "ChangeRequest",
    "ConfigSnapshot",
    "Decision",
    "InvariantSpec",
    "ResearchEntry",
    "ScopeContract",
    "ScopeDecision",
    "ScopeEnforcer",
    "SnapshotFile",
    "append_entry",
    "append_proposal",
    "build_bench_regression_entry",
    "build_falsified_entry",
    "build_promote_entry",
    "build_scope_refused_entry",
    "latest_entry",
    "latest_promote",
    "load_scope_contract",
    "read_entries",
    "render_daily_report",
    "render_findings_md",
    "snapshot_from_disk",
    "snapshot_from_json",
    "snapshot_to_json",
    "write_daily_report",
    "write_findings_md",
]
