"""astra.grammar — STAGE protocol parser + leak detection.

Implements spec v0.128 §4.3 Master Contract STAGE channels (Surface 4):
- THINK / TOOL / SPEECH-as-default + SILENCE
- v0.128 corrected strip rule: SPEECH is text AFTER the LAST `</think>` close,
  not just text outside `<think>...</think>` tags. This handles Qwen 3.6's
  reasoning-model nested-thinking pattern where outer raw deliberation
  appears BEFORE the formal `<think>` block.

Day 3 lands:
- parser.py:        StageParser, StageOutput, ToolCall, parse_stage
- strip_rules.py:   canonical regexes + find_speech_start / has_unclosed_think
- leak_detector.py: LeakDetector, LeakEvent, LeakPattern + canon loaders
- canon/:           wall_clock_patterns.txt + astra_substrate_patterns.txt
"""

from astra.grammar.leak_detector import (
    Boundary,
    CompiledLeakDetector,
    LeakDetector,
    LeakEvent,
    LeakPattern,
    Severity,
)
from astra.grammar.parser import StageOutput, StageParser, ToolCall, parse_stage
from astra.grammar.strip_rules import (
    THINK_CLOSE_RE,
    THINK_OPEN_RE,
    THINK_RE,
    TOOL_RE,
    count_think_open_close,
    find_speech_start,
    has_unclosed_think,
)

__all__ = [
    "THINK_CLOSE_RE",
    "THINK_OPEN_RE",
    "THINK_RE",
    "TOOL_RE",
    "Boundary",
    "CompiledLeakDetector",
    "LeakDetector",
    "LeakEvent",
    "LeakPattern",
    "Severity",
    "StageOutput",
    "StageParser",
    "ToolCall",
    "count_think_open_close",
    "find_speech_start",
    "has_unclosed_think",
    "parse_stage",
]
