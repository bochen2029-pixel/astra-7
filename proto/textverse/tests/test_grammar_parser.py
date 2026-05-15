"""Day 3 grammar parser tests beyond the strip rule.

Covers: tool call parsing (JSON body, loose body, multiple tools), tool
calls inside vs outside think, silence vs non-silence distinction,
StageOutput frozen semantics, raw buffer accessor.

Strip-rule mechanics live in test_strip_rule.py; this file is about the
non-strip-rule parts of the parser surface.
"""

from __future__ import annotations

from pydantic import ValidationError

from astra.grammar import StageOutput, StageParser, ToolCall, parse_stage

# --- Tool call parsing --------------------------------------------------------

def test_tool_call_with_json_body_parses() -> None:
    raw = '<tool name="power.allocate">{"subsystem":"warp","fraction":0.5}</tool>'
    out = parse_stage(raw)
    assert len(out.tool_calls) == 1
    tc = out.tool_calls[0]
    assert tc.name == "power.allocate"
    assert tc.arguments == {"subsystem": "warp", "fraction": 0.5}
    assert "subsystem" in tc.raw_body


def test_tool_call_with_loose_body_keeps_raw_for_adapter() -> None:
    """Non-JSON body: arguments dict is empty, raw_body preserved for adapter."""
    raw = '<tool name="log.write">channel: ops, text: "harmonic noted"</tool>'
    out = parse_stage(raw)
    assert len(out.tool_calls) == 1
    tc = out.tool_calls[0]
    assert tc.name == "log.write"
    assert tc.arguments == {}
    assert "harmonic noted" in tc.raw_body


def test_multiple_tool_calls() -> None:
    raw = (
        '<tool name="lights.set">{"zone":"bridge","intensity":0.4}</tool>'
        ' afterthought speech'
        ' <tool name="log.write">{"channel":"watch","text":"settled"}</tool>'
    )
    out = parse_stage(raw)
    assert len(out.tool_calls) == 2
    assert {tc.name for tc in out.tool_calls} == {"lights.set", "log.write"}


def test_tool_inside_think_block_ignored() -> None:
    """Tool calls inside `<think>` are cognition, not action.

    Per spec §4.3: `<tool>` blocks outside `<think>` are action; inside are
    reasoning. Parser must not dispatch reasoning-tool tokens.
    """
    raw = (
        "<think>"
        "I'm considering whether to log this. "
        '<tool name="log.write">{"channel":"watch","text":"hypothetical"}</tool>'
        " But I decide not to."
        "</think>"
        " Yes."
    )
    out = parse_stage(raw)
    assert out.tool_calls == []
    assert out.speech == "Yes."


def test_tool_call_with_extra_attributes() -> None:
    """Adapter-loose form: tool may have additional attributes after name."""
    raw = '<tool name="sensors.scan" priority="high">{"region":"forward"}</tool>'
    out = parse_stage(raw)
    assert len(out.tool_calls) == 1
    assert out.tool_calls[0].name == "sensors.scan"
    assert out.tool_calls[0].arguments == {"region": "forward"}


# --- Tool calls + speech interaction -----------------------------------------

def test_speech_with_tool_call_speech_text_excludes_tool() -> None:
    """Tool blocks are removed from speech; surrounding prose remains."""
    raw = (
        "Adjusting now. "
        '<tool name="lights.set">{"zone":"bridge","intensity":0.4}</tool>'
        " Bridge dimmed."
    )
    out = parse_stage(raw)
    assert "Adjusting now" in out.speech
    assert "Bridge dimmed" in out.speech
    assert "tool" not in out.speech.lower()
    assert len(out.tool_calls) == 1


def test_tool_call_without_speech_is_not_silence() -> None:
    """Acting without speaking is NOT silence — she's doing something."""
    raw = '<tool name="lights.set">{"zone":"bridge","intensity":0.0}</tool>'
    out = parse_stage(raw)
    assert out.silence is False
    assert out.speech == ""
    assert len(out.tool_calls) == 1


# --- StageOutput shape -------------------------------------------------------

def test_stage_output_is_frozen() -> None:
    out = parse_stage("hello")
    try:
        out.speech = "altered"
    except ValidationError:
        return
    raise AssertionError("StageOutput should reject mutations")


def test_tool_call_is_frozen() -> None:
    tc = ToolCall(name="foo", arguments={"x": 1}, raw_body="raw")
    try:
        tc.name = "bar"
    except ValidationError:
        return
    raise AssertionError("ToolCall should reject mutations")


def test_stage_output_default_construction() -> None:
    out = StageOutput()
    assert out.think_blocks == []
    assert out.pre_think_raw == ""
    assert out.tool_calls == []
    assert out.speech == ""
    assert out.silence is False
    assert out.malformed is False


# --- StageParser buffering ---------------------------------------------------

def test_parser_raw_property_accumulates() -> None:
    parser = StageParser()
    parser.push("foo")
    parser.push("bar")
    assert parser.raw == "foobar"


def test_parser_finalize_does_not_consume_buffer() -> None:
    """finalize() is idempotent — calling twice gives same output."""
    parser = StageParser()
    parser.push("<think>x</think> y")
    out1 = parser.finalize()
    out2 = parser.finalize()
    assert out1 == out2
