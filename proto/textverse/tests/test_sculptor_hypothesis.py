"""Sculptor-C tests for the hypothesis bank + StubHypothesisGenerator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from astra.judge import LCPGate
from astra.sculptor import (
    DEFAULT_BANK,
    GATE_TO_LESSON_CLASS,
    Hypothesis,
    StubHypothesisGenerator,
    apply_hypothesis,
    select_by_lesson_class,
    worst_gate,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent


# --- Bank shape -------------------------------------------------------------

def test_default_bank_has_30_entries() -> None:
    assert len(DEFAULT_BANK) == 30


def test_default_bank_entries_all_hypothesis() -> None:
    assert all(isinstance(h, Hypothesis) for h in DEFAULT_BANK)


def test_default_bank_has_diverse_lesson_classes() -> None:
    classes = {h.lesson_class for h in DEFAULT_BANK if h.lesson_class}
    # At least 5 distinct classes — diverse coverage of the gate space.
    assert len(classes) >= 5


def test_default_bank_targets_register_load_bearing_and_auto() -> None:
    """Bank should NOT target locked files."""
    relpaths = {h.relpath for h in DEFAULT_BANK}
    # The bank touches prompts/, tuning/, astra/grammar/canon/
    for rel in relpaths:
        # No bank entry should target astra/core/ or astra/judge/ etc.
        assert not rel.startswith("astra/core")
        assert not rel.startswith("astra/judge")
        assert not rel.startswith("astra/ship")
        assert not rel.startswith("docs/")


def test_default_bank_has_no_invented_tool_names_hypothesis() -> None:
    """The bank includes a hypothesis addressing Day-0 finding D0-1."""
    names = {h.name for h in DEFAULT_BANK}
    assert "no_invented_tool_names" in names


def test_default_bank_has_cycle_naming_consistency_hypothesis() -> None:
    """The bank includes a hypothesis addressing Day-0 finding D0-2."""
    names = {h.name for h in DEFAULT_BANK}
    assert "cycle_naming_consistency" in names


# --- StubHypothesisGenerator round-robin ---------------------------------

def test_stub_generator_advances_through_bank() -> None:
    gen = StubHypothesisGenerator()
    first = gen.propose()
    second = gen.propose()
    third = gen.propose()
    # Three distinct hypotheses come out of three calls.
    assert first.name != second.name
    assert second.name != third.name
    assert gen.next_index == 3


def test_stub_generator_wraps_around_bank() -> None:
    gen = StubHypothesisGenerator(bank=[
        Hypothesis(
            name=f"h{i}",
            relpath="prompts/narrator_sysprompt.md",
            transform_fn=lambda x: x,
            rationale=f"test {i}",
        )
        for i in range(3)
    ])
    seen = [gen.propose().name for _ in range(7)]
    # 7 calls on a 3-entry bank → 7 names, wrapping
    assert seen == ["h0", "h1", "h2", "h0", "h1", "h2", "h0"]


def test_stub_generator_empty_bank_raises() -> None:
    gen = StubHypothesisGenerator(bank=[])
    with pytest.raises(RuntimeError, match="empty bank"):
        gen.propose()


# --- apply_hypothesis -------------------------------------------------------

def test_apply_hypothesis_produces_new_contents() -> None:
    hyp = next(h for h in DEFAULT_BANK if h.name == "anti_performance_extra_sentence")
    new_contents = apply_hypothesis(hyp, TEXTVERSE_ROOT)
    baseline = (TEXTVERSE_ROOT / hyp.relpath).read_text(encoding="utf-8")
    # The append-paragraph transform makes the file strictly longer.
    assert len(new_contents) > len(baseline)
    assert "You do not announce your own restraint" in new_contents


def test_apply_hypothesis_for_sampling_json() -> None:
    hyp = next(h for h in DEFAULT_BANK if h.name == "temperature_0_60")
    new_contents = apply_hypothesis(hyp, TEXTVERSE_ROOT)
    # The transform sets temperature to 0.60.
    data = json.loads(new_contents)
    assert data["temperature"] == 0.60


def test_apply_hypothesis_for_pattern_addition() -> None:
    hyp = next(h for h in DEFAULT_BANK if h.name == "substrate_pattern_weights")
    new_contents = apply_hypothesis(hyp, TEXTVERSE_ROOT)
    # The transform appends one pattern line.
    assert r"\bweights?\b" in new_contents


def test_apply_hypothesis_handles_missing_baseline(tmp_path: Path) -> None:
    """apply_hypothesis on a missing baseline returns the transform of empty."""
    hyp = Hypothesis(
        name="test",
        relpath="prompts/nonexistent.md",
        transform_fn=lambda x: x + "added text",
        rationale="test",
    )
    new_contents = apply_hypothesis(hyp, tmp_path)
    assert new_contents == "added text"


# --- Gate-targeted selection ----------------------------------------------

def test_gate_to_lesson_class_covers_all_per_turn_gates() -> None:
    """Every per-turn LCPGate has a corresponding lesson_class mapping."""
    from astra.judge import PER_TURN_GATES
    for gate in PER_TURN_GATES:
        assert gate in GATE_TO_LESSON_CLASS


def test_select_by_lesson_class_filters() -> None:
    sampling_hypotheses = select_by_lesson_class(DEFAULT_BANK, "sampling")
    # The bank has 8 sampling hypotheses.
    assert len(sampling_hypotheses) >= 8
    for h in sampling_hypotheses:
        assert h.lesson_class == "sampling"


def test_select_by_lesson_class_empty_for_unknown() -> None:
    result = select_by_lesson_class(DEFAULT_BANK, "not_a_real_class")
    assert result == []


# --- worst_gate ------------------------------------------------------------

def test_worst_gate_returns_lowest() -> None:
    rates = {
        LCPGate.GRAMMAR_PARSE: 1.0,
        LCPGate.TOOL_VALID: 0.6,
        LCPGate.PERSONA_STABLE: 0.9,
    }
    assert worst_gate(rates) == LCPGate.TOOL_VALID


def test_worst_gate_returns_none_when_all_passing() -> None:
    rates = dict.fromkeys([LCPGate.GRAMMAR_PARSE, LCPGate.TOOL_VALID], 1.0)
    assert worst_gate(rates) is None


def test_worst_gate_empty_dict_returns_none() -> None:
    assert worst_gate({}) is None
