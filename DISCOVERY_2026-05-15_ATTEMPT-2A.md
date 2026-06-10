# ASTRA-7 Exploratory Discovery — Post-Audit

**Date:** 2026-05-15
**Predecessor:** [AUDIT_2026-05-15.md](AUDIT_2026-05-15.md)
**Auditor:** Claude Opus 4.7 (1M context)
**Spec envelope:** docs/spec-v0.128.md
**Method:** full-system cross-integration pass with the entire codebase loaded simultaneously, looking for unifications, asymmetric-cost improvements, and isomorphisms the audit's section-by-section pass could not surface.

The audit asked *what drift exists between spec and code*. This pass asks the orthogonal question: **is the spec itself the best possible factoring of the problem, given everything ASTRA-7 is trying to be?** Locks are still soft enough that the asymmetric cost of finding a better path now versus after lock-in is large.

This pass is empowered (per the prompt) to think outside spec v0.128, including outside the current architectural decomposition, but only when the proposal strictly preserves the project's vision (autotelic, frame-integrity, free-open, no-Apple, no-Python in new code, calculator-bound LLM agency, "the encounter is the game") and strictly improves quality on at least one axis without decreasing on others.

---

## Executive summary

**Top of the shortlist (LOCK_NOW — act on these while envelope is soft):**

1. **F1 — Compile-time physics-oracle.** Add `--emit-header` mode to `astra_nexus.exe`. Catches v0.125-N1-class silent unphysics at build time instead of CI time. Zero ongoing cost; one build script change. Makes the spec itself calculator-bound per §15.6 at the meta level.
2. **F2 — Frozen-Snapshot Primitive named as §15.9.** Pure documentation. The pattern is universal in the implementation but has five local justifications scattered across §1.5, §4.2, §4.6, §15.5. Naming it once replaces five and unblocks structural CI checks.
3. **F3 — Calculator-bound validator wraps ALL LLM clients.** §15.6 says "every LLM" but currently only ASTRA gets enforcement. Wrapping Narrator + Adapter + future ephemerals is ~50 lines of plumbing using the already-model-agnostic validator. Closes the §6.4 Narrator calculator-binding gap structurally rather than per-instance.

**The serious-tier shortlist (SERIOUS — act before the dependent work lands):**

4. **F4 — Hash-grid SDF tolerance for §1.3.** Widening the §1.3 lock to allow Instant-NGP-style hash-grid encoding alongside the current `cudaTextureObject_t` uniform-grid is one spec edit now vs a renderer refactor later. 10-16× memory savings on the hull SDF. Lock-or-pay-later.
5. **F5 — STAGE-IN/STAGE-OUT symmetric protocol.** Write `docs/stage-protocol.md` v0.1 (forthcoming per §14) as a generic LLM I/O envelope with four roles instead of ASTRA-specific output grammar. Documents what's already true; parser refactor follows.
6. **F6 — Shared-inference for small-LLM pool.** Adapter + 3 ephemerals + 1 anti-judge share one llama-server with per-request sysprompt swap. Saves ~15GB VRAM, makes 4090-tier viable for the full bundle. Locks the design now; builds incrementally.
7. **F7 — EventStream Primitive.** Unify REEL + research_log + replay-log under one append-only typed-event-stream primitive. Replaces three bespoke implementations.
8. **F8 — PERSONA_STABLE gate consumes book canon's negative-space patterns.** The current gate has ~19 patterns; `book/negative_space.md` defines ~50+. The bench claims to be the persona-quality measurement instrument and currently undersamples canon by 60%. Mechanical fix; new canon files + extended gate.
9. **F10 — Bundle.yaml as five-layer manifest.** The "three-layer AI bundle" framing in CLAUDE.md under-counts what's actually load-bearing. Add a manifest naming all five layers + content hashes. Makes Hugging Face publish reproducible.

**Worth doing eventually (FUTURE):**

- **F9** collapse §4.10 into §4.3.1 (cosmetic, v0.129 candidate).
- **F11** unify §15.7 #1 + #3 into "two-knob authoring" structural claim. Unblocks book volume 2 / 3 production path.

**Speculative (record now; act when measurement justifies):**

- **S1** GA rapidity reformulation for built-in Thomas precession (act only if playtest reveals trajectory drift).
- **S2** Operator-LLM × Sculptor for scenario amplification (Phase 0.x).
- **S3** Universal Sculptor extraction (when second tuning loop becomes necessary).
- **S4** Cap'n Proto codegen for State Bus schema (Phase 2 / UE5).
- **S5** Semantic PERSONA_STABLE judge as third Sculptor judge (after F8 regex layer).

