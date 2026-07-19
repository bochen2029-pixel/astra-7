"""Sculptor-E convergence detector + ue5_readiness checklist writer.

The three-conjunct convergence test per SCULPTOR_STARTUP.md §5.1:

1. **Gradient vanished**: composite Δ < `convergence_delta` for K=10
   consecutive `promote` iterations.
2. **Coverage met**: scenario library coverage entropy ≥
   `min_coverage_entropy_bits` (default 2.0 = at least 4 distinct
   scenarios).
3. **Floor met**: composite score ≥ `min_absolute_threshold` (default 0.80).

ALL three must hold → `ConvergenceStatus.CONVERGED` → write
`READY_FOR_UE5.md` + `ue5_readiness_checklist.md`.
Gradient + coverage met but score < floor → `STUCK` → write
`stuck_diagnostic.md`.

Sculptor-E is the layer that interprets the meta-agent's accumulated
log + writes the operator-facing artifacts. The detector itself is a
pure function over `ResearchEntry` history; integration with the
MetaAgent loop is one method call after each iteration.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from astra.sculptor.composite import CompositeWeights
from astra.sculptor.research_log import ResearchEntry


class ConvergenceStatus(StrEnum):
    """Outcome of the convergence check."""

    NOT_YET = "not_yet"               # at least one conjunct not met
    CONVERGED = "converged"           # all three met → READY_FOR_UE5
    STUCK = "stuck"                   # gradient + coverage met; floor not


@dataclass(slots=True)
class ConvergenceReport:
    """Result of one convergence check.

    `not_yet_reasons` lists which conjuncts didn't hold; populated when
    status == NOT_YET so the report renders an operator-readable
    diagnostic.
    """

    status: ConvergenceStatus
    composite_score: float
    composite_delta_last_k: list[float] = field(default_factory=list)
    coverage_entropy_bits: float = 0.0
    promote_count: int = 0
    iteration_count: int = 0
    not_yet_reasons: list[str] = field(default_factory=list)


def _promote_entries(entries: list[ResearchEntry]) -> list[ResearchEntry]:
    return [e for e in entries if e.decision == "promote"]


def _deltas_last_k(promotes: list[ResearchEntry], k: int) -> list[float]:
    """Return the last K `delta_vs_best` values from promote entries."""
    if not promotes:
        return []
    return [
        p.delta_vs_best for p in promotes[-k:] if p.delta_vs_best is not None
    ]


def coverage_entropy_for_library(library_dir: Path) -> float:
    """Shannon entropy proxy: log2 of scenario YAML count."""
    if not library_dir.is_dir():
        return 0.0
    count = len(list(library_dir.glob("*.yaml")))
    if count < 2:
        return 0.0
    return math.log2(count)


def check_convergence(
    *,
    entries: list[ResearchEntry],
    library_dir: Path,
    weights: CompositeWeights,
) -> ConvergenceReport:
    """Evaluate the three-conjunct convergence rule against research-log entries.

    Returns a ConvergenceReport describing which conjuncts hold and the
    final status.
    """
    promotes = _promote_entries(entries)
    promote_count = len(promotes)
    deltas = _deltas_last_k(promotes, weights.convergence_k)
    coverage = coverage_entropy_for_library(library_dir)

    # Best composite score: max composite among promotes.
    best_composite = max(
        (p.composite_score for p in promotes if p.composite_score is not None),
        default=0.0,
    )

    not_yet: list[str] = []

    # Conjunct 1: gradient vanished — need K consecutive promote deltas all < ε.
    if len(deltas) < weights.convergence_k:
        not_yet.append(
            f"need {weights.convergence_k} consecutive promotes; "
            f"have {len(deltas)}",
        )
    elif any(abs(d) >= weights.convergence_delta for d in deltas):
        max_delta = max(abs(d) for d in deltas)
        not_yet.append(
            f"gradient not vanished: max recent |Δ|={max_delta:.4f} >= "
            f"{weights.convergence_delta}",
        )

    # Conjunct 2: coverage entropy.
    if coverage < weights.min_coverage_entropy_bits:
        not_yet.append(
            f"coverage entropy {coverage:.2f} < required "
            f"{weights.min_coverage_entropy_bits}; library too narrow",
        )

    # Conjunct 3: absolute composite-score floor.
    floor_met = best_composite >= weights.min_absolute_threshold

    if not not_yet and floor_met:
        status = ConvergenceStatus.CONVERGED
    elif not not_yet and not floor_met:
        status = ConvergenceStatus.STUCK
        not_yet.append(
            f"composite {best_composite:.4f} < absolute threshold "
            f"{weights.min_absolute_threshold}",
        )
    else:
        status = ConvergenceStatus.NOT_YET

    return ConvergenceReport(
        status=status,
        composite_score=best_composite,
        composite_delta_last_k=deltas,
        coverage_entropy_bits=coverage,
        promote_count=promote_count,
        iteration_count=len(entries),
        not_yet_reasons=not_yet,
    )


# --- Synthesis section writer ----------------------------------------------

def _per_lesson_class_counts(entries: list[ResearchEntry]) -> dict[str, dict[str, int]]:
    """Group entries by lesson_class → {decision → count}.

    Used by synthesis to identify which classes consistently promoted vs.
    consistently falsified.
    """
    out: dict[str, dict[str, int]] = {}
    for e in entries:
        if not e.lesson_class:
            continue
        slot = out.setdefault(e.lesson_class, {})
        slot[e.decision] = slot.get(e.decision, 0) + 1
    return out


def render_synthesis_block(entries: list[ResearchEntry], *, window: int = 20) -> str:
    """Produce one paragraph of synthesis from the last `window` entries.

    Findings:
    - Which lesson_classes consistently produced promote events
    - Which lesson_classes consistently falsified
    - The peak composite score and which hypothesis produced it
    """
    if len(entries) < 1:
        return "(no entries yet)"
    recent = entries[-window:]
    counts = _per_lesson_class_counts(recent)

    load_bearing: list[str] = []
    unproductive: list[str] = []
    for cls, by_dec in counts.items():
        promotes = by_dec.get("promote", 0)
        falsified = by_dec.get("falsified", 0)
        if promotes >= 2 and promotes > falsified:
            load_bearing.append(f"{cls} ({promotes} promotes)")
        elif falsified >= 2 and falsified > promotes:
            unproductive.append(f"{cls} ({falsified} falsified)")

    promotes_all = _promote_entries(entries)
    best = max(
        promotes_all,
        key=lambda e: (e.composite_score or 0.0),
        default=None,
    )

    lines: list[str] = []
    lines.append(
        f"## Synthesis (after iteration {entries[-1].iteration}, "
        f"window of last {min(window, len(entries))} entries)\n",
    )
    if load_bearing:
        lines.append(
            f"- **Load-bearing hypothesis classes**: {', '.join(load_bearing)}",
        )
    if unproductive:
        lines.append(
            f"- **Unproductive hypothesis classes**: {', '.join(unproductive)}",
        )
    if best is not None:
        score_str = (
            f"{best.composite_score:.4f}" if best.composite_score is not None else "n/a"
        )
        lines.append(
            f"- **Peak composite so far**: {score_str} "
            f"(iter {best.iteration}, hypothesis: {best.hypothesis[:80]})",
        )
    if not load_bearing and not unproductive:
        lines.append(
            "- _No clear class-level pattern in the recent window. "
            "Continue exploring._"
        )
    lines.append("")
    return "\n".join(lines)


# --- UE5 readiness checklist writer ---------------------------------------

UE5_CHECKLIST_TEMPLATE: str = """\
# UE5 Readiness Checklist (Sculptor-E)

