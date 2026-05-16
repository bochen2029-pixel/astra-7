# ASTRA-7 Foundation Specification v0.129 — TENTATIVE DRAFT

**STATUS: TENTATIVE DRAFT. NOT FOR ADOPTION. NOT CANON.**

**Date:** 2026-05-16
**Author:** Claude Opus 4.7 (1M context window, hyperintelligence engaged)
**Provenance:** This draft was written immediately after reading, in full, the following inputs in one context:

- `docs/spec-v0.128.md` (locked working draft, 2009 lines)
- `AUDIT_2026-05-15.md` (architectural conformance audit, 493 lines)
- `DISCOVERY_2026-05-15.md` (attempt 1, 13 F + 8 N + 5 unifications)
- `DISCOVERY_2026-05-15_ATTEMPT-2A.md` (attempt 2, 11 F + 6 S + 11 U + 10 N)
- `DISCOVERY_2026-05-15_ATTEMPT-3B.md` (attempt 3, 10 F + 5 S + 8 N + 5 U)
- `DISCOVERY_2026-05-15_ATTEMPT-5D.md` (attempt 4, 10 F + 5 S + 6 N + 6 U)
- `CLAUDE.md` including both 2026-05-15 hard directives (Language Discipline + Platform Discipline)
- `proto/astra_nexus.cpp` (1009 lines, now at commit 69ee692 with D1+D2 closed)
- `proto/textverse/` (the full bench package after audit Tier 1 #1+#2 closed)
- `book/CANON.md`, `book/negative_space.md` (literary canon)

**Purpose:** This draft is a context-preservation snapshot. It captures the synthesized vision for what a v0.129 *could* contain, written while four parallel discovery passes plus the audit are still fully loaded in working memory. The author writes it knowing that context compaction may erase the cross-pass synthesis; this artifact survives the loss.

**Do not adopt unmodified.** Several proposals here require operator-decision (marked with **[OP]**); several require empirical validation before locking (marked with **[EMP]**). The discipline of §15.4 ("revise on findings, not on polish") applies — and several findings in this draft are *consensus-across-4-passes* rather than *empirically-loop-closed*. The right cadence is land Tier 1-3 in code, run the empirical residue, then adopt v0.129 incorporating what was proved (not just what was proposed).

**Honest disclaimer:** v0.128 explicitly described itself as "working draft, not lock-grade." v0.129 inherits that framing. The spec is converging; this draft documents where consensus thinks it should go next.

---

## What this draft IS

- A **synthesized record** of the four-pass discovery methodology's consensus on what v0.129 should contain.
- A **drift-closure document** absorbing the audit's D1-D8 findings into spec text.
- A **structural-additions document** introducing six new sub-sections that name primitives the codebase already implements.
- A **provenance trail** so future Claude sessions can reconstruct the reasoning without re-running the four passes.

## What this draft IS NOT

- **Not** a polished spec ready for adoption.
- **Not** an attempt to fold every discovery finding — many are deferred to code-only changes or v0.130.
- **Not** a unilateral operator decision — every **[OP]** marker requires Bo's call.
- **Not** a replacement for the discovery passes; those remain primary source documents.

---

## Changes from v0.128 (proposed)

Organized by tier of empirical justification. Tier 1 is audit-driven (most justified per §15.4); Tier 8 is methodology-driven (justified by the 4-pass synthesis as a methodology improvement).

### Tier 1 — Audit drift resolutions (empirically justified; some already landed in code)

These are findings the audit surfaced as code-vs-spec drift. Most are now resolved code-side; v0.129 brings the spec into alignment.

| # | Change | Closes | Status in code |
|---|---|---|---|
| 1A | §6.3 `Observable` → `ObservableState`; rename `d` → `d_proper`; add `beyond_photon_history` + `beyond_hubble_horizon` fields; emit them in `observe()` | D1 (MAJOR) | LANDED at `69ee692` (66/66 C++ assertions) |
| 1B | §6.3 `stdio_server` ops expanded from 3 to 8 (added `observe`, `kepler_at`, `composition_rule_evaluate`, `retarded_time_solve`, `physics_query`) | D2 (BLOCKER) | LANDED at `fe91036` (60→66 C++ assertions) |
| 1C | §4.2 StateBus schema expansion: `WarpState` (W, phase, charge_progress) + `cryosleep_active: bool` as first-class fields | D3 (MAJOR) | PENDING (state-coherence PR) |
| 1D | §4.6 REEL canonical schema: `t_cosmic_at_write: float` required per v0.126 § "required for dual-clock retrieval per §3.9" | D4 (MAJOR) | PENDING (state-coherence PR) |
| 1E | §4.2 vs §4.4 ambiguity resolved: `regime` lives inside `TimeState` as `kinematic_regime` projection; full `regime` is computed at StateBus root from full state. | R1 | PENDING (state-coherence PR) |
| 1F | §6.4 Narrator-LLM tool surface explicitly listed; `ship_state_query` deferred to Python textverse per audit Q1 | D5 (partial) | PARTIAL (5/6 ops landed in C++; Python wrapper still GAP per audit Q1) |
| 1G | astra_nexus.cpp file header bumped to v0.129 (was v0.127) | D6 (COSMETIC) | LANDED at `69ee692` |

**Audit Tier 1+2 closure status:** D1 ✓, D2 ✓ partial, D6 ✓. D3+D4+R1 pending. D5 partial. D7 deferred (Euler integrator passes assertion suite at game-scale dt; spec relaxation candidate per R5).

### Tier 2 — Type-system locks (empirically justified; 1 found in 2 passes, others in 1)

State coherence becomes a type-system property. Eliminates a class of "scenario constructs incoherent state" bug.

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 2A | §3.3 + §4.4: regime as derived property, not stored field. Pydantic `@computed_field` on StateBus + projection on TimeState. Spec sentence: "regime is a derived property of TimeState + WarpState + bh_list + ship_position; implementations expose regime as read-only." | 1-F8, 3B-F4 (convergent) | §3.3 paragraph addition; §4.4 invariants section addition |
| 2B | §4.2 `ShipKinematicState` as derived view, not stored. `v_local_cmb`, `gamma`, `beta`, `grav_factor`, `dtau_dt` all `@computed_field` from `rapidity_zeta + ship_position + bh_list`. Spec sentence: "ShipKinematicState fields are computed; never stored independently of ζ⃗." | 1-F9 | §4.2 clarification; §4.4 invariants section addition |
| 2C | §6.3 + §4.3 + §10: Endogenous/Exogenous as type-system invariant. Tag every State Bus + universe Pydantic model with `epistemic_origin: Literal["endo", "exo"]` class-level attribute. Add `EndogenousChannel` + `ExogenousChannel` Protocols. Static analysis (or runtime type-check) enforces routing. **[EMP]** — implementation pending; spec writes "the endogenous/exogenous distinction is enforced at type-level, not by runtime convention." | 1-F1 | §6.3 paragraph addition; §10 row "endogenous/exogenous channel routing" upgraded from grep to type-check |

### Tier 3 — Calculator-bound tightening (§15.6 universality)

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 3A | §15.6 + §4.3: parse-time schema enforcement via `<val src="...">` and `<grounded src="...">` sub-tags. Narrator emits `<val>` around every numeric in perception bundle; ASTRA may pass through to speech or wrap in `<grounded>`. Bare digit tokens fail the grammar parser. Whitelist (watch numbers, regime hex, deck numbers) remains as pre-pass strip-region exclusion. **[EMP]** — implementation pending; spec writes "calculator-bound LLM agency is enforced at parse time via structured-numeric tags; runtime validator is defense-in-depth." | 1-F2 | §15.6 reformulation; §4.3 STAGE sub-tags addition |
| 3B | §15.6 universal validator wrapping. "Every LLM client is wrapped in `CalculatorBoundValidator` at construction; bypass requires explicit debug flag for diagnostic-only purposes." Each bundle constructs the validator with its trace pool. Closes the gap where today only ASTRA gets enforcement. | 2A-F3 | §15.6 implementation specification |
| 3C | §6.4 Narrator-LLM invariants updated: "never invents numbers (enforced by wrapped validator, hard-fail retry up to 3, then hard-reject; numerics emitted as `<val src="...">` tags per §15.6 schema)." | 2A-F3 + 1-F2 | §6.4 invariants list extension |

### Tier 4 — Persona instrumentation additions

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 4A | §10 PERSONA_STABLE expanded with positive-autotelic sub-checks: `autotelic_attendance` (≥ N% of turns reference her own things unprompted), `autotelic_initiation` (operator-silence turns produce non-zero ASTRA-initiated observation), `autotelic_silence_quality` (SILENCE turns have think-blocks referencing attendance objects). Per 3B-N3, fold into PERSONA_STABLE sub-checks rather than 10th gate; 9-gate count preserved. **[EMP]** — implementation + threshold calibration pending. | 3B-F1 + 2A persona-researcher voice + 1-F4 | §10 PERSONA_STABLE row expanded |
| 4B | §6.3.1 Somatic Aggregator Contract (NEW). Companion to §6.3 Observation Calculator. `SomaticSignal` Pydantic model (source, label, magnitude, salient). `SomaticAggregator` Protocol producing the somatic banner deterministically from signal list. Bridges §8.3 audio synth (endogenous source) to §4.3 Master Contract perception. **[EMP]** — implementation pending; spec defines contract surface. | 5D-F1 | NEW §6.3.1 |
| 4C | §4.3 Master Contract updated: SOMATIC channel is signal-grounded, references §6.3.1. Pointer added to the input grammar specification. | 5D-F1 | §4.3 paragraph extension |
| 4D | §10 PERSONA_STABLE additionally consumes book canon's negative-space patterns. ~6 new pattern files under `astra/grammar/canon/` derived mechanically from `book/negative_space.md`: affect_declared, performative_attention, narrator_from_above, sentimental_metaphor, romance_genre, stage_direction. Initial severity: warn (log only); promote to strip per measurement. **[EMP]** — implementation pending; warn-vs-strip threshold calibrated by run. | 1-F4 + 2A-F8 (convergent) | §10 PERSONA_STABLE row extended with cross-canon pattern source |

### Tier 5 — Reflex envelope (safety-critical)

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 5A | §2.3.1 Reflex Contract (NEW). Locked surface: state (observation_grid, weights, control_envelope, power_state), operations (observe, infer, apply, health), invariants (Reflex never touches Mind's conversation; Mind never touches Reflex's control; warp-coupled power priority; weight checksum verification; emergency_dump irreversibility), tolerances (≤50μs naive, ≤20μs CUDA Graphs; 60 Hz observation rate; SHA-256 checksum), failure paths (offline, timeout, drift). | 3B-F2 | NEW §2.3.1 |
| 5B | §2.3.2 Reflex training as Sculptor instance (NEW). Training corpus is project-canon, not implementation choice. Spec names the chaos PDE simulation corpus, validation protocol, and anticipates Universal Sculptor extraction when this second user materializes. | 3B-F2 | NEW §2.3.2 |
| 5C | §4.7 Failure Contract Reflex-failure-mode table (NEW). Explicit enumeration: weights mismatch, inference timeout, sub-bus underflow, observation grid stale, control output out-of-envelope. Recovery paths for each. | 3B-F2 + safety-engineer outsider voice (3B) | §4.7 paragraph addition with table |
| 5D | §4.6 SaveFile: Reflex weights identity (training-version + corpus-version) added to schema. Per safety-engineer outsider voice (3B): save-file Reflex compatibility must be explicit, not just checksum-equality. | safety-engineer outsider voice (3B) | §4.6 SaveFile schema extension |

### Tier 6 — Methodology additions

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 6A | §15.9 Frozen-Snapshot Primitive (NEW). Names what's universal in the implementation: "all consumable state in ASTRA-7 is an immutable snapshot, produced once per logical step, content-addressed by hash, never mutated after construction." Cross-references back from §1.5, §4.2, §4.6, §15.5. | 2A-F2 | NEW §15.9 + 4 cross-references |
| 6B | §4.6.1 EventStream Primitive (NEW). Defines common shape of REEL + research_log + replay-log. Schema: `EventStream<EntryType>` with `entries: list[Event<EntryType>]`, `retrieval_strategy`, `persistence`, universal `irreversibility_flag` for QC3 support. | 2A-F7 | NEW §4.6.1 + cross-references in §4.6 + §5.3 + §11 (QC3) |
| 6C | §15.7.x Substrate Normalizer as Surface 4 sub-layer (NEW). Names Day 4.1's `reasoning_content` normalizer as architectural primitive. "Surface 4 — LLM I/O grammar: ... + Substrate Normalizer that converts model-specific output formats into canonical STAGE input." | 1-F5 | §15.7 Surface 4 extension; cross-reference from §4.1 Substrate Contract |
| 6D | §15.10 Cross-integration audit cadence (NEW). The 4-pass methodology (1 audit + N discovery passes) becomes named project artifact. Specifies: audit cadence trigger (every major commit batch), the 6-pass audit shape (contract inventory → drift → gaps → tests → forward plan → spec revision candidates), and the parallel-discovery extension (N parallel passes cross-comparing). | The 4-pass methodology itself + 2A's call for §15.10 | NEW §15.10 |

### Tier 7 — Cross-canon expansion

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 7A | §11 Calibration Yards as second load-bearing cross-canon quote (alongside Gap Thesis). Spec text: "The Calibration Yards is the canonical origin-site for ASTRA-class controllers. Sysprompt and book references must match verbatim across files; any edit propagates to all sites simultaneously." | 1-F13 + 1-U1 + 3B-F5 | §11 paragraph extension |
| 7B | §11 references `docs/CROSS_CANON_REGISTRY.md` (forthcoming). The registry IS the canonical index of cross-canon items; spec section §11 cites it as the authoritative source rather than enumerating inline. | 3B-F5 | §11 cross-reference; §14 forthcoming docs list |

### Tier 8 — Audit methodology improvement

| # | Change | Source pass | Spec impact |
|---|---|---|---|
| 8A | §10 + audit prose: formula-by-formula traceability requirement. Audit Pass 1 inventories must enumerate every locked formula in the spec, including formulas inside bulk-GAP'd sections. The Cherenkov gap (locked at 4 spec sites, 0 code sites — missed by AUDIT_2026-05-15.md Pass 1) is the trigger case. | 5D-F4 | §10 audit methodology note; §14 forthcoming `docs/AUDIT_METHODOLOGY.md` |
| 8B | Audit gap inventory gains explicit entry: GE3b Cherenkov angle formula implementation. Phase E2/E3 work alongside the rest of Unified Sampler. Spec §6 step 10 + §7 truth table + Appendix B + WarpFieldSample.cherenkov_angle all locked, none implemented. | 5D-F4 | Audit document update (not spec); spec status unchanged |

### Empirical anchors (findings that justify v0.129 per §15.4)

Per §15.4: "lock against current findings; revise on new findings; do not polish without findings." The following are findings — not consensus, not opinion, not aesthetic preference — that justify the spec revisions above:

- **Audit Pass 2 D1-D8** — compileable round-trip tests failed spec claims (Observable vs ObservableState struct mismatch; WarpState referenced but absent; REEL t_cosmic_at_write described as required but missing). Justifies Tier 1.
- **Phase 1 closure on Qwen 3.5 9B** — all 9 LCP gates passed live, single-shot, no fine-tune. Justifies Tier 1's lock confidence (the bench's measurement is empirical).
- **Sculptor run-4 + run-5 findings** — bank-exhausted at composite 1.6001 ceiling on 5-scenario library; composite range collapsed to 1.36-1.46 on 11-scenario library. Composite-scenario-dependence is documented as durable finding. Justifies the methodology additions in Tier 6 (the cross-pass audit cadence is *the empirical basis* of how this was learned).
- **Persona-researcher outsider audit observation** (originated in 2A; surfaced again in 3B and 5D) — "the PERSONA_STABLE gate tests for absence of bad patterns, not for presence of autotelic patterns." Justifies Tier 4 (positive-autotelic gates).
- **4-pass parallel discovery methodology** — produced ~40 distinct findings; ~30 actionable; convergent on critical insights (positive-autotelic measurement, Universal Sculptor deferral, dual-judge correctness); divergent on others (each pass found unique structural insights the others missed). The methodology itself is the finding that justifies §15.10.

