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
from astra.sculptor.convergence import (
    ConvergenceReport,
    ConvergenceStatus,
    check_convergence,
    render_synthesis_block,
    write_stuck_diagnostic,
    write_ue5_readiness_checklist,
)
from astra.sculptor.hypothesis import (
    HypothesisGenerator,
    StubHypothesisGenerator,
    apply_hypothesis,
)
from astra.sculptor.judges import (
    DualJudge,
    render_transcript_for_judge,
)
from astra.sculptor.pytest_gate import (
    DEFAULT_PYTEST_TIMEOUT_S,
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
from astra.sculptor.runner_loop import IterationStatus
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
    model_name: str = "astra"
    api_key: str | None = None
    extra_payload: dict[str, object] | None = None
    scope_contract: ScopeContract = field(init=False)
    enforcer: ScopeEnforcer = field(init=False)
    weights: CompositeWeights = field(init=False)
    budget: Budget = field(init=False)
    hypothesis_generator: HypothesisGenerator = field(default_factory=StubHypothesisGenerator)
    dual_judge: DualJudge | None = None
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
                # Revert and log. Distinguish timeout / unparseable-fail / real-fail
                # in the rationale so future operator forensics have signal.
                target_path.write_text(baseline_contents, encoding="utf-8")
                if pytest_result.timed_out:
                    rationale = (
                        f"pytest timed out at iter {self.iteration_count} "
                        f"(>{int(DEFAULT_PYTEST_TIMEOUT_S)}s); change reverted. "
                        f"Likely substrate-setup overhead, not a real bench break."
                    )
                elif not pytest_result.failed_tests:
                    rationale = (
                        f"pytest exited {pytest_result.exit_code} with no FAILED "
                        f"markers (collection error or environmental flake); "
                        f"change reverted."
                    )
                else:
                    rationale = (
                        f"pytest suite broke at iter {self.iteration_count}; "
                        f"{len(pytest_result.failed_tests)} test(s) failed; "
                        f"change reverted."
                    )
                entry = build_bench_regression_entry(
                    iteration=self.iteration_count,
                    failed_tests=pytest_result.failed_tests,
                    rationale=rationale,
                )
                append_entry(self._research_log_path(), entry)
                self._regenerate_findings()
                return IterationDecision(entry=entry, applied_to_disk=False)

        # 6. Evaluate (multi-run averaged) — first pass without judge signal.
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
            model_name=self.model_name,
            api_key=self.api_key,
            extra_payload=self.extra_payload,
        )

        # 6.1 Substrate-unhealthy graceful halt (B2 fix). If the bundle's
        # health probe failed even after retry-with-backoff, the substrate
        # has hit a hard limit (per-hour quota, auth lockout, outage). Don't
        # log a misleading falsification; surface it as operator_signal,
        # touch pause.flag, and return — operator can resume after fixing
        # the substrate condition.
        if avg_result.overall_status == IterationStatus.SERVER_UNHEALTHY:
            target_path.write_text(baseline_contents, encoding="utf-8")
            entry = ResearchEntry(
                iteration=self.iteration_count,
                decision="operator_signal",
                rationale=(
                    f"substrate unhealthy beyond retry budget at iter "
                    f"{self.iteration_count}; halting Sculptor and touching "
                    f"pause.flag. Resume with `astra sculptor-resume` after "
                    f"verifying substrate (rate quota, auth, network)."
                ),
                lesson_class="substrate_health",
            )
            append_entry(self._research_log_path(), entry)
            self._regenerate_findings()
            self._touch_pause_flag()
            return IterationDecision(entry=entry, applied_to_disk=False)

        # 6.5 If a dual-judge is wired, score the produced transcripts and
        # fold the judge signal into the composite. The judge sees rendered
        # operator+ASTRA prose only (no <think>, no perception bundles).
        if self.dual_judge is not None and avg_result.averaged_composite is not None:
            judge_signal = await self._compute_judge_signal(avg_result)
            avg_result.averaged_composite = avg_result.averaged_composite.model_copy(
                update={
                    "judge_pro_minus_anti": judge_signal,
                    "components": {
                        **avg_result.averaged_composite.components,
                        "judge_pro_minus_anti": (
                            self.weights.w_judge_pro_minus_anti
                            * judge_signal
                        ),
                    },
                    # Update composite_score to reflect the new judge contribution.
                    "composite_score": (
                        avg_result.averaged_composite.composite_score
                        - avg_result.averaged_composite.components.get(
                            "judge_pro_minus_anti", 0.0,
                        )
                        + self.weights.w_judge_pro_minus_anti * judge_signal
                    ),
                },
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
                # Synthesis #1 fix: tag promote entries with lesson_class so
                # render_synthesis_block can identify load-bearing classes,
                # not just unproductive ones (falsified entries already have it).
                lesson_class=hypothesis.lesson_class,
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
            self.maybe_write_synthesis(window=20)
            if self._converged():
                self.write_convergence_artifacts()
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
        """Convergence check delegating to Sculptor-E's check_convergence."""
        report = self.convergence_status()
        return report.status == ConvergenceStatus.CONVERGED

    def convergence_status(self) -> ConvergenceReport:
        """Build a ConvergenceReport from the current research log."""
        entries = read_entries(self._research_log_path())
        return check_convergence(
            entries=entries,
            library_dir=self.textverse_root / "astra" / "scenarios" / "library",
            weights=self.weights,
        )

    def write_convergence_artifacts(self) -> ConvergenceReport:
        """If converged or stuck, write the appropriate artifact file.

        - CONVERGED → tuning/ue5_readiness_checklist.md +
                      tuning/READY_FOR_UE5.md flag
        - STUCK     → tuning/stuck_diagnostic.md
        - NOT_YET   → no artifact written

        Returns the ConvergenceReport so the caller can act on it.
        """
        report = self.convergence_status()
        if report.status == ConvergenceStatus.CONVERGED:
            scenario_count = len(
                list((self.textverse_root / "astra" / "scenarios" / "library").glob("*.yaml")),
            )
            write_ue5_readiness_checklist(
                self.textverse_root / "tuning" / "ue5_readiness_checklist.md",
                convergence=report,
                weights=self.weights,
                anchor_scenarios=list(self.scope_contract.anchor_scenarios),
                scenario_count=scenario_count,
            )
            ready_flag = self.textverse_root / "tuning" / "READY_FOR_UE5.md"
            ready_flag.write_text(
                "# READY_FOR_UE5\n\n"
                f"Sculptor declared convergence at iteration "
                f"{report.iteration_count}.\n"
                f"Composite: {report.composite_score:.4f}\n",
                encoding="utf-8",
            )
        elif report.status == ConvergenceStatus.STUCK:
            write_stuck_diagnostic(
                self.textverse_root / "tuning" / "stuck_diagnostic.md",
                report,
                self.weights,
            )
        return report

    def maybe_write_synthesis(self, window: int = 20) -> None:
        """Append a synthesis block to findings.md every `window` iterations."""
        if self.iteration_count % window != 0 or self.iteration_count == 0:
            return
        entries = read_entries(self._research_log_path())
        synthesis = render_synthesis_block(entries, window=window)
        findings_path = self._findings_path()
        existing = (
            findings_path.read_text(encoding="utf-8")
            if findings_path.is_file()
            else ""
        )
        findings_path.parent.mkdir(parents=True, exist_ok=True)
        findings_path.write_text(existing + "\n\n" + synthesis, encoding="utf-8")

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

    def _touch_pause_flag(self) -> None:
        """Write tuning/pause.flag so the next iteration boundary halts."""
        flag = self.textverse_root / self.scope_contract.signals.get("pause_flag", "")
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("paused by substrate-unhealthy graceful halt\n", encoding="utf-8")

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

    async def _compute_judge_signal(
        self,
        avg_result: AveragedIterationResult,
    ) -> float:
        """Mean (pro − anti) across all transcripts produced this iteration.

        Renders each scenario's TurnRecord list as plain prose (operator
        + ASTRA only, no <think>) and asks the dual-judge to score.
        """
        if self.dual_judge is None:
            return 0.0
        transcripts: list[str] = []
        for run in avg_result.runs:
            for report in run.scenario_reports:
                rendered = render_transcript_for_judge(
                    [rec.model_dump() for rec in report.turn_records],
                )
                transcripts.append(rendered)
        if not transcripts:
            return 0.0
        return await self.dual_judge.evaluate_many(transcripts)


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
