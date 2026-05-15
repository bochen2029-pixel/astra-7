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
    finally:
        # Cleanup: restore baseline.
        narrator_path.write_text(original_narrator, encoding="utf-8")


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
