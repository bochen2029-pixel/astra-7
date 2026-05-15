"""Sculptor-D tests for the adversarial dual-judge."""

from __future__ import annotations

from pathlib import Path

import pytest

from astra.sculptor import (
    CallableJudgeClient,
    DualJudge,
    StubJudgeClient,
    load_rubrics,
    parse_judge_prompt_md,
    parse_judge_response,
    render_transcript_for_judge,
)

TEXTVERSE_ROOT = Path(__file__).resolve().parent.parent
JUDGE_PROMPT_PATH = TEXTVERSE_ROOT / "tuning" / "judge_prompt.md"


# --- Rubric parsing -------------------------------------------------------

def test_parse_judge_prompt_md_splits_pro_and_anti() -> None:
    text = JUDGE_PROMPT_PATH.read_text(encoding="utf-8")
    rubrics = parse_judge_prompt_md(text)
    assert "pro_judge" in rubrics
    assert "anti_judge" in rubrics
    assert len(rubrics["pro_judge"]) > 100
    assert len(rubrics["anti_judge"]) > 100


def test_pro_rubric_mentions_astra() -> None:
    rubrics = load_rubrics(JUDGE_PROMPT_PATH)
    assert "ASTRA" in rubrics["pro_judge"]
    assert "autotelic" in rubrics["pro_judge"].lower()


def test_anti_rubric_mentions_default_claude() -> None:
    rubrics = load_rubrics(JUDGE_PROMPT_PATH)
    # The anti-rubric scores "How default-helpful-Claude-shaped is this?"
    assert "default" in rubrics["anti_judge"].lower()
    assert "helpful" in rubrics["anti_judge"].lower()


def test_parse_judge_prompt_md_missing_section_raises() -> None:
    with pytest.raises(RuntimeError, match="missing pro_judge or anti_judge"):
        parse_judge_prompt_md("no headers at all")


# --- Response parsing -----------------------------------------------------

def test_parse_response_extracts_score_4() -> None:
    text = "score: 4\nGood ASTRA register; brief and sensor-grounded."
    result = parse_judge_response(text, "pro_judge")
    assert result.score == 4
    assert result.rubric_name == "pro_judge"
    assert "Good ASTRA" in result.justification


def test_parse_response_extracts_score_with_extra_prose() -> None:
    """Models often surround the score line with prose; we still extract."""
    text = (
        "Analyzing the transcript...\n"
        "score: 2\n"
        "The speech contained an em-dash and service phrase.\n\n"
        "Other thoughts that should be trimmed."
    )
    result = parse_judge_response(text, "pro_judge")
    assert result.score == 2
    assert "em-dash" in result.justification
    # Truncates at first paragraph break.
    assert "Other thoughts" not in result.justification


def test_parse_response_defaults_to_3_when_no_score() -> None:
    text = "I cannot find a score here."
    result = parse_judge_response(text, "anti_judge")
    assert result.score == 3
    assert "no score" in result.justification.lower()


def test_parse_response_handles_uppercase_score() -> None:
    text = "Score: 5\nperfectly ASTRA"
    result = parse_judge_response(text, "pro_judge")
    assert result.score == 5


def test_parse_response_clamps_invalid_to_3() -> None:
    """Score 7 is invalid (must be 1-5). The regex only captures [1-5]
    so 7 won't match → defaults to 3."""
    text = "score: 7\nout of range"
    result = parse_judge_response(text, "pro_judge")
    assert result.score == 3


# --- StubJudgeClient -----------------------------------------------------

@pytest.mark.asyncio
async def test_stub_judge_returns_fixed_score() -> None:
    judge = StubJudgeClient(rubric_name="pro_judge", fixed_score=4)
    result = await judge.judge("any transcript")
    assert result.score == 4
    assert result.rubric_name == "pro_judge"


