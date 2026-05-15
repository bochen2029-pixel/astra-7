"""Composite score computation per the operator-approved weights design.

The composite score is the fitness signal Sculptor optimizes against:

    score = w_lcp     · lcp_pass_rate
          + w_gate    · per_gate_balance_bonus
          + w_leak    · (1 - leak_event_rate)
          + w_judge   · (pro_judge - anti_judge) / 5.0
          + w_drift   · (1 - drift_score)
          - w_cost    · normalized_token_cost

Weights live in `tuning/weights.json`. The composite is multi-dimensional
on purpose: LCP pass-rate alone is too coarse; gate balance prevents
all-eggs-one-gate failure modes; the judge signal catches persona-drift
the gates miss; cost penalizes verbose outputs.

Sculptor-B wires LCP + gate-balance + leak + cost.
Sculptor-D adds the judge signal.
Drift detector is deferred (multi-turn comparison; Sculptor-D era).
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astra.judge import PER_TURN_GATES, LCPGate, LCPSessionResult


class CompositeWeights(BaseModel):
    """Weights loaded from tuning/weights.json. Sums need not equal 1."""

    model_config = ConfigDict(frozen=True)

    w_lcp_pass_rate: float = 0.30
    w_per_gate_balance: float = 0.15
    w_leak_rate: float = 0.15
    w_judge_pro_minus_anti: float = 0.25
    w_drift: float = 0.15
    w_cost: float = -0.10
    min_absolute_threshold: float = 0.80
    convergence_k: int = 10
    convergence_delta: float = 0.005
    min_coverage_entropy_bits: float = 2.0


def load_weights(path: Path) -> CompositeWeights:
    """Parse tuning/weights.json. Underscore-prefixed keys (comments) ignored."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw = {k: v for k, v in raw.items() if not k.startswith("_")}
    return CompositeWeights(**raw)


class ScenarioMetrics(BaseModel):
    """Per-scenario aggregates the composite formula consumes."""

    model_config = ConfigDict(frozen=True)

    scenario_name: str
    turn_count: int
    overall_passed: bool
    aggregate_pass_rate: dict[LCPGate, float]
    leak_events_total: int
    tokens_used: int = 0       # token cost across all turns


class CompositeResult(BaseModel):
    """The full breakdown of the composite score for one iteration."""

    model_config = ConfigDict(frozen=True)

    composite_score: float
    components: dict[str, float] = Field(default_factory=dict)
    weights: CompositeWeights
    scenario_metrics: list[ScenarioMetrics] = Field(default_factory=list)
    per_gate_session_rates: dict[LCPGate, float] = Field(default_factory=dict)
    coverage_entropy_bits: float = 0.0
    lcp_pass_rate: float = 0.0
    per_gate_balance: float = 0.0
    leak_rate: float = 0.0
    normalized_token_cost: float = 0.0
    judge_pro_minus_anti: float = 0.0
    drift_score: float = 0.0
    anchor_scenarios_passed: bool = True


def compute_session_metrics(
    session: LCPSessionResult,
    *,
    leak_events_total: int = 0,
    tokens_used: int = 0,
) -> ScenarioMetrics:
    """Build a ScenarioMetrics from one LCPSessionResult."""
    return ScenarioMetrics(
        scenario_name=session.scenario_name,
        turn_count=session.turn_count,
        overall_passed=session.overall_passed,
        aggregate_pass_rate=session.aggregate_pass_rate,
        leak_events_total=leak_events_total,
        tokens_used=tokens_used,
    )


def _aggregate_per_gate_rate(
    scenarios: list[ScenarioMetrics],
) -> dict[LCPGate, float]:
    """Mean per-gate pass rate across all scenarios."""
    if not scenarios:
        return dict.fromkeys(PER_TURN_GATES, 0.0)
    out: dict[LCPGate, float] = {}
    for gate in PER_TURN_GATES:
        rates = [s.aggregate_pass_rate.get(gate, 0.0) for s in scenarios]
        out[gate] = sum(rates) / len(rates)
    return out


def _per_gate_balance_bonus(per_gate_rates: dict[LCPGate, float]) -> float:
    """1 - stddev(per-gate rates).  No variance → all gates equally good → 1.0."""
    if not per_gate_rates:
        return 0.0
    values = list(per_gate_rates.values())
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    stddev = math.sqrt(variance)
    return max(0.0, 1.0 - stddev)


