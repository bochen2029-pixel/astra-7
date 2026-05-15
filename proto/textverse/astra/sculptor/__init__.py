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

from astra.sculptor.composite import (
    CompositeResult,
    CompositeWeights,
    ScenarioMetrics,
    composite_to_dict,
    compute_composite,
    compute_session_metrics,
    load_weights,
)
from astra.sculptor.config import (
    TRACKED_FILES,
    ConfigSnapshot,
    SnapshotFile,
    snapshot_from_disk,
    snapshot_from_json,
    snapshot_to_json,
)
from astra.sculptor.pytest_gate import (
    DEFAULT_PYTEST_TIMEOUT_S,
    CadenceState,
    PytestResult,
    run_pytest_subprocess,
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
from astra.sculptor.runner_loop import (
    IterationResult,
    IterationStatus,
    run_iteration,
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
    "DEFAULT_PYTEST_TIMEOUT_S",
    "TRACKED_FILES",
    "CadenceState",
    "ChangeRequest",
    "CompositeResult",
    "CompositeWeights",
    "ConfigSnapshot",
    "Decision",
    "InvariantSpec",
    "IterationResult",
    "IterationStatus",
    "PytestResult",
    "ResearchEntry",
    "ScenarioMetrics",
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
    "composite_to_dict",
    "compute_composite",
    "compute_session_metrics",
    "latest_entry",
    "latest_promote",
    "load_scope_contract",
    "load_weights",
    "read_entries",
    "render_daily_report",
    "render_findings_md",
    "run_iteration",
    "run_pytest_subprocess",
    "snapshot_from_disk",
    "snapshot_from_json",
    "snapshot_to_json",
    "write_daily_report",
    "write_findings_md",
]
