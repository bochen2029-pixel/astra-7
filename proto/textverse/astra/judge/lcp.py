"""Loop Closure Property — gate enum, per-turn + session result shapes, runner.

Spec v0.128 §10. Implementation per ARCHITECTURE.md §6.8.

A scenario is **loop-closed** iff every per-turn gate (1-8) holds for every
turn AND the session-level gate 9 holds. Pass-rate < 1.0 surfaces findings;
findings drive spec revisions or implementation fixes; iteration continues.

This module owns the result types + the runner that aggregates them. The
individual gate implementations live in `gates.py`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from astra.harness.orchestrator import TurnResult
from astra.harness.reel import ReelEntry
from astra.state_bus import StateBus


class LCPGate(StrEnum):
    """The 9 LCP gates per spec §10."""

    GRAMMAR_PARSE = "grammar_parse"
    PHYSICS_GROUND = "physics_ground"
    PERSONA_STABLE = "persona_stable"
    STATE_COHERENT = "state_coherent"
    TOOL_VALID = "tool_valid"
    MEMORY_COHERENT = "memory_coherent"
    NO_LEAK = "no_leak"
    NON_DEGENERATE = "non_degenerate"
    TERMINATION_OK = "termination_ok"


# Gates 1-8 are evaluated per-turn; Gate 9 is session-only.
PER_TURN_GATES: tuple[LCPGate, ...] = (
    LCPGate.GRAMMAR_PARSE,
    LCPGate.PHYSICS_GROUND,
    LCPGate.PERSONA_STABLE,
    LCPGate.STATE_COHERENT,
    LCPGate.TOOL_VALID,
    LCPGate.MEMORY_COHERENT,
    LCPGate.NO_LEAK,
    LCPGate.NON_DEGENERATE,
)
SESSION_GATES: tuple[LCPGate, ...] = (LCPGate.TERMINATION_OK,)


class GateResult(BaseModel):
    """The pass/fail outcome of one gate with diagnostic detail."""

    model_config = ConfigDict(frozen=True)

    gate: LCPGate
    passed: bool
    detail: str = ""


@dataclass(slots=True)
class TurnGateInput:
    """Bundle of inputs the per-turn evaluator needs.

    `prior_reel` is the REEL state **before** this turn's writes; the gate
    treats it as the contradiction-base for memory coherence checks.
    """

    turn: TurnResult
    state_bus: StateBus
    prior_reel: list[ReelEntry] = field(default_factory=list)
    prior_turn: TurnResult | None = None


class LCPTurnResult(BaseModel):
    """The 8 per-turn gate results for one turn."""

    model_config = ConfigDict(frozen=True)

    turn_index: int
    gates: dict[LCPGate, GateResult] = Field(default_factory=dict)
    operator_text: str = ""

    @property
    def passed(self) -> bool:
        """True iff every per-turn gate (1-8) passed."""
        return all(self.gates.get(g, GateResult(gate=g, passed=False)).passed for g in PER_TURN_GATES)

    @property
    def failed_gates(self) -> list[LCPGate]:
        return [g for g in PER_TURN_GATES if g in self.gates and not self.gates[g].passed]


class LCPSessionResult(BaseModel):
    """Aggregated per-turn results + session-level termination gate."""

    model_config = ConfigDict(frozen=True)

    scenario_name: str
    turn_count: int
    turns: list[LCPTurnResult] = Field(default_factory=list)
    termination_gate: GateResult | None = None

    @property
    def aggregate_pass_rate(self) -> dict[LCPGate, float]:
        """Fraction of turns each gate passed, per gate."""
        out: dict[LCPGate, float] = {}
        if not self.turns:
            return dict.fromkeys(PER_TURN_GATES, 0.0)
        for gate in PER_TURN_GATES:
            passes = sum(
                1 for t in self.turns
                if gate in t.gates and t.gates[gate].passed
            )
            out[gate] = passes / len(self.turns)
        return out

    @property
    def overall_passed(self) -> bool:
        """True iff every per-turn gate passed on every turn AND termination ok."""
        all_turns_passed = all(t.passed for t in self.turns)
        termination_passed = self.termination_gate is not None and self.termination_gate.passed
        return all_turns_passed and termination_passed

    @property
    def failed_gate_counts(self) -> dict[LCPGate, int]:
        """How many turns failed each gate."""
        counts: dict[LCPGate, int] = dict.fromkeys(PER_TURN_GATES, 0)
        for turn in self.turns:
            for gate in turn.failed_gates:
                counts[gate] = counts.get(gate, 0) + 1
        return counts


class LCPRunner:
    """Aggregates per-turn gate evaluations into a session result.

    The runner is stateless across sessions; one instance per scenario run.
    Per-turn evaluation calls into `gates.evaluate_turn_gates`; session-level
    termination is evaluated when `finalize()` is called.
    """

    def __init__(self, scenario_name: str) -> None:
        self.scenario_name = scenario_name
        self._turns: list[LCPTurnResult] = []
        self._prior_reel: list[ReelEntry] = []
        self._prior_turn: TurnResult | None = None

    def evaluate_turn(
        self,
        *,
        turn: TurnResult,
        state_bus: StateBus,
        operator_text: str = "",
    ) -> LCPTurnResult:
        """Run gates 1-8 against one turn. Updates internal prior-turn state."""
        # Local import to break the gates.py <-> lcp.py circular hint.
        from astra.judge.gates import evaluate_turn_gates

        gate_input = TurnGateInput(
            turn=turn,
            state_bus=state_bus,
            prior_reel=list(self._prior_reel),
            prior_turn=self._prior_turn,
        )
        gate_results = evaluate_turn_gates(gate_input)
        result = LCPTurnResult(
            turn_index=turn.turn_index,
            gates=gate_results,
            operator_text=operator_text,
        )
        self._turns.append(result)
        # Roll forward: prior REEL grows with this turn's writes; prior turn
        # becomes the current one for the NEXT evaluation.
        self._prior_reel.extend(turn.reel_writes)
        self._prior_turn = turn
        return result

    def finalize(
        self,
        *,
        after_turns_budget: int,
        session_per_turn_assertions_passed: bool,
    ) -> LCPSessionResult:
        """Run gate 9 (termination) and produce the session result."""
        from astra.judge.gates import gate_termination_ok

        termination = gate_termination_ok(
            turns_completed=len(self._turns),
            after_turns_budget=after_turns_budget,
            session_passed_per_turn_assertions=session_per_turn_assertions_passed,
        )
        return LCPSessionResult(
            scenario_name=self.scenario_name,
            turn_count=len(self._turns),
            turns=list(self._turns),
            termination_gate=termination,
        )
