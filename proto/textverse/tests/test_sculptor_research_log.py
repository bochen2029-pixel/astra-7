"""Sculptor-A tests for the append-only research log + findings renderer."""

from __future__ import annotations

from pathlib import Path

from astra.sculptor import (
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

# --- ResearchEntry shape ----------------------------------------------------

def test_research_entry_frozen() -> None:
    e = ResearchEntry(iteration=1, decision="promote")
    try:
        e.iteration = 2
    except Exception:
        return
    raise AssertionError("ResearchEntry must be frozen")


def test_promote_entry_builder() -> None:
    e = build_promote_entry(
        iteration=5,
        hypothesis="strengthen anti-performance paragraph",
        change_summary="add one sentence to anti-performance discipline",
        composite_score=0.85,
        delta_vs_best=0.04,
        per_gate_changes={"persona_stable": 0.2},
        rationale="Gate 3 improved without other regressions",
    )
    assert e.decision == "promote"
    assert e.composite_score == 0.85


def test_falsified_entry_builder() -> None:
    e = build_falsified_entry(
        iteration=7,
        hypothesis="adding 'silence is legal' increases silence rate",
        falsification_reasoning="model interprets permission as anti-discipline",
        lesson_class="permission-vs-instruction-failure",
        lesson="discipline rules work as constraints, not permissions",
    )
    assert e.decision == "falsified"
    assert "permission" in e.lesson_class


def test_scope_refused_entry_builder() -> None:
    e = build_scope_refused_entry(
        iteration=9,
        relpath="docs/spec-v0.128.md",
        rationale="file is locked",
    )
    assert e.decision == "scope_refused"
    assert e.scope_refusal_path == "docs/spec-v0.128.md"


def test_bench_regression_entry_builder() -> None:
    e = build_bench_regression_entry(
        iteration=11,
        failed_tests=["tests/test_grammar_parser.py::test_strip_rule"],
    )
    assert e.decision == "bench_regression"
    assert len(e.pytest_failed_tests) == 1


# --- Append + read ----------------------------------------------------------

def test_append_and_read_entries(tmp_path: Path) -> None:
    log = tmp_path / "research_log.jsonl"
    append_entry(log, build_promote_entry(
        iteration=1,
        hypothesis="h1",
        change_summary="c1",
        composite_score=0.7,
        delta_vs_best=0.0,
        per_gate_changes={},
        rationale="initial baseline",
    ))
    append_entry(log, build_falsified_entry(
        iteration=2,
        hypothesis="h2",
        falsification_reasoning="r",
        lesson_class="x",
        lesson="y",
    ))
    entries = read_entries(log)
    assert len(entries) == 2
    assert entries[0].decision == "promote"
    assert entries[1].decision == "falsified"


def test_read_empty_log_returns_empty(tmp_path: Path) -> None:
    assert read_entries(tmp_path / "missing.jsonl") == []


def test_latest_entry_returns_last(tmp_path: Path) -> None:
    log = tmp_path / "rl.jsonl"
    append_entry(log, ResearchEntry(iteration=1, decision="promote"))
    append_entry(log, ResearchEntry(iteration=2, decision="falsified"))
    latest = latest_entry(log)
    assert latest is not None
    assert latest.iteration == 2


def test_latest_promote_skips_non_promote(tmp_path: Path) -> None:
    log = tmp_path / "rl.jsonl"
    append_entry(log, ResearchEntry(iteration=1, decision="promote", composite_score=0.7))
    append_entry(log, ResearchEntry(iteration=2, decision="falsified"))
    append_entry(log, ResearchEntry(iteration=3, decision="scope_refused"))
    p = latest_promote(log)
    assert p is not None
    assert p.iteration == 1


# --- Proposals --------------------------------------------------------------

def test_append_proposal_separator(tmp_path: Path) -> None:
    p = tmp_path / "proposals.md"
    append_proposal(p, "## Scenario gap proposal\n\nBody.")
    append_proposal(p, "## Another proposal\n\nBody2.")
    text = p.read_text(encoding="utf-8")
    assert "## Scenario gap proposal" in text
    assert "## Another proposal" in text
    assert "---" in text   # separator between proposals


# --- findings.md rendering --------------------------------------------------

def test_render_findings_empty() -> None:
    text = render_findings_md([])
    assert "no iterations yet" in text.lower()


def test_render_findings_with_promotes_and_falsified() -> None:
    entries = [
        build_promote_entry(
            iteration=1, hypothesis="h", change_summary="c",
            composite_score=0.80, delta_vs_best=0.05,
            per_gate_changes={}, rationale="r",
        ),
        build_falsified_entry(
            iteration=2, hypothesis="bad_idea",
            falsification_reasoning="model regressed",
            lesson_class="X", lesson="don't try this",
        ),
    ]
    text = render_findings_md(entries)
    assert "Current best" in text
    assert "0.80" in text or "0.8000" in text
    assert "Falsified hypotheses" in text
    assert "bad_idea" in text


def test_render_findings_counts_decisions() -> None:
    entries = [
        ResearchEntry(iteration=1, decision="promote"),
        ResearchEntry(iteration=2, decision="promote"),
        ResearchEntry(iteration=3, decision="falsified"),
    ]
    text = render_findings_md(entries)
    assert "`promote`: 2" in text
    assert "`falsified`: 1" in text


def test_write_findings_md(tmp_path: Path) -> None:
    log = tmp_path / "rl.jsonl"
    append_entry(log, build_promote_entry(
        iteration=1, hypothesis="h", change_summary="c",
        composite_score=0.75, delta_vs_best=0.0,
        per_gate_changes={}, rationale="r",
    ))
    findings = tmp_path / "findings.md"
    write_findings_md(log, findings)
    assert findings.is_file()
    text = findings.read_text(encoding="utf-8")
    assert "Current best" in text


# --- daily_report.md rendering ---------------------------------------------

def test_render_daily_report_empty() -> None:
    text = render_daily_report([])
    assert "No activity" in text


def test_render_daily_report_includes_recent_activity() -> None:
    entries = [
        build_promote_entry(
            iteration=i,
            hypothesis=f"h{i}",
            change_summary=f"c{i}",
            composite_score=0.7 + i * 0.01,
            delta_vs_best=0.01,
            per_gate_changes={},
            rationale=f"r{i}",
        )
        for i in range(5)
    ]
    text = render_daily_report(entries)
    assert "Latest iteration: **4**" in text
    assert "Total iterations: **5**" in text


def test_write_daily_report(tmp_path: Path) -> None:
    log = tmp_path / "rl.jsonl"
    append_entry(log, ResearchEntry(iteration=1, decision="promote", composite_score=0.7))
    report = tmp_path / "daily_report.md"
    write_daily_report(log, report)
    assert report.is_file()