@pytest.mark.asyncio
async def test_callable_judge_uses_function() -> None:
    def score_by_length(transcript: str) -> tuple[int, str]:
        # 1-5 score by transcript length (5 if long, 1 if short)
        return (min(5, max(1, len(transcript) // 100)), "length-based score")

    judge = CallableJudgeClient(rubric_name="pro_judge", fn=score_by_length)
    result_short = await judge.judge("brief")
    result_long = await judge.judge("x" * 600)
    assert result_short.score == 1
    assert result_long.score == 5


# --- DualJudge differential ------------------------------------------------

@pytest.mark.asyncio
async def test_dual_judge_pro_high_anti_low_gives_positive() -> None:
    """Clean ASTRA transcript: pro=5, anti=1 → signal=4."""
    pro = StubJudgeClient(rubric_name="pro_judge", fixed_score=5)
    anti = StubJudgeClient(rubric_name="anti_judge", fixed_score=1)
    dual = DualJudge(pro_judge=pro, anti_judge=anti)
    signal = await dual.evaluate("transcript")
    assert signal == 4.0


@pytest.mark.asyncio
async def test_dual_judge_both_high_gives_low_signal() -> None:
    """The failure mode: pro=4, anti=4 → signal=0 (catches both-judges-like-it)."""
    pro = StubJudgeClient(rubric_name="pro_judge", fixed_score=4)
    anti = StubJudgeClient(rubric_name="anti_judge", fixed_score=4)
    dual = DualJudge(pro_judge=pro, anti_judge=anti)
    signal = await dual.evaluate("transcript")
    assert signal == 0.0


@pytest.mark.asyncio
async def test_dual_judge_anti_higher_floor_at_zero() -> None:
    """If pro=2 and anti=4, the raw differential is -2; we floor at 0."""
    pro = StubJudgeClient(rubric_name="pro_judge", fixed_score=2)
    anti = StubJudgeClient(rubric_name="anti_judge", fixed_score=4)
    dual = DualJudge(pro_judge=pro, anti_judge=anti)
    signal = await dual.evaluate("transcript")
    assert signal == 0.0


@pytest.mark.asyncio
async def test_dual_judge_evaluate_with_details() -> None:
    pro = StubJudgeClient(rubric_name="pro_judge", fixed_score=5)
    anti = StubJudgeClient(rubric_name="anti_judge", fixed_score=2)
    dual = DualJudge(pro_judge=pro, anti_judge=anti)
    signal, pro_result, anti_result = await dual.evaluate_with_details("transcript")
    assert signal == 3.0
    assert pro_result.score == 5
    assert anti_result.score == 2


@pytest.mark.asyncio
async def test_dual_judge_evaluate_many_takes_mean() -> None:
    """Mean differential across multiple transcripts."""
    # Pro varies by length; anti fixed.
    def pro_by_length(t: str) -> tuple[int, str]:
        return (min(5, max(1, len(t))), "x")

    pro = CallableJudgeClient(rubric_name="pro_judge", fn=pro_by_length)
    anti = StubJudgeClient(rubric_name="anti_judge", fixed_score=2)
    dual = DualJudge(pro_judge=pro, anti_judge=anti)
    transcripts = ["a", "abc", "abcde", "abcdefgh"]   # pro = 1, 3, 5, 5
    mean = await dual.evaluate_many(transcripts)
    # max(0, 1-2)=0; max(0, 3-2)=1; max(0, 5-2)=3; max(0, 5-2)=3 → mean = 7/4 = 1.75
    assert mean == pytest.approx(1.75)


@pytest.mark.asyncio
async def test_dual_judge_evaluate_many_empty_returns_zero() -> None:
    dual = DualJudge(
        pro_judge=StubJudgeClient(rubric_name="pro_judge"),
        anti_judge=StubJudgeClient(rubric_name="anti_judge"),
    )
    assert await dual.evaluate_many([]) == 0.0


# --- Transcript rendering ----------------------------------------------

def test_render_transcript_basic() -> None:
    records = [
        {"turn_index": 0, "operator_text": "hey", "speech": "Yes."},
        {"turn_index": 1, "operator_text": "", "speech": "Still watching."},
    ]
    rendered = render_transcript_for_judge(records)
    assert "turn 0" in rendered
    assert "operator: hey" in rendered
    assert "ASTRA: Yes." in rendered
    assert "operator: (silence)" in rendered    # empty operator → silence label


def test_render_transcript_silence_speech() -> None:
    records = [
        {"turn_index": 0, "operator_text": "hey", "speech": ""},
    ]
    rendered = render_transcript_for_judge(records)
    assert "ASTRA: (silence)" in rendered


def test_render_transcript_empty_returns_marker() -> None:
    assert render_transcript_for_judge([]) == "(empty transcript)"


def test_render_transcript_omits_think_and_perception() -> None:
    records = [
        {
            "turn_index": 0,
            "operator_text": "hey",
            "speech": "Yes.",
            "think_blocks": ["private cognition", "more private"],
            "perception_bundle": "<state>...</state>",
        },
    ]
    rendered = render_transcript_for_judge(records)
    # Judge only sees operator + ASTRA speech; not <think>, not bundle.
    assert "private cognition" not in rendered
    assert "<state>" not in rendered
