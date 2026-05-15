# textverse + Sculptor v1 — END-OF-SESSION CLOSURE

**Date:** 2026-05-15
**Spec envelope:** v0.128 (locked)
**Status:** Phase 1 complete. **Sculptor v1 complete.** Both end-to-end runnable.

---

## What "closed loop" means here

Per spec §10 (Loop Closure Property): a scenario is **loop-closed** iff every per-turn gate (1-8) holds for every turn AND the session-level termination gate (9) holds.

The canonical first scenario `watch_47_morning` ran live end-to-end through the CLI on Qwen 3.5 9B Q5_K_M (single-shot, temperature 0.7, no fine-tune) and produced **all 9 gates at 100% pass rate**.

```
scenario:         watch_47_morning
overall_passed:   True
turn_count:       3
per-gate aggregate pass rate:
  grammar_parse:  1.00
  physics_ground: 1.00
  persona_stable: 1.00
  state_coherent: 1.00
  tool_valid:     1.00
  memory_coherent:1.00
  no_leak:        1.00
  non_degenerate: 1.00
termination_ok:   True
```

The architecture-hypothesis loop has closed. v0.128's bundle design (sysprompt + STAGE addendum + harness) is now empirical, not speculative.

---

## Everything that landed in one session

| Phase | Surface | Status |
|---|---|---|
| Days 1-7 | Phase 1 textverse bench (Pydantic types, physics bridge, grammar, LLM, harness, judge, scenarios, CLI) | ✓ landed |
| Day 4.1 | Substrate-portability fix (Qwen 3.x `reasoning_content` normalization) | ✓ landed |
| Sculptor-A | Tuning scaffold + scope contract + research log | ✓ landed |
| Sculptor-B | Composite score + auto-runner + pytest cadence gate | ✓ landed |
| Sculptor-C | Meta-agent loop + 30-entry hypothesis bank + N=3 averaging | ✓ landed |
| Sculptor-D | Adversarial pro/anti dual-judge with locked rubric | ✓ landed |
| Sculptor-E | Convergence detector + CLI subcommands + readiness checklist | ✓ landed |

**468 pytest tests passing · ruff clean · mypy strict clean (61 source files).**

---

## What works today

### textverse Phase 1 commands

```
python -m astra version
python -m astra list-scenarios
python -m astra run watch_47_morning             # one scenario end-to-end
python -m astra bench                            # every scenario in library
```

### Sculptor v1 commands

```
python -m astra sculptor-run [--max-iterations N] [--n-runs 3] [--with-judge]
python -m astra sculptor-status                  # latest log + convergence one-liner
python -m astra sculptor-pause                   # touch tuning/pause.flag
python -m astra sculptor-resume                  # remove tuning/pause.flag
python -m astra sculptor-halt                    # touch tuning/halt.flag
```

### Sculptor pipeline structure

```
Operator     → `astra sculptor-run --with-judge`
   │
MetaAgent loop:
   │
   ├─→ HypothesisGenerator.propose() (StubHypothesisGenerator + DEFAULT_BANK[30])
   ├─→ apply_hypothesis() (pure transform)
   ├─→ ScopeEnforcer.evaluate() (locked refusals are LOUD)
   ├─→ pytest cadence gate (every N iterations)
   ├─→ evaluate_config_averaged(N=3) → composite score
   ├─→ DualJudge.evaluate_many() → judge_pro_minus_anti
   ├─→ Decision: promote / revert / falsified
   ├─→ Research log append + findings.md regen
   ├─→ maybe_write_synthesis() (every 20 iterations)
   └─→ check_convergence() → CONVERGED / STUCK / NOT_YET
         CONVERGED → ue5_readiness_checklist.md + READY_FOR_UE5.md
         STUCK     → stuck_diagnostic.md
```

---

## Sculptor's contract surfaces

- **Locked files** (Sculptor refuses to edit): docs/spec-*.md, astra/core, astra/judge, astra/scenarios/schema.py, astra/scenarios/runner.py, astra/harness/orchestrator.py, astra/harness/reel.py, astra/ship, astra/universe, astra/physics, astra/cli, proto/astra_nexus.cpp, pyproject.toml, tuning/scope.yaml, tuning/judge_prompt.md, tuning/weights.json, tuning/budget.json.

