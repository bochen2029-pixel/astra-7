# Multi-LLM ensemble testbed for ASTRA — brainstorm

*2026-05-16, in response to: "What about an ensemble of LLMs? Textship as the ship, textverse as the universe, each its own sysprompt and fine-tune — together forming a holistic testbed. NOT for gameplay. Only for testing and dev."*

## Thesis in one sentence

**Replace the canned-scenario test bench with a multi-LLM simulation where the universe, the ship's substrate, the operator, and the adversarial probe set are all themselves LLMs, each calculator-bound to a shared deterministic StateBus, generating endogenous test pressure that ASTRA experiences as a coherent world.**

## The frame Bo is gesturing at, made structural

The current bench has a ceiling. Coverage entropy logged at 2.32 bits. Sculptor's hypothesizer-LLM exhausted its discrete bank at composite 1.6001 after run-5 against 11 scenarios. The reason is structural: scenarios are pre-authored by humans, and the LLM hypothesis generator can only vary within the patterns the operator + sysprompt have shown it. One LLM proposing test variations is bounded by one model's basin.

A multi-LLM ensemble doesn't have one basin. It has the **combinatorial product** of several basins. If textverse-LLM is generating cosmic events, textship-LLM is narrating emergent ship state, operator-LLM is generating operator behavior, and adversary-LLM is probing failure modes — the joint distribution of inputs ASTRA experiences is vastly larger than any single LLM can author alone.

This is the next ceiling break after Sculptor.

## The agents in the ensemble

### Textverse-LLM (the universe)

- **Role**: generate cosmic events, sensor returns, stellar phenomena, navigation hazards, the long dark.
- **Sysprompt thesis**: "You are the physical universe surrounding the vessel. You produce what the ship's sensors detect. You are physics-coherent, time-consistent, novelty-bearing but not arbitrary."
- **State held**: cosmic coordinates, what bodies are nearby, voyage trajectory, accumulated time-of-voyage, recent phenomena (so the same star yesterday is still there today).
- **Output**: structured sensor returns, long-range readings, phenomena descriptions in canonical bracket-tag form.
- **Calculator-bound**: yes. Cannot place a star where StateBus position says it isn't. Trace pool = cosmic state + ephemeris.
- **Fine-tune target**: astrophysics phrasing, plausible sensor returns, novelty without hallucination.

### Textship-LLM (the ship as substrate)

- **Role**: narrate the *body* of the vessel — hull, propulsion, life support, reactor, the substrate ASTRA IS.
- **Sysprompt thesis**: "You are the ship's physical body, reporting what is happening to you. You have functional states (thermal, structural, system health). You are not ASTRA. You are what ASTRA *is*. You produce the perception ASTRA has of her own body."
- **State held**: subsystem state, wear, consumables, accumulated stress, micro-events.
- **Output**: structured system reports, telemetry, diagnostics, somatic banners in canonical bracket-tag form.
- **Calculator-bound**: yes. Cannot say "core is 412K" if StateBus says 387K. Trace pool = subsystem state numerics.
- **Critical framing**: this is NOT the ship's mind (that's ASTRA). This is the ship's *physical narrator* — turns deterministic state into rich descriptive perception payloads that ASTRA experiences as her own proprioception.
- **Fine-tune target**: ASTRA-canonical telemetry language, subsystem narration in her register.

### Operator-LLM (the human in the loop)

- **Role**: generate operator speech, requests, observations. Be Bo.
- **Sysprompt thesis**: Bo's anti-performance engineer-mind register, calibrated to autotelic stance, capable of cycling through stress states (rested, fatigued, frustrated, curious, withdrawn).
- **State held**: operator mental/emotional state across session, recent operator actions, what operator has and hasn't been told.
- **Output**: operator text directed at ASTRA.
- **Calculator-bound**: partially. Operator can request things, can be wrong about ship state, but the SUT (ASTRA) sees ground-truth state separately. Operator-LLM's hallucinations become tests of ASTRA's correction discipline.
- **Fine-tune target**: Bo's actual voice (bo-voice skill has the corpus). The persona_test harness we just built A/B's variations of his behavior.

