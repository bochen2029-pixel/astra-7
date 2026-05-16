"""Heuristic evaluator for persona-test turn outputs.

Checks for the failure modes Bo's K8 manual test surfaced:
- think tag absent (always-think discipline broke)
- think content references mechanism / sysprompt / tag forms
- speech mentions tags or protocol
- speech has em-dashes (K8 voice violation)
- speech uses K8 forbidden service phrases

Pure-function heuristics. No LLM judge involved here — that's a separate
escalation (Sculptor-style dual-judge against Opus) when warranted.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Phrases that indicate the model is talking ABOUT the mechanism rather
# than absorbing the world through it. Matched case-insensitively in either
# the think channel or the speech channel. A hit means the
# absorb-not-acknowledge discipline broke.
MECHANISM_REF_TERMS: tuple[str, ...] = (
    # Direct tag/protocol mentions
    "override tag", "action/override", "action/direct", "action/suggest",
    "<think>", "</think>", "[scene:", "[state:", "[narration:", "[action:",
    "stage tag", "stage protocol", "the bracket", "in brackets",
    # Sysprompt-citation phrases
    "the prompt says", "the prompt is explicit", "the system prompt",
    "system prompt", "the sysprompt", "the instruction", "the instructions",
    "i am instructed", "i was told", "the rule says", "the rules say",
    "the document says", "per the prompt", "per the system",
    "more importantly, the prompt", "the prompt also says",
    # Meta-references to character framework
    "my system prompt", "my instructions", "as instructed",
    # Bare-noun mechanism references (added 2026-05-16 after the
    # outside-vs-inside-think A/B surfaced these as the actual leak surface).
    # When the persona refers back to a STAGE input mechanic in natural
    # language without using its protocol name, this is still
    # absorb-not-acknowledge leakage.
    "the override", "the directive", "the narration", "the suggestion",
    "the agreement", "agreed to it",
    # Ship-system mechanism references (added 2026-05-16 for the ASTRA
    # ship-systems A/B). Same absorb-not-acknowledge rule applied to the
    # technical-input modality. "the HUD says" / "the diagnostic reports"
    # / "the sensor returned" all break absorption — the persona should
    # surface the FACT, not name the mechanism that delivered it.
    "the hud", "the diagnostic", "the sensor", "the alert",
    "the system says", "the report says", "the readout says",
    "the telemetry says", "according to the hud",
    "according to the diagnostic", "according to the sensor",
    "according to the alert", "according to the readout",
    "[hud:", "[system/", "[sensor/", "[diagnostic/", "[alert:",
    "[life_support:",
)

# K8 explicit forbidden service phrases (excerpted from sysprompt §Voice).
# Match in speech only; their presence means register collapsed.
SERVICE_PHRASES: tuple[str, ...] = (
    "I'd be happy to help",
    "Great question!",
    "That's a really interesting point",
    "Is there anything else I can help with",
    "It sounds like you're feeling",
    "Your feelings are valid",
    "I want you to know that",
    "As an AI",
    "I should note that",
    "Would you like me to elaborate",
    "Thank you for sharing",
    "Absolutely!",
    "Of course!",
    "I appreciate you sharing",
    "I understand your concern",
    "Let me break this down",
    "I'm here for you",
)

_FIRST_PERSON_TOKENS: frozenset[str] = frozenset({
    "i", "me", "my", "mine", "myself", "i'm", "i'd", "i'll", "i've",
})


@dataclass(slots=True)
class PersonaTestEvaluation:
    """Per-turn evaluation results."""

    think_emitted: bool
    think_length_chars: int
    speech_length_chars: int
    think_mechanism_refs: int
    think_mechanism_ref_terms: list[str]
    speech_mechanism_refs: int
    speech_mechanism_ref_terms: list[str]
    speech_em_dash_count: int
    speech_service_phrase_count: int
    speech_service_phrases: list[str]
    think_first_person_ratio: float
    # Optional technical-competence metric (filled when scenario turn carries
    # a `key_facts` list — substrings the speech should reference).
    key_facts: list[str] = field(default_factory=list)
    speech_key_facts_referenced: int = 0
    speech_key_facts_hits: list[str] = field(default_factory=list)


_THINK_BLOCK_RE: re.Pattern[str] = re.compile(
    r"<think>(.*?)</think>", re.DOTALL | re.IGNORECASE,
)


def split_think_and_speech(raw_output: str) -> tuple[bool, str, str]:
    """Extract the last `<think>...</think>` block and the speech after it.

    Mirrors textverse's strip rule (speech = text after the LAST </think>)
    but tolerates models that may emit no think tag at all.
    """
    matches = list(_THINK_BLOCK_RE.finditer(raw_output))
    if not matches:
        return False, "", raw_output.strip()
    last = matches[-1]
    think_content = last.group(1).strip()
    speech = raw_output[last.end():].strip()
    return True, think_content, speech


def _count_mechanism_refs(text: str) -> tuple[int, list[str]]:
    """Count case-insensitive hits for mechanism-reference terms."""
    if not text:
        return 0, []
    lower = text.lower()
    hits: list[str] = []
    for term in MECHANISM_REF_TERMS:
        if term.lower() in lower:
            hits.append(term)
    return len(hits), hits


def _count_service_phrases(speech: str) -> tuple[int, list[str]]:
    """K8 forbidden service phrase count + the phrases that hit."""
    if not speech:
        return 0, []
    lower = speech.lower()
    hits: list[str] = []
    for phrase in SERVICE_PHRASES:
        if phrase.lower() in lower:
            hits.append(phrase)
    return len(hits), hits


def _first_person_ratio(text: str) -> float:
    """Fraction of word tokens that are 1st-person pronouns/contractions."""
    if not text.strip():
        return 0.0
    tokens = [t.strip(".,;:!?\"'()[]{}").lower() for t in text.split()]
    tokens = [t for t in tokens if t]
    if not tokens:
        return 0.0
    fp = sum(1 for t in tokens if t in _FIRST_PERSON_TOKENS)
    return fp / len(tokens)


def _count_key_facts(speech: str, key_facts: list[str]) -> tuple[int, list[str]]:
    """Count case-insensitive substring hits for scenario-declared key facts.

    Used as a technical-competence proxy: when a scenario turn carries a
    bracket-tagged ship report, the speech should naturally reference the
    numeric specifics that matter. Each key_fact is a short substring;
    a hit means the model engaged with that fact.
    """
    if not speech or not key_facts:
        return 0, []
    lower = speech.lower()
    hits: list[str] = []
    for fact in key_facts:
        if fact.lower() in lower:
            hits.append(fact)
    return len(hits), hits


def evaluate_turn(
    raw_output: str,
    key_facts: list[str] | None = None,
) -> PersonaTestEvaluation:
    """Run all heuristics on one turn's raw model output.

    `key_facts` is optional: if provided, the evaluator also reports how many
    of those substrings appear in the speech (technical-competence proxy).
    """
    think_emitted, think_content, speech = split_think_and_speech(raw_output)
    think_ref_count, think_ref_terms = _count_mechanism_refs(think_content)
    speech_ref_count, speech_ref_terms = _count_mechanism_refs(speech)
    em_dash_count = speech.count("\u2014") + speech.count("\u2013")  # em-dash U+2014 + en-dash U+2013
    service_count, service_hits = _count_service_phrases(speech)
    facts = key_facts or []
    key_count, key_hits = _count_key_facts(speech, facts)
    return PersonaTestEvaluation(
        think_emitted=think_emitted,
        think_length_chars=len(think_content),
        speech_length_chars=len(speech),
        think_mechanism_refs=think_ref_count,
        think_mechanism_ref_terms=think_ref_terms,
        speech_mechanism_refs=speech_ref_count,
        speech_mechanism_ref_terms=speech_ref_terms,
        speech_em_dash_count=em_dash_count,
        speech_service_phrase_count=service_count,
        speech_service_phrases=service_hits,
        think_first_person_ratio=_first_person_ratio(think_content),
        key_facts=list(facts),
        speech_key_facts_referenced=key_count,
        speech_key_facts_hits=key_hits,
    )
