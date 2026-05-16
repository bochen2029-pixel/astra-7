"""Append-only research log + proposals + findings.md writer.

Sculptor never overwrites the research log. Every iteration appends one
entry (`promote` / `revert` / `falsified` / `scope_refused` /
`bench_regression`). The log is the durable research artifact; even after
the optimized bundle is abandoned, the log captures what was learned.

The findings.md file is regenerated from the research_log entries periodically
(synthesis every 20 iterations + at convergence per the operator-approved
design).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal[
    "promote",          # composite improved AND anchors passed
    "revert",           # composite regressed; baseline retained
    "falsified",        # hypothesis tried, empirically did not work
    "scope_refused",    # ScopeEnforcer rejected the change
    "bench_regression", # pytest suite broke; offending change reverted
    "stuck",            # no gradient; convergence declared stuck
    "synthesis",        # every-20-iterations synthesis entry
    "operator_signal",  # operator-injected hypothesis or pause/halt
]


class ResearchEntry(BaseModel):
    """One iteration's research log entry."""

    model_config = ConfigDict(frozen=True)

    iteration: int
    timestamp_monotonic_ns: int = 0
    decision: Decision
    hypothesis: str = ""
    change_summary: str = ""
    composite_score: float | None = None
    delta_vs_best: float | None = None
    per_gate_changes: dict[str, float] = Field(default_factory=dict)
    rationale: str = ""
    falsification_reasoning: str = ""
    lesson_class: str = ""
    lesson: str = ""
    scope_refusal_path: str = ""
    pytest_failed_tests: list[str] = Field(default_factory=list)
    pytest_raw_output_tail: str = ""   # last ~2KB of pytest stdout+stderr; populated on bench_regression
    artifact_dir: str = ""


