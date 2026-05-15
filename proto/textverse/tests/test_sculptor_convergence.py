"""Sculptor-E tests for convergence detector + ue5_readiness + synthesis."""

from __future__ import annotations

from pathlib import Path

from astra.sculptor import (
    CompositeWeights,
    ConvergenceStatus,
    ResearchEntry,
    check_convergence,
    convergence_one_line,
    coverage_entropy_for_library,
    render_stuck_diagnostic,
    render_synthesis_block,
    render_ue5_readiness_checklist,
    write_stuck_diagnostic,
    write_ue5_readiness_checklist,
)
from astra.sculptor.convergence import ConvergenceReport

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent
LIBRARY_DIR = TEXTVERSE_ROOT / "astra" / "scenarios" / "library"


def _make_promote(iteration: int, composite_score: float, delta: float = 0.001) -> ResearchEntry:
    return ResearchEntry(
        iteration=iteration,
        decision="promote",
        hypothesis=f"h{iteration}",
        composite_score=composite_score,
        delta_vs_best=delta,
        lesson_class="persona_stability",
    )


# --- coverage_entropy_for_library -----------------------------------------

def test_coverage_entropy_real_library() -> None:
    """The current library has at least 1 scenario; entropy = log2(count)."""
    entropy = coverage_entropy_for_library(LIBRARY_DIR)
    # 1 scenario → 0 bits; 2 → 1 bit; etc. v0 ships exactly 1 scenario.
    assert entropy >= 0.0


def test_coverage_entropy_empty_dir(tmp_path: Path) -> None:
    assert coverage_entropy_for_library(tmp_path) == 0.0


def test_coverage_entropy_four_scenarios_two_bits(tmp_path: Path) -> None:
    for i in range(4):
        (tmp_path / f"s{i}.yaml").write_text("name: x", encoding="utf-8")
    entropy = coverage_entropy_for_library(tmp_path)
    assert abs(entropy - 2.0) < 1e-9


# --- check_convergence ----------------------------------------------------

def test_convergence_not_yet_when_few_promotes(tmp_path: Path) -> None:
    """Fewer than K promotes → status NOT_YET."""
    entries = [_make_promote(i, 0.85, delta=0.001) for i in range(5)]
    # Make library have 4 scenarios so coverage is met.
    for i in range(4):
        (tmp_path / f"s{i}.yaml").write_text("name: x", encoding="utf-8")
    weights = CompositeWeights()
    report = check_convergence(entries=entries, library_dir=tmp_path, weights=weights)
    assert report.status == ConvergenceStatus.NOT_YET
    assert any("need 10 consecutive promotes" in r for r in report.not_yet_reasons)


def test_convergence_converged_when_all_three(tmp_path: Path) -> None:
    """K=10 promotes with tiny deltas + 4 scenarios + score >= 0.80 → CONVERGED."""
    entries = [_make_promote(i, 0.85, delta=0.001) for i in range(12)]
    for i in range(4):
        (tmp_path / f"s{i}.yaml").write_text("name: x", encoding="utf-8")
    weights = CompositeWeights()
    report = check_convergence(entries=entries, library_dir=tmp_path, weights=weights)
    assert report.status == ConvergenceStatus.CONVERGED
    assert report.composite_score >= 0.80


def test_convergence_stuck_when_score_too_low(tmp_path: Path) -> None:
    """Gradient + coverage met but composite < 0.80 → STUCK."""
    entries = [_make_promote(i, 0.65, delta=0.001) for i in range(12)]
    for i in range(4):
        (tmp_path / f"s{i}.yaml").write_text("name: x", encoding="utf-8")
    weights = CompositeWeights()
    report = check_convergence(entries=entries, library_dir=tmp_path, weights=weights)
    assert report.status == ConvergenceStatus.STUCK
    assert report.composite_score == 0.65
    assert any("absolute threshold" in r for r in report.not_yet_reasons)


def test_convergence_not_yet_when_gradient_alive(tmp_path: Path) -> None:
    """Recent deltas above ε → NOT_YET (gradient still alive)."""
    # All deltas > 0.005 ε → gradient alive.
    entries = [_make_promote(i, 0.85, delta=0.05) for i in range(15)]
    for i in range(4):
        (tmp_path / f"s{i}.yaml").write_text("name: x", encoding="utf-8")
    weights = CompositeWeights()
    report = check_convergence(entries=entries, library_dir=tmp_path, weights=weights)
    assert report.status == ConvergenceStatus.NOT_YET
    assert any("gradient not vanished" in r for r in report.not_yet_reasons)