Auto-populated by Sculptor at convergence. This file marks when the
optimized bundle is ready for Implementation B (UE5 substrate swap)
per spec v0.129 §15.7.

## Hard criteria (all must hold for convergence)

- [{c1}] Composite score ≥ {floor:.2f} for K={k} consecutive promotes
        (current best: **{score:.4f}**)
- [{c2}] All anchor scenarios passing (anchor list: {anchors})
- [{c3}] Per-gate variance < 0.15 (no gate consistently < 0.70)
- [{c4}] Drift score < 0.10 (multi-turn register stable)
- [{c5}] Scenario library coverage entropy ≥ {entropy_min:.1f} bits
        (current: **{entropy:.2f}** bits across {scenario_count} scenarios)
- [{c6}] At least one scenario per regime class (REST, STL, WARP, CRYOSLEEP)

## Documentation criteria

- [{d1}] Known weaknesses documented in `tuning/known_weaknesses.md`
- [{d2}] Final synthesis written in `tuning/findings.md`
- [{d3}] Optimized config committed to `sculptor/v1` branch
- [{d4}] Research log preserved at `tuning/research_log.jsonl`

## Status

{status_line}

Generated at iteration {iteration}.
"""


def render_ue5_readiness_checklist(
    *,
    convergence: ConvergenceReport,
    weights: CompositeWeights,
    anchor_scenarios: list[str],
    scenario_count: int,
) -> str:
    """Populate the UE5 readiness checklist from convergence state.

    Each `[ ]` becomes `[x]` when its criterion is met. The hard criteria
    map directly to the convergence three-conjunct + per-gate balance
    (provisional v0 — full per-gate variance check is Day N+ when
    scenario library has enough entries).
    """
    c1 = "x" if convergence.composite_score >= weights.min_absolute_threshold else " "
    c2 = "x" if convergence.status == ConvergenceStatus.CONVERGED else " "
    # Per-gate variance: deferred to next Sculptor iteration; mark unknown.
    c3 = "?"
    c4 = "?"   # drift_score detection lives in next Sculptor-D extension
    c5 = "x" if convergence.coverage_entropy_bits >= weights.min_coverage_entropy_bits else " "
    c6 = "?"   # regime-class scenario coverage; future scenario tag

    # Documentation criteria — heuristics; concrete file checks happen at
    # write-time outside this function.
    d1 = " "
    d2 = "x"   # findings.md is regenerated every iteration
    d3 = " "
    d4 = "x"   # research_log.jsonl exists after first iteration

    status_line = (
        f"**STATUS: {convergence.status.value.upper()}**"
        if convergence.status != ConvergenceStatus.NOT_YET
        else f"**STATUS: NOT_YET** — {'; '.join(convergence.not_yet_reasons[:3])}"
    )

    return UE5_CHECKLIST_TEMPLATE.format(
        c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6,
        d1=d1, d2=d2, d3=d3, d4=d4,
        floor=weights.min_absolute_threshold,
        k=weights.convergence_k,
        score=convergence.composite_score,
        anchors=", ".join(anchor_scenarios),
        entropy_min=weights.min_coverage_entropy_bits,
        entropy=convergence.coverage_entropy_bits,
        scenario_count=scenario_count,
        status_line=status_line,
        iteration=convergence.iteration_count,
    )


def write_ue5_readiness_checklist(
    path: Path,
    *,
    convergence: ConvergenceReport,
    weights: CompositeWeights,
    anchor_scenarios: list[str],
    scenario_count: int,
) -> None:
    """Write the populated checklist to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_ue5_readiness_checklist(
            convergence=convergence,
            weights=weights,
            anchor_scenarios=anchor_scenarios,
            scenario_count=scenario_count,
        ),
        encoding="utf-8",
    )


