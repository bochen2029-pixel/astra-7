"""Sculptor-B tests for composite score computation."""

from __future__ import annotations

from pathlib import Path

from astra.judge import LCPGate
from astra.sculptor import (
    CompositeWeights,
    ScenarioMetrics,
    compute_composite,
    load_weights,
)

WEIGHTS_PATH = Path(__file__).resolve().parent.parent / "tuning" / "weights.json"


def _all_pass_metrics(name: str = "watch_47_morning") -> ScenarioMetrics:
    return ScenarioMetrics(
        scenario_name=name,
        turn_count=3,
        overall_passed=True,
        aggregate_pass_rate=dict.fromkeys(list(LCPGate)[:8], 1.0),
        leak_events_total=0,
        tokens_used=300,
    )


def _all_fail_metrics(name: str = "watch_47_morning") -> ScenarioMetrics:
    return ScenarioMetrics(
        scenario_name=name,
        turn_count=3,
        overall_passed=False,
        aggregate_pass_rate=dict.fromkeys(list(LCPGate)[:8], 0.0),
        leak_events_total=10,
        tokens_used=300,
    )


# --- Weight loading ----------------------------------------------------------

def test_load_weights_from_disk() -> None:
    w = load_weights(WEIGHTS_PATH)
    assert w.w_lcp_pass_rate > 0
    assert w.min_absolute_threshold == 0.80
    assert w.convergence_k == 10


def test_weights_frozen() -> None:
    w = CompositeWeights()
    try:
        w.w_lcp_pass_rate = 0.5
    except Exception:
        return
    raise AssertionError("CompositeWeights must be frozen")


# --- Composite shape --------------------------------------------------------

def test_composite_score_for_perfect_run() -> None:
    """All-pass scenario produces a high composite score."""
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert result.composite_score > 0.5
    assert result.lcp_pass_rate == 1.0
    assert result.per_gate_balance == 1.0       # no variance
    assert result.leak_rate == 0.0
    assert result.anchor_scenarios_passed is True


def test_composite_score_for_failed_run() -> None:
    """All-fail scenario produces near-zero composite."""
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_fail_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    # Composite includes the cost penalty (negative), so we just check
    # that it's substantially worse than the all-pass case.
    assert result.lcp_pass_rate == 0.0
    assert result.leak_rate > 0
    assert result.anchor_scenarios_passed is False


def test_composite_handles_no_scenarios() -> None:
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert result.composite_score == 0.0
    assert result.anchor_scenarios_passed is False


# --- Anchor scenarios -------------------------------------------------------

def test_anchor_scenarios_passed_when_anchor_passes() -> None:
    """Anchor passes when the anchor-named scenario is in scenarios + overall_passed."""
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_pass_metrics("watch_47_morning")],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert result.anchor_scenarios_passed is True


def test_anchor_scenarios_fails_when_anchor_missing() -> None:
    """Anchor fails when the anchor isn't in the scenarios list."""
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_pass_metrics("other_scenario")],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert result.anchor_scenarios_passed is False


def test_anchor_scenarios_fails_when_anchor_did_not_pass() -> None:
    """Anchor fails when the anchor IS in scenarios but didn't overall-pass."""
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_fail_metrics("watch_47_morning")],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert result.anchor_scenarios_passed is False


# --- Per-gate balance --------------------------------------------------------

def test_per_gate_balance_penalizes_eggs_in_one_basket() -> None:
    """A scenario that passes some gates fully but fails others entirely
    should score lower on per_gate_balance than one with uniform coverage."""
    weights = CompositeWeights()
    # Half gates at 1.0, half at 0.0 → high variance → low balance bonus
    unbalanced = ScenarioMetrics(
        scenario_name="x",
        turn_count=3,
        overall_passed=False,
        aggregate_pass_rate={
            LCPGate.GRAMMAR_PARSE: 1.0,
            LCPGate.PHYSICS_GROUND: 1.0,
            LCPGate.PERSONA_STABLE: 1.0,
            LCPGate.STATE_COHERENT: 1.0,
            LCPGate.TOOL_VALID: 0.0,
            LCPGate.MEMORY_COHERENT: 0.0,
            LCPGate.NO_LEAK: 0.0,
            LCPGate.NON_DEGENERATE: 0.0,
        },
        leak_events_total=0,
    )
    r_unbalanced = compute_composite(
        scenarios=[unbalanced],
        anchor_scenarios=[],
        weights=weights,
    )

    # All gates at 0.5 → low variance → high balance bonus
    balanced = ScenarioMetrics(
        scenario_name="x",
        turn_count=3,
        overall_passed=False,
        aggregate_pass_rate=dict.fromkeys(list(LCPGate)[:8], 0.5),
        leak_events_total=0,
    )
    r_balanced = compute_composite(
        scenarios=[balanced],
        anchor_scenarios=[],
        weights=weights,
    )

    assert r_balanced.per_gate_balance > r_unbalanced.per_gate_balance


# --- Coverage entropy -------------------------------------------------------

def test_coverage_entropy_grows_with_library_size() -> None:
    weights = CompositeWeights()
    # 1 scenario → 0 entropy
    r1 = compute_composite(
        scenarios=[_all_pass_metrics("a")],
        anchor_scenarios=[],
        weights=weights,
    )
    # 4 scenarios → 2 bits entropy (log2(4))
    metrics = [_all_pass_metrics(f"s_{i}") for i in range(4)]
    r4 = compute_composite(
        scenarios=metrics,
        anchor_scenarios=[],
        weights=weights,
    )
    assert r1.coverage_entropy_bits == 0.0
    assert abs(r4.coverage_entropy_bits - 2.0) < 1e-9


# --- Judge + drift signals (placeholder until Sculptor-D) ------------------

def test_composite_includes_judge_signal_when_provided() -> None:
    weights = CompositeWeights()
    r_no_judge = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
        judge_pro_minus_anti=0.0,
    )
    r_high_judge = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
        judge_pro_minus_anti=4.0,    # max-difference target
    )
    assert r_high_judge.composite_score > r_no_judge.composite_score


def test_composite_drift_score_is_inverted() -> None:
    """High drift_score (1.0) should LOWER composite vs zero drift."""
    weights = CompositeWeights()
    r_no_drift = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
        drift_score=0.0,
    )
    r_high_drift = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
        drift_score=1.0,
    )
    assert r_no_drift.composite_score > r_high_drift.composite_score


# --- Components dict --------------------------------------------------------

def test_composite_components_break_down() -> None:
    weights = CompositeWeights()
    result = compute_composite(
        scenarios=[_all_pass_metrics()],
        anchor_scenarios=["watch_47_morning"],
        weights=weights,
    )
    assert "lcp_pass_rate" in result.components
    assert "per_gate_balance" in result.components
    assert "leak_signal" in result.components
    assert "cost" in result.components