def test_convergence_not_yet_when_coverage_insufficient(tmp_path: Path) -> None:
    """Only 1 scenario → coverage entropy below threshold → NOT_YET."""
    entries = [_make_promote(i, 0.85, delta=0.001) for i in range(15)]
    (tmp_path / "single.yaml").write_text("name: x", encoding="utf-8")
    weights = CompositeWeights()
    report = check_convergence(entries=entries, library_dir=tmp_path, weights=weights)
    assert report.status == ConvergenceStatus.NOT_YET
    assert any("coverage entropy" in r for r in report.not_yet_reasons)


# --- render_synthesis_block ------------------------------------------------

def test_synthesis_empty_returns_marker() -> None:
    text = render_synthesis_block([])
    assert "(no entries yet)" in text


def test_synthesis_identifies_load_bearing_class() -> None:
    """A class with 3 promotes + 0 falsified is load-bearing."""
    entries = [
        _make_promote(i, 0.8) for i in range(3)
    ]
    text = render_synthesis_block(entries)
    assert "Load-bearing hypothesis classes" in text
    assert "persona_stability" in text


def test_synthesis_identifies_unproductive_class() -> None:
    entries = [
        ResearchEntry(
            iteration=i,
            decision="falsified",
            lesson_class="bad_class",
            hypothesis=f"h{i}",
        )
        for i in range(3)
    ]
    text = render_synthesis_block(entries)
    assert "Unproductive hypothesis classes" in text
    assert "bad_class" in text


def test_synthesis_shows_peak_composite() -> None:
    entries = [
        _make_promote(0, 0.75),
        _make_promote(1, 0.85),    # peak
        _make_promote(2, 0.80),
    ]
    text = render_synthesis_block(entries)
    assert "Peak composite" in text
    assert "0.8500" in text


# --- UE5 readiness checklist rendering ------------------------------------

def test_render_readiness_checklist_when_converged() -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.CONVERGED,
        composite_score=0.85,
        coverage_entropy_bits=2.5,
        iteration_count=42,
    )
    weights = CompositeWeights()
    text = render_ue5_readiness_checklist(
        convergence=report,
        weights=weights,
        anchor_scenarios=["watch_47_morning"],
        scenario_count=4,
    )
    assert "CONVERGED" in text
    assert "[x]" in text                              # at least one met criterion
    assert "watch_47_morning" in text
    assert "0.85" in text or "0.8500" in text


def test_render_readiness_checklist_when_not_yet() -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.NOT_YET,
        composite_score=0.65,
        coverage_entropy_bits=0.5,
        iteration_count=10,
        not_yet_reasons=["coverage too low", "score too low"],
    )
    weights = CompositeWeights()
    text = render_ue5_readiness_checklist(
        convergence=report,
        weights=weights,
        anchor_scenarios=["watch_47_morning"],
        scenario_count=1,
    )
    assert "NOT_YET" in text
    assert "coverage too low" in text or "score too low" in text


def test_write_readiness_checklist(tmp_path: Path) -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.CONVERGED,
        composite_score=0.85,
        coverage_entropy_bits=2.0,
        iteration_count=20,
    )
    path = tmp_path / "ue5_readiness_checklist.md"
    write_ue5_readiness_checklist(
        path,
        convergence=report,
        weights=CompositeWeights(),
        anchor_scenarios=["watch_47_morning"],
        scenario_count=4,
    )
    assert path.is_file()
    assert "CONVERGED" in path.read_text(encoding="utf-8")


# --- Stuck diagnostic ----------------------------------------------------

def test_render_stuck_diagnostic_mentions_score_and_floor() -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.STUCK,
        composite_score=0.65,
        promote_count=15,
        iteration_count=30,
        coverage_entropy_bits=2.5,
        composite_delta_last_k=[0.001, 0.002, -0.001],
        not_yet_reasons=["composite 0.6500 < absolute threshold 0.80"],
    )
    text = render_stuck_diagnostic(report, CompositeWeights())
    assert "0.6500" in text
    assert "0.80" in text
    assert "STUCK" in text or "stuck" in text


def test_write_stuck_diagnostic(tmp_path: Path) -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.STUCK,
        composite_score=0.7,
        promote_count=12,
        iteration_count=20,
    )
    path = tmp_path / "stuck.md"
    write_stuck_diagnostic(path, report, CompositeWeights())
    assert path.is_file()


# --- convergence_one_line --------------------------------------------------

def test_convergence_one_line_includes_status_and_metrics() -> None:
    report = ConvergenceReport(
        status=ConvergenceStatus.NOT_YET,
        composite_score=0.65,
        promote_count=5,
        iteration_count=10,
        coverage_entropy_bits=1.0,
    )
    line = convergence_one_line(report)
    assert "NOT_YET" in line
    assert "iter=10" in line
    assert "promotes=5" in line
    assert "0.6500" in line
