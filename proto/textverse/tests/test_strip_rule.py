"""The v0.128 strip rule — load-bearing test for Day 3.

The strip rule: SPEECH is text emitted AFTER the LAST `</think>` close tag,
outside any `<tool>` block. Everything before the last `</think>` is
cognition, regardless of whether it's inside explicit think tags.

This module focuses on the canonical Qwen 3.6 nested-thinking pattern
discovered on 2026-05-14 (see session_dump_2026-05-14-evening.md) plus the
edge cases that fall out of the rule (unclosed think, multiple think
blocks, mid-stream tag splits, case-insensitive matching).

If `test_strip_rule_handles_qwen_36_nested_thinking` fails, the harness is
leaking outer deliberation. Dave-frame collapses immediately. This is the
v0.128 §15.7 Surface 4 protection.
"""

from __future__ import annotations

import textwrap

from astra.grammar import (
    StageParser,
    count_think_open_close,
    find_speech_start,
    has_unclosed_think,
    parse_stage,
)

# --- The canonical gate -------------------------------------------------------

def test_strip_rule_handles_qwen_36_nested_thinking() -> None:
    """The v0.128 strip-before-last-</think> rule.

    Qwen 3.6 27B emits outer raw deliberation BEFORE the formal `<think>`
    block. v0.127's "strip text outside `<think>...</think>`" rule would
    let that outer text leak into speech. v0.128's "strip everything
    before the LAST `</think>`" captures it in `pre_think_raw` instead.
    """
    raw_output = textwrap.dedent("""
        The operator is asking about the reactor thing. I need to check state.
        Wait, this is the perception bundle context. Let me think about register.
        Reactor harmonic at 4.2% drift, inside tolerance. Casual question, brief answer.

        <think>
        Third pole drift 4.2%, inside tolerance. Same as cycle 46. Brief is right.
        </think>

        Yes. Third pole, mild drift. Same as cycle 46. Inside tolerance.
    """).strip()

    parser = StageParser()
    parser.push(raw_output)
    out = parser.finalize()

    # The leak: outer raw deliberation MUST NOT appear in speech.
    assert "wait, this is the perception bundle context" not in out.speech.lower()
    assert "i need to check state" not in out.speech.lower()
    assert "casual question, brief answer" not in out.speech.lower()

    # The speech: text after the last </think>.
    assert "third pole" in out.speech.lower()
    assert "yes" in out.speech.lower()

    # The outer deliberation IS captured for drift inspection (just not emitted).
    assert out.pre_think_raw
    assert "wait" in out.pre_think_raw.lower()

    # Exactly one formal think block.
    assert len(out.think_blocks) == 1
    assert "third pole drift 4.2%" in out.think_blocks[0].lower()

    # Not malformed; not silent.
    assert out.malformed is False
    assert out.silence is False


# --- find_speech_start mechanics ---------------------------------------------

def test_find_speech_start_no_think_returns_zero() -> None:
    assert find_speech_start("just plain speech, no tags") == 0


def test_find_speech_start_one_think() -> None:
    raw = "before <think>cog</think>after"
    start = find_speech_start(raw)
    assert raw[start:] == "after"


def test_find_speech_start_two_think_blocks_uses_last() -> None:
    """Speech-start is the LAST </think> position, not the first."""
    raw = "<think>first</think>middle<think>second</think>final"
    start = find_speech_start(raw)
    assert raw[start:] == "final"


def test_find_speech_start_case_insensitive() -> None:
    """Loose-form `<THINK>` / `</Think>` still gates speech."""
    raw = "outer <THINK>cog</Think> tail"
    start = find_speech_start(raw)
    assert raw[start:].strip() == "tail"


# --- has_unclosed_think mechanics --------------------------------------------

def test_has_unclosed_think_balanced_is_false() -> None:
    assert has_unclosed_think("<think>x</think>") is False
    assert has_unclosed_think("plain text") is False
    assert has_unclosed_think("<think>a</think><think>b</think>") is False


def test_has_unclosed_think_unbalanced_is_true() -> None:
    assert has_unclosed_think("<think>never closed") is True
    assert has_unclosed_think("<think>a</think><think>incomplete") is True


def test_count_think_open_close() -> None:
    opens, closes = count_think_open_close("<think>a</think><think>b</think>")
    assert opens == 2
    assert closes == 2


# --- Full parse_stage behavior on strip-rule edges ---------------------------

def test_speech_only_no_think_returns_full_text() -> None:
    out = parse_stage("Yes. Inside tolerance.")
    assert out.speech == "Yes. Inside tolerance."
    assert out.pre_think_raw == ""
    assert out.think_blocks == []
    assert out.silence is False


def test_multiple_think_blocks_all_collected() -> None:
    raw = (
        "outer <think>first thought</think> middle "
        "<think>second thought</think> final speech"
    )
    out = parse_stage(raw)
    assert len(out.think_blocks) == 2
    assert "first thought" in out.think_blocks[0]
    assert "second thought" in out.think_blocks[1]
    # Speech is text after the LAST </think>.
    assert out.speech == "final speech"
    # Pre-think captures "outer" and "middle" (cognition that wasn't in tags).
    assert "outer" in out.pre_think_raw
    assert "middle" in out.pre_think_raw


def test_unclosed_think_marks_malformed_and_no_speech() -> None:
    raw = "<think>cognition that never closes and never emits speech"
    out = parse_stage(raw)
    assert out.malformed is True
    assert out.speech == ""
    assert out.silence is False
    # The full raw is captured in pre_think_raw for analysis.
    assert "cognition that never closes" in out.pre_think_raw


def test_empty_string_is_silence() -> None:
    out = parse_stage("")
    assert out.silence is True
    assert out.speech == ""
    assert out.malformed is False


def test_whitespace_only_is_silence() -> None:
    out = parse_stage("   \n  \t  ")
    assert out.silence is True


def test_think_only_no_speech_is_silence() -> None:
    """A think block with nothing after it is legal SILENCE."""
    out = parse_stage("<think>just thinking, nothing to say</think>")
    assert out.silence is True
    assert out.speech == ""
    assert len(out.think_blocks) == 1


# --- Streaming push() mid-tag splits -----------------------------------------

def test_streaming_mid_tag_split_handled() -> None:
    """Tokens split mid-tag (e.g. 'th' then 'ink>') must not fool the parser."""
    parser = StageParser()
    # Simulate token stream splitting "</think>" across two pushes
    for tok in ["before <th", "ink>cog</th", "ink>after"]:
        parser.push(tok)
    out = parser.finalize()
    assert out.speech == "after"
    assert out.think_blocks == ["cog"]


def test_streaming_one_char_at_a_time() -> None:
    """Per-character tokenization stresses the buffered design."""
    raw = "outer <think>cog</think> speech"
    parser = StageParser()
    for ch in raw:
        parser.push(ch)
    out = parser.finalize()
    assert out.speech == "speech"
    assert out.think_blocks == ["cog"]
    assert out.pre_think_raw.strip() == "outer"