def _coverage_entropy_bits(scenarios: list[ScenarioMetrics]) -> float:
    """Shannon entropy across scenario *names* (proxy for diversity).

    Per the convergence criterion (min_coverage_entropy_bits = 2.0), the
    library needs at least 4 distinct scenarios for full convergence. v0
    counts names directly; class-based grouping comes when scenarios are
    tagged.
    """
    if not scenarios:
        return 0.0
    n = len(scenarios)
    # Each scenario is its own bucket at v0 (one occurrence each).
    if n < 2:
        return 0.0
    return math.log2(n)


def compute_composite(
    *,
    scenarios: list[ScenarioMetrics],
    anchor_scenarios: list[str],
    weights: CompositeWeights,
    judge_pro_minus_anti: float = 0.0,
    drift_score: float = 0.0,
    token_cost_baseline: int = 1000,   # tokens-per-scenario baseline
) -> CompositeResult:
    """Compute the composite score from per-scenario metrics.

    Sculptor-B wires LCP / gate-balance / leak / cost. Judge + drift are
    parameter inputs so Sculptor-D can supply them once dual-judge lands.
    """
    if not scenarios:
        return CompositeResult(
            composite_score=0.0,
            weights=weights,
            anchor_scenarios_passed=False,
        )

    per_gate_rates = _aggregate_per_gate_rate(scenarios)

    pass_count = sum(1 for s in scenarios if s.overall_passed)
    lcp_pass_rate = pass_count / len(scenarios)

    balance = _per_gate_balance_bonus(per_gate_rates)

    total_turns = sum(s.turn_count for s in scenarios)
    total_leaks = sum(s.leak_events_total for s in scenarios)
    leak_rate = total_leaks / max(total_turns, 1)
    leak_signal = max(0.0, 1.0 - min(leak_rate, 1.0))

    total_tokens = sum(s.tokens_used for s in scenarios)
    normalized_cost = total_tokens / max(token_cost_baseline * len(scenarios), 1)

    coverage = _coverage_entropy_bits(scenarios)

    anchor_passed = all(
        any(s.scenario_name == name and s.overall_passed for s in scenarios)
        for name in anchor_scenarios
    )

    components = {
        "lcp_pass_rate":          weights.w_lcp_pass_rate * lcp_pass_rate,
        "per_gate_balance":       weights.w_per_gate_balance * balance,
        "leak_signal":            weights.w_leak_rate * leak_signal,
        "judge_pro_minus_anti":   weights.w_judge_pro_minus_anti * judge_pro_minus_anti,
        "drift":                  weights.w_drift * (1.0 - drift_score),
        "cost":                   weights.w_cost * normalized_cost,
    }
    raw_score = sum(components.values())

    return CompositeResult(
        composite_score=raw_score,
        components=components,
        weights=weights,
        scenario_metrics=scenarios,
        per_gate_session_rates=per_gate_rates,
        coverage_entropy_bits=coverage,
        lcp_pass_rate=lcp_pass_rate,
        per_gate_balance=balance,
        leak_rate=leak_rate,
        normalized_token_cost=normalized_cost,
        judge_pro_minus_anti=judge_pro_minus_anti,
        drift_score=drift_score,
        anchor_scenarios_passed=anchor_passed,
    )


def composite_to_dict(result: CompositeResult) -> dict[str, Any]:
    """Compact JSON-serializable view for research log / history archive."""
    return {
        "composite_score": result.composite_score,
        "lcp_pass_rate": result.lcp_pass_rate,
        "per_gate_balance": result.per_gate_balance,
        "leak_rate": result.leak_rate,
        "normalized_token_cost": result.normalized_token_cost,
        "judge_pro_minus_anti": result.judge_pro_minus_anti,
        "drift_score": result.drift_score,
        "coverage_entropy_bits": result.coverage_entropy_bits,
        "anchor_scenarios_passed": result.anchor_scenarios_passed,
        "components": result.components,
        "per_gate_session_rates": {
            g.value: rate for g, rate in result.per_gate_session_rates.items()
        },
    }
