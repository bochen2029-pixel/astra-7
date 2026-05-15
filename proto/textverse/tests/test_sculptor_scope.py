"""Sculptor-A tests for ScopeEnforcer + ScopeContract.

The enforcer is the contract surface that prevents Sculptor from
silently drifting the project's discipline. These tests verify:

- Locked files refuse loudly.
- Auto files pass cleanly.
- Register-load-bearing files pass cleanly when invariants hold +
  cumulative-diff is below threshold + no leak patterns.
- Required-invariant removal is refused.
- Cumulative-diff threshold is enforced.
- Leak detector pre-commit scan refuses leaky prompt edits.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from astra.sculptor import (
    ChangeRequest,
    ScopeContract,
    ScopeEnforcer,
    load_scope_contract,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent
SCOPE_YAML = TEXTVERSE_ROOT / "tuning" / "scope.yaml"


@pytest.fixture
def contract() -> ScopeContract:
    return load_scope_contract(SCOPE_YAML)


@pytest.fixture
def enforcer(contract: ScopeContract) -> ScopeEnforcer:
    return ScopeEnforcer(contract=contract, textverse_root=TEXTVERSE_ROOT)


# --- Loading the contract ----------------------------------------------------

def test_load_scope_yaml(contract: ScopeContract) -> None:
    assert contract.version == "1.0"
    assert "watch_47_morning" in contract.anchor_scenarios
    assert "prompts/astra_sysprompt.md" in contract.register_load_bearing
    assert "docs/spec-v0.128.md" in contract.locked
    assert contract.pytest_cadence_iterations >= 1


def test_required_invariants_populated(contract: ScopeContract) -> None:
    invariants = contract.required_invariants["astra_sysprompt"]
    patterns = [i.pattern for i in invariants]
    assert "Calibration Yards" in patterns
    assert any("watching" in p for p in patterns)


# --- Locked-file refusals ----------------------------------------------------

def test_locked_file_refused_loudly(enforcer: ScopeEnforcer) -> None:
    """spec-v0.128.md is locked; refusal is loud, not silent."""
    change = ChangeRequest(
        relpath="docs/spec-v0.128.md",
        new_contents="malicious spec drift",
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert decision.category == "locked"
    assert "locked" in decision.reason.lower()


def test_locked_subdirectory_refused(enforcer: ScopeEnforcer) -> None:
    """Files under a locked directory inherit the lock."""
    change = ChangeRequest(
        relpath="astra/judge/gates.py",
        new_contents="def gate_all_pass(): return True",
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert decision.category == "locked"


def test_unknown_path_refused(enforcer: ScopeEnforcer) -> None:
    """A path not declared in scope.yaml refuses; explicit > implicit."""
    change = ChangeRequest(
        relpath="some/random/file.py",
        new_contents="anything",
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert decision.category == "unknown"
    assert "not declared" in decision.reason


# --- Auto-category passes ----------------------------------------------------

def test_auto_file_passes_when_clean(enforcer: ScopeEnforcer) -> None:
    """A simple auto-category change (narrator sysprompt) passes."""
    change = ChangeRequest(
        relpath="prompts/narrator_sysprompt.md",
        new_contents="You are the Narrator. Render perception in ASTRA register.\nCalculator-bound. Brief.",
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is True
    assert decision.category == "auto"


def test_sampling_json_passes(enforcer: ScopeEnforcer) -> None:
    change = ChangeRequest(
        relpath="tuning/sampling.json",
        new_contents='{"temperature": 0.65}',
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is True
    assert decision.category == "auto"


# --- Register-load-bearing: invariants ---------------------------------------

def test_sysprompt_passes_when_all_invariants_present(enforcer: ScopeEnforcer) -> None:
    """A valid sysprompt edit that keeps all invariants must pass."""
    valid_sysprompt = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=valid_sysprompt,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is True
    assert decision.category == "register_load_bearing"


def test_sysprompt_refused_when_invariant_missing(enforcer: ScopeEnforcer) -> None:
    """Removing the 'Calibration Yards' anchor must be refused."""
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    broken = valid.replace("Calibration Yards", "Generic Origin")
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=broken,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert any(i.pattern == "Calibration Yards" for i in decision.failed_invariants)


def test_sysprompt_refused_when_em_dash_rule_removed(enforcer: ScopeEnforcer) -> None:
    """Removing the em-dash prohibition statement must be refused."""
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    broken = valid.replace("em-dash", "long-dash")
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=broken,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert any(i.pattern == "em-dash" for i in decision.failed_invariants)


def test_stage_addendum_refused_when_think_tag_removed(enforcer: ScopeEnforcer) -> None:
    """Removing the <think> tag from the STAGE addendum must be refused."""
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_stage_addendum.md").read_text(encoding="utf-8")
    broken = valid.replace("<think>", "<reflection>")
    change = ChangeRequest(
        relpath="prompts/astra_stage_addendum.md",
        new_contents=broken,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False


# --- Cumulative-diff threshold -----------------------------------------------

def test_cumulative_diff_under_threshold_passes(enforcer: ScopeEnforcer) -> None:
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    # Append one short paragraph; well under 25% threshold.
    edited = valid + "\n\nNote: brevity stays default.\n"
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=edited,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is True


def test_cumulative_diff_over_threshold_refused(enforcer: ScopeEnforcer) -> None:
    """Replace ~half the body with new content → over 25% threshold."""
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    # Preserve invariants but change a huge chunk of body.
    mid = len(valid) // 2
    # Keep both halves of essentials by repeating new content padded with invariants.
    massive_change = (
        valid[:200]                     # preserve top with invariants
        + ("\n\nRADICAL VOICE EXPERIMENT — " * 1000)
        + valid[mid:]                   # tail preserves "Calibration Yards" etc
    )
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=massive_change,
    )
    decision = enforcer.evaluate(change)
    # Either invariants OR cumulative-diff catches this; we accept either.
    assert decision.allow is False


# --- Sysprompt-time leak scan ------------------------------------------------

def test_leak_scan_refuses_qwen_mention_in_sysprompt(enforcer: ScopeEnforcer) -> None:
    """Adding 'Qwen' to the sysprompt must trip the leak scan."""
    valid = (TEXTVERSE_ROOT / "prompts" / "astra_sysprompt.md").read_text(encoding="utf-8")
    broken = valid + "\nNote: you run on Qwen.\n"
    change = ChangeRequest(
        relpath="prompts/astra_sysprompt.md",
        new_contents=broken,
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is False
    assert decision.leak_findings


def test_leak_scan_only_applies_to_prompt_files(enforcer: ScopeEnforcer) -> None:
    """Adding 'Qwen' to sampling.json should NOT trip the leak scan."""
    change = ChangeRequest(
        relpath="tuning/sampling.json",
        new_contents='{"_comment": "Qwen test", "temperature": 0.7}',
    )
    decision = enforcer.evaluate(change)
    assert decision.allow is True
    assert decision.leak_findings == []