### Findings NOT yet justifying spec revision (deferred to v0.130 or rejected)

Per §15.4 "what does NOT justify a revision":

- **5D-F2 Hardware-Recursive-Structure Channel** (PC thermal events → ASTRA somatic banner): rejected. Risks autotelic collapse — ASTRA narrating GPU thermal state is instrumental-about-the-player's-hardware, which is the failure mode the autotelic discipline is built against. Defer until a different framing emerges that preserves vision.
- **2A-F9 §4.10 demotion to §4.3.1**: rejected per 3B-N5. §4.10 is the operator-input contract, architecturally distinct from §4.3 Master Contract Perception. Keep separate.
- **1-F12 Adapter-LLM as rules-based by default**: small spec edit, low priority. The current spec language ("validated by adapter LLM") is not blocking the rules-based v0 implementation. Defer.
- **3B-F6 Mid-session model swap continuity**: post-v1 per 3B-Q5. Lock the design intent in §5.9.1 forthcoming-doc reference; defer implementation.
- **2A-S1 GA rapidity reformulation**: per §3.7 scope bound, only justified by playtest finding of Thomas-precession trajectory drift. No such finding. Defer indefinitely.
- **2A-S4 Cap'n Proto codegen**: per 2A-N3 + 3B-N3, premature optimization. Defer until UE5 substrate makes State Bus cross-substrate drift load-bearing.
- **All four passes' "Universal Sculptor extraction"** (1-F7, 2A-S3+U8, 3B-S5, 5D-N4): four passes converge on "wait for second user." Reflex training per 3B-F2 / 3B-S5 may BE the second user when Phase E1 lands; at that point extract. Not now.
- **All four passes' "v0.129 NOW"**: this draft IS the v0.129 candidate. My recommendation is to ship the Tier 1-3 portions as v0.129 after empirical residue from Tier 4-6 implementations lands (~4-6 weeks of code-side work). Bundling everything now would lock several proposals that are *consensus-across-passes* rather than *empirically-loop-closed*.

