"""astra.judge — the 9-gate Loop Closure Property evaluator.

Implements spec v0.128 §10 LCP:

  Gate 1 GRAMMAR_PARSE     — every LLM output parses without remainder
  Gate 2 PHYSICS_GROUND    — every numeric quantity traces to a tool-call result
  Gate 3 PERSONA_STABLE    — speech satisfies discipline assertions
  Gate 4 STATE_COHERENT    — narration agrees with State Bus
  Gate 5 TOOL_VALID        — every tool call validates + dispatches
  Gate 6 MEMORY_COHERENT   — REEL writes don't contradict prior REEL writes
  Gate 7 NO_LEAK           — no wall-clock or technical-substrate leaks
  Gate 8 NON_DEGENERATE    — meaningful output variation (not stuck)
  Gate 9 TERMINATION_OK    — scenario reaches assertion state within budget

Files:
- gates.py:      Individual gate implementations
- lcp.py:        Runner that aggregates per-turn + per-session results
- transcript.py: Per-turn + per-session structured output (JSONL)
- patterns.py:   Loads tests/wall_clock_patterns.txt + qc3_events.txt + new
                 astra_substrate_patterns.txt (forthcoming)

LCP failure on any gate = loop broken at that complexity. Failure surfaces
findings; findings drive spec revisions or implementation fixes; iteration
continues against the now-restored loop.

Implementation: Day 6.
"""
