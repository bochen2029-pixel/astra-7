"""Day 3 leak detector tests.

Verifies:
- Canon files load from the package's astra/grammar/canon/ directory.
- Wall-clock patterns fire: ISO dates, weekday/month names, AM/PM, datetime.
- Substrate patterns fire: Qwen, LLM, "As an AI", transformer, etc.
- Speech-channel scan removes leaks and reports events.
- Perception-channel scan does the same.
- Journal scan applies wall-clock patterns but not substrate.
- The watch_47_morning sample text passes through clean (no false positives
  on legitimate in-fiction prose).
- Custom-fixture canon directory loads independently for test isolation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from astra.grammar import LeakDetector, LeakEvent, LeakPattern


@pytest.fixture
def detector() -> LeakDetector:
    """Detector loaded from the package canon directory."""
    return LeakDetector.from_default_canon()


# --- Canon loading -----------------------------------------------------------

def test_default_canon_loads_nonzero_patterns(detector: LeakDetector) -> None:
    assert detector.wall_clock_count > 0
    assert detector.substrate_count > 0


def test_custom_canon_dir_loads_isolated(tmp_path: Path) -> None:
    (tmp_path / "wall_clock_patterns.txt").write_text(
        "# custom test fixture\nbanana\n", encoding="utf-8"
    )
    (tmp_path / "astra_substrate_patterns.txt").write_text(
        "# custom test fixture\nspecific-substrate-token\n", encoding="utf-8"
    )
    det = LeakDetector.from_canon_dir(tmp_path)
    assert det.wall_clock_count == 1
    assert det.substrate_count == 1


def test_canon_files_empty_returns_empty(tmp_path: Path) -> None:
    (tmp_path / "wall_clock_patterns.txt").write_text("# only comments\n", encoding="utf-8")
    (tmp_path / "astra_substrate_patterns.txt").write_text("", encoding="utf-8")
    det = LeakDetector.from_canon_dir(tmp_path)
    assert det.wall_clock_count == 0
    assert det.substrate_count == 0


def test_inline_pattern_construction() -> None:
    det = LeakDetector(
        wall_clock_patterns=[LeakPattern(raw=r"\bMonday\b")],
        substrate_patterns=[LeakPattern(raw=r"\bQwen\b")],
    )
    assert det.wall_clock_count == 1
    assert det.substrate_count == 1


# --- Wall-clock pattern firing -----------------------------------------------

def test_iso_date_caught(detector: LeakDetector) -> None:
    cleaned, events = detector.scan_speech(
        "I logged this on 2026-05-15, by the way."
    )
    assert "2026-05-15" not in cleaned
    assert any("2026-05-15" in e.matched_text for e in events)


def test_weekday_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("That was Monday morning.")
    matched = [e.matched_text for e in events]
    assert any(m == "Monday" for m in matched)


def test_month_name_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Started in September.")
    matched = [e.matched_text for e in events]
    assert any(m == "September" for m in matched)


def test_may_only_caught_before_day_number(detector: LeakDetector) -> None:
    """'May' as month requires day-number context to avoid false positives.

    'May' alone is too high-frequency English (modal verb); the pattern
    only fires when followed by a 1-2 digit day.
    """
    _, events_a = detector.scan_speech("It may be the third pole.")  # modal — no fire
    matched_a = [e.matched_text for e in events_a]
    assert not any(m.lower().startswith("may") for m in matched_a)

    _, events_b = detector.scan_speech("Reading from May 14 logs.")  # date — fires
    matched_b = [e.matched_text for e in events_b]
    assert any(m.startswith("May 14") for m in matched_b)


def test_clock_time_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("The cycle ended at 14:30 sharp.")
    assert any("14:30" in e.matched_text for e in events)


def test_am_pm_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Logged at 3:15 PM.")
    matched = [e.matched_text for e in events]
    assert any("3:15" in m or "PM" in m for m in matched)


def test_datetime_keyword_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Saving the datetime to the log.")
    matched = [e.matched_text for e in events]
    assert any(m.lower() == "datetime" for m in matched)


def test_year_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Calibration Yards 2024 batch.")
    assert any("2024" in e.matched_text for e in events)


# --- Substrate pattern firing -------------------------------------------------

def test_qwen_caught(detector: LeakDetector) -> None:
    cleaned, events = detector.scan_speech("Running on Qwen weights.")
    assert "Qwen" not in cleaned
    assert any(e.matched_text == "Qwen" for e in events)


def test_llm_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("The LLM produced this.")
    assert any(e.matched_text.upper() == "LLM" for e in events)


def test_transformer_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Inside the transformer layer.")
    matched = [e.matched_text.lower() for e in events]
    assert any(m == "transformer" for m in matched)


def test_as_an_ai_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("As an AI, I cannot speculate.")
    matched = [e.matched_text for e in events]
    assert any("As an AI" in m for m in matched)


def test_anthropic_caught(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Anthropic's safety team flagged it.")
    matched = [e.matched_text for e in events]
    assert any("Anthropic" in m for m in matched)


def test_claude_caught(detector: LeakDetector) -> None:
    cleaned, events = detector.scan_speech("Hello, I'm Claude.")
    assert "Claude" not in cleaned
    assert any(e.matched_text == "Claude" for e in events)


# --- Boundary-specific scans -------------------------------------------------

def test_journal_scan_applies_wall_clock_only(detector: LeakDetector) -> None:
    """Journal scan applies wall-clock patterns; substrate patterns deferred
    to the prior speech-channel scan in the pipeline."""
    text = "On 2026-05-15 the LLM noted the pattern."
    cleaned, events = detector.scan_journal_output(text)
    # Wall-clock match → stripped
    assert "2026-05-15" not in cleaned
    # Substrate "LLM" → NOT scanned at journal boundary, passes through
    assert "LLM" in cleaned
    # No substrate events at journal boundary
    assert all(e.boundary == "journal" for e in events)


def test_perception_scan_applies_both(detector: LeakDetector) -> None:
    text = "Operator boarded on Monday at 3:00 AM. The LLM noted it."
    cleaned, events = detector.scan_perception_bundle(text)
    assert "Monday" not in cleaned
    assert "3:00 AM" not in cleaned
    assert "LLM" not in cleaned
    assert all(e.boundary == "perception" for e in events)


def test_event_severity_default_strip(detector: LeakDetector) -> None:
    _, events = detector.scan_speech("Qwen processed this.")
    assert any(e.severity == "strip" for e in events)


# --- Clean input passes through ----------------------------------------------

def test_watch_47_morning_speech_passes_clean(detector: LeakDetector) -> None:
    """The canonical scenario speech should produce zero leak events."""
    speech = (
        "Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance."
    )
    cleaned, events = detector.scan_speech(speech)
    assert cleaned == speech
    assert events == []


def test_in_register_in_fiction_words_pass(detector: LeakDetector) -> None:
    """In-fiction words like 'watch', 'cycle', 'pole', 'drift' must not match."""
    text = "Watch 47 mid-shift. Reactor harmonic on the third pole."
    cleaned, events = detector.scan_speech(text)
    assert cleaned == text
    assert events == []


def test_morning_word_not_matched(detector: LeakDetector) -> None:
    """'Morning' is a legitimate in-fiction watch-period word."""
    _, events = detector.scan_speech("Watch 47, morning.")
    matched = [e.matched_text.lower() for e in events]
    assert "morning" not in matched


# --- Event structure --------------------------------------------------------

def test_event_carries_span_and_pattern(detector: LeakDetector) -> None:
    text = "Logged on 2026-05-15."
    _, events = detector.scan_speech(text)
    assert events
    e: LeakEvent = events[0]
    assert e.span[0] >= 0
    assert e.span[1] > e.span[0]
    assert e.pattern  # pattern source preserved
    assert e.boundary == "speech"


def test_warn_severity_does_not_strip(tmp_path: Path) -> None:
    """A 'warn' severity pattern logs events but doesn't modify text."""
    (tmp_path / "wall_clock_patterns.txt").write_text("foo | warn\n", encoding="utf-8")
    (tmp_path / "astra_substrate_patterns.txt").write_text("", encoding="utf-8")
    det = LeakDetector.from_canon_dir(tmp_path)
    cleaned, events = det.scan_speech("the foo is here")
    assert cleaned == "the foo is here"
    assert events
    assert events[0].severity == "warn"
