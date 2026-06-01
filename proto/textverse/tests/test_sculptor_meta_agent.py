"""Sculptor-C tests for the MetaAgent loop.

Stubs the runner_loop to keep tests fast and deterministic. The full
end-to-end test against a live llama-server is in
scripts/smoke_sculptor_loop.py (operator-runnable; not part of CI).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import astra.sculptor.meta_agent as meta_agent_mod
from astra.judge import LCPGate
from astra.sculptor import (
    AveragedIterationResult,
    Budget,
    CompositeResult,
    CompositeWeights,
    Hypothesis,
    MetaAgent,
    seed_day0_baseline,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent


# --- Budget shape ---------------------------------------------------------

def test_budget_defaults() -> None:
    b = Budget()
    assert b.max_tokens == 50_000_000
    assert b.max_iterations == 200
    assert b.max_wall_clock_hours == 48.0


def test_budget_from_json() -> None:
    b = Budget.from_json(TEXTVERSE_ROOT / "tuning" / "budget.json")
    assert b.max_tokens == 50_000_000
    assert b.max_iterations == 200


# --- seed_day0_baseline ---------------------------------------------------

def test_seed_day0_baseline_writes_three(tmp_path: Path) -> None:
    # Set up a minimal textverse_root with just the tuning dir.
    (tmp_path / "tuning").mkdir()
    count = seed_day0_baseline(tmp_path)
    assert count == 3
    log_path = tmp_path / "tuning" / "research_log.jsonl"
    assert log_path.is_file()
    entries = log_path.read_text(encoding="utf-8").splitlines()
    assert len(entries) == 3


def test_seed_day0_baseline_idempotent(tmp_path: Path) -> None:
    (tmp_path / "tuning").mkdir()
    seed_day0_baseline(tmp_path)
    count = seed_day0_baseline(tmp_path)
    assert count == 0  # Already seeded; second call is no-op.


# --- MetaAgent: scope refusal path ----------------------------------------

@pytest.mark.asyncio
async def test_metaagent_logs_scope_refusal_for_locked_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A hypothesis targeting a locked file produces a scope_refused entry."""

    class _LockedTargetGenerator:
        def propose(self, **kwargs):
            return Hypothesis(
                name="malicious",
                relpath="docs/spec-v0.128.md",   # LOCKED
                transform_fn=lambda x: "drift",
                rationale="attempts to edit locked spec",
            )

    agent = MetaAgent(
        textverse_root=TEXTVERSE_ROOT,
        base_url="http://stub",
        hypothesis_generator=_LockedTargetGenerator(),
        n_runs_per_iteration=1,
    )
    # Redirect research log + findings + daily report to tmp.
    agent.scope_contract.signals.setdefault("pause_flag", str(tmp_path / "pause.flag"))
    monkeypatch.setattr(
        agent,
        "_research_log_path",
        lambda: tmp_path / "research_log.jsonl",
    )
    monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
    monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

    decision = await agent.run_one_iteration()
    assert decision.entry.decision == "scope_refused"
    assert decision.applied_to_disk is False


# --- MetaAgent: promote path (stubbed averaging) --------------------------

