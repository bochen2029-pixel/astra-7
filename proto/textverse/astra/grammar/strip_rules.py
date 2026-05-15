"""Strip rules — v0.128 corrected SPEECH determination per §4.3 + §15.7.

The v0.128 strip rule: **SPEECH is text emitted AFTER the LAST `</think>`
close tag, outside any `<tool>` block.** Everything before the last
`</think>` is cognition, regardless of whether it's inside explicit think
tags.

This is the architectural fix for the Qwen 3.6 27B nested-thinking pattern
discovered on 2026-05-14: reasoning models emit outer raw deliberation
BEFORE their formal `<think>` block. v0.127's strip rule ("text outside
`<think>...</think>` tags") would let that outer deliberation leak into
SPEECH and through to the operator-facing TTS — Dave-frame collapse.

The corrected rule captures the outer deliberation in `pre_think_raw`
(available to the drift detector for analysis) and emits it to no
operator-facing channel.

This module exposes the regex constants and the speech-start finder.
The full parser logic lives in `parser.py` and references this module's
constants directly so tests can verify strip mechanics independently.
"""

from __future__ import annotations

import re

# Canonical tag regexes. DOTALL so `.` matches newlines (think blocks span
# multiple lines). IGNORECASE so loose-form `<THINK>` from some models still
# matches — defense-in-depth.
THINK_RE: re.Pattern[str] = re.compile(
    r"<think>(.*?)</think>",
    re.DOTALL | re.IGNORECASE,
)

THINK_OPEN_RE: re.Pattern[str] = re.compile(r"<think>", re.IGNORECASE)
THINK_CLOSE_RE: re.Pattern[str] = re.compile(r"</think>", re.IGNORECASE)

# Tool block: `<tool name="op_name" ...>body</tool>`. Name attribute can use
# single or double quotes; body can be JSON or loose-form text (adapter LLM
# normalizes to validated JSON downstream).
TOOL_RE: re.Pattern[str] = re.compile(
    r"""<tool\s+name=["']([^"']+)["'][^>]*>(.*?)</tool>""",
    re.DOTALL | re.IGNORECASE,
)


def find_speech_start(raw: str) -> int:
    """Return the index in `raw` immediately after the LAST `</think>` close.

    If `raw` contains no closed `<think>` block, returns 0 (speech starts at
    the beginning). This is the speech-channel boundary marker.

    Per v0.128 §4.3 strip rule: text BEFORE this index is cognition; text
    AFTER this index (outside `<tool>` blocks) is SPEECH.
    """
    last_close = list(THINK_CLOSE_RE.finditer(raw))
    if not last_close:
        return 0
    return last_close[-1].end()


def count_think_open_close(raw: str) -> tuple[int, int]:
    """Return (opens, closes) count of think tags in raw.

    Used to detect malformed output (unclosed `<think>` at stream end).
    """
    opens = len(THINK_OPEN_RE.findall(raw))
    closes = len(THINK_CLOSE_RE.findall(raw))
    return opens, closes


def has_unclosed_think(raw: str) -> bool:
    """True iff `raw` contains more `<think>` opens than `</think>` closes.

    Indicates malformed output — stream truncation, or model emitted an
    open tag without ever closing it. The parser treats this as cognition
    in full and emits NO speech.
    """
    opens, closes = count_think_open_close(raw)
    return opens > closes
