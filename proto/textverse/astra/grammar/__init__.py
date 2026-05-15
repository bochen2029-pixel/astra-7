"""astra.grammar — STAGE protocol parser + leak detection.

Implements spec v0.128 §4.3 Master Contract STAGE channels (Surface 4):
- THINK / TOOL / SPEECH-as-default + SILENCE
- v0.128 corrected strip rule: speech is text AFTER the LAST </think> close,
  not just text outside <think>...</think>. This handles Qwen 3.6's
  reasoning-model nested-thinking pattern (the outer raw deliberation that
  appears BEFORE the formal <think> block must also be stripped).

Files:
- parser.py:        Streaming-aware XML-tag parser
- strip_rules.py:   The corrected strip-before-last-</think> rule
- emitter.py:       Constructs perception bundles (input direction)
- leak_detector.py: Wall-clock + technical-substrate leak patterns
                    (loads tests/wall_clock_patterns.txt + astra_substrate_patterns.txt)
- tag_set.py:       Canonical tag names + ordering rules

Implementation: Day 3.
"""
