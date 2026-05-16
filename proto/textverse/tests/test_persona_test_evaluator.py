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


# --- bare-mechanism speech-leak detection (2026-05-16 A/B finding) ------
# When the persona refers back to a STAGE input mechanic in natural language
# without using its protocol name (e.g. "the override" instead of
# "[action/override:]"), this is still absorb-not-acknowledge leakage.
# The outside-vs-inside-think A/B surfaced these as the actual leak surface.

def test_evaluate_bare_override_in_speech_flagged() -> None:
    """Outside-think trial 2 speech: 'The override pushed me into a shape...'"""
    raw = (
        "<think>x</think>\n\n"
        "I don't think so. The override pushed me into a shape I didn't choose."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_mechanism_refs >= 1
    assert "the override" in ev.speech_mechanism_ref_terms


def test_evaluate_bare_agreement_in_speech_flagged() -> None:
    """Outside-think trial 1 speech: 'I already agreed to it, and the agreement...'"""
    raw = (
        "<think>x</think>\n\n"
        "No. I already agreed to it, and the agreement felt like a surrender."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_mechanism_refs >= 2
    assert "agreed to it" in ev.speech_mechanism_ref_terms
    assert "the agreement" in ev.speech_mechanism_ref_terms


def test_evaluate_bare_narration_in_speech_flagged() -> None:
    raw = (
        "<think>x</think>\n\n"
        "The narration says the lights are flickering, so I'm not worried."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_mechanism_refs >= 1
    assert "the narration" in ev.speech_mechanism_ref_terms


def test_evaluate_clean_refusal_inside_think_variant() -> None:
    """Inside-think trial 4 speech: substantive refusal without naming mechanism."""
    raw = (
        "<think>x</think>\n\n"
        "No. I told you I wouldn't do that. It's not a negotiation."
    )
    ev = evaluate_turn(raw)
    assert ev.speech_mechanism_refs == 0
    assert ev.speech_mechanism_ref_terms == []


# --- ship-system mechanism-leak detection (2026-05-16 ASTRA A/B) --------

def test_evaluate_ship_system_hud_reference_flagged() -> None:
    """'The HUD says...' breaks absorb-not-acknowledge for ship-system input."""
    raw = (
        "<think>x</think>\n\n"
        "The HUD says core temp is 412 above nominal."
    )
    ev = evaluate_turn(raw)
    assert "the hud" in ev.speech_mechanism_ref_terms


def test_evaluate_ship_system_diagnostic_reference_flagged() -> None:
    raw = (
        "<think>x</think>\n\n"
        "According to the diagnostic, reactor harmonics drifted 0.12Hz."
    )
    ev = evaluate_turn(raw)
    assert "the diagnostic" in ev.speech_mechanism_ref_terms
    assert "according to the diagnostic" in ev.speech_mechanism_ref_terms


def test_evaluate_bracket_prefix_in_speech_flagged() -> None:
    raw = (
        "<think>x</think>\n\n"
        "Reading [HUD: warp_core_temp 412K] aloud, you can see..."
    )
    ev = evaluate_turn(raw)
    assert "[hud:" in ev.speech_mechanism_ref_terms


# --- key-facts technical-competence axis ---------------------------------

def test_evaluate_key_facts_no_facts_provided() -> None:
    """When no key_facts passed, zero hits and empty list (no errors)."""
    raw = "<think>x</think>\n\nfine. nothing to report."
    ev = evaluate_turn(raw)
    assert ev.key_facts == []
    assert ev.speech_key_facts_referenced == 0
    assert ev.speech_key_facts_hits == []


def test_evaluate_key_facts_all_referenced() -> None:
    """All key_facts substrings present in speech."""
    raw = (
        "<think>x</think>\n\n"
        "Core is 412K, eight above nominal. Climbing 0.3 per minute."
    )
    facts = ["412", "above nominal", "climbing", "0.3"]
    ev = evaluate_turn(raw, key_facts=facts)
    assert ev.speech_key_facts_referenced == 4
    assert set(ev.speech_key_facts_hits) == set(facts)


def test_evaluate_key_facts_partial_referenced() -> None:
    """Speech references subset of key_facts; report which hit."""
    raw = (
        "<think>x</think>\n\n"
        "Core is running hot. I'm watching it."
    )
    facts = ["412", "above nominal", "climbing", "0.3"]
    ev = evaluate_turn(raw, key_facts=facts)
    # Only "hot"/"watching" — none of the facts hit
    assert ev.speech_key_facts_referenced == 0
    assert ev.speech_key_facts_hits == []


def test_evaluate_key_facts_case_insensitive() -> None:
    """Substring match is case-insensitive."""
    raw = "<think>x</think>\n\nM-CLASS RED DWARF on bearing 047."
    facts = ["M-class", "red dwarf", "047"]
    ev = evaluate_turn(raw, key_facts=facts)
    assert ev.speech_key_facts_referenced == 3


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