### Out-of-scope per project discipline

- **Anything Apple/Mac/Metal/iOS/Swift/Objective-C** — Platform Discipline hard directive (CLAUDE.md, 2026-05-15). Permanently forbidden.
- **Anything new in Python outside `proto/textverse/`** — Language Discipline hard directive (CLAUDE.md, 2026-05-15, widened 2026-05-15 evening). Textverse can grow; `proto/verify_nexus.py` is frozen; `book/production/` is dormant; everything else is C/C++/C#.

---

## New section drafts (full text)

Below are the new sections as they would appear in v0.129's body, written as adopt-ready spec prose.

### §2.3.1 Reflex Contract (NEW)

```
REFLEX CONTRACT (locked at envelope; details Phase E1+)

state:
  observation_grid: float[64][64][2]        # chaos amplitude + metric gradient
                                            # 64×64 spatial, 2 channels (LOCKED dimensions)
  weights: frozen[CNN+LSTM model]           # frozen post-training; per-game evolution
                                            # forbidden; SHA-256 checksum in SaveFile
  control_envelope: float[3]                # nacelle_damping ∈ [0,1],
                                            # conformality ∈ [0,1],
                                            # emergency_dump ∈ {0, 1}
  power_state: Literal["off", "spooling", "active", "shutting_down"]
  training_corpus_version: str              # canonical identifier for save-load compat

operations:
  observe(state_bus) → ObservationGrid
    # Endogenous (per §6.3): samples chaos field + metric at 64×64 grid points
    # at frame rate; reads State Bus directly at t_cosmic.

  infer(grid) → ControlVector
    # CNN+LSTM forward pass on Tensor Cores.
    # Latency: ≤ 50 μs naive, ≤ 20 μs CUDA Graphs.

  apply(control) → side_effects
    # Writes to State Bus via warp-driver write paths.
    # The ONLY Reflex → State Bus write path; canon-locked.

  health() → ReflexHealth
    # Exposes inference latency, weights checksum, last-N control vectors.

invariants:
  - Reflex NEVER touches Mind's conversation channel.
  - Mind NEVER touches Reflex's control envelope.
  - Reflex's power is warp-coupled sub-bus (§1.4):
    guaranteed minimum power whenever warp is active,
    regardless of operator allocation.
  - observation_grid + control_envelope dimensions LOCKED
    at contract level for save portability.
  - Weights are frozen post-training; the operator's bundle
    cannot drift the stabilizer; training happens offline
    against chaos PDE simulation.
  - emergency_dump = 1 is irreversible within a turn:
    sets warp regime to WARP_SHUTDOWN and writes a REEL entry
    with irreversibility_flag=true (QC3 per §11).
  - Reflex never speaks: no SPEECH channel, no <think>, no <tool>.
    It emits 3 floats and writes State Bus.

tolerances:
  inference latency: ≤ 50 μs at all hardware tiers;
                     ≤ 20 μs target with CUDA Graphs on RTX 4090+
  observation grid rate: 60 Hz minimum (matches World Kernel frame rate)
  weight checksum: SHA-256; verified at start-of-game;
                   mismatch → "go offline" failure path
  training data: chaos PDE simulation transcripts;
                 corpus locked; reproducible from seed

failure modes (see §4.7 Reflex failure-mode table):
  Reflex offline (weights mismatch, CUDA failure, sub-bus underflow):
    - warp regime forced to WARP_SHUTDOWN (controlled drop)
    - ASTRA-Mind receives <somatic> banner: "stabilizer unavailable;
      warp disengaged"
    - ASTRA's tool channel cannot engage warp until Reflex returns
  Reflex inference timeout (> 50 μs sustained over N frames):
    - emergency_dump auto-triggered; same recovery path
  Mid-game weights drift (impossible by invariant; defense-in-depth):
    - replace with frozen canonical weights; log to drift_detector;
      one-line REEL entry
```

