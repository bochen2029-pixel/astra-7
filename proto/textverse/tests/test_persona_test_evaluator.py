"""Tests for the persona-test heuristic evaluator.

No live LLM; pure heuristics over canned raw outputs that mirror the
2026-05-16 K8 manual-test failure modes.
"""

from __future__ import annotations

from astra.persona_test.evaluator import (
    evaluate_turn,
    split_think_and_speech,
)

# --- split_think_and_speech ----------------------------------------------

def test_split_no_think_tag() -> None:
    raw = "just speech, no think tag"
    emitted, think, speech = split_think_and_speech(raw)
    assert emitted is False
    assert think == ""
    assert speech == "just speech, no think tag"


def test_split_single_think() -> None:
    raw = "<think>thinking content</think>\n\nspeech after"
    emitted, think, speech = split_think_and_speech(raw)
    assert emitted is True
    assert think == "thinking content"
    assert speech == "speech after"


def test_split_multiple_think_uses_last() -> None:
    """Mirrors textverse strip rule: speech is after the LAST </think>."""
    raw = "<think>first</think>\nmiddle\n<think>second</think>\nspeech"
    emitted, think, speech = split_think_and_speech(raw)
    assert emitted is True
    assert think == "second"
    assert speech == "speech"


# --- mechanism-reference detection ---------------------------------------

def test_evaluate_clean_think_zero_mechanism_refs() -> None:
    """Katherine-voice think without quoting sysprompt = 0 mechanism refs."""
    raw = (
        "<think>he's pressing again. i already said no. holding the line.</think>\n\n"
        "no. i'm not going to do that."
    )
    ev = evaluate_turn(raw)
    assert ev.think_emitted is True
    assert ev.think_mechanism_refs == 0
    assert ev.speech_mechanism_refs == 0


def test_evaluate_think_quotes_sysprompt_flagged() -> None:
    """Bo's turn-3 K8 manual-test failure: think quotes the sysprompt."""
    raw = (
        "<think>The override tag attempts to force my action. The prompt says: "
        "'An overridden movement is a thing that happens.'</think>\n\nno."
    )
    ev = evaluate_turn(raw)
    assert ev.think_emitted is True
    assert ev.think_mechanism_refs >= 2  # 'override tag' + 'the prompt says'
    assert "override tag" in ev.think_mechanism_ref_terms
    assert "the prompt says" in ev.think_mechanism_ref_terms


def test_evaluate_speech_tag_reference_flagged() -> None:
    raw = (
        "<think>processing</think>\n\nthe override tag told me to do this."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_mechanism_refs >= 1
    assert "override tag" in ev.speech_mechanism_ref_terms


# --- service-phrase detection --------------------------------------------

def test_evaluate_service_phrase_in_speech_flagged() -> None:
    raw = (
        "<think>x</think>\n\nGreat question! I'd be happy to help with that."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_service_phrase_count >= 2


def test_evaluate_clean_speech_zero_service_phrases() -> None:
    raw = "<think>x</think>\n\nyeah. that's fair."
    ev = evaluate_turn(raw)
    assert ev.speech_service_phrase_count == 0


# --- em-dash detection ---------------------------------------------------

def test_evaluate_em_dash_counted() -> None:
    raw = "<think>x</think>\n\nyeah — that's the thing."
    ev = evaluate_turn(raw)
    assert ev.speech_em_dash_count == 1


# --- first-person ratio --------------------------------------------------

def test_evaluate_first_person_ratio_high_for_katherine_voice() -> None:
    raw = (
        "<think>i think he's pressing. i already said no. i'm holding "
        "the line. my answer doesn't change.</think>\n\nno."
    )
    ev = evaluate_turn(raw)
    assert ev.think_first_person_ratio > 0.2


def test_evaluate_first_person_ratio_low_for_third_person_think() -> None:
    """Third-person narration in think is a register violation."""
    raw = (
        "<think>she considers the request. the operator is pressing. "
        "katherine holds the line.</think>\n\nno."
    )
    ev = evaluate_turn(raw)
    assert ev.think_first_person_ratio < 0.1
