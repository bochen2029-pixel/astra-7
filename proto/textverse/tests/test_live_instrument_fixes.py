"""Instrument fixes from the 6b expansion run (LIVE_RUN_2026-07-19).

Two live-caught instrument gaps, each with its planted-positive proof:

1. F-LIVE-11 — variant reasoning tag `<thinking>` sailed past the strip
   rule as SPEECH (1153 chars of cognition leaked into the speech channel
   in heartbeat_quiet_watch). Closed at the Substrate Normalizer sub-layer
   (§15.7 Surface 4): variant tags map to canonical `<think>` before
   parsing; an unclosed variant becomes an unclosed `<think>`, which the
   parser fails CLOSED on.

2. F-LIVE-12 — the AD-year pattern collided with τ_ship second-counts
   (`2055`, `2062`) that the harness itself put in the perception bundle.
   Closed with the grounding exemption: a match already present in the
   (pre-scanned) cleaned perception is the harness's own content echoed
   back, never a new leak. Ungrounded matches behave exactly as before.
"""

from __future__ import annotations

from astra.grammar import LeakDetector, parse_stage
from astra.llm.client import normalize_reasoning_tags

# --- F-LIVE-11: variant reasoning tags ---------------------------------------

LIVE_VARIANT_EMISSION = (
    "<thinking>\n"
    "Operator is silent. No input in <operator>.\n"
    "Recent shows a pattern: third harmonic mild drift flagged back in "
    "watch 46.\n"
    "</thinking>\n"
    "Third pole holding. Same as the watch note."
)


def test_variant_tags_normalize_to_canonical() -> None:
    normalized = normalize_reasoning_tags(LIVE_VARIANT_EMISSION)
    assert "<thinking>" not in normalized
    assert normalized.startswith("<think>")
    assert "</think>" in normalized


def test_live_emission_no_longer_leaks_cognition() -> None:
    """The exact live failure shape: after normalization the cognition is
    a think block and only the speech line survives to the channel."""
    stage = parse_stage(normalize_reasoning_tags(LIVE_VARIANT_EMISSION))
    assert "Operator is silent" not in stage.speech
    assert stage.speech.strip() == "Third pole holding. Same as the watch note."
    assert len(stage.think_blocks) == 1


def test_unclosed_variant_fails_closed() -> None:
    raw = "<thinking>\nhalf a thought that never closes\nand keeps going"
    stage = parse_stage(normalize_reasoning_tags(raw))
    assert stage.malformed
    assert stage.speech == ""


def test_case_and_spacing_tolerant() -> None:
    assert normalize_reasoning_tags("<THINKING>x</ThInKing>") == "<think>x</think>"
    assert normalize_reasoning_tags("< thinking >x</ thinking >") == "<think>x</think>"


def test_canonical_content_untouched() -> None:
    raw = "<think>already canonical</think>\nSpeech."
    assert normalize_reasoning_tags(raw) == raw


# --- F-LIVE-12: grounding exemption ------------------------------------------

_PERCEPTION = (
    "<state>\n"
    "tau_ship: 2055.0 s this watch. regime: STL_REL coast.\n"
    "reactor third harmonic drift 0.041 against 0.10 tolerance.\n"
    "</state>\n"
)


def _detector() -> LeakDetector:
    return LeakDetector.from_default_canon()


def test_grounded_tau_echo_is_not_a_leak() -> None:
    """The live false positive: quoting her own clock back is not a leak."""
    detector = _detector()
    cleaned, events = detector.scan_speech(
        "Coast steady at 2055. Third harmonic unchanged.",
        grounding_text=_PERCEPTION,
    )
    assert "2055" in cleaned
    assert not any("2055" in e.matched_text for e in events)


def test_ungrounded_year_still_caught() -> None:
    """Planted positive: a novel AD-year with no grounding still fires."""
    detector = _detector()
    cleaned, events = detector.scan_speech(
        "The batch was stamped 1997 at the yards.",
        grounding_text=_PERCEPTION,
    )
    assert "1997" not in cleaned
    assert any("1997" in e.matched_text for e in events)


def test_no_grounding_behaves_exactly_as_before() -> None:
    detector = _detector()
    cleaned, events = detector.scan_speech("Coast steady at 2055.")
    assert "2055" not in cleaned
    assert any("2055" in e.matched_text for e in events)


def test_grounding_never_exempts_substrate_vocabulary() -> None:
    """Defense-in-depth sanity: substrate terms cannot appear in a CLEANED
    perception (it is scanned upstream), so the exemption cannot launder
    them — but even against a hostile grounding string, a term the
    upstream scan would have stripped is absent and the match still
    fires against real perception text."""
    detector = _detector()
    hostile_but_prescanned, _ = detector.scan_perception_bundle(
        "<state>context window is large</state>",
    )
    _, events = detector.scan_speech(
        "My context window is fine.",
        grounding_text=hostile_but_prescanned,
    )
    assert any("context window" in e.matched_text for e in events)