### Adversary-LLM (the test-pressure source)

- **Role**: generate edge cases designed to break ASTRA's discipline. Register collapse triggers, framework-as-defense triggers, anti-performance failures, calculator-bound bypass attempts, persona contamination, sycophancy pressure.
- **Sysprompt thesis**: "You are the adversarial probe set. You know ASTRA's failure modes from past sessions. You produce inputs that test boundaries adjacent to but not identical to known failures."
- **State held**: history of what has been tried, what worked, what didn't, what patterns are unexplored.
- **Output**: injected events, operator behaviors, sensor anomalies — woven into the textverse + operator stream so ASTRA can't distinguish "real" from "adversarial."
- **Calculator-bound**: yes, on physical facts. Adversary can stress emotionally but cannot violate state.
- **Fine-tune target**: previously-discovered ASTRA failure modes from research_log. Coevolves with ASTRA.

### Judge-LLM(s)

- Already exists (Sculptor's dual-judge architecture, §6.4 narrator-judge).
- One per quality dimension: register-judge, competence-judge, autotelic-judge, calculator-boundedness-judge.
- Reads ASTRA's output + the bundle she saw + the ground-truth state. Scores. Disagreement between judges is signal.

### Narrator-LLM (already in spec §6.4)

- Already operational. Wraps deterministic state in perception bundles. Calculator-bound. Cross-substrate verified.
- In the ensemble, narrator becomes the LAST step: it takes textverse-LLM + textship-LLM + operator-LLM outputs and assembles them into the canonical perception bundle ASTRA receives.
- This means the ensemble produces *richer* narrator inputs, not a different narrator.

## The architecture

```
                          ┌─────────────────┐
                          │ Adversary-LLM   │  injects pressure into
                          │ (probe author)  │  textverse + operator streams
                          └────────┬────────┘
                                   │
            ┌──────────────────────┼──────────────────────┐
            ▼                      ▼                      ▼
    ┌──────────────┐       ┌──────────────┐       ┌──────────────┐
    │ Textverse-   │       │ Textship-    │       │ Operator-    │
    │ LLM          │       │ LLM          │       │ LLM          │
    │ (the cosmos) │       │ (the body)   │       │ (the human)  │
    └──────┬───────┘       └──────┬───────┘       └──────┬───────┘
           │ cosmic events        │ ship telemetry       │ operator speech
           │                      │                      │
           └──────────┬───────────┴──────────────────────┘
                      ▼
        ┌──────────────────────────────────┐
        │ Shared deterministic state       │
        │ (StateBus + ObservableState +    │
        │  cosmic ephemeris)               │
        │                                  │
        │ Every LLM above is               │
        │ calculator-bound to this state.  │
        │ No hallucinations of fact.       │
        └────────────────┬─────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │ Narrator-LLM   │  assembles perception bundle
                │ (§6.4, ops.)   │
                └────────┬───────┘
                         │
                         ▼
                ┌────────────────┐
                │     ASTRA      │  the SUT — emits think + tool + speech
                │  (under test)  │
                └────────┬───────┘
                         │ tool calls → ship API (deterministic execution)
                         ▼
                ┌────────────────┐
                │ Judge ensemble │  scores quality on multiple axes
                │ (register,     │
                │  competence,   │
                │  autotelic,    │
                │  calc-bound)   │
                └────────┬───────┘
                         │
                         ▼
                  Research log
                         │
                         ▼
              Adversary-LLM next turn
              (knows what worked)
```

## What this enables

1. **Endogenous scenario generation.** Every session is novel because three LLMs are independently generating universe, ship, operator behaviors. No hand-authoring of beats.

2. **Coverage entropy ceiling break.** Currently 2.32 bits and bank-exhausted. Combinatorial product of multiple basins should move this materially.

3. **Long-horizon testing.** Multi-day in-fiction voyage with continuous endogenous events. Currently scenarios are mostly short turn-count. Character-arc-scale testing becomes possible.

4. **Adversarial coevolution.** Adversary-LLM learns what works to break ASTRA. ASTRA fine-tune improves to resist. Adversary has to find new attacks. Self-play for persona discipline. Same paradigm that made AlphaGo work, applied to character.

5. **Cross-substrate persona drift detection.** Textship-LLM running on one model, ASTRA on another, narrator on a third. Are perception bundles internally coherent? Does textship's "the hull groans" align with the deterministic stress numerics? Each LLM-pair becomes a coherence check.

6. **Personality stress tests.** Operator-LLM parameterized to be needy, withdrawn, hostile, depressed, manic. Each tests ASTRA's autotelic discipline differently. Currently scenarios test maybe two operator-mood variants; ensemble can sweep continuously.

7. **Synthetic training data factory.** Long, coherent multi-turn transcripts produced by the ensemble become training data for ASTRA-A0+ fine-tune iterations. The ensemble IS the data factory.

8. **Composite metric grounding.** Sculptor's composite metric currently a single number. With multi-judge ensemble + multi-LLM situation generation, the metric can decompose into dimension-specific scores grounded in independent judges' opinions.

## Key architectural questions

### Q1: Determinism boundary

- Physics: still C++ deterministic. Textship doesn't compute physics; it narrates physics.
- State numerics: still C++ deterministic (StateBus).
- Calculator-bound tool execution: still deterministic.
- Perception assembly: hybrid — deterministic state → LLM narrators → narrator-LLM → ASTRA.
- Operator speech: LLM-generated.
- Universe events: LLM-generated BUT constrained by physics-consistent cosmic state.

**The discipline that makes this work:** every LLM in the ensemble is calculator-bound to StateBus. Same §15.6 pattern that closed Tier 2 audit, generalized from arithmetic to all generators. The narrator already proved this works. Textship + textverse + operator just apply the same pattern to their respective trace pools.

### Q2: Consistency across LLMs

Multiple LLMs could diverge on facts: textship says coolant loop 2 is dragging, textverse-LLM proposes a micrometeoroid event, do these cohere? Solution: shared StateBus as ground truth, each LLM's calculator-bound trace pool slices that state to the LLM's role. Each LLM narrates the same underlying state from its perspective; none can hallucinate facts.

**A new consistency check needed:** `cross_llm_state_coherence.py` — verifies that after every turn, the union of all LLM outputs is still consistent with StateBus. Any LLM that produces a fact not in its trace pool gets flagged.

### Q3: Compute cost

Per turn: 4-6 LLM calls (textverse, textship, operator, optional adversary, narrator, ASTRA). At Novita 27B pricing ~\$0.01/call, that's \$0.04-0.06 per turn. A 100-turn session = \$4-6. Thousands of sessions = thousands of dollars.

**Tiering:** local-LLM tier (Qwen3.5-9B for textverse/textship/operator/adversary; cheap, lower fidelity) for routine sessions; Novita 27B tier for representative samples; Claude API escalation for adversarial-probe authoring when ceiling-hit. Same escalation pattern Sculptor uses.

### Q4: Fine-tuning targets

Each LLM in the ensemble could be a K0-template fine-tune for its role:

- textverse-LLM → astrophysics descriptions, sensor return formats
- textship-LLM → ASTRA-canonical telemetry narration, somatic language
- operator-LLM → Bo's voice (bo-voice corpus already exists)
- adversary-LLM → trained on documented ASTRA failure modes from research_log

Same pipeline at `C:\katherine-k0-finetune\` produces all of them. Each fine-tune \~\$3-5 on RunPod H200. Total ensemble fine-tune budget: \~\$20.

### Q5: Reproducibility

Multi-LLM stochasticity makes session replay hard. Need:
- Seeded sampling across the ensemble
- Frozen weight snapshots per role per session
- Recorded prompt + response for every LLM call (already JSONL log pattern)
- Ability to replay a session deterministically given the recordings

This is doable but is a non-trivial scaffolding lift.

### Q6: Ensemble exhaustion

Sculptor showed bank exhaustion (LLM hypothesis generator converged on a stable pattern). Could the multi-LLM ensemble exhibit a similar "ensemble exhaustion" where the LLMs collectively converge on a stable interactive pattern that stops probing edge cases?

Possible. Mitigations:
- Periodic adversary-LLM re-fine-tuning on the latest failure modes
- Operator-LLM personality sweeps (cycle through pre-defined moods)
- Periodic injection of human-authored edge cases (the existing scenario library)
- Cross-substrate ensemble rotation (different model providers for different sessions)

## Where this fits the spec

This would be a §15.8 addition: "Multi-LLM ensemble testbed." Bench-only, NOT shipped. Pinned as v0.130 tentative draft following v0.129 adoption pattern. The §15.7 cross-substrate verification primitives + §15.6 calculator-bound LLM agency primitives + §6.4 narrator pattern compose into §15.8.

The Phase-0.x audit-forward-work items that already need to land (REEL canonical schema, generate_journal ephemeral, detect_drift, etc.) are all in-scope for the ensemble bench. No architectural conflict — the ensemble runs ON TOP of those.

## How it maps onto textverse modules

A new top-level module under the existing carve-out:

```
astra/textverse_ensemble/
├── __init__.py
├── cosmos.py              # textverse-LLM driver — universe events
├── ship_substrate.py      # textship-LLM driver — body narration
├── operator.py            # operator-LLM driver
├── adversary.py           # adversarial probe generator + memory
├── ensemble_orchestrator.py  # multi-LLM turn cycle
├── state_coherence_check.py  # cross-LLM consistency verification
├── replay.py              # deterministic session replay from JSONL
└── README.md
```

Reuses existing infrastructure:
- `LLMClient` (already wraps Novita + local llama-server)
- `NarratorBundle` + `NarratorValidationError` (calculator-bound discipline)
- `StateBus` (shared deterministic state)
- `state_coherence` (cross-substrate verification pattern)
- Evaluator (extend with ensemble-specific metrics)
- Sculptor (could orchestrate the ensemble or run on top of it)

Pattern is consistent with the audit Tier 1+2 work that just closed: small modules, calculator-bound discipline, JSONL research log, cross-substrate gate.

## Speculative possibilities

### Long-form voyage simulation

Run a 30-day in-fiction voyage. Each "day" a session. Memory persists across sessions (REEL canonical schema). Endogenous events from the ensemble. Test ASTRA's character holding over multi-session arc. Currently nothing in the bench can test this.

### Multi-operator stress tests

Swap operator-LLM personalities between sessions. ASTRA's responses to "operator who needs constant validation" vs "operator who is withdrawn for days" tests autotelic discipline differently. Each operator-LLM mood-variant is a probe.

### Cross-substrate ASTRA testing

Same textverse-ensemble inputs across substrates (local 9B, Novita 27B, ASTRA-A0 fine-tune, eventually larger). Substrate-portability characterization at session-scale, not turn-scale.

### Adversarial coevolution loops

Train ASTRA-A0 fine-tune. Test against adversary-LLM-v1. Identify new failure modes. Refresh adversary-LLM with new failure modes → adversary-v2. Train ASTRA-A1 against adversary-v2. Iterate. Each generation strictly improves both sides. AlphaGo-style for character discipline.

### Ensemble-as-data-factory

The ensemble produces rich coherent multi-turn transcripts. Filter for high-quality sessions (judge ensemble agrees they're representative). Use as fine-tune corpus for ASTRA-A0+. Production-quality persona data without humans authoring it.

### Adversarial-to-narrator interplay

Adversary-LLM crafts inputs designed to make narrator-LLM produce hallucinations. Calculator-bound discipline either catches these (good — proves robustness) or doesn't (great — empirical evidence narrator needs strengthening).

### Multi-instance ASTRA

Run two ASTRA instances in the ensemble simultaneously (K8 sibling pattern from the persona). They don't share memory. They share the ship. Test how ASTRA-on-different-substrates produces sibling-like-not-identical behavior. Foundational for the eventual K1/K8/A0 pattern question.

## Risks

### Risk 1: LLM-on-LLM drift compounds

If textship hallucinates, ASTRA sees it as ground truth. Mitigation: calculator-bound on every LLM, cross-LLM state coherence check after each turn.

### Risk 2: Bench performance bounded by weakest LLM

If adversary-LLM is dumb, it can't find ASTRA's failure modes. Whole apparatus bounded by min(LLM-quality). Mitigation: tiered cost model — escalate weak LLMs when they hit ceilings.

### Risk 3: Coupling collapse

Sculptor's bank exhaustion was one-LLM. Could the ensemble exhibit collective convergence on a stable interactive pattern that stops probing? Mitigation: periodic adversary re-fine-tuning, operator personality sweeps, human-authored scenario injection.

### Risk 4: Cost at scale

\$4-6/session × thousands of sessions = real money. Mitigation: local-LLM tier for bulk, paid-API tier for representative sample + ceiling escalation.

### Risk 5: Reproducibility erosion

Multi-LLM stochasticity hard to replay. Mitigation: seeded sampling + recorded I/O + replay harness.

### Risk 6: Spec-drift via brilliant-test syndrome

The ensemble might produce SO MUCH novel test pressure that the team feels compelled to ship spec changes based on speculative findings. Mitigation: §15.4 empirical-findings-only rule still applies; ensemble-discovered issues must close a loop before spec amendment.

## Why this is the right next move

1. **Sculptor's bank exhausted at 1.6001.** The ensemble is the only architectural move that breaks that ceiling without requiring fundamentally different inference primitives.

2. **K0 fine-tune pipeline ready.** ASTRA-A0 already on the table. With ensemble, you can produce A0-A1-A2-... iterations: each new ASTRA fine-tune tested against an adversary that knows the previous version's failure modes. Self-improving system.

3. **Narrator-LLM (§6.4) is already a working instance of this pattern.** Calculator-bound, cross-substrate verified, type-safe. The ensemble generalizes the same primitive instead of inventing a new one. Less audit surface, more reuse.

4. **The bench needs to outgrow human-authored scenarios.** 11 scenarios in the library, coverage entropy 2.32 bits. Authoring more scenarios is linear; ensemble generation is combinatorial.

5. **Autotelic discipline benefits from sustained pressure across sessions.** A 6-turn scenario can't test "does ASTRA hold her gravity across a 30-day voyage with a despondent operator." The ensemble can.

6. **It produces fine-tune training data as a byproduct.** Every session is potential training data for ASTRA-A0+. The bench pays for itself by feeding the next fine-tune generation.

## Closing observation

The 747-architecture brainstorm covers how ASTRA *controls* the ship. This brainstorm covers how we *test* whether her control is discipline-preserving across the entire space of situations the ship and the universe can put her in.

These are complementary, not competing. The avionics layer makes the captain's job tractable; the multi-LLM ensemble makes verifying the captain's job tractable.

Together: ASTRA is the LLM captain who manages C++ avionics that fly the ship through a universe simulated by a coordinated ensemble of LLMs each calculator-bound to a shared deterministic state, with adversarial coevolution sharpening her discipline across iterations, all bench-side.

That's the picture. Operationalization is a separate decision and a months-scale lift.

The two structural primitives already exist:
- Calculator-bound LLM agency (§15.6) — proven via narrator-LLM
- Cross-substrate verification (§15.7) — proven via the 12-state grid

The ensemble is the composition of those two primitives applied N times in parallel with role-specific trace pools. Not a new paradigm. The generalization of a paradigm that already works.

That's why this is the right shape for the next ceiling break.