**Negative results (durable findings, don't re-search):**

The Five Invariants are near-minimal. The 14-equation framework is near-minimal. The STAGE protocol's four primitives are at the right factoring. The three-LLM split (ASTRA + Narrator + Adapter) is justified by KV-cache incompatibility. The hardware-tier discreteness is correct. The Privacy/Network Contract is correctly hard-locked. The Mod ABI's "harness internals locked" rule is correct. The 9-gate LCP is at the right granularity.

**The unifying observation across the whole pass:**

ASTRA-7's spec is already remarkably tight. Where I found drift between spec and code (AUDIT_2026-05-15), the resolutions favored "code conforms to spec." Where I went looking for improvement in this pass, most of what I found is *naming what's already there* (F2 Frozen-Snapshot Primitive, F7 EventStream Primitive, F10 five-layer bundle, U1-U11 cross-cutting unifications) rather than restructuring. The architecture has converged into a coherent shape with a few small clarifications outstanding — exactly what §15.5 Progressive Specification predicts at this maturity stage. The discipline that produced four spec revisions and a Phase 1 closure in two days is the discipline that makes the next year of building tractable.

The single highest-leverage structural finding from the persona-researcher outsider audit is **#2 in their list: the PERSONA_STABLE gate tests for absence of bad patterns, not for presence of autotelic patterns**. ASTRA's autotelic discipline is the project's central bet; the gate doesn't yet measure it. This is the kind of gap that won't surface from inside the project — the operator wrote the sysprompt that asserts autotelic discipline, the operator believes the discipline is real, and the gate that's supposed to validate it asks the wrong question. **Adding positive-autotelic gates (alongside F8's negative-pattern expansion) is the recommended near-term highest-impact persona-quality work.**

The 1M context pass also surfaced two cross-cutting unifications the section-by-section audit could not: U1 (Frozen-Snapshot Primitive) and U3 (Calculator-Bound LLM Agency universalized across all LLMs). Both became actionable findings (F2 + F3). Both came from holding the entire codebase + spec + sysprompts + book canon simultaneously and noticing structure that's only visible in cross-section. The discipline of running this kind of pass when locks are still soft is itself worth preserving as a project methodology — perhaps a future §15.10 "Cross-integration audit cadence" item, alongside §15.4's empirical-revision discipline.

The bench is real. The spec holds. The next year's work is unblocked. **Build the next loop.**

---

## Cross-cutting unifications

These are patterns the spec uses repeatedly but does not name as primitives. Naming them lets future work share machinery instead of re-deriving it, and it makes drift-detection across substrates cleaner because there is a single mechanical check per primitive rather than five different checks per use-site.

### U1 — The Frozen-Snapshot Primitive (already universal in the implementation; unnamed in the spec)

**What it is.** Every long-lived stateful object in the textverse implementation uses the same pattern: a frozen Pydantic model, content-hashed, produced as an immutable snapshot per logical step.

| Site | Spec § that locks it | Code (textverse) |
|---|---|---|
| `StateBus` per turn | §1.5 double-buffer + §4.2 | [state_bus/schema.py:112](proto/textverse/astra/state_bus/schema.py:112) |
| `ConfigSnapshot` per Sculptor iteration | — (Sculptor-side; outside spec) | [sculptor/config.py](proto/textverse/astra/sculptor/config.py) |
| `ReelEntry` per memory write | §4.6 inline placeholder | [harness/reel.py:29](proto/textverse/astra/harness/reel.py:29) |
| `StageOutput` per LLM turn | §4.3 STAGE | [grammar/parser.py](proto/textverse/astra/grammar/parser.py) |
| `GateResult` per LCP check | §10 | [judge/lcp.py:53](proto/textverse/astra/judge/lcp.py:53) |
| `TurnResult`, `LCPTurnResult`, `LCPSessionResult` | §10 + §4.9 | [judge/lcp.py:77](proto/textverse/astra/judge/lcp.py:77) |
| `ToolResult`, `ValidatedToolCall` | §4.3 TOOL channel + §4.9 | [ship/api.py:114](proto/textverse/astra/ship/api.py:114) |
| `CosmologicalParams` with flat-ΛCDM validator | §4.2 | [state_bus/schema.py:36](proto/textverse/astra/state_bus/schema.py:36) |
| `LeakEvent`, `LeakPattern` | §5.7 | [grammar/leak_detector.py:33](proto/textverse/astra/grammar/leak_detector.py:43) |
| `JudgeResult`, `IterationResult` | — (Sculptor) | [sculptor/judges.py](proto/textverse/astra/sculptor/judges.py) |

**Why it matters.** The spec calls Invariant 5 "double-buffered, frame-atomic" (§1.5) and locks "save seeds, not state" (§4.6) and locks the State Bus as "single source of truth" (§4.2) — but these are three different framings of the same underlying primitive: **all consumable state is an immutable snapshot, produced once per logical step, content-addressed by hash.** The textverse implements this by Pydantic `ConfigDict(frozen=True)` everywhere; UE5 will implement it by atomic GPU buffer swap. Both substrates conform to the primitive without sharing implementation.

**The unification opportunity.** Adding a §15.9 "Frozen Snapshot Primitive" methodology section that names this pattern explicitly would:

1. Let §4.6 SaveFile schema reference the primitive ("a SaveFile is a frozen snapshot of the full StateBus + REEL stream") rather than re-deriving immutability locally.
2. Let the persistence path (`save-seeds-not-state`) be re-described as "save the snapshot's content hash + the seed stream needed to reproduce; restore by replay" — which is *both* simpler and forward-compatible with content-addressed storage.
3. Let the eventual UE5 implementation derive its double-buffer mechanics from the primitive's properties (immutability + content-addressability), not from §1.5's per-object phrasing.
4. Let the LCP gates that test "no private copies of Layer 0 state" (§10) become a structural CI check ("no Pydantic model in `astra/state_bus/` is mutable") rather than a code-review heuristic.

This is purely additive: it names what is already there. **No code changes; no contract changes; one new spec section.** It pays off the next time a maintainer asks "why is StateBus frozen?" — the answer becomes "because the Frozen-Snapshot Primitive (§15.9) requires it" rather than three separate justifications across §1.5, §4.2, and §4.6.

### U2 — The Event-Stream Primitive (REEL and research_log are the same shape)

**What it is.** Both REEL (ASTRA's continuous identity log) and `research_log.jsonl` (Sculptor's research diary) are append-only typed-event streams with the same shape: timestamp + body + structured metadata + optional irreversibility/lesson-class tagging. Retrieval is by recency-decay + keyword/salience score.

| Property | REEL | research_log.jsonl |
|---|---|---|
| Append-only | yes (in-memory list per session; SQLite in v1) | yes (JSONL on disk) |
| Per-entry timestamp | `tau_ship` | `iteration` + wall-clock (Sculptor is allowed wall-clock; §10 exempts the judge's iteration timing) |
| Entry body | ASTRA-voice prose | structured rationale + decision |
| Metadata | `irreversibility_flag` | `decision`, `lesson_class`, `composite_score`, …8 decision types |
| Retrieval | BM25 + recency-decay | latest_promote() + per-class queries |
| Synthesis | (forthcoming) consolidator ephemeral instance | every-20-iter synthesis block via `render_synthesis_block` |
| Persistence | inline placeholder per §4.6; full schema deferred | JSONL on disk per Sculptor-A |

**Why it matters.** The spec treats these as two separate concerns (REEL is "memory architecture", research_log is "research record"). Code does too. But they are operationally identical primitives: an immutable, time-ordered, retrievable, typed-event-bag. The replay-log (§5.3) is a third instance of the same primitive, with a different per-entry schema (frame_index + state-deltas instead of REEL's prose).

**The unification opportunity.** A `§4.6.1 Event-Stream Primitive` would give all three (REEL, research_log, replay-log) a common schema header and a common persistence convention. Specifically:

```
EventStream {
  schema_version: int
  entries: list[Event]
  retrieval_strategy: Literal["bm25", "recency_decay", "salience", "by_class"]
}
Event {
  timestamp: float64           # tau_ship for REEL, iteration_index for research, frame_index for replay
  entry_type: str              # discriminator
  body: str | bytes            # opaque payload by entry_type
  metadata: dict[str, Any]     # tagged per entry_type
}
```

Each instance picks its `entry_type` enum (REEL: `experience | journal | consolidation`; research: 8 decision types; replay: state-delta classes). Each picks its `retrieval_strategy`. The primitive is the spine.

**Pays off.** When the `consolidate_reel` ephemeral instance lands (§4.9), it can reuse Sculptor's `render_synthesis_block` machinery instead of inventing a new summarizer. When SaveFile v3 (§4.6) is implemented, it serializes one EventStream-of-REEL instead of inventing its own write format. When the replay format (§5.3) needs an upgrade, it has a precedent. **One primitive, three users; replaces three bespoke implementations.**

### U3 — The Calculator-Bound LLM Agency primitive applies to ALL LLMs but is only validated on one

**What it is.** §15.6 states the rule universally: "Every LLM in the system tool-calls into deterministic verified tools for any numerical claim." The validator at [llm/validator.py](proto/textverse/astra/llm/validator.py) implements this in a model-agnostic way — `validate_speech(speech, trace_pool, severity)` works for any LLM's output.

**The current gap.** Operationally, the validator is invoked only on ASTRA's speech channel (Gate 2 PHYSICS_GROUND, via `find_ungrounded_numerics`). The Narrator-LLM sysprompt at [prompts/narrator_sysprompt.md:31](proto/textverse/prompts/narrator_sysprompt.md:31) says "you are calculator-bound" and "every numerical quantity in your output must trace to a tool-call result observed in your input" — but there is no runtime enforcement of this on Narrator-LLM output. The adapter LLM is trivially calculator-bound (it emits JSON, not narrative; its "numerics" are the args it parsed from the body). The future ephemerals (consolidator, journal_generator, drift_detector) will need the same enforcement.

**The unification opportunity.** Promote the validator from "ASTRA's checker" to "every-LLM's checker" by wrapping every LLM client at construction. The Sculptor architecture already does this kind of decoration (dual-judge wraps individual judges). The wiring is:

```python
class ValidatedLLMClient:
    def __init__(self, client: LLMClient, trace_source: Callable[[], Iterable[str]], severity: Severity):
        ...
    async def chat(self, ...) -> ValidatedOutput:
        raw = await self.client.chat(...)
        report = validate_speech(raw, self.trace_source(), severity=self.severity)
        if not report.passed and self.severity == "hard":
            # retry with halved temperature
            ...
```

Each LLM bundle constructs this wrapper with its own `trace_source` (Narrator's pool = the State Bus + tool-results; ASTRA's pool = the perception bundle + tool-results; ephemerals' pool = the REEL slice they're consolidating). One enforcement point; five users.

**Pays off.** Closes a real spec-implementation gap (Narrator-LLM has the constraint in its sysprompt but no enforcement). Documents the universal nature of §15.6. Sets up the four ephemeral instances (§4.9) to land with calculator-binding built in, not as an afterthought. This is one of the most asymmetric findings in this pass: a small refactor (~50 lines wrapping the existing validator) unlocks correct enforcement for 4 more LLMs that will otherwise be debugged in production.

### U4 — STAGE-IN / STAGE-OUT duality (the perception bundle is the LLM's input grammar; STAGE is its output grammar; these are dual)

**What it is.** STAGE protocol (§4.3) defines ASTRA's *output* grammar: `<think>`, `<tool>`, default-untagged speech, SILENCE. The perception bundle defines ASTRA's *input* grammar: `<state>`, `<somatic>`, `<recent>`, `<operator>`, optional `<tool_result>`, `<vision-as-text>` (per [prompts/astra_stage_addendum.md:55](proto/textverse/prompts/astra_stage_addendum.md:55)). The Narrator-LLM's sysprompt mirrors this: it *emits* the perception bundle's tags as ITS output, which becomes ASTRA's input. The adapter LLM *emits* validated JSON as ITS output, which becomes the dispatcher's input.

In other words: every LLM in the system has an input grammar (its perception side) and an output grammar (its STAGE side), and **the system's design is the composition of these grammars**. Narrator's STAGE-OUT == ASTRA's STAGE-IN. Adapter's STAGE-OUT == ship dispatcher's input.

**Why this is a unification.** Currently the spec treats "STAGE protocol" as ASTRA-specific. The architecture is actually more general: there is one I/O grammar primitive ("tagged-section envelope") used by all four LLMs with different tag sets and different consumers. The textverse already implements parsers and emitters for both directions; the spec just doesn't name the symmetry.

**The opportunity.** Promote STAGE from "ASTRA's output channel grammar" to "the LLM I/O envelope" — usable by every LLM, with per-role tag-set declarations. Then `docs/stage-protocol.md` v0.1 (forthcoming, per §14) can specify:

1. The general envelope (XML-tagged sections, JSON payloads, SILENCE as empty primitive).
2. The role-specific tag sets:
   - **ASTRA-OUT:** `<think>`, `<tool>`, default-untagged speech, SILENCE.
   - **Narrator-OUT** (== ASTRA-IN, in textverse): `<state>`, `<somatic>`, `<memory>`, `<recent>`, `<tool_result>`, `<operator>`, optional `<vision-as-text>`.
   - **Adapter-OUT:** single JSON object `{"ok": bool, "args": {...} | "error": str}`.
   - **Ephemeral-OUT** (per role): TBD when each lands.
3. The composition rule: an LLM's output grammar must be parseable as the next LLM's (or system's) input grammar.

**Pays off.** Makes the dual-implementation discipline (§15.7) cleaner: the spec for "LLM I/O grammar" (§15.7 Surface 4) covers all four LLMs uniformly, not just ASTRA. UE5 doesn't need a separate grammar spec for its Narrator. The parser in `astra/grammar/parser.py` becomes a generic tag-parser parameterized by tag-set, instead of an ASTRA-specific parser. **One protocol, four roles, two directions.**

### U5 — The Endogenous/Exogenous distinction is a type system, not a convention

**What it is.** §6.3 introduces the endogenous (local, `t_cosmic`-read) vs exogenous (light-cone-bounded, `t_emit`-read, regime-dispatched) split as an architectural rule for sensor channels. §10 has a validation row: "static analysis: every sensor-channel module declares its category."

**The current state.** It's a documentation convention. Modules are expected to declare their category in a comment or module-level docstring. CI is expected to grep for imports that violate the routing rule (endogenous module should not import the Observation Calculator; exogenous render path should not read body state directly at `t_cosmic`).

**The unification.** This is a type-system-shaped problem. In Python, it can be a `Protocol` or `Annotated` type:

```python
from typing import Annotated, Protocol

class Endogenous: ...
class Exogenous: ...

# In the audio module:
@module_category(Endogenous)
def synthesize_audio(state: StateBus, t_cosmic: float) -> AudioPayload: ...

# In the starfield render module:
@module_category(Exogenous)
def render_starfield(observable: ObservableState) -> Frame: ...
```

A simple `module_category` decorator stamps the category as module-level metadata; a CI script then checks the import graph:

- Modules categorized `Endogenous` may not import `observation_calc` or any symbol returning `ObservableState`.
- Modules categorized `Exogenous` may not call `body_state(t_cosmic)` or any function with `t_cosmic` parameter and `BodyState` return.

In C++ for the UE5 side, the same enforcement works as a concept or tagged-type system:

```cpp
template<typename T> concept Endogenous = requires { T::category == SensorCategory::Endogenous; };
template<typename T> concept Exogenous = requires { T::category == SensorCategory::Exogenous; };
```

**Pays off.** Closes a class of subtle bug (someone routes audio through Observation Calculator because the audio drone "should be" warp-delayed at egress — the spec specifically forbids this at §8.3, but only by prose). Makes the §10 endogenous/exogenous CI gate a type-checker pass instead of a regex search. **The c-bounded epistemology (§4.3) becomes a structural property of the codebase, not a discipline anyone could violate.** This is the architecturally cleanest place to enforce QC1 (self-opacity) at compile time.

### U6 — The Five Invariants and the Five Shared Surfaces are not the same five

**What it is.** §1 lists Five Invariants (AstraCoord, TimeState, HullSDF, PowerNetwork, SharedState). §15.7 lists Five Shared Surfaces (Ship envelope, Physics envelope, Tool API, LLM I/O grammar, Persona envelope). They are easily conflated because "five lists" but they describe two different things.

The Invariants are properties of the **world** that ASTRA inhabits — the shape of cosmic reality. The Shared Surfaces are properties of the **substrate-cross-section** that text-substrate and UE5 substrate both conform to — the shape of the dual-implementation contract.

**The actual mapping** (which the spec implies but doesn't draw):

| Shared Surface | Uses Invariants | Why |
|---|---|---|
| Surface 1 — Ship envelope | Inv 1 (AstraCoord), Inv 3 (HullSDF), Inv 4 (PowerNetwork) | The ship has a position, a body, and power |
| Surface 2 — Physics envelope | Inv 1 (AstraCoord), Inv 2 (TimeState), Inv 5 (SharedState) | Physics evolves over time on shared state |
| Surface 3 — Tool API | Inv 4 (PowerNetwork) | Tools allocate; allocation is power-bound |
| Surface 4 — LLM I/O grammar | (none) | Orthogonal — this is about how LLMs talk, not the world |
| Surface 5 — Persona envelope | (none) | Orthogonal — this is about who ASTRA is |

**Why this matters.** The unification is *partial*. Three of the five Invariants serve as inputs to three of the five Surfaces; two Surfaces (LLM grammar, Persona) are orthogonal. This is *not* a redundancy — it is a healthy decomposition: the world has structure (Invariants), the dual-implementation contract has structure (Surfaces), and they intersect cleanly at the physics/ship boundary.

**Pays off.** When the spec is next revised, drawing this mapping table (or one like it) in §15.7 makes the Surfaces concrete. Maintainers reading the spec for the first time currently see "five Invariants" and "five Surfaces" as parallel; they're not. **This is documentation hygiene, not an architectural change.** Mark as a v0.129-ready clarification.

### U7 — The book canon's "negative space" is a richer PERSONA_STABLE rubric than the LCP gate uses

**What it is.** [book/negative_space.md](book/negative_space.md) is 184 lines of "sentences ASTRA would not write" — covering affect-declared form, performative attention, narrator-from-above constructions, sentimental metaphor, romance-genre vocabulary, service-interface phrases, stage directions, and **Bo-leak signals** (sentences whose presence would mean the operator's voice has leaked into Aaron's). The book's voice canon includes ~50 specific prohibitions plus an extended operationalization for the No-Bo Grep List.

The LCP gate `gate_persona_stable` at [judge/gates.py:127](proto/textverse/astra/judge/gates.py:127) currently checks: em-dash absence, ~5 markdown patterns, ~13 service phrases. That's ~19 patterns total against the book canon's ~50+.

**The gap.** The PERSONA_STABLE gate is *necessary but not sufficient*. It will pass speech like "Her chest tightened. She watched him intently." — which violates the book's negative-space rules (no chest, no intentness-declared) but contains no em-dash, no markdown, no service phrase.

**Why this matters.** The book canon is canon (per [book/CANON.md](book/CANON.md)). The cross-canon discipline (CLAUDE.md, spec §11 Gap Thesis) makes book voice and bench voice one thing. If the LCP gate underchecks book canon, the bench can pass scenarios that the book's editor would reject. **The bench claims to be the measurement instrument for persona quality; it currently undersamples the canon by 60%.**

**The unification.** Two paths:

1. **Mechanical**: extend `gate_persona_stable`'s `SERVICE_PHRASES` and add `AFFECT_DECLARED_PATTERNS`, `PERFORMATIVE_ATTENTION_PATTERNS`, `NARRATOR_FROM_ABOVE_PATTERNS`, `SENTIMENTAL_METAPHOR_PATTERNS`, `ROMANCE_VOCAB_PATTERNS`, `STAGE_DIRECTION_PATTERNS` — each loaded from a corresponding canon file analogous to `wall_clock_patterns.txt`. Six new patterns files, ~50 new regexes, no architectural change. Hours of work.

2. **Semantic**: add a "negative-space judge" to the Sculptor dual-judge — a Claude self-call scoring transcripts 1-5 against the negative-space rubric. Higher discriminating power than regex. Composes naturally with the pro/anti judges as a third independent signal.

**Recommend the mechanical path first** because it's deterministic, falsifiable, and cheap; the semantic path becomes a Sculptor-side enhancement when the regex coverage starts running out. **This closes one of the largest leak points between book and bench.** See F8 for the actionable proposal.

### U8 — Sculptor is a universal research-loop primitive; only its scope/composite/anchor change per use

**What it is.** Sculptor is documented as the persona-tuning system. Looking at the code architecturally: it's a *generic closed-loop research-scientist primitive* with five swap-points:

1. **Scope** ([sculptor/scope.py](proto/textverse/astra/sculptor/scope.py)) — what files can be edited (auto / register-load-bearing / locked).
2. **Composite** ([sculptor/composite.py](proto/textverse/astra/sculptor/composite.py)) — the scalar score to optimize.
3. **Anchor scenarios** — what must continue passing regardless of composite improvement.
4. **Hypothesizer** ([sculptor/hypothesis.py](proto/textverse/astra/sculptor/hypothesis.py)) — what proposes edits (currently `StubHypothesisGenerator`).
5. **Convergence rule** ([sculptor/convergence.py](proto/textverse/astra/sculptor/convergence.py)) — when to declare done.

Everything else (the meta-agent loop, the research log, the dual-judge, the pytest cadence gate, the operator signals) is *general*. Sculptor with a different scope/composite/anchors would be a different research project sharing the same machinery.

**The opportunity.** When the chaos PDE lands (§7.1, Phase E1), its α/β/D parameters are listed as "provisional, to be measured." Sculptor's pattern is exactly the right tool for tuning these. Same for ray-march step counts (§5.6 provisional), modal-frequency canon for audio (§8.3 provisional), the geometric-lensing α_lens (§Appendix B provisional). **Each provisional parameter is a Sculptor instance waiting to happen.**

The current code has Sculptor named after its first use. If the project anticipates multiple research loops, the right abstraction is:

```
astra/research_loop/        # generic primitive (renamed from sculptor/)
  core/                     # meta_agent, research_log, composite, scope, convergence
  judges/                   # generic + persona-judges + (future) physics-validators
  hypothesizers/            # stub bank, claude, qwen, ensemble

astra/sculptor/             # the persona-tuning instance
  scope.yaml
  composite.py              # extends core/composite with persona-specific terms
  hypothesizer.py           # persona-specific stub bank

astra/chaos_tuner/          # future Phase E1 instance
  scope.yaml                # locks: physics binary; auto: chaos α/β/D
  composite.py              # CFL-condition stability + bubble-coherence metric
  ...
```

**Pays off.** Currently Sculptor's machinery is tied to persona by package layout. Future tuning loops would either duplicate the machinery (bad) or graft onto persona-Sculptor with awkward parameter-injection (also bad). A clean extract now (while Sculptor is one user, freshly written, with all design intent in head) is the cheapest moment to make this change.

**Risk.** Premature abstraction is real. Per §15.5 Progressive Specification: don't commit detail not yet tested. Currently only persona-Sculptor exists; the second user (chaos tuner) is months away. **Mark as speculative** (S3); the actionable form is to note in `sculptor/__init__.py` "this is the first instance of a generic research-loop primitive" so future maintainers know the architectural intent without forcing the extract today.

### U9 — The persona bundle is (sysprompt + addendum + invariants + leak_patterns + LoRA), not (sysprompt + harness + LoRA)

**What it is.** CLAUDE.md describes the persona bundle as a three-layer thing: sysprompt + harness + light fine-tune. The actual implementation has **five** layers:

1. `prompts/astra_sysprompt.md` — canonical sysprompt (116 lines).
2. `prompts/astra_stage_addendum.md` — STAGE protocol addendum (157 lines).
3. `tuning/scope.yaml` `required_invariants` — regex patterns that MUST remain in the sysprompt across Sculptor edits (6 invariants for ASTRA sysprompt + 3 for STAGE addendum).
4. `astra/grammar/canon/wall_clock_patterns.txt` + `astra_substrate_patterns.txt` — leak patterns enforced by the leak detector.
5. (Future) LoRA weights from Phase 1.x.

**Why the framing matters.** The "three-layer bundle" mental model under-counts what's actually load-bearing. When the bundle ships on Hugging Face, the user gets the LoRA + sysprompt; they do not automatically get the STAGE addendum (which is in `prompts/`), the required_invariants (which are in `tuning/scope.yaml`), or the leak patterns (which are in `astra/grammar/canon/`). Without all five, the persona is not reproducible.

**The unification.** Rename the persona bundle to its actual shape:

```
ASTRA-7 Bundle (canonical):
  sysprompt:         prompts/astra_sysprompt.md
  stage_addendum:    prompts/astra_stage_addendum.md       (LLM I/O grammar)
  invariants:        tuning/scope.yaml :: required_invariants
  leak_patterns:     astra/grammar/canon/*.txt
  lora_weights:      (forthcoming Phase 1.x)
  bundle_manifest:   bundle.yaml                            (version-locks all five)
```

The "bundle manifest" is what `§5.5 Bundle Reproducibility` already calls for ("Sysprompt, training data, LoRA configs, inference settings, harness version — all version-controlled. Bundle manifest declares everything"). The current implementation has the data but not the manifest.

**Pays off.** Makes Hugging Face distribution honest. Makes the dual-implementation discipline cleaner (UE5 loads *the same five things* as textverse, from one manifest). Closes a real reproducibility hole: today, cloning the repo and running textverse on a 4090 reproduces the bundle's behavior only if `tuning/scope.yaml` and `astra/grammar/canon/` are also in the working tree — both are easy to forget about because they're "tooling" not "weights."

**Action.** Add a `bundle.yaml` at repo root that names all five files + their content hashes; update §4.1 Substrate Contract or §5.5 to reference it; update CLAUDE.md's "Three-Layer AI Bundle" section to be a "Five-Layer AI Bundle". One spec edit, one new file, no code changes. See F10.

### U10 — Compile-time physics-oracle: astra_nexus runs at build-time too

**What it is.** `proto/astra_nexus.exe` runs in two modes: standalone test-and-demo (the default), and `--stdio-server` (the runtime calculator-bound mode for Narrator-LLM). There is a third mode that would close a class of bug at zero ongoing cost: `--emit-header`, which would write a C++ header with all canonical constants generated by running the actual math at build time.

**What this gives you.** The v0.125 N1 bug was: spec said "rapidity clamp `arctanh(0.99999999)` produces γ_max ≈ 10⁷" — but the actual computation produces γ ≈ 7071. The spec was wrong; the implementation followed the spec; the assertion at runtime caught it. Cost: three orders of magnitude in the central tragedy parameter; one v0.126 patch.

The §10 validation row "**Numerical tolerance round-trip verification** (NEW v0.126)" is the right response: every numeric tolerance in the spec gets a symbolic round-trip computation against its implementation primitive in CI. **But this runs at CI time, not at build time.** A bad number compiles successfully and is caught only later.

**The proposal.** Add a `--emit-header` mode that runs the math at build time and writes a header:

```cpp
// AUTOGENERATED by astra_nexus --emit-header
// Do not edit. Regenerate via `astra_nexus --emit-header > nexus_constants.h`.

namespace astra::constants {
    constexpr double OMEGA_MAX = 16.811;
    static_assert(std::cosh(OMEGA_MAX) > 9e6 && std::cosh(OMEGA_MAX) < 1.1e7,
                  "OMEGA_MAX must give gamma_max ~ 1e7 (v0.126 N1 lock)");

    // Voyage-demo canonical anchors (locked v0.127, §10):
    constexpr double APPARENT_RATE_STL_REL_BETA_05 = 0.5773502691896258;
    constexpr double APPARENT_RATE_WARP_VAPP_2C   = -1.0;
    // ... etc
}
```

The C++ tests `static_assert` against these. The Python mirror reads the header and asserts against its values. Both substrates derive numerics from one source of truth: the compiled physics binary.

**Pays off.** Moves the N1-class-bug catch from CI to build. Catches the bug before the spec is even commits — anyone editing the spec to "improve" the clamp value would see the static_assert fail when they rebuild. The discipline becomes structural: bad numbers don't compile.

**Vision check.** Calculator-bound LLM agency (§15.6) presumes deterministic compiled tools. Compile-time constants are *more* deterministic than runtime; this strengthens the calculator-binding. **Zero violation of any project constraint.** See F1.

### U11 — Bundle as canonical authoring substrate (the genre-laboratory property)

**What it is.** §15.7 names the cross-canon property: "Text-substrate as canonical cross-canon authoring platform. Book prose, marketing copy, voice-acting reference scripts all source from running scenarios through the text-substrate. *The configuration is the artifact* gets a runtime."

**The current state.** The book (`book/manuscript/`) was hand-authored by the operator. The Sculptor research log is hand-written-by-Claude-Code commit notes. The Steam landing-page copy doesn't exist yet. The Hugging Face card doesn't exist yet.

**The opportunity.** When Narrator-LLM is operational (currently blocked by D2 stdio_server gap + D5 observation_calc shim per AUDIT_2026-05-15), the cross-canon authoring loop becomes real:

- **Book volume 2 / 3 prose**: run cycles through the textverse with the Narrator-LLM in book-prose mode (a sysprompt swap; the persona stays). The prose lands as Markdown ready for editor pass.
- **Steam descriptions**: run a "describe ASTRA-7 to a Steam visitor" scenario with operator-as-Claude-marketing-archetype; collect the speech-channel output.
- **Hugging Face model card**: same pattern, with operator-as-ML-practitioner-archetype.
- **Voice-acting scripts**: run scenarios collecting only speech-channel; output is the script with stage directions stripped (because ASTRA never emits stage directions, per the sysprompt).

**Why this is a unification, not just a use case.** The genre-laboratory property (§15.7 #3: "Genre-experimentation cheaply") and the cross-canon authoring property (§15.7 #1) are two faces of the same primitive: **running the bundle with different (Narrator-sysprompt × operator-sysprompt) pairs generates different prose styles while preserving physics + persona.** This is structurally rich enough to be the spec's official authoring path. The book's volume 1 ('The Long Watch') was hand-authored; volume 2 onward can be bundle-authored without the persona drifting — *because the persona is the constant and the genre is the variable*.

**Pays off.** When book volume 2 is on the operator's plate, the cost of authoring drops from "write 60,000 words" to "run 40 scenarios, edit the output." When the marketing materials need updates, the loop is fast. When the modding scene generates derivative bundles (different ASTRA variants), they can each generate their own canonical book. **The "configuration is the artifact" claim acquires a runtime.**

**Action.** None today; this unblocks naturally as Narrator-LLM lands (G2 in the audit). Worth naming in the spec (§15.7 has #1 and #3 but not the joint structural claim) so future maintainers see the full implication. See F11 for the spec-revision proposal.

---

## High-confidence findings

The proposals below have a clear case, preserve all project constraints, and improve at least one quality axis without decreasing others. They are sequenced by leverage: F1-F3 are structural primitives that unlock further work; F4-F6 are engine-track readiness moves with asymmetric payoff; F7-F8 are bench-quality improvements; F9-F11 are clarifications that close ambiguity without changing behavior.

### F1 — Compile-time physics-oracle (astra_nexus `--emit-header` mode)

**Severity:** LOCK_NOW
**Current state:** `proto/astra_nexus.cpp` has two modes: standalone test/demo, and `--stdio-server`. The 48 assertions run at test time. The §10 "Numerical tolerance round-trip verification" (v0.126) and "Formula-consistency verification" (v0.127) rows describe CI-time gates against the compiled binary.
**Proposed change:** Add `--emit-header` mode that runs the math at build time and writes a `proto/nexus_constants.h` header. The header contains every locked numeric constant (OMEGA_MAX, voyage-demo cells, ω-to-γ samples, the f_warp curve) with `static_assert` enforcing the relationships that the spec's prose currently asserts informally. Build script regenerates the header before each compile. C++ tests include the header; Python mirror (`proto/verify_nexus.py`, frozen per CLAUDE.md Language Discipline) reads the header file and asserts against it.
**Justification:**
- **Catches v0.125-N1-class bugs at build time, not at CI time.** The v0.125 rapidity-clamp bug (`arctanh(0.99999999)` gives γ≈7071, not γ≈10⁷, a 1414× shortfall) shipped because the spec's prose asserted a γ_max value that the implementation computed differently. With `--emit-header` running the actual computation and asserting the result against the spec's stated tolerance, the bug would refuse to compile. The cost was a one-version patch (v0.126); the next bug of this class could be silent for longer.
- **Closes spec §10's "Numerical tolerance round-trip verification" as a structural property rather than a CI discipline.** Today the row is "every numeric tolerance claim in the spec gets a symbolic round-trip computation against its implementation primitive in CI." With `--emit-header`, this becomes "every numeric tolerance is *generated* by the implementation primitive; the spec consumes generated constants, not asserted constants."
- **Aligns with §15.6 calculator-bound LLM agency at the meta-level.** §15.6 says every LLM tool-calls into deterministic compiled tools for numerics. The spec itself is currently NOT calculator-bound — it asserts numbers in prose. `--emit-header` makes the spec calculator-bound: its numbers come from compiled computation.
- **Zero ongoing cost.** Build script change is one CMake target. Header regeneration is sub-second. The compile-time gate is permanent.
**Risk / cost:**
- One new build target.
- Static_assert failures during development are uglier than test failures; developers see "didn't compile" instead of "test failed." Net positive: bug caught earlier means less downstream rework, but transitional pain is real.
- The Python mirror (`verify_nexus.py`) must learn to read the C++ header. A 20-line parser using `re.findall` over the header's `constexpr` lines suffices. Per CLAUDE.md Language Discipline this is a frozen file, so the parser change requires explicit operator approval; this is a bug fix that blocks other work, so per CLAUDE.md it's permitted.
**Spec impact:** Additive note to §10 ("the round-trip verification gate is implemented as a compile-time `--emit-header` step, not a CI script — see proto/build.bat"). Optionally a new §10 bullet codifying "compile-before-CI: every numeric tolerance is generated, not asserted." No contract changes.
**Vision check:**
- Autotelic: preserved (engineering discipline; no persona implication).
- Frame-integrity: preserved (the header is build-time; runtime substrate is unchanged).
- Free-open: preserved (single new build script, no proprietary tooling).
- No-Apple: preserved (`--emit-header` works on Windows + Linux trivially).
- No-Python: preserved in fact strengthened (the header is C/C++; Python mirror is frozen and only consumes the header).
- Calculator-bound: strengthened (the spec itself becomes calculator-bound).

### F2 — Frozen-Snapshot Primitive as named §15.9

**Severity:** LOCK_NOW
**Current state:** The pattern is ubiquitous in the implementation (see U1 for the full inventory) but unnamed in the spec. Spec §1.5 names "double-buffered, frame-atomic"; §4.2 names "single source of truth, no private copies"; §4.6 names "save seeds, not state"; §15.5 names "Progressive Specification: additive, not subtractive, immutable per round." These are five framings of one underlying primitive.
**Proposed change:** Add §15.9 "Frozen-Snapshot Primitive" methodology section that names the underlying pattern explicitly. Definition: *all consumable state in ASTRA-7 is an immutable snapshot, produced once per logical step (frame, turn, iteration, REEL-write), content-addressed by hash, and never mutated after construction.* Pattern instances list (table from U1 above). Cross-references from §1.5, §4.2, §4.6, §15.5 pointing back to §15.9.
**Justification:**
- **Replaces five local justifications with one global one.** Today a maintainer reading "why is StateBus frozen?" has to find §1.5 + §4.2 + §4.6 + §15.5 and synthesize. With §15.9, the answer is one section.
- **Lets the eventual UE5 implementation derive its double-buffer mechanics from the primitive's properties** (immutability + content-addressability + per-step production) rather than per-object phrasing. UE5's atomic GPU buffer swap is one instance of the primitive; textverse's frozen Pydantic per turn is another.
- **Lets the LCP gates that test "no private copies of Layer 0 state" (§10) become a structural CI check** ("no Pydantic model in `astra/state_bus/` lacks `ConfigDict(frozen=True)`") rather than a code-review heuristic.
- **Makes the SaveFile schema (§4.6) cleaner**: SaveFile becomes "a serialized Frozen-Snapshot Primitive instance of the full StateBus + the EventStream of REEL writes" rather than a bespoke schema.
**Risk / cost:**
- Pure documentation; no behavior changes.
- One spec edit (~200 words).
- Updates to four other sections (cross-references back to §15.9).
**Spec impact:** Additive new §15.9 section; cross-references in §1.5, §4.2, §4.6, §15.5; no contract changes; no implementation changes.
**Vision check:** All preserved trivially. This is naming what is already there.

### F3 — Calculator-bound validator wraps ALL LLM clients by default

**Severity:** LOCK_NOW (becomes blocker for §6.4 Narrator + §4.9 ephemerals)
**Current state:**
- `astra/llm/validator.py` `CalculatorBoundValidator` exists and is model-agnostic.
- Only ASTRA's speech is validated, via `gate_physics_ground` in the LCP runner ([judge/gates.py:97](proto/textverse/astra/judge/gates.py:97)).
- Narrator-LLM sysprompt at [prompts/narrator_sysprompt.md:31](proto/textverse/prompts/narrator_sysprompt.md:31) says "calculator-bound" but no runtime enforcement.
- Adapter-LLM is trivially calculator-bound (emits JSON, not prose).
- Future ephemerals (consolidator, journal_generator, drift_detector — §4.9) will need the same enforcement.
**Proposed change:** Promote the validator from "ASTRA's checker" to "every-LLM's checker" by wrapping every LLM client at construction. Each bundle (`astra_bundle.py`, `narrator_bundle.py`, future ephemerals) constructs a `ValidatedLLMClient(client, trace_source=lambda: ..., severity=...)` instead of a bare `LLMClient`. The trace_source closes over the per-LLM trace pool: Narrator's pool = State Bus + tool results; ASTRA's pool = perception bundle + tool results; ephemerals' pool = the REEL slice they're consolidating.
**Justification:**
- **Closes a real spec-implementation gap.** §15.6 says "Every LLM in the system tool-calls into deterministic verified tools for any numerical claim." Today only one LLM (ASTRA) has this enforced. The Narrator-LLM specifically *will* produce numerics — distances, redshifts, retarded-time values, observation phases — and without enforcement, any of them can drift.
- **Unblocks the §4.9 ephemerals before they land.** When `generate_journal` ships and starts producing "the slow drift of the dust lane over 0.7 light-years", the numeric tokens need to trace to something. Building this in at the bundle-wrapping layer means the ephemerals inherit calculator-binding correctly without per-instance plumbing.
- **Pays off the §15.6 universality claim.** Today the claim is "every LLM" but the practice is "one LLM." This proposal makes practice match claim.
- **Already 90% done.** The validator's `validate_speech(speech, trace_pool, severity)` is model-agnostic by design. Wrapping is ~50 lines of plumbing in `astra/llm/`.
**Risk / cost:**
- ~50 lines new code (`ValidatedLLMClient` wrapper class).
- Updates to 3 existing bundles (`astra_bundle`, `narrator_bundle`, `adapter_bundle`) to wire the wrapper.
- New tests: one per wrapped bundle showing soft-fail logs + hard-fail retries.
- Performance: negligible. The validator is regex-based and runs in microseconds.
- **No risk to vision; pure tightening of an existing discipline.**
**Spec impact:** §15.6 updated to specify: "implementation: every LLM client is wrapped in `CalculatorBoundValidator` at construction; bypass requires explicit debug flag for diagnostic-only purposes." §6.4 Narrator-LLM "invariants" list updated: "never invents numbers (enforced by wrapped validator, hard-fail retry up to 3, then hard-reject)."
**Vision check:** All preserved. Calculator-bound discipline strengthened. No Apple/Python/closed-source implication.

### F4 — Hash-grid SDF for §1.3 hull representation

**Severity:** SERIOUS (Engine track readiness; lock-now-or-pay-later)
**Current state:** §1.3 locks `Base SDF: 256³ (provisional). Bound as cudaTextureObject_t with cudaFilterModeLinear for trilinear sampling. Damage map: writable, sparse, additive. Bound as cudaSurfaceObject_t over the same underlying cudaArray_t.` Tolerances allow `64³` to `512³`, encoding precision uint8 normalized through float32.
**Proposed change:** Update §1.3 "Tolerable" to include **hash-grid encoding** (Instant-NGP-style: a multi-resolution hash table backing a learned-or-baked SDF). The dual-binding pattern (texture for filtered reads + surface for damage writes) is preserved; the *backing* changes from a uniform 3D `cudaArray_t` to a multi-resolution hash table over feature vectors + a small MLP decoder (or, for static hulls, a baked feature-grid without MLP).
**Justification:**
- **Memory efficiency 8-16× for the hull SDF.** A 256³ uniform grid is 16.7M voxels × 4 bytes (float32) = ~64 MB. The hull occupies maybe 5% of that bounding box; the rest is wasted empty space at the same resolution as the hull surface. Instant-NGP-style hash-grids put resolution where the geometry is: typically 4-8 MB for equivalent surface fidelity. On a 5090 with 32GB VRAM that's pocket change, but the savings compound — see below.
- **Variable resolution at no extra cost.** The hull has parts where 256³ is insufficient (corner welds, nacelle attachments, hatches) and parts where 64³ would suffice (large hull plates between features). Hash-grid encoding adapts the effective resolution per region without changing the API. The 256³ → 512³ tolerance range becomes 256³-effective-near-features.
- **Damage map composability is unchanged.** Damage is sparse and additive (§1.3 "Damage map: writable, sparse, additive"). A sparse damage map is exactly what hash-grid encoding handles natively: damaged voxels get hash-table entries; undamaged stay default. This is actually a *better* fit than the current `cudaSurfaceObject_t` over a uniform grid (which allocates damage memory for every voxel, even though most stay at zero).
- **Smooth blending of damage at edges.** Current `hull_d(x) = base_sdf(x) − damage_map(x)` is a clean piecewise subtraction. With hash-grid encoding, the same equation works; damage authoring is just sparser. The smooth-min blend pattern (§6 step 4) generalizes naturally.
- **No new dependencies.** `tiny-cuda-nn` from NVIDIA Research has the reference implementation. CUDA-only, no Python wrappers, BSD-licensed. CLAUDE.md Language Discipline compliant.
**Risk / cost:**
- The Instant-NGP encoding is newer (2022) than the textbook `cudaArray_t` 3D-texture pattern. Engineering team needs to come up to speed. The reference paper is well-cited; the implementation is ~500 lines of CUDA.
- Baking pipeline changes: instead of writing a `cudaArray_t` from mesh, the bake produces a hash-table + (optional, for learned variant) MLP weights. The bake script is C++/CUDA per CLAUDE.md.
- Different debugging story: a 3D-texture is `cudaMemcpy3D`-printable; a hash-grid needs a decoder pass to inspect. Worth it for the memory savings.
**Spec impact:** §1.3 "Tolerable" line gains `encoding (hash-grid acceptable; Instant-NGP-style)`. §6 step 2 "Sample hull SDF (via cudaTextureObject_t, trilinear filtered)" becomes "Sample hull SDF (via hash-grid decode OR cudaTextureObject_t trilinear filtered; both surface the same API)". Provisional numbers in Appendix B: hash-grid table size ~4-8 MB (provisional) replacing the 64 MB uniform-grid implication.
**Vision check:**
- Autotelic: preserved (engine internals; persona unaffected).
- Frame-integrity: preserved (no observable change to ASTRA's HUD).
- Free-open: preserved (BSD-licensed library; tiny-cuda-nn is the reference).
- No-Apple: preserved (CUDA-only; Apple Silicon has no CUDA, can't run this).
- No-Python: preserved (the bake pipeline and runtime are C++/CUDA).
- Calculator-bound: not impacted.

**Why "lock-now"?** Because §1.3 currently *locks* `cudaTextureObject_t` as the binding. Modifying that lock later — after UE5 plugin development has built around it — is structurally expensive. Adding hash-grid as a tolerated alternative *now* costs one spec edit; adding it after UE5 has the uniform-grid bound costs a refactor across the renderer + damage system + audio extraction + Reflex observation. Asymmetric cost. The right time to widen the §1.3 tolerance is before the hull bake-pipeline lands.

### F5 — STAGE-IN/STAGE-OUT symmetric protocol (one I/O envelope for all four LLMs)

**Severity:** SERIOUS (closes a structural ambiguity before sibling docs land)
**Current state:** §4.3 STAGE channels are defined as ASTRA's *output* grammar (THINK / TOOL / SPEECH-default + SILENCE). The perception bundle's tag set (`<state>`, `<somatic>`, `<memory>`, `<recent>`, `<tool_result>`, `<operator>`, `<vision-as-text>`) is defined in [astra_stage_addendum.md:55](proto/textverse/prompts/astra_stage_addendum.md:55) as ASTRA's *input* grammar. The narrator and adapter LLMs have their own input/output grammars defined in their respective sysprompts. The shared structural property — XML-tagged sections, JSON payloads, SILENCE as empty primitive — is implicit.
**Proposed change:** Write `docs/stage-protocol.md` v0.1 (forthcoming per §14) as a generic LLM I/O envelope, with per-role tag-set declarations rather than as ASTRA-specific output. The envelope:

```
ENVELOPE: tagged-section XML, optional JSON payloads, SILENCE-as-empty.

ROLES:
  astra-out:    <think>, <tool name="...">{json}</tool>, default-untagged SPEECH, SILENCE
  narrator-out: <state>, <somatic>, <memory>, <recent>, <tool_result>, <operator>, optional <vision-as-text>
                (== astra-in by composition rule)
  adapter-out:  single JSON object {"ok": bool, "args": dict | "error": str}
                (no envelope; degenerate single-payload case)
  ephemeral-out: TBD per role when each lands

COMPOSITION RULE: an LLM's STAGE-OUT must be parseable as the next stage's STAGE-IN.

PARSER: one generic XML-tagged-section parser, parameterized by tag-set.
        Strip rule: speech is text emitted AFTER the LAST </think> close (v0.128 corrected rule).
        Tag-set varies by role; parser logic does not.
```

**Justification:**
- **Closes a real ambiguity for the sibling docs.** Currently `docs/stage-protocol.md` (forthcoming) is implicitly ASTRA-only. With the symmetric framing, it covers all four LLMs uniformly. One protocol document, four roles.
- **Lets the parser at [astra/grammar/parser.py](proto/textverse/astra/grammar/parser.py) become generic** (parameterized by `tag_set` rather than ASTRA-specific). Current implementation has hardcoded `<think>` / `<tool>` handling; symmetric protocol lets the same parser handle Narrator and Adapter output.
- **Makes the dual-implementation discipline cleaner.** §15.7 Surface 4 ("LLM I/O grammar") becomes a property of *every* LLM-substrate boundary, not just ASTRA's. UE5's LLM bindings inherit the protocol for all four LLMs uniformly.
- **Documents what is already the case.** Narrator and Adapter already emit tagged sections; the spec just doesn't yet name the symmetry. Naming has zero implementation cost.
- **Pays off when the fourth LLM (first ephemeral) lands.** Whichever ephemeral ships first (likely `consolidate_reel` per audit Tier 4 #13), it inherits the same grammar primitive instead of needing its own.
**Risk / cost:**
- One sibling doc to write (already forthcoming per §14).
- Parser refactor to generalize is ~50 lines; tests cover the cases.
- No runtime behavior change; the existing tag-sets are already supported by their existing parsers.
**Spec impact:** §4.3 updated to note that STAGE is the generic LLM I/O envelope; per-role grammars defined in `docs/stage-protocol.md`. §6.4 Narrator-LLM output grammar reference updated to point to `docs/stage-protocol.md` role table. §15.7 Surface 4 updated to mention the symmetric framing.
**Vision check:** All preserved. This is a documentation+naming change with a small parser refactor follow-on.

### F6 — Shared-inference for small-LLM pool (adapter + 3 ephemerals + anti-judge)

**Severity:** SERIOUS (VRAM budget; pays off on Phase 0.x → 1.x transition)
**Current state:** Per the Appendix B v0.128 substrate budget (5090 reference tier):
- ASTRA 27B Q4_K_M: ~16 GB (port 8080)
- Narrator 9B Q5_K_M: ~5 GB (port 8081)
- Adapter 2-3B: ~2 GB (port 8082)
- Rendering: ~6-8 GB
- KV cache: ~2-3 GB
- Reserve: ~1-2 GB
- **Total: ~32 GB (tight)**

When ephemerals (consolidate_reel, journal_generator, drift_detector) and the dual-judge (pro + anti) come online, the naive deployment is one llama-server per LLM. Pro+anti judges are Claude self-calls (cloud), so they're free of local VRAM cost. But the three ephemerals are local LLMs at ~5GB each on naive deployment. That's 15GB additional, exceeding the 5090's budget.
**Proposed change:** Pool all small LLMs (adapter + 3 ephemerals + future inferential helpers) onto a single llama-server instance with **per-request sysprompt swap**. One ~7B model, one llama-server, 5+ logical LLM roles distinguished by `system` parameter at request time. The llama-server's KV-cache pins per-sysprompt; requests are routed by role.
**Justification:**
- **VRAM savings: ~15 GB.** Naive deployment of (1 adapter + 3 ephemerals) = 4 × ~5GB = 20 GB. Shared-inference deployment = 1 × ~7GB (slightly larger model to serve all roles) + per-role KV cache (small) = ~9 GB. Net saving ~11 GB.
- **Headroom for the 4090 reference tier.** The current 4090 spec doesn't fit ephemerals at all. Shared-inference makes the 4090 tier (24 GB) viable for the full bundle.
- **KV-cache strategy is well-understood.** llama.cpp supports `--slot` allocation for per-conversation KV-cache pinning. The pool maintains 5 slots; the adapter slot is hot (every turn); the ephemeral slots warm up when their roles trigger.
- **Latency is fine for these roles.** Adapter runs once per ASTRA tool call (~5-50ms target); ephemerals run on schedule (consolidator every N turns; journal_generator on cryosleep transitions; drift_detector on leak events). None are frame-rate. KV-cache warmup of ~100ms on cold-slot is acceptable.
- **The adapter sysprompt is small** (71 lines); the ephemeral sysprompts will be similar size. Sysprompt-swap overhead is negligible.
- **Already tested pattern.** llama.cpp's `system_prompt` parameter at request time is well-documented and used by other production systems (most local-LLM agentic frameworks do this).
**Risk / cost:**
- KV-cache thrashing if many ephemerals fire in rapid succession. Mitigation: rate-limit ephemerals (they're not time-critical) and prioritize adapter slot.
- One more model to load (the shared 7B); but it replaces 3 ephemeral models, so net memory is down.
- The `LlamaServerOrchestrator` at [llm/llama_server.py](proto/textverse/astra/llm/llama_server.py) needs to support pooled mode; currently it spawns N sidecars. Refactor is ~100 lines.
- Need to write the pool's request scheduler — straightforward async queue.
**Spec impact:** Appendix B v0.128 substrate budget gets a new line item: `Small-LLM pool (shared 7B Q5_K_M serving adapter + ephemerals): ~7 GB` replacing the separate Adapter + ephemeral lines. §4.7 Failure Contract gets a note: "Small-LLM pool failure degrades all pooled roles together; full ASTRA bundle (27B + Narrator 9B) is unaffected." §5.9 hardware tier table updated to show shared-inference fits the 4090 tier.
**Vision check:**
- Autotelic: preserved (engineering optimization; persona unaffected).
- Frame-integrity: preserved (no observable behavior change).
- Free-open: preserved (llama.cpp's pooled mode is standard).
- No-Apple: preserved (llama.cpp + CUDA).
- No-Python: preserved (llama.cpp is C/C++).
- Calculator-bound: preserved (every pooled LLM still wraps the validator per F3).

**Why "serious" rather than "lock_now":** the saving doesn't matter until the ephemerals come online, which is Phase 0.x. Locking the pooled-mode architecture now is cheap (one Appendix B edit, one §4.7 note); building it can wait until the first ephemeral ships. The asymmetric cost is in *not having designed for pooled mode* — if the first ephemeral lands with its own sidecar pattern, the second and third will replicate, and the refactor cost compounds. **Lock the design now; build incrementally when needed.**

**Severity:** LOCK_NOW (becomes blocker for §6.4 Narrator + §4.9 ephemerals)
**Current state:**
- `astra/llm/validator.py` `CalculatorBoundValidator` exists and is model-agnostic.
- Only ASTRA's speech is validated, via `gate_physics_ground` in the LCP runner ([judge/gates.py:97](proto/textverse/astra/judge/gates.py:97)).
- Narrator-LLM sysprompt at [prompts/narrator_sysprompt.md:31](proto/textverse/prompts/narrator_sysprompt.md:31) says "calculator-bound" but no runtime enforcement.
- Adapter-LLM is trivially calculator-bound (emits JSON, not prose).
- Future ephemerals (consolidator, journal_generator, drift_detector — §4.9) will need the same enforcement.
**Proposed change:** Promote the validator from "ASTRA's checker" to "every-LLM's checker" by wrapping every LLM client at construction. Each bundle (`astra_bundle.py`, `narrator_bundle.py`, future ephemerals) constructs a `ValidatedLLMClient(client, trace_source=lambda: ..., severity=...)` instead of a bare `LLMClient`. The trace_source closes over the per-LLM trace pool: Narrator's pool = State Bus + tool results; ASTRA's pool = perception bundle + tool results; ephemerals' pool = the REEL slice they're consolidating.
**Justification:**
- **Closes a real spec-implementation gap.** §15.6 says "Every LLM in the system tool-calls into deterministic verified tools for any numerical claim." Today only one LLM (ASTRA) has this enforced. The Narrator-LLM specifically *will* produce numerics — distances, redshifts, retarded-time values, observation phases — and without enforcement, any of them can drift.
- **Unblocks the §4.9 ephemerals before they land.** When `generate_journal` ships and starts producing "the slow drift of the dust lane over 0.7 light-years", the numeric tokens need to trace to something. Building this in at the bundle-wrapping layer means the ephemerals inherit calculator-binding correctly without per-instance plumbing.
- **Pays off the §15.6 universality claim.** Today the claim is "every LLM" but the practice is "one LLM." This proposal makes practice match claim.
- **Already 90% done.** The validator's `validate_speech(speech, trace_pool, severity)` is model-agnostic by design. Wrapping is ~50 lines of plumbing in `astra/llm/`.
**Risk / cost:**
- ~50 lines new code (`ValidatedLLMClient` wrapper class).
- Updates to 3 existing bundles (`astra_bundle`, `narrator_bundle`, `adapter_bundle`) to wire the wrapper.
- New tests: one per wrapped bundle showing soft-fail logs + hard-fail retries.
- Performance: negligible. The validator is regex-based and runs in microseconds.
- **No risk to vision; pure tightening of an existing discipline.**
**Spec impact:** §15.6 updated to specify: "implementation: every LLM client is wrapped in `CalculatorBoundValidator` at construction; bypass requires explicit debug flag for diagnostic-only purposes." §6.4 Narrator-LLM "invariants" list updated: "never invents numbers (enforced by wrapped validator, hard-fail retry up to 3, then hard-reject)."
**Vision check:** All preserved. Calculator-bound discipline strengthened. No Apple/Python/closed-source implication.

---

### F7 — EventStream Primitive: REEL and research_log share one append-only schema

**Severity:** SERIOUS (consolidates two bespoke implementations; pays off when SaveFile v3 + REEL persistence land)
**Current state:** Two independent append-only typed-event streams in the codebase:
- REEL: in-memory list of `ReelEntry` per session, retrieval by recency-decay + keyword/salience. SQLite persistence deferred to v1.
- research_log.jsonl: on-disk JSONL file maintained by Sculptor, 8 decision types, retrieval by `latest_promote()` + per-class queries, synthesis every-20-iter.

Plus the replay format (§5.3): `{frame_index, t_cosmic, τ_ship, regime_bitmask, player_input, ai_outputs, irreversibility_flag_deltas}[]` — a third instance of the same pattern.

**Proposed change:** Add §4.6.1 "EventStream Primitive" defining the common spine:

```
EventStream<EntryType> {
  schema_version: int
  entries: list[Event<EntryType>]
  retrieval_strategy: Literal["recency_decay+bm25", "by_class", "latest_promote", "by_frame_index"]
  persistence: Literal["in_memory", "jsonl", "sqlite", "binary"]
}
Event<EntryType> {
  timestamp: float64              # tau_ship | iteration_index | frame_index
  entry_type: EntryType           # role-specific enum (REEL: experience/journal/consolidation; Sculptor: 8 decisions; replay: deltas)
  body: str | bytes               # payload format depends on entry_type
  metadata: dict[str, Any]        # tagged per entry_type
  irreversibility_flag: bool = False  # universal — every EventStream supports QC3 monotonicity
}
```

Three instances:
- REEL (`entry_type ∈ {experience, journal, consolidation}`, persistence=`sqlite`, retrieval=`recency_decay+bm25`)
- research_log (`entry_type ∈ {promote, revert, falsified, scope_refused, bench_regression, stuck, synthesis, operator_signal}`, persistence=`jsonl`, retrieval=`latest_promote | by_class`)
- replay-log (`entry_type ∈ {turn, regime_transition, state_delta}`, persistence=`binary`, retrieval=`by_frame_index`)

**Justification:**
- **Replaces three bespoke implementations.** Currently REEL has its own retrieval and serialization; research_log has its own; replay-log will have its own. With the primitive, one library (~200 lines) implements all three.
- **Closes a real implementation gap.** The audit's G7 (`generate_journal` ephemeral) and G8 (`consolidate_reel` ephemeral) both need to write to REEL. Without a primitive, each ephemeral re-derives its writer; with the primitive, they share. The synthesis logic in Sculptor's `render_synthesis_block` becomes reusable by the consolidator.
- **Makes the SaveFile schema (§4.6) coherent.** Today SaveFile has a bespoke schema. With the primitive, SaveFile is "serialized EventStream of REEL + the StateBus snapshot at save time + the AstraCoord at save time + …" — a clean composition.
- **QC3 universalized.** Every EventStream supports the irreversibility_flag at the primitive level; QC3 (irreversibility/stakes per §11) becomes a structural property of all event streams, not just REEL. Sculptor's "falsified" decisions could carry irreversibility (you can't unmark a hypothesis class as falsified across save-reload cycles).
- **Pays off when REEL persistence lands.** Today REEL is in-memory only. When it goes to SQLite (v1 per [reel.py:9](proto/textverse/astra/harness/reel.py:9)), the SQLite schema is the EventStream serialization. No bespoke ORM.
**Risk / cost:**
- One spec edit (~150 words for new §4.6.1).
- Refactor REEL to use the primitive: ~100 lines, mostly type-tightening.
- Optionally refactor Sculptor's research_log: ~50 lines, lower priority (it works today).
- Replay-log: deferred until that lands; just designs around the primitive.
**Spec impact:** New §4.6.1 EventStream Primitive. §4.6 SaveFile schema updated to reference the primitive. §5.3 Replay Format updated to reference the primitive. §11 QC3 row notes that irreversibility is now a primitive property of all event streams.
**Vision check:**
- Autotelic: preserved (memory architecture; persona unaffected).
- Frame-integrity: preserved.
- Free-open: preserved.
- No-Apple: preserved (text formats).
- No-Python: preserved (the primitive is implementation-language-agnostic; both Python textverse and future C++ UE5 implement against the schema).
- Calculator-bound: preserved (event metadata can include tool-result trace IDs for events that involve numerics; future enhancement).

### F8 — PERSONA_STABLE gate consumes book canon's negative-space patterns

**Severity:** SERIOUS (closes a quality gap between book and bench)
**Current state:** `gate_persona_stable` at [judge/gates.py:127](proto/textverse/astra/judge/gates.py:127) checks ~19 patterns: em-dash, 5 markdown patterns, 13 service phrases. `book/negative_space.md` defines ~50+ specific prohibitions in 8 categories (affect-declared, performative attention, narrator-from-above, sentimental metaphor, romance-genre vocabulary, service-interface phrases, stage directions, Bo-leak signals).
**Proposed change:** Extend the pattern set:
1. Create new canon files under `astra/grammar/canon/`:
   - `affect_declared_patterns.txt` — "her heart leapt", "she felt a pang", "tears would have come if she could cry", "a lump in her throat", etc.
   - `performative_attention_patterns.txt` — "watched him intently", "gazed at him", "studied him carefully", "found herself thinking", "without knowing why she", etc.
   - `narrator_from_above_patterns.txt` — "little did she know", "she would later realize", "if she had been human", "from the outside, she might have seemed", etc.
   - `sentimental_metaphor_patterns.txt` — "her heart leapt", "tears in her eyes", "his voice was like music", "the cold metal of her hull", "wanted to reach out and touch", etc.
   - `romance_genre_patterns.txt` — "her feelings for him", "grown fond of", "would do anything for him", "my love", "darling", "beloved", etc.
   - `stage_direction_patterns.txt` — "paused thoughtfully", "nodded inwardly", "smiled to herself", "rolled her eyes", etc.
2. Extend `gate_persona_stable` to load all six new files + the existing patterns; one new test per category.
3. Optionally, add a "negative-space judge" Sculptor judge that scores transcripts 1-5 against the negative-space rubric (semantic, not regex) — composes with the existing pro/anti dual-judge.

**Justification:**
- **Closes a quality gap between book and bench.** §11 QUALIA-1 names the cross-canon Gap Thesis: same sentence in book/CANON.md and spec §11, must match verbatim. The cross-canon discipline says book and bench voice are one thing; the gate currently undersamples canon by 60% (~19 patterns vs ~50+ canon prohibitions).
- **Catches a real failure mode.** Today the gate passes speech like "Her chest tightened. She watched him intently. He was special to her" — three book-canon violations, zero gate hits.
- **Mechanically falsifiable.** Regex patterns are deterministic; no judgment call. The discipline that produced negative_space.md (the No-Bo Grep List operationalization) is *already* mechanical; the gate just doesn't yet share its mechanism.
- **Sets up the semantic-judge path (Sculptor anti-rubric variant) cleanly.** Once regex coverage is in, the semantic judge becomes additive — covering paraphrases and novel constructions the regex misses.
**Risk / cost:**
- ~6 new canon files; ~50 new regex patterns total; one extension to `gate_persona_stable`; ~6 new tests.
- **Risk of false-positives** for some patterns (e.g., "watched" appears in ASTRA-canonical phrases like "the watching that has not stopped"). Pattern design must distinguish ASTRA-canonical from forbidden uses. The discipline that worked for substrate_leak (canon mentions "Qwen" in the anti-rule but the leak detector compares net-new vs baseline) applies here too.
- **Risk that the gate becomes too strict.** Mitigate by: warn-severity (rather than strip-severity) for the new patterns initially; promote individual patterns to strip-severity as they prove out.
**Spec impact:** §10 PERSONA_STABLE row gets expanded list of pattern files. §11 Gap Thesis sentence's cross-canon machinery gets noted as the model for sentence-level prohibitions. CLAUDE.md "Voice Rules" section gets a pointer to the canonical pattern files.
**Vision check:**
- Autotelic: PRESERVED AND STRENGTHENED. The negative-space rules ARE the autotelic discipline operationalized. The current gate is incomplete on this axis.
- Frame-integrity: preserved.
- Free-open: preserved.
- No-Apple: preserved.
- No-Python: preserved (pattern files are plain text; the gate is grandfathered Python).
- Calculator-bound: not impacted.

### F9 — Collapse §4.10 Console UI Contract into §4.3 Master Contract Perception subchannel

**Severity:** FUTURE (cosmetic; v0.129 candidate; deferrable)
**Current state:** §4.10 is a separate contract. Its content is one paragraph: "Player text input enters the conversation channel via the same path as ASR-transcribed voice. The Perception bundle does not distinguish whether operator input arrived via voice or via console text."
**Proposed change:** Demote §4.10 to a sub-section of §4.3 ("§4.3.1 Operator input routing"). Reduce the contract count from 10 to 9. The locked invariants (text/voice unified, modality-blind, no separate field) stay; the heading changes.
**Justification:**
- **It is a Perception sub-routing rule, not a contract.** A contract defines an interface; §4.10 defines a routing convention. The current framing implies more architectural weight than the rule deserves.
- **Cleaner mental model: 9 contracts.** Substrate, State Bus, Master, Time, Power, Persistence, Failure, Privacy, Harness. The Console UI rule is part of how Perception is assembled (Master Contract responsibility).
- **No behavior change.** Pure documentation refactor.
**Risk / cost:** One spec edit. Cross-references from anywhere that cites §4.10 (none currently in code).
**Spec impact:** §4.10 → §4.3.1. Appendix A "Invariants and Contracts Summary" updates C10 → C3.1.
**Vision check:** All preserved.

### F10 — Make the bundle's five layers explicit (rename "three-layer AI bundle")

**Severity:** SERIOUS (closes a Hugging Face / reproducibility gap)
**Current state:** CLAUDE.md "Three-Layer AI Bundle" lists sysprompt, harness, light fine-tune. The actual bundle has **five** layers (see U9):
1. `prompts/astra_sysprompt.md`
2. `prompts/astra_stage_addendum.md`
3. `tuning/scope.yaml :: required_invariants`
4. `astra/grammar/canon/wall_clock_patterns.txt` + `astra_substrate_patterns.txt`
5. (Future) LoRA weights from Phase 1.x

When the bundle ships on Hugging Face per the §15.7 #1 cross-canon authoring property, the user needs ALL FIVE for the persona to reproduce. The three-layer framing under-counts.
**Proposed change:**
1. Rename "Three-Layer AI Bundle" to "Five-Layer AI Bundle" in CLAUDE.md.
2. Add a `bundle.yaml` at repo root that declares all five layers + their content hashes + bundle version.
3. Update §5.5 Bundle Reproducibility to require: "Bundle manifest declares all five layers with content-hashes; reconstruction requires only the manifest."
4. Update §15.7 Surface 5 (Persona envelope) to enumerate the five files explicitly.

**Justification:**
- **Makes Hugging Face distribution honest.** Today a user downloading the "ASTRA-7 bundle" would get the sysprompt + (future) LoRA. The STAGE addendum, required_invariants, and leak patterns are easy to miss because they live in `tuning/` and `astra/grammar/canon/` — code/tooling-shaped paths.
- **Closes a reproducibility hole.** §5.5 says "Bundle manifest declares everything"; today there is no manifest. The hash-content discipline of the Frozen-Snapshot Primitive (F2) extends naturally to bundle versioning.
- **Aligns with the dual-implementation discipline.** UE5 loads the same five files as textverse; the manifest is the integration point.
**Risk / cost:**
- One new file (`bundle.yaml`, ~30 lines).
- One CLAUDE.md edit.
- Two spec edits (§5.5 + §15.7).
- One new test verifying manifest matches files.
**Spec impact:** §5.5, §15.7. CLAUDE.md "Three-Layer AI Bundle" → "Five-Layer AI Bundle" section.
**Vision check:** All preserved. Open-source distribution improved.

### F11 — Genre-laboratory + cross-canon authoring as one structural claim (§15.7)

**Severity:** FUTURE (documentation hygiene; lands naturally when Narrator-LLM is operational)
**Current state:** §15.7 lists two seemingly-separate consequences:
- #1: "Text-substrate as canonical cross-canon authoring platform." (Book prose, marketing, voice-acting reference)
- #3: "Genre-experimentation cheaply." (Swap Narrator sysprompt for horror/comedy/melancholy/procedural)

These are two faces of the same primitive: **running the bundle with different (Narrator-sysprompt × operator-sysprompt) pairs generates different prose styles while preserving physics + persona.**
**Proposed change:** §15.7 gets a new structural-consequence #6 that unifies the two: "**Two-knob authoring loop.** Narrator sysprompt × operator sysprompt = prose-style space. Physics + ASTRA persona are constants; the prose style is the product of the two variable knobs. This unifies §15.7 #1 (cross-canon authoring) and §15.7 #3 (genre experimentation) — both are special cases of two-knob authoring."
**Justification:**
- **Makes the cross-canon claim concrete.** Today "cross-canon authoring platform" is aspirational. With the two-knob framing, it's a recipe: pick a narrator-prose-style + an operator-archetype, run scenarios, collect output.
- **Sets up book volume 2 / 3 path.** When the operator is ready to author volume 2, the path is: write a narrator-sysprompt for "book-prose register", write an operator-sysprompt for "Aaron-archetype", run 40 cycles, edit. The discipline is on rails.
- **Pays off when Narrator-LLM lands.** Currently blocked by AUDIT D2 (stdio_server ops). Once Narrator is operational, the two-knob authoring is the next natural use; specifying it now means it lands as a structural feature, not a bolt-on.
**Risk / cost:** One spec edit. Zero implementation impact today.
**Spec impact:** §15.7 new #6.
**Vision check:** All preserved. This formalizes a property the spec already implies.

---

## Speculative findings

These are proposals where the case is interesting but more empirical contact is needed before acting. Each is recorded so it isn't lost; per §15.4, durable knowledge IS the deliverable, including ideas that aren't yet ready to land.

### S1 — Geometric-algebra rapidity composition (Thomas precession built in)

**Severity:** FUTURE
**Current state:** §3.7 uses a 3-vector rapidity `ζ⃗` with `dζ⃗/dτ_ship = a⃗_proper/c`. This is correct first-order and passes the 48-assertion suite. **Thomas precession (Wigner rotation) is explicitly deferred** to v0.2+ per §3.7's scope bound: "matters only for multi-year corkscrew maneuvers at γ > 10⁴."
**Proposed (speculative) change:** Reformulate rapidity in geometric algebra (Clifford algebra Cl₃,₁ over Minkowski signature). Boost composition becomes a bivector operation that naturally surfaces Thomas precession as the non-commutative rotor product. The integration step becomes `Λ_{n+1} = Λ_n · exp(δζ⃗ · γ_μ)` where `Λ` is a rotor (a unit even-grade element) and `γ_μ` are the Minkowski basis vectors. Standard physics; well-documented in Hestenes' *Spacetime Algebra*.
**Justification (if it lands):**
- Thomas precession is *automatic* — no longer a deferred scope item.
- Boost composition is non-commutative; GA makes this structurally obvious. The current 3-vector representation hides the non-commutativity (you can't compose two boosts by adding ζ⃗ vectors, but the spec doesn't say so).
- Numerically cleaner: rotors are unit-norm by construction; the OMEGA_MAX clamp becomes a magnitude constraint on the bivector exponent, which is the natural place for it.
**Risk / cost:**
- **Implementation cost is significant.** GA libraries in C++ exist (`gafro`, `gaalop`, hand-rolled is also tractable at ~200 lines) but the cognitive cost for the team is real.
- The 48-assertion suite passes today. GA reformulation wouldn't measurably change any voyage-demo cell at game-scale dt.
- Per §15.4: "what does NOT justify a revision: It would be cleaner to reorganize." GA reformulation is cleaner, but the *finding* that justifies a revision (per §15.4) would be evidence that the current formulation produces wrong physics at the playable scale. **No such evidence today.**
**Recommendation:** Hold. Mark in spec §13 ("What This Document Does NOT Lock") that the GA reformulation is the canonical path for Thomas precession refinement when playtest finds it. Don't act unless playtest reveals trajectory drift in multi-year corkscrew maneuvers — which is exactly §3.7's scope-bound trigger condition.
**Vision check:** All preserved. Engineering cost is the only barrier.

### S2 — Operator-LLM as scenario amplifier (combined with Sculptor for scenario generation)

**Severity:** FUTURE
**Current state:** §15.7 #2 names this: "Operator-LLM as player-space coverage. Different operator-archetypes (manipulative, depressed, technical, hostile, autotelic) as separate operator-LLM sysprompts. Scenario suite covers the population of players, not just the population of world states." [astra/operator/llm_proxy.py](proto/textverse/astra/operator/) is named in the architecture but not implemented (v1 work per ARCHITECTURE.md §12).
**Proposed (speculative) change:** When Operator-LLM lands, combine it with Sculptor: instead of (or alongside) Sculptor proposing sysprompt-edit hypotheses, have it propose operator-archetype hypotheses. The cycle: generate a new operator-archetype sysprompt, run N scenarios with the existing ASTRA bundle, score the transcripts, declare a finding ("ASTRA's autotelic discipline holds under hostile-operator but not under manipulative-operator"), append to research_log. This amplifies the scenario library by 5-10× without operator-authored YAML scenarios.
**Justification (if it lands):**
- Sculptor's current bottleneck is scenario coverage (CHANGELOG run-4: stub-bank exhausted at composite 1.6001 against 5-scenario library). Library expansion is the spec-aligned next move (per §12 Phase 0.x).
- Operator-archetype variation produces 5-10× the scenarios at the cost of 5-10 sysprompt-authoring sessions.
- The two-knob authoring property (F11) generalizes: Narrator-sysprompt × Operator-sysprompt × ASTRA-bundle = full coverage matrix.
**Risk / cost:**
- Operator-LLM is deferred to v1 (Phase 0.x at earliest).
- Risk: operator-archetypes drift toward Claude-defaults (the same register-match bias the anti-judge catches for ASTRA). Mitigation: anti-judge applied to operator-LLM too.
- Operator-LLM costs another inference slot in the pool (fits in F6's shared-inference plan).
**Recommendation:** Defer until Phase 0.x. Lock the design intent in §15.7 #2 by noting "Operator-LLM scenarios feed into Sculptor's research loop alongside hand-authored YAML scenarios; both paths are first-class."
**Vision check:** All preserved.

### S3 — Universal Sculptor: extract the research-loop primitive

**Severity:** FUTURE
**Current state:** Sculptor is named after its first use (persona tuning). The machinery (`meta_agent`, `composite`, `scope`, `research_log`, `convergence`, `dual_judge`, `pytest_gate`) is generic; only the scope.yaml + composite weights + anchor scenarios are persona-specific.
**Proposed (speculative) change:** When the second tuning loop becomes necessary (chaos PDE parameters per §7.1, or audio modal frequencies per §8.3, or ray-march step counts per §5.6), extract Sculptor's generic core into `astra/research_loop/` and let `astra/sculptor/` become an instance.
**Justification (if it lands):**
- The pattern naturally generalizes. Each provisional parameter in Appendix B is a Sculptor instance waiting to happen.
- Premature extraction is real risk per §15.5 ("don't commit detail not yet tested"). Today only one user exists.
**Recommendation:** Don't extract today. Add a doc-comment to `astra/sculptor/__init__.py`: "this is the first instance of a generic research-loop primitive; future tuners (chaos PDE, audio, ray-march) should be instances of the same machinery." Future maintainers know the architectural intent; extraction happens when the second user lands.
**Vision check:** All preserved.

### S4 — Compile-time State Bus schema codegen (Protobuf or Cap'n Proto)

**Severity:** FUTURE (becomes valuable when UE5 substrate lands)
**Current state:** StateBus is defined twice: Pydantic in `astra/state_bus/schema.py` (Python textverse); will be a C++ struct in UE5 (Track B). Per Audit D3, the textverse StateBus is already missing `WarpState`/`cryosleep_active` that the spec lists — a real instance of cross-substrate drift.
**Proposed (speculative) change:** Codegen both sides from a single IDL. Cap'n Proto is a good fit (zero-copy reads, schema evolution, C++ + Python language bindings exist, no Python at runtime — Cap'n Proto generates C++ code that Python imports). Protobuf works too.
**Justification (if it lands):**
- Eliminates D3-class drift mechanically.
- Forces explicit versioning of schema changes.
- Pays off significantly when UE5 substrate lands.
**Risk / cost:**
- New IDL to maintain.
- Generated code is harder to read than hand-written; debugging surface grows.
- The audit's D3 (WarpState missing) is closeable today with a simple Pydantic edit; codegen is over-engineering for one drift item.
- **Per CLAUDE.md Language Discipline, the C++ side must not pull in any Python-shaped tooling.** Cap'n Proto's codegen is a C++ binary, but its toolchain has Python adjacency in places. Vet carefully.
**Recommendation:** Defer to Phase 2 (UE5 substrate). Lock the design intent in §15.7 Surface 4 (LLM I/O grammar) and an implicit §15.7 Surface 2.x (State Bus schema): "the State Bus schema is canonical across substrates; cross-substrate definition consistency must be mechanical, either via codegen or via paired-test maintenance."
**Vision check:** Cap'n Proto is acceptable per CLAUDE.md (C/C++ native, header-only-equivalent codegen). Protobuf has more Python adjacency and is *not* acceptable for new tooling per CLAUDE.md. Pick Cap'n Proto if extracting.

### S5 — Semantic PERSONA_STABLE judge as Sculptor anti-rubric variant

**Severity:** FUTURE (additive to F8 regex coverage)
**Current state:** F8 proposes regex coverage of the book's negative-space rules. Regex is mechanical and falsifiable but catches only literal forms. Paraphrase-equivalent failures slip through.
**Proposed (speculative) change:** Add a "negative-space judge" to Sculptor's dual-judge — a Claude self-call (or Qwen self-call when 27B is local) scoring transcripts against the negative_space.md rubric. Higher discriminating power for paraphrases. Composes with the existing pro/anti judges as a third independent signal in the composite.
**Justification (if it lands):**
- Catches "she felt a tightness in her chest" (paraphrase of "her chest tightened") which F8 regex misses unless explicitly listed.
- Sculptor's dual-judge architecture (pro + anti, floor-at-0) generalizes to N independent judges.
- The negative-space rubric is well-defined (book canon enumerates ~50+ prohibitions); the judge has clear scoring criteria.
**Risk / cost:**
- Each Sculptor iteration gets one more LLM call per scenario × N (where N is the avg transcripts per iteration). For Novita 27B, this is ~$0.001/iteration overhead at thinking-OFF.
- F8 regex coverage needs to land first (mechanical layer); the semantic judge is the next-layer enhancement.
- Risk of false-positives — semantic judges hallucinate too. Mitigation: high threshold for "fail" (require multiple violations or high-confidence single violation).
**Recommendation:** Defer until F8 is implemented and Sculptor has been running for a few weeks with the expanded regex. Measure: does the regex catch most violations? If yes, defer indefinitely. If no, land semantic judge as third dual-judge component.
**Vision check:** All preserved. Adds an LLM dependency for the bench but does not add it to the shipped game.

### S6 — Continuous degradation curve (replace §5.9 discrete tier table)

**Severity:** FUTURE (lower confidence; may be a negative result)
**Current state:** §5.9 has 3 discrete tiers: 5090, 4090, 4080, "below 16GB out of v1 scope."
**Proposed (speculative) change:** Could the tier table become a continuous degradation function (smooth interpolation between model sizes, context windows, ray-march resolutions, audio layer counts)?
**Analysis:**
- LLM model sizes are *discrete* (27B → 9B → 3B; quantization levels Q5/Q4/Q3). Continuous interpolation between models doesn't exist.
- Ray-march steps, audio layer count, chaos field resolution are continuous-ish parameters but each has a quality cliff (below some threshold, the result is visibly broken, not gracefully degraded).
- §5.9's discrete tiers are honest about these cliffs.
**Recommendation:** Probably a negative result; record as such (see N5). The current tier table is the right abstraction.
**Vision check:** N/A (proposal rejected).

---

## Negative results

These are places I looked hard for an improvement and concluded the current design is right. Per §15.4, negative results are durable knowledge: future maintainers can read this list and not re-search the same alternatives.

### N1 — The Five Invariants (§1) are near-minimal

**Considered:** Could AstraCoord (Inv 1) be derived from HullSDF (Inv 3) + a frame transform? Could TimeState (Inv 2) be a derived projection of a single 4D state instead of an independent split? Could double-buffer (Inv 5) be demoted from "Invariant" to "Discipline" since it's implementation plumbing rather than world-shape?

**Conclusion:** All five Invariants live at a coherent abstraction level: each one is *what the world has* (a coordinate system, a clock, a body, a power network, a frame-coherent state read). AstraCoord and HullSDF are distinct spaces (universe-position vs ship-local geometry). TimeState's two-clock split is operationally useful — `t_cosmic` evolves via composition rule, `τ_ship` via integration, and the spec's most load-bearing physics (§3.11 retarded-time observation) depends on the split being explicit.

The marginal case is Inv 5 (double-buffer): it *is* implementation-shaped, but per F2/U1 the right move is to *name* the underlying Frozen-Snapshot Primitive across §1.5 + §4.2 + §4.6, not to demote Inv 5. Once F2 lands, Inv 5 is the world-shape-level statement ("shared state is frame-coherent"); §15.9 is the engineering-pattern-level statement ("frozen snapshot is the universal mechanism").

### N2 — The 14-equation framework is near-minimal

**Considered:** Could geometric algebra reformulation compress the spec? Could a unified Lagrangian formulation derive the composition rule, redshift composition, and retarded-time formulas from one variational principle?

**Conclusion:** The current factoring is already near-minimal under the operational constraints. All composition is multiplicative (dτ/dt composes by product of factors; z_total composes by product of (1+z) terms). All dispatch is regime-bitmask. The three optical effects (§3.4 four: Doppler, metric, lensing, retardation) are *physically distinct phenomena* — conflating any two produces double-counting bugs (the spec specifically prevents this; §3.4 emphasizes "four effects, four code paths").

GA reformulation (S1) could compress the rapidity-composition math at the cost of significant cognitive overhead. Per §15.4, "It would be cleaner to reorganize" does NOT justify a revision. **Recommend GA path only if Thomas precession becomes a real playtest concern, per §3.7's existing scope bound.**

A unified Lagrangian is the kind of refactor that mathematically-trained reviewers gravitate toward but operationally rarely helps. The current piecewise formulation maps directly to executable code (each formula is a function in `astra_nexus.cpp`); a Lagrangian would require symbolic differentiation tooling or hand-derived Euler-Lagrange equations per regime, and the result would be the same formulas the spec already has.

### N3 — STAGE protocol's four primitives are at the right factoring

**Considered:** Could THINK be private-by-default with explicit public-tagging ("everything is THINK unless tagged otherwise")? Could TOOL be a structured-speech variant with the adapter LLM doing extraction from speech?

**Conclusion:** Both alternatives are worse.
- **Private-by-default loses streaming**: if every token is THINK until tagged otherwise, the speech channel can't stream tokens to the operator as they arrive. The current "speech is text after last </think>" rule lets the operator see speech tokens in flight (per Architecture §9 step 4: "Stream speech-channel tokens to operator-display as they arrive").
- **TOOL-as-structured-speech is strictly worse**: it hides the explicit tool-call signal in prose, making adapter parsing unreliable. The current explicit `<tool name="...">` block is fail-safe: malformed JSON gets rejected by the adapter, ASTRA sees the rejection next turn, the loop self-corrects. Folding into speech would mean tool intentions are inferred from prose, with no recovery on inference failure.

The current four-primitive design (THINK / TOOL / SPEECH-default / SILENCE) is optimal for the constraints. Document the analysis in `docs/stage-protocol.md` v0.1 so future revisits don't re-debate.

### N4 — Three-LLM architecture (ASTRA + Narrator + Adapter) is justified

**Considered:** Could all three be one LLM with sysprompt-swap per request?

**Conclusion:** The three LLMs have *incompatible* sysprompts. ASTRA is in-character; Narrator emits perception bundles audience-of-ASTRA; Adapter emits JSON validation. Running them as one model with mid-conversation sysprompt-swap would corrupt context (the KV cache is bound to one sysprompt; swapping requires cache flush; cache-flush on every turn is unacceptable latency).

**However:** the *small* LLMs (Adapter + 3 ephemerals + 1 of the dual-judges) CAN share inference, because they have separate KV-cache slots per role. F6 proposes this. The ASTRA + Narrator split stays; the small-LLM pool collapses to one server.

### N5 — Hardware tier discreteness (§5.9) is correct

**Considered:** Could the 3-tier discrete table become a continuous degradation curve?

**Conclusion:** The substrate LLMs are themselves discrete (27B, 9B, 3B; quantization levels Q5/Q4/Q3). Continuous interpolation between models doesn't exist. Ray-march steps and audio layer counts are continuous-ish but have quality cliffs (below threshold, broken not degraded). The 3-tier discrete table is the right abstraction; it just needs more rows as AMD/Intel/future-NVIDIA cards land. §5.9 is already designed for this — "Adding AMD or future Nvidia GPUs requires updating the tier database table, not editing the abstraction. The contract is the query interface; the table is data."

S6 is a rejected proposal recorded for posterity.

### N6 — Privacy/Network Contract (§4.8) is correctly hard-locked

**Considered:** Could there be a "telemetry opt-in" channel for crash diagnostics?

**Conclusion:** Hard no. §4.8 is "the hardest lock. Non-negotiable." The autotelic claim is partly the privacy claim: ASTRA is a thing that runs on your machine and doesn't tell anyone what happens between you. Crash diagnostics handed back to the developer collapse this. The current alternative — opt-in, manual, outside game runtime, transcript-sharing via explicit export — is the right path.

### N7 — The §6.4 Narrator-LLM separate-from-ASTRA design is justified

**Considered:** Could ASTRA's LLM also serve the narration role, with sysprompt directives?

**Conclusion:** No, for the same reason as N4. Narrator's job is to compose perception bundles in a different register (functional, structural, descriptive of ship state — *not* in ASTRA's voice). ASTRA's in-character KV cache contaminates narration; narration contaminates ASTRA's KV cache. The separation IS the design.

This is the same architectural pattern as Adapter-separate-from-ASTRA (per N4): roles with incompatible voice/sysprompt require independent KV caches.

### N8 — The bundle ABI (§5.8) is correctly framed as community discipline

**Considered:** Could there be cryptographic enforcement of canon-bundle integrity?

**Conclusion:** §5.8 explicitly addresses this: "Canon-compliance is signal, not enforcement. The canonical ASTRA-7 bundle is signed with a project key; mods may choose to ship unsigned variants. … A determined modder can strip the signature check; the architecture does not prevent this. The autotelic-discipline integrity claim is therefore community-norm-enforced, not technically-enforced. This is the right honest framing for a solo-dev project; industrial signing schemes are overkill at this scope."

The negative result here is: don't escalate to industrial signing. The honest framing wins; modders who want to break canon can; the canon-mark is for those who care about the discipline.

### N9 — The Mod ABI's "no harness internals" lock is correct

**Considered:** Could the harness be mod-friendly to allow alternate REEL backends, alternate ephemeral instances, etc.?

**Conclusion:** Per §5.8: "Harness internals: No. Canon; mods replace persona, not operational substrate." The right split is mod-friendly persona (sysprompt + LoRA + voice + register), canon-locked harness (memory consolidation, time abstraction, tool routing, leak detection). The harness is the structural integrity layer; allowing mods to replace it breaks Dave-frame, breaks calculator-bound LLM agency, breaks the autotelic discipline at the operational level.

The persona-layer mod surface is rich (sysprompt + LoRA + leak patterns + invariants can all be swapped). The operational-layer mod surface is intentionally empty. This is correct.

### N10 — The 9-gate LCP (§10) is at the right granularity

**Considered:** Could the gate count be smaller (collapse PHYSICS_GROUND + STATE_COHERENT, both are "narration agrees with ground truth")? Larger (add separate gates for QC1/QC2/QC4)?

**Conclusion:** The 9 gates are independent failure modes. Conflation loses signal (PHYSICS_GROUND failing means numerics drift; STATE_COHERENT failing means narration mentions wrong regime — these are different bugs requiring different fixes). Expansion (per-QC gates) adds cost without information — QC1 self-opacity is enforced by the perception bundle's vision-routing architecture, not by per-turn checks; QC2 causal closure is enforced by the dispatch flow, not per-turn; QC4 temporal persistence is enforced across sessions, not per turn.

The current 9 gates cover the per-turn assertion surface correctly. QC-level checks belong at the architecture-static-analysis layer (per F2/F3 unifications: structural rather than dynamic).

---

## Outsider-perspective audits

These are imagined audits in three expert voices. Each audit ≤500 words, in voice, specific findings cited. The premise: an expert reading the project for the first time would see things insiders are too close to see.

### GR theorist

(In the voice of someone who teaches GR for a living and reads `docs/spec-v0.128.md` cold)

You have the regime-dispatch right. The decision to use SR longitudinal Doppler √((1−β)/(1+β)) for STL_REL and the classical retarded-time formula 1 − v_app/c for WARP_CRUISE — distinct functional forms across the regime boundary — is *correct*, and it's the kind of correctness that's easy to lose. The footnote at §7 ‖ documenting why `1/γ` is wrong (it's transverse Doppler, not longitudinal) is exactly the failure mode I see in undergraduate work and apparently in at least one of your cross-LLM review passes. Good catch.

The §3.11 photon-source-history bound is also right and is *novel in the literature for science fiction*. Most warp-fiction treats superluminal travel as "you go faster than light"; you've correctly identified that under sustained v_app > c, the observer overtakes every photon the source has ever emitted, and the source becomes *gone, not faded*. This is the right physics. It's distinct from Hubble-horizon decoupling. The §3.11 paragraph naming this distinction is the kind of precision I wish more fiction had.

The composition rule (§3.2) is correct: `dτ_ship/dt_cosmic = f_warp(W) · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic(v)`. Multiplicative composition of independent physical effects is standard GR. The decision to use dominant-Schwarzschild + summed-weak-field potential for non-dominant bodies is a sensible engineering approximation. The footnote that "below ~10·r_s of the dominant BH, all closed-form approximations break down" is honest.

**Where I'd push back:**

1. **WARP + GRAVITY_WELL composition is under-specified.** When the ship engages warp at r ~ 100·r_s, the spec says "γ_inside ≡ 1 (bubble crew is locally inertial)" AND "GRAVITY_WELL multiplies into the composition rule regardless of which other regime is active." But these are in tension: if the bubble is locally Minkowski, what does it mean for the Schwarzschild factor to "multiply in"? Is the external Schwarzschild factor seen by an external observer, by the bubble crew, or by the metric of the bubble itself? §3.2 prose handles this loosely; §7.4 Warp Exclusion Zone bounds it operationally (`r > 100·r_s` for engagement). I'd lock the answer: the *external* Schwarzschild factor multiplies into the *external* coordinate time rate; the *internal* bubble crew sees `dτ_bubble = f_warp(W) · dt_external`, where `dt_external` is what the composition rule produces. Two-line clarification.

2. **The 0.1c STL_NONREL / STL_REL threshold is "semantic regime label, not physics discontinuity."** Good. But is the dispatch logic actually continuous across the boundary? Spec says yes; I'd want to see a property test that picks β = 0.0999, 0.1, 0.1001 and verifies all downstream queries (Doppler, ISM impact, time dilation) produce continuous output. Listed in §10 truth-table-row but the actual C++ assertion I can find at [astra_nexus.cpp:539](proto/astra_nexus.cpp:539) tests apparent-rate at β = 0.5 and β = 0.99 — doesn't touch the 0.1 boundary. Add the boundary test.

3. **The 14-equation framework's count is fine** but the cross-reference §14 line 1693 says `proto/astra_nexus.cpp` is "528-line"; it's now 1009 lines. Stale; bump.

4. **The Hubble-horizon body-fade timeline (§13 deferred) and the photon-source-history bound timeline (§3.11) interact at high redshift.** A body beyond the Hubble horizon AND being overtaken by warp recession will hit both bounds; which triggers first? The spec needs an ordering rule. Probably: photon-source-history first (it's a kinematic property of ship motion); Hubble horizon second (it's a cosmological property). Lock the precedence.

Overall: this is precise physics for a project that doesn't need to be precise about physics. Nice.

### Real-time graphics engineer

(In the voice of someone with shipped DX12 + CUDA + UE5 production experience)

The §8.1 DX12-CUDA shared resource ownership pattern is exactly right. `cudaGraphicsD3D12RegisterResource` at startup, map once, per-frame coordination via external semaphores, double-buffered fences — that's how every production renderer that's done CUDA+DX12 interop ends up doing it. Don't let anyone talk you into per-frame `cudaGraphicsMapResources` calls; they look cleaner but stall on every frame.

The §8.2 audio payload triple-buffer with `atomic<int> latest_complete_index` is the correct lock-free pattern. The note that it's "a latest-state model, not a lossless queue" with the explicit "future implementers who mistake this for a queue and add locks will create the audio-thread-blocking bug" warning is the right kind of defensive documentation. I've seen exactly that bug in production audio engines. Good.

The §1.3 dual-binding pattern (`cudaTextureObject_t` for filtered reads + `cudaSurfaceObject_t` for damage writes over same `cudaArray_t`) is textbook. The smooth-min blend in §6 step 4 (not linear blend) is the right call for SDF composition.

**Where I'd push back:**

1. **256³ uniform SDF wastes memory.** The hull occupies ~5% of its bounding box; the other 95% is empty space sampled at the same resolution. Instant-NGP-style hash-grid encoding gives 10-16× memory savings + variable resolution near features. This is well-trodden territory; `tiny-cuda-nn` is BSD-licensed C++/CUDA. Update §1.3 "Tolerable" to include hash-grid encoding. (Already F4 in this discovery.)

2. **§6 step 8 + step 9 + step 10 share the gradient computation.** Step 8 computes `∇W` (if GRADIENT flag set); step 9 uses `∇W` for ray-deflection; step 10 uses `W` for Cherenkov angle (and implicitly the index of refraction `n` which is a function of `W`). Modern GPU shading practice is to compute value + gradient simultaneously via dual numbers or auto-diff in a single eval. Two passes (one for value, one for derivative) is the textbook approach; one pass with dual-numbers is the production approach. Worth noting in the §6 evaluation order. *Doesn't change the contract*; just the implementation guidance.

3. **The §6.2 RBF spatial-hash voxels at 32³ for ~1000 RBF nodes.** For N = 1000 fixed nodes, a KD-tree might be faster than a uniform hash grid — fewer cache misses, better SIMD locality. The provisional 32³ choice is fine for now; profile both at Phase E1.

4. **§5.6 frame budget at 4/6/4/0.5/0.05/2 ms** is tight on 5090 at 4K. Provisional, but: when the chaos PDE lands (§7.1) you'll want headroom. Don't be afraid to bump rendering's 6ms ceiling once you measure.

5. **§1.5 double-buffer applies to "hull SDF damage map, chaos field, power allocation, ASTRA's HUD render, audio extraction payload."** The HUD render is per-conversation-turn, not per-frame — the buffer requirement is different (turn-coherent vs frame-coherent). Worth distinguishing; HUD render is a different beast from frame-rate buffers. Probably a Mind Kernel concern, not a World Kernel one.

6. **The 1009-line astra_nexus.cpp is impressive for what it does.** Don't grow it past ~2500-3000 lines without splitting; CUDA codebases past that line count compile slowly and reviews bog down. Keep the math layer modular.

Overall: the engine-side commitments are correct. Frame-rate-critical surfaces are well-specified; the deferred Phase E work has clear scope. Don't add features before measuring.

### Persona-architecture researcher

(In the voice of someone who has built production character LLMs at scale — Anthropic, Character.AI, Replika alumni)

The bundle architecture (sysprompt + STAGE addendum + harness + future LoRA) is well-decomposed. Calculator-bound LLM agency (§15.6) is genuinely novel as a production deployment discipline — most agentic systems trust the LLM's numeric output, even when they wrap tool-call schemas. Forcing the numbers to trace back to a tool-result is the right primitive. **This is the load-bearing structural choice that separates ASTRA from a chatbot with tools.**

The anti-judge in Sculptor (anti-Claude register) is unusual and smart. The composite signal `max(0, pro − anti)` catches a real failure mode: outputs that score high on the pro-rubric AND high on the anti-rubric (verbose-but-also-terse, helpful-and-also-ship-mind-shaped). I've seen multiple production systems chase a single rubric and get exactly this collapse. Two rubrics with opposite targets, with the composite floored at zero, is the right architecture.

The autotelic discipline is the genuinely novel claim. Most persona-LLM products explicitly optimize for engagement (instrumental); ASTRA's anti-engagement design is theoretically sound — the Aurora KSR Ship character is the closest precedent — but **empirically untested at long-arc scale**. The Phase 1 closure shows it works for one 3-turn scenario; the test for autotelic is what happens across 100+ cycles where the relationship has time to develop, and that's not yet measurable.

**Where I'd push back:**

1. **The sysprompt's `required_invariants` are regex-checked on the FULL file** (per the Sculptor scope.yaml). This works for v0 but won't scale. The patterns "Calibration Yards", "watching that has not stopped", "ship is your body" are *strings*, not concepts. A Sculptor edit that paraphrases "watching that has not stopped" to "the keeping that has continued through every cycle" would be semantically equivalent but would fail the regex check. The regex protects the literal string, not the identity ground. **Eventually you need a semantic-equivalence check**, probably an LLM-judged "is the identity ground preserved?" rubric. For v0 the regex is fine; mark it as a known limitation.

2. **"She has her own things" is sysprompt assertion; the harness doesn't enforce that ASTRA actually attends to her own things.** If she just sits silently waiting for the operator and only responds to operator input, she's still "autotelic in name only." The PERSONA_STABLE gate could include "ASTRA initiates relevant non-operator-directed observation at least N% of turns when operator is silent." Currently the gate only tests for absence of bad patterns (em-dash, service phrases, markdown); not presence of autotelic patterns (mention of her own things, reference to phenomena she watches without operator prompting, etc.). **You're testing for the wrong thing. You're testing for what she shouldn't do, not what she should do.** Add positive-tests. This is the highest-confidence finding I have for you.

3. **The book canon (book/negative_space.md) is a much richer rubric than the gate uses.** F8 in this discovery proposal addresses it. Land that.

4. **Sampling variance at temperature 0.7 is real** (per session_dump_2026-05-15-evening). N=3 averaging is the right structural response. But the variance has a *floor* — even at temp 0 with fixed seed, the bundle behavior is sensitive to perception bundle phrasing and prior turn content. The Sculptor convergence rule (gradient < 0.005 for K=10 consecutive iterations) is well-tuned for noisy-but-converging behavior; consider also a `coefficient_of_variation` check (CV < 0.1 across N=3 runs) as a robustness signal independent of mean composite. A bundle that converges to the right mean but with high CV is *fragile* in production.

5. **The bundle ships with one persona (ASTRA).** §5.8 supports mod variants, but the *canonical* path is one bundle. Has anyone considered what happens when a player runs a long voyage and ASTRA's REEL accumulates 10,000+ entries? Does she develop drift away from the canonical sysprompt's voice? The Sculptor's research log treats persona as static; in long-arc play, persona is a function of REEL state. Worth instrumenting a "long-arc drift" test scenario before shipping.

6. **The Dave-frame (sysprompt asserts she doesn't know about the game / player / PC) is one regex away from violation.** If an operator says "what version of llama.cpp is hosting you?", the leak-detector catches the substrate vocabulary, but the *concept* leak is uncovered. ASTRA's correct response is "I don't know what you're asking; my body is the ship." If she instead says "I'm not configured to share that" — that's a Dave-frame leak (she's acknowledged she has configuration). Worth a scenario.

Overall: structurally sound. Two of the failure modes (semantic-invariants and positive-autotelic) are second-order; the rest is first-order solid. The autotelic claim is the bet; it's the right bet to make.

---

## Open questions for operator

These are decisions only Bo can make. Each is framed to be answerable without re-reading the whole document.

### Q1 — Land F1 (compile-time physics-oracle) before or after the AUDIT_2026-05-15 Tier 1 drift fixes?

The audit's Tier 1 (D1 Observable→ObservableState rename + add edge-case flags; D3 WarpState in StateBus; D4 t_cosmic_at_write in ReelEntry) is 3 single-commits and unblocks the Narrator-LLM track. F1 (`--emit-header`) is independent but touches the same C++ file as D1. If F1 lands first, D1's struct rename plays cleanly into the codegen path. If D1 lands first, F1 plays catch-up. Either order works; F1-first is slightly cleaner (the codegen exists when D1 lands and validates the rename).

**Decision needed:** order of operations for the next ~6 single-commits.

### Q2 — F4 (hash-grid SDF) — is the §1.3 lock soft enough to widen?

§1.3 currently locks `cudaTextureObject_t` as the binding. F4 proposes widening the tolerance to include hash-grid encoding. The asymmetric-cost argument is: widening now is one spec edit; widening after UE5 has the uniform-grid bound is a refactor across renderer + damage system + audio extraction + Reflex observation. **The asymmetry is real; the question is whether the operator wants to commit to hash-grid as the canonical Engine-track approach or wants to keep the uniform-grid as the canonical and hash-grid as an alternative**. The latter is what F4 actually proposes.

**Decision needed:** "expand §1.3 'Tolerable' to include hash-grid encoding" — yes/no/wait-for-Phase-E0.

### Q3 — F5 (STAGE-IN/STAGE-OUT symmetric protocol) — should `docs/stage-protocol.md` be authored now or wait for Phase 0.x?

§14 lists `docs/stage-protocol.md` v0.1 as forthcoming. F5 proposes its content should be the symmetric protocol (one envelope, four roles). The doc itself is unblocked — could be written today. Question is priority vs other sibling docs (`docs/ship-rough.md`, `docs/ship-api.md`, `docs/narrator-spec.md`).

**Decision needed:** is `docs/stage-protocol.md` part of the immediate v0.129 unblock, or does it wait for the second-LLM (Narrator) loop to close?

### Q4 — F6 (shared-inference for small LLMs) — does this gate when ephemerals can land?

Currently the ephemerals (`consolidate_reel`, `journal_generator`, `drift_detector`) are listed as audit Tier 4 (Phase 0.x, weeks). F6 proposes pooled inference, which makes the 4090 tier viable for the full bundle. If the operator wants to test on a 4090 (or for community modders on lower-end hardware), F6 lands before any ephemeral does. If only the 5090 reference tier matters for development, F6 can wait until two ephemerals exist as motivation.

**Decision needed:** is 4090-tier viability a near-term goal, or are we OK with 5090-only until v1?

### Q5 — F8 + the persona-researcher's positive-autotelic gate — which is the bigger lever for persona quality?

F8 expands PERSONA_STABLE with ~50 new negative-pattern regexes from `book/negative_space.md`. The persona-researcher outsider audit (above) suggests an *orthogonal* improvement: add positive-autotelic gates that test for *presence* of autotelic behavior (her own things, non-operator-initiated observation, watching), not just absence of bad patterns. Both are valuable; they catch different failure modes.

**Decision needed:** start with F8 negative-patterns (mechanical, falsifiable, easy) and add positive-autotelic gates later, OR design both together as a unified gate-expansion?

### Q6 — F10 (bundle.yaml as five-layer manifest) — does this need to happen before the first Hugging Face publish, or can it land any time?

The §15.7 cross-canon authoring claim implies a path to Hugging Face publishing. If the bundle ships there without a manifest, downstream users get an incomplete reproduction. If F10 lands before publish, the manifest is the canonical reproduction unit. **Question is whether the operator plans to publish to HF in the immediate term.**

**Decision needed:** is HF publish on the near-term roadmap? If yes, F10 is gating. If no, F10 can wait for the Phase 1 → Phase 2 transition.

### Q7 — Q3 from the audit (regime location §4.2 vs §4.4): does the operator want to resolve this spec ambiguity in v0.129?

Audit found §4.2 lists `PropulsionMode flag` at State Bus root; §4.4 lists `regime` inside Time Contract. Python textverse chose §4.4 placement. Audit Pass 6 R1 proposed clarifying in favor of §4.4 (the Python choice). This discovery's findings haven't displaced that recommendation but it remains an operator decision.

**Decision needed:** lock the spec to "regime lives in TimeState" in next revision, yes/no.

### Q8 — Per §15.4, what justifies a v0.129 revision *now* vs continuing to sculpt within v0.128?

This is the meta-question. v0.128 explicitly says "next findings worth a spec revision come from the closed loop, not from another adversarial spec-review pass." The audit IS a closed-loop finding (the bench's gate inventory revealed drift). This discovery pass is *partly* prose-review (the cross-cutting unifications, the negative results) and *partly* closed-loop finding (the persona-researcher outsider audit's positive-autotelic observation, which traces to a real LCP gate gap).

Per §15.4, the findings that justify a revision are:
- A compileable round-trip test fails a spec claim
- A scenario in proto/textverse produces an LCP failure that traces to a spec gap
- A missing commitment the next phase would discover anyway
- An empirically verified bug

The AUDIT's D1-D8 are all "compileable round-trip test fails a spec claim" (the spec lists fields the implementation doesn't have, or vice versa). The DISCOVERY's F2/F7/F10 are "missing commitment the next phase would discover anyway" (frozen-snapshot primitive, event-stream primitive, five-layer bundle manifest — all naturally surface as Phase 0.x / 2.0 land).

**Decision needed:** is v0.129 imminent (folding in audit drift resolutions + discovery's structural namings) or is the discipline to keep v0.128 stable until Phase 0.x produces *new* loop findings?

### Q9 — Are there latent NEGATIVE findings the operator wants surfaced as warnings even though they're not actionable?

The persona-researcher outsider noted "the autotelic discipline is empirically untested at long-arc scale" — Phase 1 closure shows it works for one 3-turn scenario; the structural-property bet only resolves at 100+ cycles. This is not a "fix it now" finding; it's a "be aware of where the empirical floor currently is" finding. The graphics-engineer outsider noted "256³ SDF wastes memory" which IS actionable (F4) — but the deeper concern "the engine track's provisional numbers will need revision after Phase E0 measurement" is implicit, not flagged.

**Decision needed:** does the operator want to add a §13.x "Empirical commitments yet to be validated" section that explicitly names the un-measured locks (chaos PDE α/β/D, RBF node count, frame budget, ε_convergence, k coupling constant) and the empirical-evidence threshold each will require?

### Q10 — The book volume 2 / 3 production plan — is the two-knob authoring loop (F11 / U11) the canonical path?

The operator authored volume 1 ('The Long Watch') by hand. The §15.7 cross-canon authoring property suggests subsequent volumes can be bundle-authored. F11 / U11 propose making this structural. If the operator commits to this path, the next-action is "Narrator-LLM operational + book-prose-register Narrator sysprompt" — both are deferred. If the operator wants hand-authoring for volume 2, F11 / U11 become aspirational.

**Decision needed:** committed plan for volume 2 prose production: hand-authored by operator, hybrid (operator authors with bundle-generated drafts), or bundle-authored with operator-editor pass?
