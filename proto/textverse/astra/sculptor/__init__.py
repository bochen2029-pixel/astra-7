"""astra.sculptor — autonomous self-tuning pipeline over the textverse bench.

Sculptor is the bounded-sculpting agent per spec §15.4 ("lock envelope,
sculpt within bounds; revise only on adversarial-finding-justified loop
measurement"). It sits on top of the Phase 1 bench: textverse provides
the measurement (LCP gates + scenarios), Sculptor provides the
hypothesis-driven optimization.

The deliverable is durable knowledge: a research log of what was tried,
what worked, what didn't, why. The optimized bundle is a snapshot; the
log outlives any specific model.
"""

from astra.sculptor.averaging import (
    AveragedIterationResult,
    evaluate_config_averaged,
    is_fragile,
)
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
from astra.sculptor.hypothesis import (
    DEFAULT_BANK,
    GATE_TO_LESSON_CLASS,
    Hypothesis,
    HypothesisGenerator,
    StubHypothesisGenerator,
    apply_hypothesis,
    select_by_lesson_class,
    worst_gate,
)
from astra.sculptor.judges import (
    CallableJudgeClient,
    DualJudge,
    JudgeClient,
    JudgeResult,
    LlamaJudgeClient,
    RubricName,
    StubJudgeClient,
    build_default_dual_judge,
    load_rubrics,
    parse_judge_prompt_md,
    parse_judge_response,
    render_transcript_for_judge,
)
from astra.sculptor.meta_agent import (
    Budget,
    IterationDecision,
    MetaAgent,
    seed_day0_baseline,
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
    "DEFAULT_BANK",
    "DEFAULT_PYTEST_TIMEOUT_S",
    "GATE_TO_LESSON_CLASS",
    "TRACKED_FILES",
    "AveragedIterationResult",
    "Budget",
    "CadenceState",
    "CallableJudgeClient",
    "ChangeRequest",
    "CompositeResult",
    "CompositeWeights",
    "ConfigSnapshot",
    "Decision",
    "DualJudge",
    "Hypothesis",
    "HypothesisGenerator",
    "InvariantSpec",
    "IterationDecision",
    "IterationResult",
    "IterationStatus",
    "JudgeClient",
    "JudgeResult",
    "LlamaJudgeClient",
    "MetaAgent",
    "PytestResult",
    "ResearchEntry",
    "RubricName",
    "ScenarioMetrics",
    "ScopeContract",
    "ScopeDecision",
    "ScopeEnforcer",
    "SnapshotFile",
    "StubHypothesisGenerator",
    "StubJudgeClient",
    "append_entry",
    "append_proposal",
    "apply_hypothesis",
    "build_bench_regression_entry",
    "build_default_dual_judge",
    "build_falsified_entry",
    "build_promote_entry",
    "build_scope_refused_entry",
    "composite_to_dict",
    "compute_composite",
    "compute_session_metrics",
    "evaluate_config_averaged",
    "is_fragile",
    "latest_entry",
    "latest_promote",
    "load_rubrics",
    "load_scope_contract",
    "load_weights",
    "parse_judge_prompt_md",
    "parse_judge_response",
    "read_entries",
    "render_daily_report",
    "render_findings_md",
    "render_transcript_for_judge",
    "run_iteration",
    "run_pytest_subprocess",
    "seed_day0_baseline",
    "select_by_lesson_class",
    "snapshot_from_disk",
    "snapshot_from_json",
    "snapshot_to_json",
    "worst_gate",
    "write_daily_report",
    "write_findings_md",
]