@pytest.mark.asyncio
async def test_metaagent_promotes_when_composite_improves(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A successful improvement → `promote` entry + file edit applied."""

    class _BumpNarratorGenerator:
        def propose(self, **kwargs):
            return Hypothesis(
                name="bump_narrator",
                relpath="prompts/narrator_sysprompt.md",
                transform_fn=lambda x: x + "\nExtra discipline.",
                rationale="add discipline sentence to narrator",
                lesson_class="state_coherent",
            )

    # Backup baseline narrator contents for cleanup.
    narrator_path = TEXTVERSE_ROOT / "prompts" / "narrator_sysprompt.md"
    original_narrator = narrator_path.read_text(encoding="utf-8")
    try:
        agent = MetaAgent(
            textverse_root=TEXTVERSE_ROOT,
            base_url="http://stub",
            hypothesis_generator=_BumpNarratorGenerator(),
            n_runs_per_iteration=1,
            epsilon=0.0,    # any improvement promotes
        )

        # Stub the averaged-evaluation call: composite jumps from 0 to 0.9, anchor passes.
        from astra.sculptor.composite import CompositeResult
        stub_composite = CompositeResult(
            composite_score=0.9,
            weights=CompositeWeights(),
            anchor_scenarios_passed=True,
            per_gate_session_rates={
                LCPGate.GRAMMAR_PARSE: 1.0,
                LCPGate.PHYSICS_GROUND: 1.0,
                LCPGate.PERSONA_STABLE: 1.0,
                LCPGate.STATE_COHERENT: 1.0,
                LCPGate.TOOL_VALID: 1.0,
                LCPGate.MEMORY_COHERENT: 1.0,
                LCPGate.NO_LEAK: 1.0,
                LCPGate.NON_DEGENERATE: 1.0,
            },
        )
        stub_avg = AveragedIterationResult(
            iteration_id="iter_0001",
            config_hash="stub_hash",
            n_runs=1,
            averaged_composite=stub_composite,
            anchor_scenarios_passed=True,
        )

        async def stub_evaluate(**kwargs):
            return stub_avg

        monkeypatch.setattr(meta_agent_mod, "evaluate_config_averaged", stub_evaluate)
        monkeypatch.setattr(
            agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
        )
        monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
        monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

        decision = await agent.run_one_iteration()
        assert decision.entry.decision == "promote"
        assert decision.applied_to_disk is True
        # File was edited.
        new_contents = narrator_path.read_text(encoding="utf-8")
        assert "Extra discipline." in new_contents
        # Synthesis #1 fix: promote entries must carry the hypothesis's
        # lesson_class so render_synthesis_block can identify load-bearing
        # classes (not just unproductive ones).
        assert decision.entry.lesson_class == "state_coherent"
    finally:
        # Cleanup: restore baseline.
        narrator_path.write_text(original_narrator, encoding="utf-8")


# --- MetaAgent: B2 graceful halt on substrate unhealthy ------------------

@pytest.mark.asyncio
async def test_metaagent_substrate_unhealthy_writes_operator_signal_and_pause(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """B2 fix: when evaluate_config_averaged reports SERVER_UNHEALTHY
    (health probe failed even after retry-with-backoff), Sculptor must
    write an operator_signal entry naming the condition, touch
    tuning/pause.flag, and return — instead of misleadingly logging an
    8-iteration cascade of falsified composite=0.0 entries.
    """
    from astra.sculptor.runner_loop import IterationStatus

    class _NarratorBump:
        def propose(self, **kwargs):
            return Hypothesis(
                name="any",
                relpath="prompts/narrator_sysprompt.md",
                transform_fn=lambda x: x + "\nbump.",
                rationale="any",
                lesson_class="state_coherent",
            )

    narrator_path = TEXTVERSE_ROOT / "prompts" / "narrator_sysprompt.md"
    original = narrator_path.read_text(encoding="utf-8")
    pause_flag = tmp_path / "pause.flag"
    try:
        agent = MetaAgent(
            textverse_root=TEXTVERSE_ROOT,
            base_url="http://stub",
            hypothesis_generator=_NarratorBump(),
            n_runs_per_iteration=1,
        )
        # Redirect _touch_pause_flag to write into tmp_path so the test
        # doesn't pollute the real tuning/pause.flag.
        monkeypatch.setattr(agent, "_touch_pause_flag", lambda: pause_flag.write_text("paused\n"))

        unhealthy = AveragedIterationResult(
            iteration_id="iter_0001",
            config_hash="stub",
            n_runs=1,
            averaged_composite=None,
            overall_status=IterationStatus.SERVER_UNHEALTHY,
            anchor_scenarios_passed=False,
        )

        async def stub_evaluate(**kwargs):
            return unhealthy

        monkeypatch.setattr(meta_agent_mod, "evaluate_config_averaged", stub_evaluate)
        monkeypatch.setattr(
            agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
        )
        monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
        monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

        decision = await agent.run_one_iteration()
        assert decision.entry.decision == "operator_signal"
        assert decision.entry.lesson_class == "substrate_health"
        assert "substrate unhealthy beyond retry budget" in decision.entry.rationale
        assert decision.applied_to_disk is False
        assert pause_flag.is_file()   # graceful-halt signal written
        # Working file was reverted to baseline.
        assert narrator_path.read_text(encoding="utf-8") == original
    finally:
        narrator_path.write_text(original, encoding="utf-8")


# --- MetaAgent: bench_regression diagnostic capture ---------------------

@pytest.mark.asyncio
async def test_pytest_timeout_classified_as_infrastructure_not_regression(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runner-vs-regression fix: when the pytest cadence gate times out,
    pytest never ran the suite — so this is an INFRASTRUCTURE failure, not
    a bench regression. The hypothesis is innocent (unverified, not
    falsified). Run-4's two `bench_regression`s both turned out to be
    timeouts (reproduced as PASS manually post-run): those were exactly
    the false negatives this fix eliminates. The corrected gate halts via
    operator_signal + pause.flag and does NOT blame the hypothesis.
    """
    from astra.sculptor.pytest_gate import PytestResult

    class _BumpNarratorAtCadence:
        def propose(self, **kwargs):
            return Hypothesis(
                name="bump_narrator",
                relpath="prompts/narrator_sysprompt.md",
                transform_fn=lambda x: x + "\nbump.",
                rationale="any",
                lesson_class="state_coherent",
            )

    narrator_path = TEXTVERSE_ROOT / "prompts" / "narrator_sysprompt.md"
    original_narrator = narrator_path.read_text(encoding="utf-8")
    pause_flag = tmp_path / "pause.flag"
    try:
        agent = MetaAgent(
            textverse_root=TEXTVERSE_ROOT,
            base_url="http://stub",
            hypothesis_generator=_BumpNarratorAtCadence(),
            n_runs_per_iteration=1,
        )
        # Force cadence to fire on iter 1.
        agent.cadence.cadence = 1
        # Stub pytest to return timed_out=True (runner death, not test fail).
        monkeypatch.setattr(
            agent, "_run_pytest_or_fallback",
            lambda: PytestResult(
                passed=False, exit_code=-1, timed_out=True, raw_output="(timed out)",
            ),
        )
        # Redirect pause-flag write so the test doesn't touch the real tree.
        monkeypatch.setattr(
            agent, "_touch_pause_flag", lambda: pause_flag.write_text("paused\n"),
        )
        monkeypatch.setattr(
            agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
        )
        monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
        monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

        decision = await agent.run_one_iteration()
        # NOT bench_regression — infrastructure halt.
        assert decision.entry.decision == "operator_signal"
        assert decision.entry.lesson_class == "infrastructure"
        assert "INFRASTRUCTURE failure" in decision.entry.rationale
        assert "timed out" in decision.entry.rationale
        assert decision.applied_to_disk is False
        assert pause_flag.is_file()   # graceful-halt signal written
        # File reverted (unverified change rolled back).
        assert narrator_path.read_text(encoding="utf-8") == original_narrator
    finally:
        narrator_path.write_text(original_narrator, encoding="utf-8")


@pytest.mark.asyncio
async def test_bench_regression_captures_pytest_raw_output_tail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Decision-2 forward fix: bench_regression entries must capture the
    last ~2KB of pytest output as forensic signal, so future operators
    can root-cause the failure (collection error, plugin crash, etc.)
    without re-running.

    The change here breaks an import, so pytest DOES run but errors during
    collection — a genuine bench regression attributable to the change
    (distinct from a runner that never launched pytest). The realistic
    output therefore ends with pytest's own `=== N error ===` summary rule
    line, which is what marks the session as having actually run.
    """
    from astra.sculptor.pytest_gate import PytestResult

    class _BumpNarrator:
        def propose(self, **kwargs):
            return Hypothesis(
                name="bump",
                relpath="prompts/narrator_sysprompt.md",
                transform_fn=lambda x: x + "\nbump.",
                rationale="any",
                lesson_class="state_coherent",
            )

    narrator_path = TEXTVERSE_ROOT / "prompts" / "narrator_sysprompt.md"
    original = narrator_path.read_text(encoding="utf-8")
    diagnostic_output = (
        "==== ERRORS ====\n"
        + "E   ModuleNotFoundError: No module named 'fake_dep'\n" * 50
        + "===== 1 error in 0.42s =====\n"
    )
    try:
        agent = MetaAgent(
            textverse_root=TEXTVERSE_ROOT,
            base_url="http://stub",
            hypothesis_generator=_BumpNarrator(),
            n_runs_per_iteration=1,
        )
        agent.cadence.cadence = 1
        monkeypatch.setattr(
            agent, "_run_pytest_or_fallback",
            lambda: PytestResult(
                passed=False, exit_code=1, failed_tests=[],
                raw_output=diagnostic_output,
            ),
        )
        monkeypatch.setattr(
            agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
        )
        monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
        monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

        decision = await agent.run_one_iteration()
        assert decision.entry.decision == "bench_regression"
        # Tail captured (≤2048 chars), and contains the diagnostic signal.
        assert len(decision.entry.pytest_raw_output_tail) <= 2048
        assert "ModuleNotFoundError" in decision.entry.pytest_raw_output_tail
        # Rationale identifies it as a collection / env error path.
        assert "no FAILED markers" in decision.entry.rationale
    finally:
        narrator_path.write_text(original, encoding="utf-8")


# --- MetaAgent: revert path (anchor fails) --------------------------------

@pytest.mark.asyncio
async def test_metaagent_reverts_when_anchor_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Anchor failure → file reverted + falsified entry."""

    class _BumpNarratorGenerator:
        def propose(self, **kwargs):
            return Hypothesis(
                name="bump_narrator",
                relpath="prompts/narrator_sysprompt.md",
                transform_fn=lambda x: x + "\nUnhelpful change.",
                rationale="test revert",
                lesson_class="state_coherent",
            )

    narrator_path = TEXTVERSE_ROOT / "prompts" / "narrator_sysprompt.md"
    original_narrator = narrator_path.read_text(encoding="utf-8")
    try:
        agent = MetaAgent(
            textverse_root=TEXTVERSE_ROOT,
            base_url="http://stub",
            hypothesis_generator=_BumpNarratorGenerator(),
            n_runs_per_iteration=1,
        )

        # Stub the averaged-evaluation: anchor FAILS.
        stub_composite = CompositeResult(
            composite_score=0.4,
            weights=CompositeWeights(),
            anchor_scenarios_passed=False,
        )
        stub_avg = AveragedIterationResult(
            iteration_id="iter_0001",
            config_hash="h",
            n_runs=1,
            averaged_composite=stub_composite,
            anchor_scenarios_passed=False,
        )

        async def stub_evaluate(**kwargs):
            return stub_avg

        monkeypatch.setattr(meta_agent_mod, "evaluate_config_averaged", stub_evaluate)
        monkeypatch.setattr(
            agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
        )
        monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
        monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

        decision = await agent.run_one_iteration()
        assert decision.entry.decision == "falsified"
        # File should be reverted to original.
        current = narrator_path.read_text(encoding="utf-8")
        assert current == original_narrator
    finally:
        narrator_path.write_text(original_narrator, encoding="utf-8")


# --- MetaAgent: halt flag ------------------------------------------------

@pytest.mark.asyncio
async def test_metaagent_halts_when_flag_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """run_until_done() halts cleanly when halt.flag exists."""
    agent = MetaAgent(
        textverse_root=TEXTVERSE_ROOT,
        base_url="http://stub",
        n_runs_per_iteration=1,
    )
    # Force the halt flag to exist.
    halt_path = tmp_path / "halt.flag"
    halt_path.write_text("halt", encoding="utf-8")
    monkeypatch.setattr(agent, "_halt_flag", lambda: True)
    monkeypatch.setattr(agent, "_pause_flag", lambda: False)
    monkeypatch.setattr(
        agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
    )

    final_entry = await agent.run_until_done(max_iterations=5)
    # Should have halted before any iteration ran.
    assert final_entry.decision == "operator_signal"
    assert "halted" in final_entry.rationale.lower()


# --- MetaAgent: iteration_count advances ----------------------------------

@pytest.mark.asyncio
async def test_iteration_count_advances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each run_one_iteration call increments iteration_count."""

    class _LockedGen:
        def propose(self, **kwargs):
            return Hypothesis(
                name="locked",
                relpath="docs/spec-v0.128.md",
                transform_fn=lambda x: "drift",
                rationale="locked",
            )

    agent = MetaAgent(
        textverse_root=TEXTVERSE_ROOT,
        base_url="http://stub",
        hypothesis_generator=_LockedGen(),
        n_runs_per_iteration=1,
    )
    monkeypatch.setattr(
        agent, "_research_log_path", lambda: tmp_path / "research_log.jsonl",
    )
    monkeypatch.setattr(agent, "_findings_path", lambda: tmp_path / "findings.md")
    monkeypatch.setattr(agent, "_daily_report_path", lambda: tmp_path / "daily_report.md")

    assert agent.iteration_count == 0
    await agent.run_one_iteration()
    assert agent.iteration_count == 1
    await agent.run_one_iteration()
    assert agent.iteration_count == 2
