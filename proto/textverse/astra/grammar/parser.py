"""STAGE protocol parser per spec v0.129 §4.3 + §6.2.

Parses ASTRA-LLM's raw output into the four STAGE channels:
- `think_blocks`:  contents of each closed `<think>...</think>` block.
- `pre_think_raw`: outer raw deliberation before the LAST `</think>`,
                   captured for drift analysis but NEVER emitted.
- `tool_calls`:    parsed `<tool name="...">...</tool>` blocks.
- `speech`:        text AFTER the LAST `</think>` close, OUTSIDE any
                   `<tool>` block. The only operator-facing channel.
- `silence`:       speech is empty AND no tool calls — a legal primitive.

The parser is streaming-aware via `push(token)` / `finalize()`. Day 3 ships
the buffered implementation (accumulate, parse on finalize). Streaming
emission per-token is a Day 5 polish.

Edge cases handled (per §6.2):
- Multiple `<think>` blocks: all contents collected; only LAST close gates speech.
- Unclosed `<think>` at end: entire output → pre_think_raw; no speech.
- `<tool>` blocks inside `<think>`: ignored (cognition contains tool reasoning,
   not action).
- `<tool>` blocks outside think: counted, removed from speech.
- Mid-token tag splits (push("th") + push("ink>")): handled by buffering.
- Case-insensitive tag matching (defense in depth for loose-form models).
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from astra.grammar.strip_rules import (
    THINK_RE,
    TOOL_RE,
    find_speech_start,
    has_unclosed_think,
)


class ToolCall(BaseModel):
    """One `<tool>` block parsed from STAGE output.

    `arguments` is the JSON-parsed dict body when parseable, else empty.
    `raw_body` preserves the unparsed body so the adapter LLM can normalize
    loose-form invocations.
    """

    model_config = ConfigDict(frozen=True)

    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    raw_body: str = ""


class StageOutput(BaseModel):
    """Result of parsing one ASTRA-LLM stream per spec §4.3."""

    model_config = ConfigDict(frozen=True)

    think_blocks: list[str] = Field(default_factory=list)
    pre_think_raw: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    speech: str = ""
    silence: bool = False
    malformed: bool = False


def _parse_tool_body(body: str) -> dict[str, Any]:
    """Best-effort parse of a `<tool>` body as JSON.

    On parse failure, return empty dict (raw_body is preserved for adapter
    fallback). No exceptions propagate — STAGE parsing must not crash on
    a single malformed tool block.
    """
    stripped = body.strip()
    if not stripped:
        return {}
    try:
        parsed = json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def parse_stage(raw: str) -> StageOutput:
    """Parse one complete STAGE output string into channels.

    Per spec §4.3 + §6.2 + the v0.128 corrected strip rule.
    """
    # Unclosed <think> ⇒ malformed: entire output is cognition; no speech.
    if has_unclosed_think(raw):
        return StageOutput(
            think_blocks=[m.group(1) for m in THINK_RE.finditer(raw)],
            pre_think_raw=raw.strip(),
            tool_calls=[],
            speech="",
            silence=False,
            malformed=True,
        )

    think_blocks = [m.group(1) for m in THINK_RE.finditer(raw)]
    speech_start = find_speech_start(raw)

    # Tool calls live OUTSIDE think blocks (tools inside think are cognition,
    # not action). To enforce: first scrub think contents to "" for tool
    # discovery, then match.
    raw_without_think = THINK_RE.sub("", raw)
    tool_calls: list[ToolCall] = [
        ToolCall(
            name=tm.group(1),
            arguments=_parse_tool_body(tm.group(2)),
            raw_body=tm.group(2),
        )
        for tm in TOOL_RE.finditer(raw_without_think)
    ]

    # pre_think_raw: everything before the LAST </think>, MINUS think contents
    # MINUS any tool blocks that appeared in the cognition region.
    pre_region_with_think = raw[:speech_start]
    pre_clean = TOOL_RE.sub("", THINK_RE.sub("", pre_region_with_think))
    pre_think_raw = pre_clean.strip()

    # speech: from speech_start to end, MINUS any tool blocks.
    speech_region = raw[speech_start:]
    speech_clean = TOOL_RE.sub("", speech_region)
    speech = speech_clean.strip()

    silence = (speech == "") and (not tool_calls)

    return StageOutput(
        think_blocks=think_blocks,
        pre_think_raw=pre_think_raw,
        tool_calls=tool_calls,
        speech=speech,
        silence=silence,
        malformed=False,
    )


class StageParser:
    """Streaming-aware STAGE parser.

    Call `push(token)` for each token as it arrives from the LLM SSE stream.
    Call `finalize()` after the stream closes to get the parsed channels.

    Day 3 ships the buffered implementation: all tokens accumulate; parsing
    happens once at finalize. This is correct for mid-token tag splits and
    multi-block outputs. Day 5 may add per-token speech-channel emission for
    live display (requires speech-start tracking; not needed for correctness).
    """

    def __init__(self) -> None:
        self._buf: list[str] = []

    def push(self, token: str) -> None:
        """Accumulate one token's worth of raw LLM output."""
        self._buf.append(token)

    @property
    def raw(self) -> str:
        """Current accumulated raw output (read-only convenience)."""
        return "".join(self._buf)

    def finalize(self) -> StageOutput:
        """Parse the accumulated buffer and return the StageOutput."""
        return parse_stage(self.raw)