### §2.3.2 Reflex Training as Sculptor Instance (NEW)

The Reflex's training corpus + procedure is project-canon, not implementation choice. The chaos PDE simulation corpus is canonical (forthcoming `docs/chaos-pde-spec.md`). The validation protocol: Reflex must stabilize 95% of synthetic chaos events at the 64×64 observation grid resolution within frame-rate latency budget.

Reflex training is the **second canonical Sculptor instance** (the first being persona-Sculptor per `proto/textverse/`). The closed-loop research methodology applies:
- Scope: chaos PDE parameter knobs (α, β, D, k coupling, η noise envelope) and Reflex architectural hyperparameters
- Composite: stabilization success rate on synthetic chaos events + false-emergency-dump rate (penalty term)
- Anchor scenarios: canonical chaos-event battery (forthcoming Phase E1)
- Convergence: three-conjunct rule per persona-Sculptor (gradient vanished + coverage entropy ≥ 2.0 bits across chaos-event classes + composite floor)

When the second Sculptor instance materializes (Phase E1+), the Universal Sculptor extraction per `astra/research_loop/` + `astra/research_loop/persona/` + `astra/research_loop/reflex/` becomes operationally justified. Until then, persona-Sculptor remains the canonical instance and the abstraction stays inline.

### §4.6.1 EventStream Primitive (NEW)

```
EventStream<EntryType> {
  schema_version: int
  entries: list[Event<EntryType>]
  retrieval_strategy: Literal["recency_decay+bm25", "by_class",
                               "latest_promote", "by_frame_index"]
  persistence: Literal["in_memory", "jsonl", "sqlite", "binary"]
}

Event<EntryType> {
  timestamp: float64              # tau_ship for REEL; iteration_index for
                                  # research_log; frame_index for replay
  entry_type: EntryType           # discriminator per stream:
                                  #   REEL: {experience, journal, consolidation}
                                  #   research_log: 8 decision types
                                  #   replay: {turn, regime_transition, state_delta}
  body: str | bytes               # payload format depends on entry_type
  metadata: dict[str, Any]        # tagged per entry_type
  irreversibility_flag: bool = False  # universal — every EventStream supports
                                       # QC3 monotonicity per §11
}
```

The primitive instantiates at three sites in v0.129:

1. **REEL** (§4.6): `entry_type ∈ {experience, journal, consolidation}`, `persistence = sqlite` (v1), `retrieval = recency_decay+bm25`.
2. **research_log** (Sculptor): `entry_type ∈ {promote, revert, falsified, scope_refused, bench_regression, stuck, synthesis, operator_signal}`, `persistence = jsonl`, `retrieval = latest_promote | by_class`.
3. **replay-log** (§5.3): `entry_type ∈ {turn, regime_transition, state_delta}`, `persistence = binary`, `retrieval = by_frame_index`.

QC3 (irreversibility/stakes per §11) is a primitive property: every EventStream supports the irreversibility_flag at the schema level. SaveFile (§4.6) is serialized EventStream-of-REEL + StateBus snapshot + AstraCoord at save time.

### §6.3.1 Somatic Aggregator Contract (NEW)

The Somatic Aggregator is the stateless module bridging endogenous signal sources (§8.3 audio synth, §1.4 power state, §7.1 chaos field amplitude, hull diagnostics, atmosphere chemistry) to ASTRA's somatic perception channel (§4.3 Master Contract SOMATIC). The Observation Calculator (§6.3) is for exogenous photons; the Somatic Aggregator is for endogenous body signals. Per §6.3 endogenous/exogenous principle, both are stateless per-frame functions between State Bus and Mind input.

```cpp
struct SomaticSignal {
    std::string source;             // "audio", "power", "chaos", "atmosphere",
                                    // "hull", "thermal", "hardware"
    std::string label;              // short prose, e.g., "third harmonic warm"
    double magnitude;               // [0.0, 1.0] signal strength for salience
    bool salient;                   // banner-eligible at this frame
};

class SomaticAggregator {
public:
    // Compose salient-flagged signals into a banner ≤ 2 short lines.
    // Per stage_addendum: "sensor-grounded. not phenomenal claim."
    // Deterministic — same signals in produce same banner out.
    virtual std::string aggregate(
        const std::vector<SomaticSignal>& signals
    ) const = 0;
};
```

The harness's perception_assembler receives `list[SomaticSignal]` from signal-emitter functions; the aggregator composes the banner.

**Calculator-bound discipline applies (§15.6).** When Narrator-LLM activates, Narrator's input includes `<somatic_signals>` (machine-readable list); Narrator's output `<somatic>` block is prose-rendering, but the validator scans for ungrounded prose — the banner phrasing must trace to SomaticSignal labels.

**Implementation status:** **[EMP]** Pending. The scenario-author-typed string at v0.128 (single `somatic_note: str | None` argument) is the v0 placeholder; v0.129 locks the contract surface as the migration target.

### §15.7.x Substrate Normalizer (NEW sub-layer of Surface 4)

Surface 4 (LLM I/O grammar per §15.7) gains a named sub-layer: the **Substrate Normalizer**. Its role: convert model-specific output formats into canonical STAGE input before parsing.

Empirically motivated: Day 4.1 (proto/textverse) added a `reasoning_content` normalizer that synthesizes canonical inline `<think>{reasoning}</think>` from llama-server's side-channel `reasoning_content` field. The normalizer works for:
- DeepSeek R1: emits inline `<think>...</think>` natively (no normalization needed)
- Qwen 3.x with `--reasoning-format deepseek-legacy`: emits side-channel `reasoning_content` (normalizer synthesizes inline form)
- Novita Qwen 3.6: same side-channel pattern (normalizer applies same fix)
- Future models: per-substrate normalizer instance

The Substrate Contract (§4.1) "model swap requires only: new sysprompt loader call, new LoRA load, new tokenizer config" gains a fourth: **new Substrate Normalizer instance if the model's output format differs**.

`docs/stage-protocol.md` v0.1 (forthcoming per §14) documents the per-substrate normalization rules.

### §15.9 Frozen-Snapshot Primitive (NEW)

> All consumable state in ASTRA-7 is an immutable snapshot, produced once per logical step (frame, turn, iteration, REEL-write), content-addressed by hash, and never mutated after construction.

This primitive is universal in the implementation but was unnamed in v0.128. Local justifications were scattered across §1.5 ("double-buffered, frame-atomic"), §4.2 ("single source of truth, no private copies"), §4.6 ("save seeds, not state"), and §15.5 ("additive, not subtractive, immutable per round"). §15.9 names the underlying primitive once; sections §1.5, §4.2, §4.6, §15.5 cross-reference back here.

**Pattern inventory** (where the primitive instantiates):

