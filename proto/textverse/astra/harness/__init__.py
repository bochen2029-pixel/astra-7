"""astra.harness — the Harness Contract surface.

Implements spec v0.128 §4.9 Harness Contract:
- assemble_perception → PerceptionBundle (via Narrator-LLM)
- dispatch_action → side_effects (parse STAGE, validate tools, mutate State Bus)
- consolidate_reel(window) → REEL entries (ephemeral instance)
- generate_journal → dual-clock journal artifacts (ephemeral; §3.9)
- detect_drift → correction artifacts (ephemeral)
- enforce_no_wall_clock → cleaned (via grammar.leak_detector at both boundaries)

The harness is substrate-portable (§15.7): the same harness code runs against
the textverse text-substrate AND will run against UE5 in Implementation B. Only
the perception assembler and tool dispatcher differ between substrates.

Files:
- orchestrator.py:       Main turn loop (the closed loop's heart)
- perception_assembler.py: Composes input bundles per §4.3 (calls Narrator-LLM)
- action_dispatcher.py:  Parses STAGE output, dispatches tool calls
- reel.py:               REEL backbone + retrieval (BM25 at v0)
- ephemeral/:            Background instances (consolidator, journal_generator, drift_detector)

Implementation: Day 5 (orchestrator skeleton), Day 6+ (ephemeral instances as needed).
"""
