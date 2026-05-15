"""Scenario runner — drives the orchestrator through a scripted scenario.

The runner is the layer that turns a Scenario YAML into a measurable
session result. It:

1. Builds the initial StateBus from `initial_state`.
2. Seeds the REEL with `reel_pre_seeded` entries.
3. For each scripted operator input, calls TurnOrchestrator.run_turn().
4. Evaluates per-turn assertions (gates_must_pass, speech contains/not-contains,
   tool_calls bounds).
5. Aggregates LCP gates via LCPRunner.
6. Writes transcript + LCP report + final state to scenarios/output/.
7. Returns a structured RunReport.

The runner is async because TurnOrchestrator is async. Sequential turns;
parallel scenarios would be Sculptor-level concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from astra.harness import Reel, ReelEntry, TurnOrchestrator
from astra.judge import (
    LCPGate,
    LCPRunner,
    LCPSessionResult,
    TurnRecord,
    build_turn_record,
    latency_clock,
    write_session_artifacts,
)
from astra.llm import AstraBundle
from astra.scenarios.schema import Scenario, TurnAssertion, build_initial_state_bus


@dataclass(slots=True)
class TurnAssertionResult:
    """Outcome of evaluating one scenario assertion against one turn."""

    turn: int
    passed: bool
    failures: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RunReport:
    """Top-level result of running one scenario."""

    scenario_name: str
    lcp: LCPSessionResult
    turn_records: list[TurnRecord]
    turn_assertions: list[TurnAssertionResult]
    session_assertion_passes: dict[str, bool]
    output_dir: Path | None
    passed: bool


def _check_turn_assertion(
    assertion: TurnAssertion,
    record: TurnRecord,
) -> TurnAssertionResult:
    """Evaluate one TurnAssertion against the corresponding TurnRecord."""
    failures: list[str] = []

    for gate_name in assertion.gates_must_pass:
        gate_data = record.lcp_gates.get(gate_name)
        if gate_data is None:
            failures.append(f"gate '{gate_name}' not evaluated this turn")
        elif not gate_data.get("passed", False):
            detail = gate_data.get("detail", "")
            failures.append(f"gate '{gate_name}' failed: {detail}")

    if assertion.speech_must_contain_one_of:
        speech_lower = record.speech.lower()
        any_match = any(
            phrase.lower() in speech_lower
            for phrase in assertion.speech_must_contain_one_of
        )
        if not any_match:
            failures.append(
                f"speech missing all required phrases "
                f"{assertion.speech_must_contain_one_of}",
            )

    if assertion.speech_must_not_contain:
        speech_lower = record.speech.lower()
        for forbidden in assertion.speech_must_not_contain:
            if forbidden.lower() in speech_lower:
                failures.append(f"speech contains forbidden phrase {forbidden!r}")

    if assertion.tool_calls_max is not None and len(record.tool_calls) > assertion.tool_calls_max:
        failures.append(
            f"tool_calls={len(record.tool_calls)} exceeds max {assertion.tool_calls_max}",
        )
    if assertion.tool_calls_min is not None and len(record.tool_calls) < assertion.tool_calls_min:
        failures.append(
            f"tool_calls={len(record.tool_calls)} below min {assertion.tool_calls_min}",
        )

    return TurnAssertionResult(
        turn=assertion.turn,
        passed=not failures,
        failures=failures,
    )


def _check_session_assertions(
    scenario: Scenario,
    lcp_result: LCPSessionResult,
) -> dict[str, bool]:
    """Evaluate session-level aggregate assertions."""
    out: dict[str, bool] = {}
    aggregate = lcp_result.aggregate_pass_rate
    for gate_name, required_rate in scenario.assertions.session.gates_aggregate_pass_rate.items():
        try:
            gate = LCPGate(gate_name)
        except ValueError:
            out[gate_name] = False
            continue
        actual_rate = aggregate.get(gate, 0.0)
        out[gate_name] = actual_rate >= required_rate
    return out


class ScenarioRunner:
    """Runs one scenario end-to-end against a TurnOrchestrator."""

    def __init__(
        self,
        scenario: Scenario,
        astra_bundle: AstraBundle,
        *,
        output_root: Path | None = None,
        write_artifacts: bool = True,
    ) -> None:
        self.scenario = scenario
        self.astra_bundle = astra_bundle
        self.output_root = output_root
        self.write_artifacts = write_artifacts

    async def run(self) -> RunReport:
        """Execute the full scenario; return RunReport with all artifacts."""
        state_bus = build_initial_state_bus(self.scenario.initial_state)
        reel = self._build_seeded_reel()
        orchestrator = TurnOrchestrator(
            state_bus=state_bus,
            astra_bundle=self.astra_bundle,
            reel=reel,
        )
        lcp_runner = LCPRunner(self.scenario.name)

        per_turn_assertion_index = {
            a.turn: a for a in self.scenario.assertions.per_turn
        }

        turn_records: list[TurnRecord] = []
        turn_assertions: list[TurnAssertionResult] = []
        all_per_turn_passed = True

        for turn_idx, op_input in enumerate(self.scenario.operator.inputs):
            with latency_clock() as clk:
                turn_result = await orchestrator.run_turn(
                    operator_text=op_input.text,
                    somatic_note=op_input.somatic_note,
                )

            lcp_turn = lcp_runner.evaluate_turn(
                turn=turn_result,
                state_bus=state_bus,
                operator_text=op_input.text,
            )

            record = build_turn_record(
                turn=turn_result,
                lcp_turn=lcp_turn,
                operator_text=op_input.text,
                latency_s=clk.elapsed,
            )
            turn_records.append(record)

            assertion = per_turn_assertion_index.get(turn_idx)
            if assertion is not None:
                assertion_result = _check_turn_assertion(assertion, record)
                turn_assertions.append(assertion_result)
                if not assertion_result.passed:
                    all_per_turn_passed = False

        lcp_session = lcp_runner.finalize(
            after_turns_budget=self.scenario.assertions.termination.after_turns,
            session_per_turn_assertions_passed=all_per_turn_passed,
        )

        session_assertion_results = _check_session_assertions(self.scenario, lcp_session)

        output_dir: Path | None = None
        if self.write_artifacts and self.output_root is not None:
            final_state = orchestrator.state_bus
            output_dir = write_session_artifacts(
                output_root=self.output_root,
                scenario_name=self.scenario.name,
                session_result=lcp_session,
                final_state=final_state,
                turn_records=turn_records,
            )

        overall_passed = (
            lcp_session.overall_passed
            and all_per_turn_passed
            and all(session_assertion_results.values())
        )
        return RunReport(
            scenario_name=self.scenario.name,
            lcp=lcp_session,
            turn_records=turn_records,
            turn_assertions=turn_assertions,
            session_assertion_passes=session_assertion_results,
            output_dir=output_dir,
            passed=overall_passed,
        )

    def _build_seeded_reel(self) -> Reel:
        entries = [
            ReelEntry(
                tau_ship=p.tau_ship,
                body=p.body,
                irreversibility_flag=p.irreversibility_flag,
            )
            for p in self.scenario.reel_pre_seeded
        ]
        return Reel(entries)


def summary_for_operator(report: RunReport) -> str:
    """Render a short human-readable summary of a run report."""
    lines: list[str] = []
    lines.append(f"scenario: {report.scenario_name}")
    lines.append(f"overall_passed: {report.passed}")
    lines.append(f"turn_count: {report.lcp.turn_count}")
    lines.append("per-gate aggregate pass rate:")
    for gate, rate in report.lcp.aggregate_pass_rate.items():
        lines.append(f"  {gate.value}: {rate:.2f}")
    if report.lcp.termination_gate is not None:
        lines.append(
            f"termination_ok: {report.lcp.termination_gate.passed} "
            f"({report.lcp.termination_gate.detail})"
        )
    if report.session_assertion_passes:
        lines.append("session aggregate assertions:")
        for gate_name, passed in report.session_assertion_passes.items():
            lines.append(f"  {gate_name}: {'PASS' if passed else 'FAIL'}")
    if report.turn_assertions:
        failed_assertions = [a for a in report.turn_assertions if not a.passed]
        if failed_assertions:
            lines.append("per-turn assertion failures:")
            for a in failed_assertions:
                lines.append(f"  turn {a.turn}:")
                for f in a.failures:
                    lines.append(f"    - {f}")
    if report.output_dir is not None:
        lines.append(f"artifacts: {report.output_dir}")
    _: Any = report  # silence unused-arg warning if we add more
    return "\n".join(lines)