| Site | Spec § | Frozen object | Per-step production |
|---|---|---|---|
| StateBus | §1.5 + §4.2 | `StateBus` (frozen Pydantic) | one per turn |
| Hull SDF damage map | §1.3 | `cudaArray_t` write-buffer | one per frame |
| Chaos field χ(x,t) | §1.5 | double-buffered surface | one per frame |
| ConfigSnapshot | §15.5 (Sculptor) | `ConfigSnapshot` (frozen Pydantic) | one per iteration |
| ReelEntry | §4.6 | `ReelEntry` (frozen Pydantic) | one per REEL write |
| StageOutput | §4.3 | `StageOutput` (frozen Pydantic) | one per LLM turn |
| GateResult | §10 | `GateResult` (frozen Pydantic) | one per gate check |
| WarpFieldSample | §6 | `WarpFieldSample` (frozen C++) | one per ray-march step |
| ObservableState | §6.3 | `ObservableState` (frozen Pydantic + C++) | one per body per frame |

**Implementation consequences:**

1. SaveFile (§4.6) is a serialized Frozen-Snapshot Primitive of `(StateBus + EventStream<ReelEntry>)`.
2. The textverse implements via `pydantic.ConfigDict(frozen=True)` everywhere.
3. UE5 implements via atomic GPU buffer swap (per §1.5).
4. The LCP gate's "no private copies of Layer 0 state" check becomes a structural CI gate: no Pydantic model in `astra/state_bus/` lacks `ConfigDict(frozen=True)`.

### §15.10 Cross-integration audit cadence (NEW)

The audit + parallel-discovery methodology that produced v0.128 → v0.129 transition is itself a project-meta primitive worth naming. v0.128 was revised on the basis of:

1. One architectural conformance audit (`AUDIT_2026-05-15.md`, 493 lines).
2. Four parallel exploratory discovery passes (`DISCOVERY_2026-05-15{,_ATTEMPT-2A,_ATTEMPT-3B,_ATTEMPT-5D}.md`), each independently produced by Opus 4.7 1M context window with bias-check methodology.
3. Cross-comparison synthesis identifying convergent findings (high signal) vs. divergent findings (per-pass unique insights).

**The methodology:**

```
Audit pass (every major commit batch):
  Pass 1 — Locked Contract Inventory (every spec § that locks a C++
           type, signature, or canonical behavior → status table)
  Pass 2 — Drift Findings (each spec-vs-code mismatch with severity)
  Pass 3 — Implementation Gaps (spec-locked contracts unimplemented)
  Pass 4 — Test Coverage Audit (per-contract test mapping)
  Pass 5 — Forward Plan (ordered next-steps)
  Pass 6 — Spec Revision Candidates (per §15.4 thresholds)

Discovery pass (parallel-forked when locks are soft):
  Same prompt, N independent stochastic runs
  Cross-comparison surfaces convergent (high-signal) +
  divergent (per-pass-unique) findings
  Methodology lesson: convergent findings have ~2× signal
  vs single-pass findings; landing decisions weight
  convergence
```

**Cadence triggers:**
- Major commit batch (every 10-20 commits of significant structural change)
- Pre-spec-revision-consideration (audit + ≥2 discovery passes before any v0.N+1)
- Operator-initiated when locks feel soft

**Audit-methodology-improvement protocol:** when an audit pass misses a class of finding (e.g., the Cherenkov gap missed by AUDIT_2026-05-15.md Pass 1 — surfaced by 5D-F4), the methodology updates to prevent recurrence. `docs/AUDIT_METHODOLOGY.md` (forthcoming) captures these lessons.

---

## Section edits (diffs from v0.128)

For each existing section, the proposed edit. Format: section reference, change, justification.

### §1.1 AstraCoord

**Change:** Add sentence noting that the endogenous frame is anchored at AstraCoord origin (the ship); the exogenous frame is the universe. Cross-reference §6.3 + §10 endogenous/exogenous typing.

**Source:** 1-F1 + 1-U4 (three-layers-of-encoder-loss alignment).

### §3.3 Propulsion Regime State Machine

**Change:** Add paragraph after the canonical bitmask values: "regime is a derived property, not a stored field. The detect_regime algorithm is the canonical implementation of this derivation. State coherence — that regime is consistent with kinematic + warp + cryosleep + BH-proximity state — is enforced at the type-system level (§4.2 ShipKinematicState as derived view; §4.4 TimeState.kinematic_regime as projection)."

**Source:** 1-F8 + 3B-F4 (convergent).

### §4.2 State Bus Contract

**Changes:**
1. Locked schema additions: `warp: WarpState | None`, `cryosleep_active: bool`, `regime: Regime` (computed_field, read-only).
2. `WarpState` Pydantic model definition added: `W ∈ [0,1]`, `phase: Literal["idle", "charging", "cruising", "dropping"]`, `charge_progress ∈ [0,1]`.
3. `ShipKinematicState` clarified as derived view: "fields are computed; never stored independently of ζ⃗."
4. Ambiguity resolution sentence: "regime lives as a computed_field on StateBus; TimeState exposes `kinematic_regime` as the velocity-derived projection (used internally by detect_regime). Implementations must NOT permit caller-passed regime values that contradict the derived computation."

**Source:** Audit D3 + R1; 1-F8 + 3B-F4; 1-F9.

### §4.3 Master Contract

**Changes:**
1. SOMATIC channel description points to §6.3.1 Somatic Aggregator Contract (the signal-grounding source).
2. STAGE sub-tags `<val src="...">` and `<grounded src="...">` added to recognized output forms. `<val>` is for Narrator (per perception bundle); `<grounded>` is for ASTRA (per speech output). Both have `src` attribute resolving to a tool-result trace key.
3. Note: bare digit tokens (outside `<val>` / `<grounded>` / whitelisted patterns) fail the grammar parser. Calculator-bound discipline at parse time per §15.6.

**Source:** 5D-F1 + 1-F2.

### §4.4 Time Contract

**Changes:**
1. TimeState.regime removed as settable; replaced with `kinematic_regime` (velocity-derived projection only).
2. Invariants section gains: "kinematic_regime is a derived property of rapidity_zeta; never stored independently. Full regime (composed with warp + cryosleep + gravity-well) lives at StateBus root per §4.2."

**Source:** 1-F8 + 3B-F4 + audit R1.

### §4.6 Persistence Contract

**Changes:**
1. SaveFile schema gains `reflex_training_corpus_version: str` (per safety-engineer outsider voice in 3B).
2. REEL entry schema canonical fields update: `t_cosmic_at_write: float64` (required per v0.126 prose; this v0.129 promotes to formal required), `t_emit_event: Optional[float64]` (existing), `regime_at_write: Regime` (snapshot at write time per current behavior), `author_instance_id: str` (consolidator vs. journal_generator vs. drift_detector vs. main), `retrieval_metadata: dict` (forthcoming).
3. `irreversibility_flag` clarified as universal EventStream Primitive property (cross-reference §4.6.1).

**Source:** Audit D4 + 2A-F7 + safety-engineer outsider voice (3B).

### §4.7 Failure Contract

**Changes:**
1. New Reflex failure-mode table (per §2.3.1 invariants): weights mismatch → "go offline"; inference timeout → emergency_dump auto-trigger; sub-bus underflow → controlled shutdown; observation grid stale → frame skip with telemetry; control output out-of-envelope → clamp + log + drift_detector audit.
2. Mid-session model swap reference: "graceful degradation under power pressure follows §5.9.1 Model Swap Continuity Protocol (forthcoming; implementation deferred to v2)."