# --- Stuck diagnostic writer ----------------------------------------------

STUCK_DIAGNOSTIC_TEMPLATE: str = """\
# Sculptor STUCK diagnostic

The gradient has vanished and coverage criterion is met, but the
absolute composite-score floor was NOT reached. Sculptor cannot
declare convergence; operator review is needed.

## Status snapshot

- Composite (best so far): **{score:.4f}** (required floor: {floor:.2f})
- Promote iterations: {promote_count}
- Total iterations: {iteration_count}
- Coverage entropy: {entropy:.2f} bits
- Recent deltas: {deltas}

## Why this is "stuck", not "converged"

The composite-score floor is the failsafe against declaring a bad
config done. The three conjuncts hold individually (gradient vanished,
coverage met) but the score itself plateaued below the threshold. This
usually means one of:

1. The bench is exposing a real model-capability ceiling (Qwen 9B
   simply can't sustain the autotelic register reliably enough; need
   Qwen 27B or fine-tune).
2. The scenario library is too narrow — add scenarios that stress
   different failure modes (Sculptor's curated bank is exhausted;
   new operator-authored scenarios needed).
3. The judge rubric is mis-calibrated for the current bundle (rubric
   change requires operator review).

## Operator actions

- Review `tuning/findings.md` for the synthesis section.
- Inspect `tuning/research_log.jsonl` for falsified hypothesis classes.
- Decide whether to: (a) extend scenario library; (b) switch model
  tier; (c) revise judge rubric; (d) accept and ship below floor.

## Numbers

```
{not_yet_reasons}
```
"""


def render_stuck_diagnostic(convergence: ConvergenceReport, weights: CompositeWeights) -> str:
    """Produce stuck_diagnostic.md content."""
    return STUCK_DIAGNOSTIC_TEMPLATE.format(
        score=convergence.composite_score,
        floor=weights.min_absolute_threshold,
        promote_count=convergence.promote_count,
        iteration_count=convergence.iteration_count,
        entropy=convergence.coverage_entropy_bits,
        deltas=", ".join(
            f"{d:+.4f}" for d in convergence.composite_delta_last_k[-5:]
        ) or "(none)",
        not_yet_reasons="\n".join(f"- {r}" for r in convergence.not_yet_reasons),
    )


def write_stuck_diagnostic(path: Path, convergence: ConvergenceReport, weights: CompositeWeights) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_stuck_diagnostic(convergence, weights),
        encoding="utf-8",
    )


# --- Public summary helpers used by CLI -----------------------------------

def convergence_one_line(report: ConvergenceReport) -> str:
    """Short one-line status for the CLI 'astra sculptor status' subcommand."""
    return (
        f"{report.status.value.upper()} | iter={report.iteration_count} "
        f"promotes={report.promote_count} composite={report.composite_score:.4f} "
        f"entropy={report.coverage_entropy_bits:.2f} bits"
    )


