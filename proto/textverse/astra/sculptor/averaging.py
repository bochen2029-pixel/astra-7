"""Multi-run averaging for primary composite scoring.

Sampling variance at temperature 0.7 is real: the same bundle produces
different LCP results across runs (Day-0 finding D0-3). For the
meta-agent's keep/revert decisions, single-run composite is too noisy.

Hybrid policy per SCULPTOR_STARTUP.md §6.2:
- **Primary composite**: N=3 runs averaged. Signal-to-noise improves √3.
- **Seeded determinism**: if `tuning/sampling.json` has `seed` set, runs
  reproduce. The seed is part of the ConfigSnapshot hash.
- **Periodic robustness**: every 20 iterations, the current best gets
  evaluated at 3 different seeds; if variance > 0.10 across seeds, log
  a `fragile_config` warning.

This module implements only the averaging layer. The cadence-driven
robustness check is in `meta_agent.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from astra.judge import LCPGate
from astra.sculptor.composite import (
    CompositeResult,
    CompositeWeights,
)
from astra.sculptor.runner_loop import (
    IterationResult,
    IterationStatus,
    run_iteration,
)


@dataclass(slots=True)
class AveragedIterationResult:
    """Result of running an iteration N times and averaging the composite."""

    iteration_id: str
    config_hash: str
    n_runs: int
    runs: list[IterationResult] = field(default_factory=list)
    averaged_composite: CompositeResult | None = None
    overall_status: IterationStatus = IterationStatus.OK
    anchor_scenarios_passed: bool = True
    composite_score_variance: float = 0.0

    @property
    def composite_score(self) -> float:
        return (
            self.averaged_composite.composite_score
            if self.averaged_composite is not None
            else 0.0
        )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def _averaged_per_gate(
    runs: list[IterationResult],
) -> dict[LCPGate, float]:
    """Average per-gate session pass rates across runs."""
    if not runs:
        return {}
    accum: dict[LCPGate, list[float]] = {}
    for run in runs:
        if run.composite is None:
            continue
        for gate, rate in run.composite.per_gate_session_rates.items():
            accum.setdefault(gate, []).append(rate)
    return {gate: _mean(rates) for gate, rates in accum.items()}


async def evaluate_config_averaged(
    *,
    base_iteration_id: str,
    n_runs: int,
    base_url: str,
    textverse_root: Path,
    library_dir: Path,
    history_root: Path,
    output_root: Path,
    weights: CompositeWeights,
    anchor_scenarios: list[str],
    judge_pro_minus_anti: float = 0.0,
    drift_score: float = 0.0,
    model_name: str = "astra",
    api_key: str | None = None,
    extra_payload: dict[str, object] | None = None,
) -> AveragedIterationResult:
    """Run `n_runs` iterations of the same config; return averaged composite.

    Each sub-iteration gets a unique iteration_id (suffixed `_runN`) so
    history archive directories don't collide. The returned
    `averaged_composite` is a CompositeResult whose `composite_score` is
    the MEAN of sub-run scores; other fields copy the last sub-run for
    metadata.

    Crash semantics:
    - Any sub-run with SERVER_UNHEALTHY status → return overall_status
      SERVER_UNHEALTHY immediately; don't continue remaining runs.
    - Sub-runs with PARTIAL status are included in the average; the
      caller decides whether PARTIAL is promote-eligible.
    """
    runs: list[IterationResult] = []
    for run_idx in range(n_runs):
        iter_id = f"{base_iteration_id}_run{run_idx + 1}"
        result = await run_iteration(
            iteration_id=iter_id,
            base_url=base_url,
            textverse_root=textverse_root,
            library_dir=library_dir,
            history_root=history_root,
            output_root=output_root,
            weights=weights,
            anchor_scenarios=anchor_scenarios,
            judge_pro_minus_anti=judge_pro_minus_anti,
            drift_score=drift_score,
            model_name=model_name,
            api_key=api_key,
            extra_payload=extra_payload,
        )
        runs.append(result)
        if result.status == IterationStatus.SERVER_UNHEALTHY:
            return AveragedIterationResult(
                iteration_id=base_iteration_id,
                config_hash=result.config_hash,
                n_runs=run_idx + 1,
                runs=runs,
                averaged_composite=None,
                overall_status=IterationStatus.SERVER_UNHEALTHY,
                anchor_scenarios_passed=False,
            )

    # Collect composites that exist (skip NO_SCENARIOS / aborts)
    valid = [r for r in runs if r.composite is not None]
    if not valid:
        return AveragedIterationResult(
            iteration_id=base_iteration_id,
            config_hash=runs[0].config_hash if runs else "absent",
            n_runs=n_runs,
            runs=runs,
            averaged_composite=None,
            overall_status=IterationStatus.NO_SCENARIOS,
            anchor_scenarios_passed=False,
        )

    composite_scores = [r.composite.composite_score for r in valid if r.composite is not None]
    mean_score = _mean(composite_scores)
    variance = _variance(composite_scores)

    # Anchor pass = ALL sub-runs must have anchor passing.
    anchor_passed = all(r.anchor_scenarios_passed for r in valid)

    # Use the last sub-run's metadata as the template; replace
    # the composite_score field and per-gate session rates with means.
    template = valid[-1].composite
    assert template is not None
    averaged = template.model_copy(
        update={
            "composite_score": mean_score,
            "per_gate_session_rates": _averaged_per_gate(runs),
            "anchor_scenarios_passed": anchor_passed,
        }
    )

    # If any sub-run was PARTIAL, the averaged status reflects that.
    has_partial = any(r.status == IterationStatus.PARTIAL for r in runs)
    overall_status = IterationStatus.PARTIAL if has_partial else IterationStatus.OK

    return AveragedIterationResult(
        iteration_id=base_iteration_id,
        config_hash=valid[-1].config_hash,
        n_runs=n_runs,
        runs=runs,
        averaged_composite=averaged,
        overall_status=overall_status,
        anchor_scenarios_passed=anchor_passed,
        composite_score_variance=variance,
    )


def is_fragile(result: AveragedIterationResult, *, variance_threshold: float = 0.01) -> bool:
    """True iff the cross-run composite variance is high.

    Variance threshold defaults to 0.01 — translates to ~10% stddev on a
    typical [0.4, 0.9] composite range. Tunable per SCULPTOR_STARTUP.md.
    """
    return result.composite_score_variance > variance_threshold