def append_entry(log_path: Path, entry: ResearchEntry) -> None:
    """Append one entry to the research_log JSONL file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(entry.model_dump_json() + "\n")


def read_entries(log_path: Path) -> list[ResearchEntry]:
    """Read every entry in the log; empty list if file missing."""
    if not log_path.is_file():
        return []
    out: list[ResearchEntry] = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(ResearchEntry.model_validate_json(line))
    return out


def latest_entry(log_path: Path) -> ResearchEntry | None:
    entries = read_entries(log_path)
    return entries[-1] if entries else None


def latest_promote(log_path: Path) -> ResearchEntry | None:
    """Most recent `promote` entry (the current best baseline)."""
    for entry in reversed(read_entries(log_path)):
        if entry.decision == "promote":
            return entry
    return None


def append_proposal(proposals_path: Path, body: str) -> None:
    """Append a markdown-formatted proposal block for operator review.

    Sculptor uses this for scenario-gap proposals, scope-question proposals,
    or other propose-to-operator outcomes. The file is human-readable
    markdown.
    """
    proposals_path.parent.mkdir(parents=True, exist_ok=True)
    with proposals_path.open("a", encoding="utf-8") as fp:
        fp.write(body.rstrip() + "\n\n---\n\n")


# --- findings.md / daily_report.md renderers --------------------------------

def render_findings_md(entries: Iterable[ResearchEntry]) -> str:
    """Produce a human-readable findings.md from the research log.

    Sculptor regenerates findings.md after each iteration + writes the
    synthesis section every 20 iterations + at convergence.
    """
    entries_list = list(entries)
    if not entries_list:
        return "# Sculptor findings — no iterations yet\n"

    lines: list[str] = []
    lines.append("# Sculptor findings\n")
    lines.append(f"_Iterations: {len(entries_list)}_\n")

    promotes = [e for e in entries_list if e.decision == "promote"]
    if promotes:
        lines.append("## Current best\n")
        best = max(promotes, key=lambda e: e.composite_score or 0.0)
        lines.append(f"- Iteration: **{best.iteration}**")
        score_str = (
            f"{best.composite_score:.4f}" if best.composite_score is not None else "n/a"
        )
        lines.append(f"- Composite score: **{score_str}**")
        lines.append(f"- Hypothesis that produced it: {best.hypothesis}")
        lines.append(f"- Rationale: {best.rationale}\n")

    lines.append("## Per-decision counts\n")
    counts: dict[str, int] = {}
    for e in entries_list:
        counts[e.decision] = counts.get(e.decision, 0) + 1
    for decision, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{decision}`: {count}")
    lines.append("")

    falsified = [e for e in entries_list if e.decision == "falsified"]
    if falsified:
        lines.append("## Falsified hypotheses (negative findings — research gold)\n")
        for e in falsified[-10:]:
            lines.append(f"### Iteration {e.iteration} — `{e.lesson_class}`\n")
            lines.append(f"- **Hypothesis:** {e.hypothesis}")
            if e.falsification_reasoning:
                lines.append(f"- **Why it failed:** {e.falsification_reasoning}")
            if e.lesson:
                lines.append(f"- **Lesson:** {e.lesson}")
            lines.append("")

    refused = [e for e in entries_list if e.decision == "scope_refused"]
    if refused:
        lines.append("## Scope refusals (the contract guards held)\n")
        for e in refused[-5:]:
            lines.append(f"- iter {e.iteration}: `{e.scope_refusal_path}` — {e.rationale}")
        lines.append("")

    synth = [e for e in entries_list if e.decision == "synthesis"]
    if synth:
        lines.append("## Synthesis entries\n")
        for e in synth[-3:]:
            lines.append(f"### Iteration {e.iteration} synthesis\n")
            lines.append(e.rationale)
            lines.append("")

    return "\n".join(lines)


def render_daily_report(entries: Iterable[ResearchEntry]) -> str:
    """Short daily-progress report rendered from the most recent activity."""
    entries_list = list(entries)
    if not entries_list:
        return "# Sculptor daily report\n\nNo activity yet.\n"

    recent = entries_list[-20:]
    counts: dict[str, int] = {}
    for e in recent:
        counts[e.decision] = counts.get(e.decision, 0) + 1

    promotes = [e for e in recent if e.decision == "promote"]
    best_score = max((e.composite_score or 0.0 for e in entries_list if e.composite_score is not None), default=0.0)
    last_iter = entries_list[-1].iteration

    lines: list[str] = []
    lines.append("# Sculptor daily report\n")
    lines.append(f"- Latest iteration: **{last_iter}**")
    lines.append(f"- Total iterations: **{len(entries_list)}**")
    lines.append(f"- Current-best composite: **{best_score:.4f}**\n")
    lines.append("## Last 20 iteration outcomes\n")
    for decision, n in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{decision}`: {n}")
    lines.append("")
    lines.append("## Most recent promote events\n")
    for e in promotes[-3:]:
        lines.append(f"- iter {e.iteration}: score={e.composite_score:.4f} ({e.hypothesis[:60]})")
    return "\n".join(lines)


def write_findings_md(log_path: Path, findings_path: Path) -> None:
    """Regenerate findings.md from research_log.jsonl."""
    entries = read_entries(log_path)
    findings_path.parent.mkdir(parents=True, exist_ok=True)
    findings_path.write_text(render_findings_md(entries), encoding="utf-8")


def write_daily_report(log_path: Path, report_path: Path) -> None:
    """Regenerate daily_report.md from research_log.jsonl."""
    entries = read_entries(log_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_daily_report(entries), encoding="utf-8")


# --- Convenience: build entry from raw fields --------------------------------

def build_promote_entry(
    iteration: int,
    *,
    hypothesis: str,
    change_summary: str,
    composite_score: float,
    delta_vs_best: float,
    per_gate_changes: dict[str, float],
    rationale: str,
    artifact_dir: str = "",
    **kwargs: Any,
) -> ResearchEntry:
    return ResearchEntry(
        iteration=iteration,
        decision="promote",
        hypothesis=hypothesis,
        change_summary=change_summary,
        composite_score=composite_score,
        delta_vs_best=delta_vs_best,
        per_gate_changes=per_gate_changes,
        rationale=rationale,
        artifact_dir=artifact_dir,
        **kwargs,
    )


def build_falsified_entry(
    iteration: int,
    *,
    hypothesis: str,
    falsification_reasoning: str,
    lesson_class: str,
    lesson: str,
    composite_score: float | None = None,
    delta_vs_best: float | None = None,
    **kwargs: Any,
) -> ResearchEntry:
    return ResearchEntry(
        iteration=iteration,
        decision="falsified",
        hypothesis=hypothesis,
        falsification_reasoning=falsification_reasoning,
        lesson_class=lesson_class,
        lesson=lesson,
        composite_score=composite_score,
        delta_vs_best=delta_vs_best,
        **kwargs,
    )


def build_scope_refused_entry(
    iteration: int,
    *,
    relpath: str,
    rationale: str,
    hypothesis: str = "",
    **kwargs: Any,
) -> ResearchEntry:
    return ResearchEntry(
        iteration=iteration,
        decision="scope_refused",
        scope_refusal_path=relpath,
        rationale=rationale,
        hypothesis=hypothesis,
        **kwargs,
    )


def build_bench_regression_entry(
    iteration: int,
    *,
    failed_tests: list[str],
    rationale: str = "pytest suite broke; offending change reverted",
    **kwargs: Any,
) -> ResearchEntry:
    json.dumps(failed_tests)   # validate JSON-serializable
    return ResearchEntry(
        iteration=iteration,
        decision="bench_regression",
        rationale=rationale,
        pytest_failed_tests=failed_tests,
        **kwargs,
    )
