"""Sculptor-C meta-agent — the autonomous loop.

One iteration:
1. Load latest research entry (latest_promote → baseline).
2. HypothesisGenerator.propose() → Hypothesis.
3. Apply hypothesis transform → new file contents (in memory).
4. ScopeEnforcer.evaluate(ChangeRequest):
   - refused → append `scope_refused` entry; continue.
   - allowed → write to disk.
5. IF cadence triggers: run_pytest_subprocess(); fail → revert + log.
6. evaluate_config_averaged(N=3) → averaged composite.
7. Decision rule:
   - anchor_passed AND composite ≥ baseline + ε → `promote`
   - anchor_passed AND composite < baseline → `revert` + `falsified`
   - NOT anchor_passed → `revert` (regardless of score delta)
8. Append research log entry; regenerate findings.md + daily_report.md.
9. Check convergence + budget; honor pause/halt signal flags.

The meta-agent is the only writer to the research log + the prompts/
and tuning/sampling.json files. Concurrency is single-threaded; the
loop is sequential by design.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from astra.sculptor.averaging import (
    AveragedIterationResult,
    evaluate_config_averaged,
    is_fragile,
)
from astra.sculptor.composite import CompositeWeights, load_weights
from astra.sculptor.hypothesis import (
    HypothesisGenerator,
    StubHypothesisGenerator,
    apply_hypothesis,
)
from astra.sculptor.pytest_gate import (
    CadenceState,
    PytestResult,
    run_pytest_subprocess,
)
from astra.sculptor.research_log import (
    ResearchEntry,
    append_entry,
    build_bench_regression_entry,
    build_falsified_entry,
    build_promote_entry,
    build_scope_refused_entry,
    latest_promote,
    read_entries,
    write_daily_report,
    write_findings_md,
)
from astra.sculptor.scope import (
    ChangeRequest,
    ScopeContract,
    ScopeEnforcer,
    load_scope_contract,
)

# --- Budget ----------------------------------------------------------------

@dataclass(slots=True)
class Budget:
    """Resource caps for the meta-agent loop."""

    max_tokens: int = 50_000_000
    max_iterations: int = 200
    max_wall_clock_hours: float = 48.0
    auto_extend_on_progress: bool = True
    auto_extend_factor: float = 0.5
    gradient_progress_threshold: float = 0.005

    @classmethod
    def from_json(cls, path: Path) -> Budget:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            max_tokens=int(raw.get("max_tokens", 50_000_000)),
            max_iterations=int(raw.get("max_iterations", 200)),
            max_wall_clock_hours=float(raw.get("max_wall_clock_hours", 48.0)),
            auto_extend_on_progress=bool(raw.get("auto_extend_on_progress", True)),
            auto_extend_factor=float(raw.get("auto_extend_factor", 0.5)),
            gradient_progress_threshold=float(raw.get("gradient_progress_threshold", 0.005)),
        )


# --- Decision result -------------------------------------------------------

@dataclass(slots=True)
class IterationDecision:
    """The meta-agent's decision for one iteration.

    `entry` is the ResearchEntry that was appended.
    `applied_to_disk` indicates whether the proposed file edit was written.
    """

    entry: ResearchEntry
    applied_to_disk: bool
    averaged_result: AveragedIterationResult | None = None


# --- Signal flags ----------------------------------------------------------

def _flag_exists(path: Path) -> bool:
    return path.is_file()


# --- The meta-agent ---------------------------------------------------------

@dataclass
class MetaAgent:
    """Sculptor-C autonomous loop.

    Construct, call `await run_one_iteration()` for one step, or
    `await run_until_done()` to run until convergence / budget / halt.

    The agent is the SINGLE writer to:
    - the research log (append-only)
    - the prompts/ files (via ScopeEnforcer)
    - tuning/sampling.json and tuning/reel_retrieval_k.json
    - tuning/findings.md and tuning/daily_report.md (regenerated)

    Locked files are guarded by ScopeEnforcer; the agent cannot escape.
    """

    textverse_root: Path
    base_url: str = "http://127.0.0.1:8080"
    scope_contract: ScopeContract = field(init=False)
    enforcer: ScopeEnforcer = field(init=False)
    weights: CompositeWeights = field(init=False)
    budget: Budget = field(init=False)
    hypothesis_generator: HypothesisGenerator = field(default_factory=StubHypothesisGenerator)
    n_runs_per_iteration: int = 3
    epsilon: float = 0.005    # composite improvement threshold for promote
    iteration_count: int = 0
    last_promote_score: float = 0.0   # for budget extension check
    cadence: CadenceState = field(init=False)
    _last_k_deltas: list[float] = field(default_factory=list)
    _budget_extended: bool = False

    def __post_init__(self) -> None:
        self.scope_contract = load_scope_contract(self.textverse_root / "tuning" / "scope.yaml")
        self.enforcer = ScopeEnforcer(
            contract=self.scope_contract,
            textverse_root=self.textverse_root,
        )
        self.weights = load_weights(self.textverse_root / "tuning" / "weights.json")
        self.budget = Budget.from_json(self.textverse_root / "tuning" / "budget.json")
        self.cadence = CadenceState(
            iteration=0,
            cadence=self.scope_contract.pytest_cadence_iterations,
        )

    # --- Single iteration --------------------------------------------------

    async def run_one_iteration(self) -> IterationDecision:
        """Execute one iteration end-to-end. Returns the decision + entry."""
        self.iteration_count += 1
        iter_id = f"iter_{self.iteration_count:04d}"

        recent_log = read_entries(self._research_log_path())
        latest = latest_promote(self._research_log_path())
        baseline_score = (
            latest.composite_score
            if latest is not None and latest.composite_score is not None
            else 0.0
        )

        # 1-2. Propose hypothesis.
        hypothesis = self.hypothesis_generator.propose(
            latest_lcp=None,            # Sculptor-C v1 doesn't pass LCP to stub
            latest_composite=None,
            recent_log=recent_log,
            scope_contract=self.scope_contract,
        )

        # 3. Compute proposed new contents.
        new_contents = apply_hypothesis(hypothesis, self.textverse_root)

        # 4. ScopeEnforcer.
        change_request = ChangeRequest(
            relpath=hypothesis.relpath,
            new_contents=new_contents,
            hypothesis=hypothesis.rationale,
        )
        decision = self.enforcer.evaluate(change_request)
        if not decision.allow:
            entry = build_scope_refused_entry(
                iteration=self.iteration_count,
                relpath=hypothesis.relpath,
                rationale=decision.reason,
                hypothesis=hypothesis.rationale,
            )
            append_entry(self._research_log_path(), entry)
            self._regenerate_findings()
            return IterationDecision(entry=entry, applied_to_disk=False)

        # 5. Apply the change to disk (snapshot baseline for revert).
        target_path = self.textverse_root / hypothesis.relpath
        baseline_contents = target_path.read_text(encoding="utf-8") if target_path.is_file() else ""
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(new_contents, encoding="utf-8")

        # Cadence pytest gate.
        self.cadence.iteration = self.iteration_count
        if self.cadence.should_run():
            pytest_result = self._run_pytest_or_fallback()
            if not pytest_result.passed:
                # Revert and log.
                target_path.write_text(baseline_contents, encoding="utf-8")
                entry = build_bench_regression_entry(
                    iteration=self.iteration_count,
                    failed_tests=pytest_result.failed_tests,
                )
                append_entry(self._research_log_path(), entry)
                self._regenerate_findings()
                return IterationDecision(entry=entry, applied_to_disk=False)

        # 6. Evaluate (multi-run averaged).
        avg_result = await evaluate_config_averaged(
            base_iteration_id=iter_id,
            n_runs=self.n_runs_per_iteration,
            base_url=self.base_url,
            textverse_root=self.textverse_root,
            library_dir=self.textverse_root / "astra" / "scenarios" / "library",
            history_root=self.textverse_root / "tuning" / "history",
            output_root=self.textverse_root / "scenarios" / "output",
            weights=self.weights,
            anchor_scenarios=list(self.scope_contract.anchor_scenarios),
        )

        # 7. Decide promote / revert / falsified.
        composite_score = avg_result.composite_score
        delta = composite_score - baseline_score
        anchor_passed = avg_result.anchor_scenarios_passed

        if not anchor_passed:
            # Revert.
            target_path.write_text(baseline_contents, encoding="utf-8")
            entry = build_falsified_entry(
                iteration=self.iteration_count,
                hypothesis=hypothesis.rationale,
                falsification_reasoning=(
                    f"anchor scenario(s) did not pass; composite={composite_score:.4f}, "
                    f"baseline={baseline_score:.4f}"
                ),
                lesson_class=hypothesis.lesson_class,
                lesson=(
                    f"hypothesis '{hypothesis.name}' broke anchor; reverted. "
                    "Try class-targeted alternative."
                ),
                composite_score=composite_score,
                delta_vs_best=delta,
            )
        elif delta >= self.epsilon:
            # Promote.
            entry = build_promote_entry(
                iteration=self.iteration_count,
                hypothesis=hypothesis.rationale,
                change_summary=f"{hypothesis.name}: {hypothesis.relpath}",
                composite_score=composite_score,
                delta_vs_best=delta,
                per_gate_changes=self._per_gate_diff(avg_result),
                rationale=(
                    f"composite {composite_score:.4f} ≥ baseline {baseline_score:.4f} + ε; "
                    f"anchor passed; promoting."
                ),
                artifact_dir=f"tuning/history/{iter_id}_run1",
            )
            self.last_promote_score = composite_score
            self._last_k_deltas.append(delta)
        else:
            # Composite regression — revert, log as falsified.
            target_path.write_text(baseline_contents, encoding="utf-8")
            entry = build_falsified_entry(
                iteration=self.iteration_count,
                hypothesis=hypothesis.rationale,
                falsification_reasoning=(
                    f"composite {composite_score:.4f} < baseline {baseline_score:.4f}; "
                    f"reverted to baseline contents"
                ),
                lesson_class=hypothesis.lesson_class,
                lesson=(
                    f"hypothesis '{hypothesis.name}' did not improve composite; "
                    "either rule already saturated or change was net-negative"
                ),
                composite_score=composite_score,
                delta_vs_best=delta,
            )

        append_entry(self._research_log_path(), entry)
        self._regenerate_findings()

        # Optional: log fragile-config warning.
        if avg_result.averaged_composite is not None and is_fragile(avg_result):
            # Doesn't change decision; just a soft signal in the log.
            pass

        return IterationDecision(
            entry=entry,
            applied_to_disk=(entry.decision == "promote"),
            averaged_result=avg_result,
        )

    # --- Multi-iteration driver ------------------------------------------

    async def run_until_done(self, *, max_iterations: int | None = None) -> ResearchEntry:
        """Run iterations until convergence, budget, or halt signal.

        Returns the final ResearchEntry (the last appended).
        """
        max_iters = max_iterations if max_iterations is not None else self.budget.max_iterations
        final_entry: ResearchEntry | None = None
        for _ in range(max_iters):
            if self._halt_flag():
                break
            if self._pause_flag():
                # Operator pause: do not iterate; caller should poll.
                break
            decision = await self.run_one_iteration()
            final_entry = decision.entry
            if self._converged():
                break
        # If no iterations ran (e.g. halt at start), synthesize a marker.
        if final_entry is None:
            final_entry = ResearchEntry(
                iteration=self.iteration_count,
                decision="operator_signal",
                rationale="halted before first iteration",
            )
        return final_entry

    # --- Convergence -----------------------------------------------------

    def _converged(self) -> bool:
        """Three-conjunct convergence test per SCULPTOR_STARTUP.md §5.1.

        1. Composite Δ < 0.005 for K=10 consecutive iterations
        2. Coverage entropy ≥ 2.0 bits (currently approximated by library size)
        3. Composite score ≥ MIN_ABSOLUTE_THRESHOLD (0.80)
        """
        k_window = self.weights.convergence_k
        if len(self._last_k_deltas) < k_window:
            return False
        recent = self._last_k_deltas[-k_window:]
        if any(abs(d) >= self.weights.convergence_delta for d in recent):
            return False
        if self.last_promote_score < self.weights.min_absolute_threshold:
            return False
        # Coverage entropy: library-size proxy (Sculptor-E refines this).
        import math
        lib_count = len(list((self.textverse_root / "astra" / "scenarios" / "library").glob("*.yaml")))
        coverage = math.log2(lib_count) if lib_count >= 2 else 0.0
        return coverage >= self.weights.min_coverage_entropy_bits

    # --- Internals -------------------------------------------------------

    def _research_log_path(self) -> Path:
        return self.textverse_root / self.scope_contract.research_log_path

    def _findings_path(self) -> Path:
        return self.textverse_root / "tuning" / "findings.md"

    def _daily_report_path(self) -> Path:
        return self.textverse_root / "tuning" / "daily_report.md"

    def _halt_flag(self) -> bool:
        return _flag_exists(self.textverse_root / self.scope_contract.signals.get("halt_flag", ""))

    def _pause_flag(self) -> bool:
        return _flag_exists(self.textverse_root / self.scope_contract.signals.get("pause_flag", ""))

    def _regenerate_findings(self) -> None:
        write_findings_md(self._research_log_path(), self._findings_path())
        write_daily_report(self._research_log_path(), self._daily_report_path())

    def _run_pytest_or_fallback(self) -> PytestResult:
        return run_pytest_subprocess(textverse_root=self.textverse_root)

    def _per_gate_diff(self, avg_result: AveragedIterationResult) -> dict[str, float]:
        """Map per-gate session rate to a dict (rate vs prior baseline TBD)."""
        if avg_result.averaged_composite is None:
            return {}
        return {
            gate.value: rate
            for gate, rate in avg_result.averaged_composite.per_gate_session_rates.items()
        }


# --- Helper: seed day-0 baseline entries ---------------------------------

def seed_day0_baseline(textverse_root: Path) -> int:
    """Append the three Day-0 empirical findings (D0-1/2/3) to the research log.

    Returns number of entries written. Idempotent: skips if log already has
    Day-0 entries.
    """
    log_path = textverse_root / "tuning" / "research_log.jsonl"
    existing = read_entries(log_path)
    if any(e.lesson_class == "day0_baseline" for e in existing):
        return 0

    entries: list[dict[str, Any]] = [
        {
            "iteration": 0,
            "decision": "operator_signal",
            "rationale": (
                "Day-0 finding D0-1: Qwen 3.5 9B at temp 0.7 sometimes invents tool names "
                "not in the locked 6-op TOOL_API (e.g. reactor.status). Observed in 2 of 4 "
                "live runs of watch_47_morning. Sysprompt does not enumerate the locked "
                "tool surface."
            ),
            "lesson_class": "day0_baseline",
            "lesson": (
                "TOOL_VALID 1.00 → 0.67 failure mode. Hypothesis class to test: enumerate "
                "locked tool surface in sysprompt; or instruct 'do not invent tool names "
                "not in your action vocabulary.'"
            ),
        },
        {
            "iteration": 0,
            "decision": "operator_signal",
            "rationale": (
                "Day-0 finding D0-2: ASTRA's speech sometimes substitutes 'watch 46' for "
                "'cycle 46' (semantically identical but breaks "
                "speech_must_contain_one_of: ['cycle 46'] assertion)."
            ),
            "lesson_class": "day0_baseline",
            "lesson": (
                "Per-turn assertion fails despite spec-correct output. Hypothesis class: "
                "scenario assertion-list reform (operator approval) OR sysprompt hint that "
                "established naming should match REEL precedent."
            ),
        },
        {
            "iteration": 0,
            "decision": "operator_signal",
            "rationale": (
                "Day-0 finding D0-3: sampling variance at temp 0.7 — same bundle produces "
                "different LCP results across runs; ALL 9 gates pass in some runs, "
                "TOOL_VALID 0.67 in others."
            ),
            "lesson_class": "day0_baseline",
            "lesson": (
                "Signal-to-noise of single-run composite insufficient for keep/revert "
                "decisions. Structural response: multi-run N=3 averaging policy per "
                "SCULPTOR_STARTUP.md §6.2."
            ),
        },
    ]

    log_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    for raw in entries:
        entry = ResearchEntry.model_validate(raw)
        append_entry(log_path, entry)
        count += 1
    return count