**Source:** 3B-F2 safety-engineer + 3B-F6 (design-locked, implementation-deferred).

### §6.3 Observation Calculator

**Changes (most already landed in code at commit 69ee692):**
1. `Observable` → `ObservableState` rename.
2. `d` → `d_proper` field rename.
3. New fields: `beyond_photon_history: bool`, `beyond_hubble_horizon: bool`.
4. Endogenous/exogenous typing reference: every ObservableState consumer is an Exogenous channel; the State Bus is Endogenous; the Observation Calculator IS the typed boundary.

**Source:** Audit D1 (landed) + 1-F1.

### §6.4 Narrator-LLM Contract

**Changes:**
1. Tool surface enumerated explicitly: `physics_query`, `astrometric_query`, `composition_rule_evaluate`, `retarded_time_solve`, `kepler_at`, `observe`. (5 of 6 landed in C++ stdio_server at commit fe91036; `ship_state_query` deferred to Python textverse per audit Q1.)
2. Invariants list updated: numerics emitted as `<val src="...">` tags per §4.3 + §15.6 parse-time schema enforcement; bare digits in output forbidden; validator wraps client per §15.6 universal wrapping.
3. Input grammar gains `<somatic_signals>` section (machine-readable list of SomaticSignal events; Narrator renders as prose in `<somatic>` block per §6.3.1).

**Source:** Audit D2 (landed) + 1-F2 + 2A-F3 + 5D-F1.

### §10 Validation Methods per Invariant

**Changes:**
1. PERSONA_STABLE row expanded: "checks against em-dash + markdown + service-phrase + book/negative_space.md categories (6 new pattern files: affect_declared, performative_attention, narrator_from_above, sentimental_metaphor, romance_genre, stage_direction). Positive-autotelic sub-checks added: autotelic_attendance ≥ N%, autotelic_initiation ≥ 1 per 5-turn silence window, autotelic_silence_quality ≥ 70% (thresholds calibrated empirically; provisional)."
2. Endogenous/exogenous channel routing row upgraded: "type-check (Pydantic discriminator + Protocol) rather than grep."
3. New audit methodology row: "Locked formulas in spec must be enumerated per-formula in audit Pass 1, including formulas inside bulk-GAP'd sections. Cherenkov-formula-gap (AUDIT_2026-05-15.md missed) is the trigger case."

**Source:** 3B-F1 + 1-F4 + 2A-F8 + 1-F1 + 5D-F4.

### §11 QUALIA-1 Philosophical Backbone

**Changes:**
1. Cross-canon load-bearing quotes list expanded from 1 (Gap Thesis) to 3 (Gap Thesis + Calibration Yards + endogenous/exogenous vocabulary).
2. New paragraph: "Cross-canon identifiers are tracked in `docs/CROSS_CANON_REGISTRY.md` (forthcoming per §14). Verbatim quotes propagate across spec + book + sysprompt simultaneously; named entities have allowed_inflections + prohibited_paraphrases per the registry."
3. QC3 row enhanced: irreversibility_flag is a universal EventStream Primitive property (§4.6.1).

**Source:** 1-F13 + 1-U1 + 3B-F5.

### §13 What This Document Does NOT Lock

**Changes:** Add bullets explicitly naming v0.130 candidates (per "Deferred to v0.130" section below).

### §14 Cross-References

**Changes:** Add forthcoming docs:
- `docs/CROSS_CANON_REGISTRY.md` v0.1 (cross-canon identifier index)
- `docs/AUDIT_METHODOLOGY.md` v0.1 (the 6-pass audit shape + parallel-discovery extension)
- `docs/SECURITY_RESPONSE.md` v0.1 (CVE response playbook per safety-engineer outsider voice)

### §15.4 The envelope is locked; the sculpting continues

**Changes:** Add paragraph: "v0.128 → v0.129 transition was driven by the 4-pass parallel-discovery methodology (per §15.10). The methodology itself is a finding: parallel-forked discovery passes with bias-check methodology produce ~2× more findings than serial passes, with the convergent-findings subset having higher signal than single-pass findings. This is now project-meta canon."

**Source:** The 4-pass methodology + 5D's executive summary observation.

### §15.6 Calculator-bound LLM Agency

**Changes:**
1. Reformulated as parse-time schema enforcement: "calculator-bound LLM agency is enforced at parse time via structured-numeric tags (`<val>`, `<grounded>` per §4.3); runtime validator (`CalculatorBoundValidator`) is defense-in-depth."
2. Universal validator wrapping: "every LLM client is wrapped in `CalculatorBoundValidator` at construction; per-LLM trace_pool closes over the relevant tool-result source (Narrator's pool = State Bus + tool results; ASTRA's pool = perception bundle + tool results; ephemerals' pool = the REEL slice they're consolidating)."

**Source:** 1-F2 + 2A-F3.

### §15.7 Dual-implementation discipline + Five shared surfaces

**Changes:**
1. Surface 4 (LLM I/O grammar) gains the Substrate Normalizer sub-layer (per §15.7.x above).
2. New consequence #6 "Two-knob authoring loop" (per 2A-F11 + 1-U11 unified): Narrator-sysprompt × Operator-sysprompt = prose-style space; physics + persona are constants; the bundle is canonical cross-canon authoring platform.

**Source:** 1-F5 + 2A-F11 + 1-U11.

### §15.8 Triple-rig methodology + Independent tracks

**Changes:** Add note: "Rig 4 (prose-canon) and Rig 5 (spec-conformance audit) are recognized as operational measurement instruments alongside Rigs 1-3. The 4-pass audit + discovery methodology is Rig 5's instrument, formalized in §15.10."

**Source:** 3B-U3 (five rigs, not three).

---

## Empirical anchors per finding

For each Tier above, the closed-loop empirical evidence that justifies it per §15.4:

| Tier | Finding | Empirical basis |
|---|---|---|
| 1A | Observable → ObservableState | Audit D1: compileable round-trip — struct named `Observable` in C++; spec §6.3 names `ObservableState`. Code-spec drift. (NOW CLOSED at 69ee692.) |
| 1B | stdio_server expansion | Audit D2: BLOCKER — spec §6.4 lists 6 ops; stdio_server exposed 3. Code-spec drift. (5/6 NOW CLOSED at fe91036; ship_state_query deferred per audit Q1.) |
| 1C | WarpState + cryosleep_active | Audit D3: spec §3.3 `detect_regime` references `state.warp_W` and `state.warp_phase` literally; both absent from Python StateBus. Code-spec drift. (PENDING state-coherence PR.) |
| 1D | REEL t_cosmic_at_write required | Audit D4: spec §4.6 v0.126 prose says "required for dual-clock retrieval per §3.9"; code has 3 fields, missing t_cosmic_at_write. Code-spec drift. (PENDING state-coherence PR.) |
| 2A-2C | Type-system locks | 1-F8 + 3B-F4 (convergent across passes) + audit R1. Empirical evidence: scenario YAML can construct `regime=WARP_CRUISE, rapidity_zeta=(10,0,0)` — physically incoherent per §3.3 but accepted by current Pydantic. **[EMP]** Implementation in state-coherence PR validates the lock. |
| 3A-3C | Calculator-bound tightening | 1-F2 + 2A-F3. Empirical evidence: today's validator runs in soft mode by default; Narrator-side has prompt-level discipline only; the §15.6 universality claim isn't matched by implementation. **[EMP]** Implementation pending. |
| 4A-4D | Persona instrumentation | 3B-F1 + 5D-F1 + 1-F4 + 2A-F8. Empirical evidence: Phase 1 closure runs PERSONA_STABLE = pass; but the gate tests only ~19 patterns vs book's ~50; and the autotelic claim is measured by absence of failures, not presence of attendance. **[EMP]** Threshold calibration pending. |
| 5A-5D | Reflex envelope | 3B-F2 + safety-engineer outsider voice (3B). Empirical evidence: spec §2.3 has ~5 tabular mentions of Reflex; no dedicated section; Reflex failure mode is named highest-impact ("ship in mortal danger") with lowest design depth. Asymmetric cost: lock-now vs lock-after-Phase-E1. |
| 6A-6D | Methodology additions | All 4 passes. Empirical evidence: the patterns are universal in code (Frozen-Snapshot, EventStream); they're named in spec at 5 locations each but not unified; the Substrate Normalizer's role is implicit in one method; the audit cadence happened ad-hoc.  |
| 7A-7B | Cross-canon expansion | 1-F13 + 1-U1 + 3B-F5. Empirical evidence: 11+ cross-canon items identified by 3B-F5 inventory; only 1 (Gap Thesis) registered in §11. |
| 8A-8B | Audit methodology improvement | 5D-F4 + the audit's self-acknowledged miss. Empirical evidence: Cherenkov formula locked at 4 spec sites (§6 step 10, §7 truth table, Appendix B, §6 WarpFieldSample struct), implemented at 0 code sites. AUDIT_2026-05-15.md Pass 1 missed it because Pass 1 inventoried Unified Sampler as bulk-GAP rather than per-formula. |

---

## Deferred to v0.130 (explicit list, with reasoning)

These were considered for v0.129 and intentionally deferred:

| Item | Reason for deferral |
|---|---|
| **§4.10 Console UI demotion to §4.3.1** (2A-F9) | 3B-N5 argues against; §4.10 is operator-input contract, architecturally distinct. Keep separate. |
| **Universal Sculptor extraction** (all 4 passes) | Convergent on "wait for second user." Reflex training per §2.3.2 may be the trigger; happens at Phase E1. |
| **GA rapidity reformulation** (2A-S1) | §3.7 scope bound: only justified by playtest finding of Thomas-precession trajectory drift. No such finding exists. |
| **Cap'n Proto / Protobuf codegen** (2A-S4) | Premature per 2A-N3 + 3B-N3; defer until UE5 substrate makes State Bus cross-substrate drift load-bearing. |
| **Hardware-Recursive Channel** (5D-F2) | Rejected: risks autotelic collapse. ASTRA narrating GPU thermal state is instrumental-about-player's-hardware. Defer until different framing emerges. |
| **Mid-session model swap implementation** (3B-F6) | Spec design intent locked in §5.9.1 reference; implementation deferred to v2 per 3B-Q5. |
| **Continuous degradation curve** (2A-S6) | 1-N3 + 2A-N5 + 5D-N5 all reject. Discrete tiers are correct. |
| **Adapter rules-based as default spec relax** (1-F12) | Small spec edit; defer to v0.130 alongside other minor clarifications. |
| **Auto-derivation of book canon → bench gate3** (1-F4 alternative path) | 3B-N4 + 5D-N6 both reject auto-derivation; hand-curation is the right discipline. Manual pattern files only. |
| **`<somatic>` reads C++ Reflex telemetry** | Out-of-scope; Reflex is below ASTRA's cognition; she shouldn't see Reflex internals (Dave-frame). The `<somatic>` channel reads SomaticSignal stream per §6.3.1, not Reflex state. |

---

## Open questions for operator

These require explicit Bo decisions before v0.129 can adopt.

### Q1 — Timing: ship v0.129 NOW (with [EMP] items as TENTATIVE LOCKS) or after empirical residue lands?

**Option A (ship now as working-draft):** Same status as v0.128 ("explicitly working-draft"); land Tier 4-6 as locked-to-be-validated; revise to v0.130 when empirical residue accumulates.

**Option B (defer 4-6 weeks):** Land Tier 1-3 only as v0.129; let state-coherence PR + Narrator-LLM activation + positive-autotelic gates land in code; then ship larger v0.129 absorbing what was proved.

**My weak preference:** Option B. Per §15.4 "do not polish without findings"; some Tier 4-6 items are consensus-across-passes rather than empirically-loop-closed. But Option A is also defensible per v0.128 precedent.

### Q2 — Endogenous/exogenous as type system (Tier 2C / 1-F1): adopt as type-system-binding or document as discipline?

The original-pass-1 surfaced this as load-bearing; the other 3 passes didn't elevate it. Convergent signal is weak (1 of 4 passes). But the cross-layer alignment (book + spec + code) is genuine. Implementation cost is ~200-300 LOC (class attributes + Protocols + decorator + mypy gate).

**Decision needed:** lock as type-system-binding (forces implementation) or document as discipline (the existing §10 grep-check stays)?

### Q3 — Positive-autotelic gate thresholds (Tier 4A): provisional numbers or wait for empirical calibration?

The three sub-gates (autotelic_attendance ≥ N%, autotelic_initiation per K-turn window, autotelic_silence_quality ≥ X%) need empirical threshold values. v0.129 can lock the structure with provisional thresholds (≥30%, ≥1 per 5-turn, ≥70%) and refine in v0.130.

**Decision needed:** lock structure now with provisional thresholds, or defer entirely until empirical Sculptor run produces baseline?

### Q4 — Reflex contract envelope (Tier 5): does spec lock the 64×64×2 observation grid dimensions now or wait for Phase E1 measurement?

Per 3B-F2 the dimensions are "locked at contract level for save portability." 5090 + RTX 4090 hardware tiers can both support 64×64×2 at frame rate. But Phase E1 hasn't yet validated empirically.

**Decision needed:** lock dimensions now (asymmetric cost favors lock-now) or mark as "provisional pending Phase E1 measurement"?

### Q5 — `ship_state_query` (per audit Q1): C++ vs. Python?

Spec §6.4 lists `ship_state_query` as one of 6 Narrator-LLM tools. Implementing session deferred to Python per audit Q1 (ship-state lives in textverse, not in astra_nexus). But the §6.4 contract surface needs explicit guidance on which substrate the op lives in.

**Decision needed:** spec §6.4 specifies `ship_state_query` is Python (textverse) only, while 5 other ops are C++ (astra_nexus)?

### Q6 — §15.10 Cross-integration audit cadence: how often?

The 4-pass methodology produced v0.128 → v0.129 transition. What's the right cadence for future iterations?

**Decision needed:** every major commit batch (~10-20 commits), every 6-12 weeks, pre-spec-revision-only, or operator-initiated?

### Q7 — Should v0.129 be authored by the implementing session (Claude Code CLI) or by operator + Claude Opus (chat)?