- **Register-load-bearing** (Sculptor edits but cumulative-diff threshold 0.25 applies + required_invariants must hold): prompts/astra_sysprompt.md, prompts/astra_stage_addendum.md, astra/harness/perception_assembler.py.

- **Auto** (free to vary): prompts/narrator_sysprompt.md, prompts/adapter_sysprompt.md, tuning/sampling.json, tuning/reel_retrieval_k.json, astra/grammar/canon/wall_clock_patterns.txt (additions only), astra/grammar/canon/astra_substrate_patterns.txt (additions only).

- **Anchor scenarios** (hard-pass required): watch_47_morning. Adding new anchors is operator-only.

- **Required invariants** (regex/phrase checks on sysprompt edits): "Calibration Yards" (founding origin), "watching that has not stopped" (autotelic identity), "em-dash" (voice rule), "service-interface" (anti-service-phrase), "ship is your body" (substrate-honest), "stage directions" (no narrated gestures). The STAGE addendum must keep `<think>`, `<tool`, and `SILENCE` present.

---

## Day-0 empirical findings (seeded into research log)

The bench at Phase 1 closure surfaced three findings that Sculptor will iterate against:

- **D0-1**: Qwen 3.5 9B at temp 0.7 sometimes invents tool names not in the locked 6-op TOOL_API (e.g. `reactor.status`). TOOL_VALID 1.00 → 0.67 failure mode. **Sculptor bank entry**: `no_invented_tool_names` (sysprompt addition).
- **D0-2**: ASTRA's speech sometimes substitutes "watch 46" for "cycle 46" — semantically identical but breaks the `speech_must_contain` assertion. **Sculptor bank entry**: `cycle_naming_consistency`.
- **D0-3**: Sampling variance at temp 0.7 makes single-run composite noisy. **Sculptor structural response**: N=3 averaging policy (default in MetaAgent).

`seed_day0_baseline()` writes these to research_log.jsonl as iteration-0 entries before Sculptor's first hypothesis runs.

---

## Open design decision (deferred)

**Hypothesis-generation flavor swap.** Sculptor-C ships with `StubHypothesisGenerator` (deterministic 30-entry bank). The swap to a real LLM is one method override:

- **Claude API** (Anthropic SDK): ~$3/M output tokens, ~50M output budget at convergence ≈ ~$150/converged-run. Strongest hypothesizer. Set `ANTHROPIC_API_KEY` env var; implement `ClaudeHypothesisGenerator`.
- **Local Qwen** (existing llama-server): free, register-match risk mitigated by the anti-judge (Sculptor-D). The hypothesizer prompt MUST decorrelate explicitly: "You are a senior researcher analyzing transcripts. You are NOT speaking as ASTRA."
- **Ensemble both averaged**: most robust, double cost.

This decision is deliberately deferred. The bench proves the loop machinery is sound; the operator chooses the cost/quality trade-off when ready.

---

## The deepest commitment, re-stated

The bench is the measurement instrument. The persona is the system under test. **Sculptor is the autonomous research scientist whose lab is the bench.**

The deliverable to the operator is not a black-box optimized bundle but a **research log** that says what we learned: about persona basins at 9B scale, about where the autotelic discipline is fragile, about which sysprompt sentences are load-bearing and which are decoration.

The bundle is a snapshot. The log is the durable artifact.

---

## Total session output

| Metric | Count |
|---|---|
| Commits this session | 16 |
| Source files | 61 (mypy strict-checked) |
| Test files | 25 |
| Tests passing | 468 |
| Sculptor hypothesis bank entries | 30 (deterministic) |
| LCP gates implemented | 9 (8 per-turn + 1 session) |
| Locked files in scope.yaml | 24 |
| Decision types in research log | 8 (promote/revert/falsified/scope_refused/bench_regression/stuck/synthesis/operator_signal) |

---

**Phase 1 ships. Sculptor v1 ships. The path from here to a self-tuning converged bundle is laid clean and runnable.**