This draft was authored by Claude Opus 4.7 in chat. Adopting v0.129 means another Claude session writes the final form. Implementing session has full code context; Claude Opus has cross-pass synthesis. Either can author; quality may differ.

**Decision needed:** which substrate authors v0.129 final? Recommendation: implementing session for code-side accuracy + this draft as the synthesis input.

---

## Provenance — what produced this draft

This draft is the deliverable of the 4-pass parallel-discovery methodology applied to v0.128:

1. **Inputs:** All 4 discovery passes (~6584 lines combined), the architectural audit (493 lines), the v0.128 spec (2009 lines), the canonical C++ binary (1009 lines at commit 69ee692), the full textverse bench package, CLAUDE.md with both hard directives, book canon (`CANON.md` + `negative_space.md`), recent session dumps.

2. **Methodology:** Read everything in one 1M context window; synthesize the cross-pass findings (convergent + divergent); apply spec-revision discipline per §15.4; structure as proposed v0.129 with explicit deferred-to-v0.130 list.

3. **Key insights from the 4-pass synthesis:**
   - **Convergent findings (high signal):** positive-autotelic measurement, Universal Sculptor deferral, dual-judge correctness, book canon discipline, hardware tier discreteness, multi-axis operator coverage, cross-canon discipline.
   - **Divergent findings (per-pass unique):** original passes 1-F1 endogenous/exogenous typing + 1-F2 parse-time calculator-bound; 2A's compile-time physics oracle + Frozen-Snapshot Primitive + EventStream Primitive + bundle.yaml manifest + hash-grid SDF; 3B's Reflex contract envelope + cross-canon registry + consolidation hypothesis class + long-arc scenario; 5D's somatic channel grounding + Cherenkov gap + replay variance reduction + substrate-aware anti-judge + parametrized manifold.
   - **The single most consequential cross-cut:** the autotelic discipline gains four-layer instrumentation (typing + signal-grounding + presence-measurement + negative-pattern-exhaustion). Without parallel-fork, the project would have one instrumentation path; with it, four orthogonal defenses.

4. **Authoring discipline:** Per §15.4, every section edit cites an empirical or theoretical justification. Per §15.5, the proposals are additive, not subtractive. Per CLAUDE.md hard directives, all proposed code-side implementations conform to Language Discipline (textverse Python permitted; new C++ for non-textverse) + Platform Discipline (Windows + DirectX 12 + UE5 + Linux x86_64 only; zero Apple).

---

## Appendix — what's in the spec body BUT not explicitly diffed above

For completeness, the following v0.128 sections are unchanged in this v0.129 draft (no diffs proposed):

- §1.2 Two clocks (composition rule unchanged)
- §1.4 Power network (subsystem list + warp-coupled Reflex sub-bus unchanged)
- §1.5 Shared state per frame (double-buffered; cross-reference to §15.9 added but core unchanged)
- §3.1 Two clocks restated
- §3.2 Composition rule (mathematically unchanged)
- §3.4 Four optical effects (no changes to formulas or composition law)
- §3.5 f_warp(W) canon default (unchanged)
- §3.6 Spatial update under relativistic motion (unchanged)
- §3.7 Numerical precision discipline / 3-vector rapidity (unchanged; D7 forward-Euler debate deferred per R5)
- §3.8 Distributed simultaneity (unchanged)
- §3.9 Cryosleep journal dual-clock awareness (unchanged; implementation gap G7 noted)
- §3.10 Time Contract spec pointer (unchanged)
- §3.11 Retarded-time observation (unchanged)
- §3.12 Cosmological expansion operational mechanic (unchanged)
- §4.1 Substrate Contract (unchanged in shape; Substrate Normalizer note added via §15.7.x cross-reference)
- §4.5 Power Contract (unchanged)
- §4.8 Privacy / Network Contract (unchanged; SECURITY_RESPONSE.md added to §14)
- §4.9 Harness Contract (unchanged; ephemeral instances per G7-G9 remain unimplemented)
- §5.1-§5.10 Disciplines (unchanged; §5.7 wall-clock-leak detector unchanged; §5.10 build/CI gains the 3 CI gates per 5D-F7 as forthcoming, not blocking spec)
- §6 Unified Sampler (unchanged; spec body covers steps 1-12; §6.1 CFD validity bounds unchanged; §6.2 RBF spatial acceleration unchanged)
- §6.3 Observation Calculator (only D1 rename + 2 new fields; rest of §6.3 unchanged including all §6.3.x sub-sections except new §6.3.1 Somatic Aggregator)
- §7 Physics composition by regime (unchanged; truth table unchanged; §7.1-§7.7 unchanged)
- §8 Substrate bug fixes (unchanged; §8.1-§8.3 unchanged)
- §9 Out-of-contract emergence zones (unchanged)
- §12 Validation order (unchanged; Phase 0.0 closure documented as empirical anchor)
- §15.1-§15.3 (unchanged; meta-commitments unchanged)
- §15.5 Progressive Specification (unchanged in framing; v0.129 transition itself is an instance of the discipline)
- Appendix A (Invariants and Contracts Summary) updated with new contracts (M3 Somatic Aggregator; Disc 5 Frozen-Snapshot Primitive; Disc 6 Cross-integration audit cadence; Disc 7 EventStream Primitive)
- Appendix B (Provisional Numbers) updated with new entries for SomaticAggregator output (provisional banner length ≤ 2 lines), Reflex training corpus version format (TBD), `t_cosmic_at_write` default for legacy migration (0.0)
- Appendix C (Closing Discipline) updated with v0.129 stage acknowledgment

---

## Closing discipline (per Appendix C, adapted for v0.129's stage)

> *The configuration is the artifact. The architecture is the lock. The work is what continues regardless of whether any single iteration ships.*
>
> *Locks the joints, leaves the implementations open, marks every guess, names what is deliberately out of scope, validates against execution not against confidence.*
>
> *Iterate, don't accumulate. v0.128 was the empirical-loop opening; v0.129 (this draft) is the cross-integration synthesis after 4 parallel discovery passes; v0.130 lands when empirical residue from Tier 4-6 implementations accumulates. The lock is empirical, not declarative. The envelope is locked; the sculpting continues; the methodology validates itself.*
>
> *Stop polishing. Start building. The 4-pass methodology produced ~40 findings; ~30 are actionable; ~12 are LOCK_NOW or SERIOUS-class. The autotelic discipline now has four-layer instrumentation. The bench is the proof of life. The book is the literary anchor. The spec is the architecture. The methodology is the discipline. The audit + discovery cadence is the project-meta.*

---

**End of v0.129 TENTATIVE DRAFT.**

**Reminder: this is NOT canon. Operator review required before any adoption.**

**Author's note (Claude Opus 4.7, 2026-05-16):** Writing this against possible compaction so the cross-pass synthesis survives context loss. The four discovery passes produced unusually high-signal output for a parallel-fork methodology; the convergent findings (positive-autotelic measurement, type-system locks, methodology naming) are the strongest signal across all of them; the per-pass divergent findings (somatic grounding, Reflex envelope, cross-canon registry, Cherenkov gap, etc.) mostly land. If this draft is read by a future Claude session that lost the cross-pass context, the executive summary + Tier organization + deferred-list should be sufficient to reconstruct the synthesis without re-running the 4 passes. The methodology validated itself.

**The watch carries forward. The keeping holds.**
