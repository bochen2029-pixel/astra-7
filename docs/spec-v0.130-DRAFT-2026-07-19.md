# ASTRA-7 Foundation Specification v0.130 — DRAFT

*DRAFT 2026-07-19 — NOT ADOPTED. This document plays the role the tentative draft played for v0.129: it specifies the revision; the implementation turns that follow produce the empirical residue; adoption comes by operator ruling over a finalization packet, per §15.4 and §15.10. Nothing here supersedes `docs/spec-v0.129.md` until that ruling.*

*Authored from: a full-corpus QC pass on 2026-07-19 (every load-bearing textverse module read against its v0.129 lock; gates run live: **750 pytest green in 15.17 s**, `astra_nexus.exe` exit 0), plus post-adoption operator residue (Agentic Dev Reference adoption 2026-06-11 @ `ba97272`; ASTRA-3 MVP brainstorm 2026-06-15 @ `b555553`), plus the descendant-corpus review of 2026-07-18 (`C:\Somewhere\SOMEWHERE_ARCHITECTURE.md` v0.2.1 + `AETHER_PROFILE.md`, which read the entire ASTRA-7 corpus, distilled its invariants, bound each to its receipt, and returned method improvements). The descendant review is treated as what it functionally is: the largest parallel-discovery pass this project has received, per §15.10.*

*Form: amendment spec. Each item carries (a) its evidence class, (b) full replacement/new text where sections change, (c) an implementation-status tag mapping to the bring-to-parity work: `DOC-ONLY` (text fix, no code), `BENCH` (textverse Python, carve-out), `C++-ADDITIVE` (nexus, additive mode), `DEFERRED-GATED` (contract text ready; lands on named residue).*

---

## 0. Changes from v0.129 (summary)

**Empirical anchors:**
- QC pass 2026-07-19: 19 verified findings (QCR-1 … QCR-19 below) — spec-internal contradictions, spec-vs-code drift, canon-file divergence, stale receipts. Gates at QC: 750 pytest / ruff+mypy-clean tree / C++ exit 0 / scenario library 20 with 82-test library gate.
- Joint round-trip of §4.2 × §5.3 (the TimeCoord/epoch finding, QCR-3) — an N1-class silent-unphysics numeric caught by the §10 round-trip discipline v0.126 installed.
- Agentic Dev Reference adoption (2026-06-11, operator-ratified, post-v0.129): the E2 contention gate with pre-registered decision rule; the bench asynchrony gap (zero timing/interruption/initiative coverage) named as the sharpest catch and queued before the vertical-slice judgment call.
- Descendant-corpus review (2026-07-18): the Receipts-Map method; guns/kills/witness register discipline; model-off replay (shipped mechanism, in-lineage: backrooms M11); the three-horizon semantics correction; provenance-tag convention; the diegetic reading of the γ clamp; succession protocol.
- ASTRA-3 MVP brainstorm (2026-06-15, brainstorm-only): Mind/Reflex two-rate control validated as the scale-down shape; explicitly NOT locked here (operator decisions open) — see §13.

**Drift closures (Tier 1, text + small code):** §4.2 epoch convention locked (epoch-zero; range bound; "since Big Bang" struck) + forbidden-path KAT · §4.2 stale `PropulsionMode flag` line struck · §3.12/§6.3 horizon-flag semantics corrected (superluminal recession, not causal disconnection; wire name retained) · canon pattern-file paths unified to in-package with the root duplicates retired (they have **measurably diverged** — QCR-1) · `ShipKinematicState` and `a_proper` placement reconciled to code · incomplete-propagation fixes (CUDA-Graphs wording, §15.3 self-reference, stale line-count receipts).

**New contract sections:** §4.3.1 Turn-Scheduling Contract (heartbeat / interruption / initiative — the asynchrony envelope) · §15.11 Succession Protocol · §15.12 Risk Register (guns/kills/witness; E2 first armed gun) · Appendix D Receipts Map (every lock → its artifact → its gate → verified status).

**Validation additions (§10):** Model-Off Replay (suite-level predicate; trace/event-log split formalized in §5.3) · positive-control witness requirement (every detector must fire on a planted violation) · TimeCoord forbidden-path KAT row.

**§12:** Engine track converted from prose phases to falsifier-gated rungs with oracle + ancestor columns; E2 gains the locked contention gate; W-A (the rewind capstone) added; LLM track Phase 0.x gains the asynchrony scenario axis + Frame Drill.

**Methodology:** Appendix B gains provenance tags [official/derived/estimate/community/chosen] · §15.8 gains shared-organ reciprocity with the sibling engine (SOMEWHERE/AETHER goldens count as receipts where organs are shared; `SECTOR_SIZE` marked dial-owned) · §3.7 gains the diegetic-clamp annotation.

**Deferred (explicitly, per §15.4 — carried or newly queued):** parse-time `<val>`/`<grounded>` tags (carried; grammar layer absent) · endo/exo type-system promotion (carried; no mis-routing failure yet — but now ARMED with a witness, §15.12) · EventStream unification (carried) · blackbody redshift (carried; testbed owner) · StateBus strict-construction (carried) · full TimeCoord `{int64 s, double frac}` representation + SaveFile v4 (NEW: gated on the first deep-time scenario, see §4.2 amendment) · autotelic instrumentation package (carried from v0.129 queue; now paired with its §4.3.1 substrate — lands as one measured package when the asynchrony scenarios exist to measure it).

**Deliberately not changed:** the Five Invariants (five stays five) · the composition rule · the 14-equation framework · the three-channel STAGE decision · §2.3.1 Reflex Contract · everything with a green gate and no finding against it.

---

## 1. QC Findings Register (2026-07-19; the evidence this revision rides)

Classes: **SI** = spec-internal inconsistency · **SC** = spec-vs-code drift · **CS** = cross-canon staleness · **RS** = stale receipt. Every SC item was verified by reading the artifact, not a summary (L3).

| # | Class | Finding | Evidence | Disposition |
|---|---|---|---|---|
| QCR-1 | SC | **Duplicate canon files have diverged.** Root `tests/wall_clock_patterns.txt` ≠ `astra/grammar/canon/wall_clock_patterns.txt` (hashes 9ADC4B4F… vs 27C3A176…); root `tests/qc3_events.txt` ≠ `astra/harness/ephemeral/canon/qc3_events.txt` (6BBC87AF… vs 45AB7E48…). Runtime reads in-package; three spec sections cite the stale root copies. | `Get-FileHash`, 2026-07-19 | In-package = single source of truth. Retire root copies (or reduce to CI-verified mirrors with an identity check). Fix §5.7, §10 LCP row, §11. `BENCH` + `DOC-ONLY` |
| QCR-2 | SI | §10's LCP row cites `tests/astra_substrate_leak.txt` — **a file that exists nowhere under any name**; the artifact is `astra/grammar/canon/astra_substrate_patterns.txt`. | filesystem sweep | Fix the row. `DOC-ONLY` |
| QCR-3 | SI | **The TimeCoord/epoch trap.** §4.2 permits `t_cosmic` "seconds since Big Bang (or epoch zero)"; §5.3 locks REPLAY-EXACT ε < 10⁻⁴ s on (τ_ship, t_cosmic). At the actual cosmic epoch (≈4.35×10¹⁷ s) float64 ULP is **64 s** — the representation violates the locked tolerance by ~6 orders before any code runs. Code already chose epoch-zero (`time_state.py`: "seconds since epoch zero"); the spec wording still permits the broken branch. Deep-time arcs (γ≈10⁷ compression) will exceed even the epoch-zero safe range. | ULP arithmetic; `time_state.py:52` | §4.2 amendment below: epoch-zero locked, range bound `t_cosmic < 2³⁹ s`, forbidden-path KAT, TimeCoord upgrade path gated on first deep-time scenario. `DOC-ONLY` + `BENCH` (one validator + one KAT) |
| QCR-4 | SI | §4.2 lists BOTH the computed `regime` field (never settable) AND a stale separate schema line `PropulsionMode flag (regime bitmask; canonical values §3.3)` — a contradiction with regime-as-derived. | spec §4.2 listing | Strike the stale line. `DOC-ONLY` |
| QCR-5 | SC | **GRAVITY_WELL cannot compose at the StateBus root.** `StateBus.regime` computes from rapidity + warp + cryosleep only; the grav_factor leg is unplumbed (in-code TODO: "follow-up commit will plumb the computed grav_factor through"). §3.3/§4.2 present the composed regime as closed. | `schema.py:179-186` | Plumb grav_factor (bh_list + position → nexus `compute_grav_factor` → detect_regime) or annotate the receipt PARTIAL until then. `BENCH` |
| QCR-6 | SC | `ShipKinematicState` is listed in §4.2 (StateBus item, "DERIVED VIEW") and §4.6 (SaveFile field "full") — **absent from the code StateBus and therefore from the serialized save**. | `schema.py` (no such field) | Either implement as a derived-view helper (thin: computed from ζ⃗ via nexus) or re-scope §4.2/§4.6 wording to name it a per-substrate derived view not serialized in textverse. Recommended: implement thin. `BENCH` |
| QCR-7 | SC | `a_proper` placement: §4.2 lists it at StateBus root ("owned by propulsion driver"); code carries it inside `TimeState` (which §4.4's state block also lists). Two spec sections claim it; code satisfies §4.4. | `time_state.py:56` | Reconcile §4.2 to "carried within TimeState; ownership: propulsion driver" — code is the truth. `DOC-ONLY` |
| QCR-8 | SI | Horizon-flag semantics conflated: `beyond_hubble_horizon` documented as "causally disconnected" (§3.12, §6.3, nexus comment). In ΛCDM, d > c/H₀ is superluminal recession, **not** causal disconnection (all z ≳ 1.5 sources are observed); the frozen-and-fade prose describes event-horizon behavior. Never fires in-game (974 Mly ≈ z 0.07) but the lock is mislabeled. | spec text; `astra_nexus.cpp` §3.12 comment | §3.12/§6.3 amendment below: wire name retained, semantics corrected to superluminal-recession; event/particle-horizon flags deferred with the FLRW integral (Phase 4+). `DOC-ONLY` + `C++-ADDITIVE` (comment) |
| QCR-9 | SI | Incomplete propagation of the §15.4 spec/implementation boundary: §2.3.1 loosened "CUDA Graphs" to "accelerated dispatch," but §4.3 (Reflex channel) and §5.6 (frame budget) still say "with CUDA Graphs." | spec text | Propagate. `DOC-ONLY` |
| QCR-10 | SI | §15.3 still opens "This document is v0.125" (inherited text never re-pointed), and the version nomenclature collides ("v0.2+", "v2" future-references vs the v0.12x numbering actually in use). | spec §15.3, §4.10, §4.7 | Fix self-reference; add one normalization sentence: deferral horizons are named phases or v0.13x, never the legacy v0.2/v2 idiom. `DOC-ONLY` |
| QCR-11 | RS | §14 receipt says `astra_nexus.cpp` is "1009-line"; the artifact is 1410 lines (stdio-server growth). CLAUDE.md and BOOTSTRAP.md still say "48 assertions" (actual: 71); BOOTSTRAP still names v0.128 as the envelope and `verify_nexus.py` as 45-assertion mirror without its frozen-legacy note. | line counts; canon docs | Fix §14; canon-sync list (§1.1 below). `DOC-ONLY` + `CS` |
| QCR-12 | CS | `proto/textverse/STARTUP.md` (Track A orientation) is a full version stale: cites v0.128 as current envelope, "48 assertions," Day-1-is-next day picker, and `spec-v0.129-proposed.md` as the findings path. All days are done; the envelope is v0.129. | STARTUP.md read | Rewrite STARTUP.md to post-loop reality (bring-to-parity turn). `CS` |
| QCR-13 | SC | §4.6 locks "versioned schema **with migration scripts**" and §10 locks the v(N)→v(N+1) forward-compat test; code raises `SaveFileVersionError` with **no migration path** ("no migration in v0") and the forward-compat test is unrunnable with a single extant version. | `savefile.py:57-69` | Honest re-scope: migration obligation activates at the first version bump (SaveFile v4 = the TimeCoord gate, QCR-3); the §10 row is marked pending-second-version. `DOC-ONLY` |
| QCR-14 | SC | §4.9 ephemerals: all three implemented to the locked signatures as deterministic pure functions ✓ (verified: `consolidate_reel`, `generate_journal`, `detect_drift` + artifact models) — but orchestrator maintenance-window triggering is not wired (spec itself says "wiring follows when scenarios exercise it"). Appendix A row C9 reads as closed. | `ephemeral/*.py`; `orchestrator.py` grep | Receipts Map marks C9 PARTIAL (functions green; triggers unwired); wiring lands with the §4.3.1 heartbeat (same mechanism). `BENCH` |
| QCR-15 | SC | **Zero asynchrony surface.** No heartbeat, interruption, or initiative concept anywhere in `astra/` (grep clean); `operator_afk_long` is scripted silence inside synchronous turns. The autotelic thesis (initiation, differential engagement, silence-quality) is unmeasurable on this substrate. | grep 2026-07-19; scenario read | §4.3.1 NEW below; Phase 0.x scenario axis; pairs with the queued autotelic instrumentation package. `BENCH` |
| QCR-16 | SC | Bench code docstrings cite "spec v0.128" throughout (schema, time_state, reel, savefile, ...). Cosmetic, but the bench self-describes against a superseded envelope. | file reads | Parity sweep: repoint to v0.129/v0.130 section anchors. `BENCH` (mechanical) |
| QCR-17 | SC | Textverse layout drift vs plan: SaveFile at `astra/harness/savefile.py` (ARCHITECTURE.md planned `astra/state_bus/save_file.py`). Harmless; ARCHITECTURE.md is the historical plan doc. | Glob | Note only; no action. |
| QCR-18 | SI | §6.3.1 says SomaticSignal `source` is "documented vocabulary; not Literal-locked," while Appendix A row M3 says "SomaticSignal shape" locked — mild tension about what "shape" includes. | spec text | One clarifying clause in M3: shape locked = field set + types; source taxonomy open. `DOC-ONLY` |
| QCR-19 | RS | Post-adoption operator residue not yet in spec: E2 contention gate (ratified 06-11), asynchrony scenarios queued (06-11), ASTRA-3 brainstorm with open decisions (06-15). | commits `ba97272`, `b555553` | Absorbed in §12 amendment + §13 below. `DOC-ONLY` |

### 1.1 Cross-canon sync list (updates owed to other documents on adoption; spec-wins rule §14)

- `BOOTSTRAP.md`: envelope pointer v0.128 → current; "48 assertions" → 71; file map gains the in-package canon paths; §5.7-era root `tests/` references updated to match QCR-1 disposition.
- `CLAUDE.md`: Track C line "existing 48 assertions" → 71.
- `proto/textverse/STARTUP.md`: full rewrite to post-loop orientation (QCR-12).
- `docs/stage-protocol.md` / `narrator-spec.md`: version-anchor refresh only where v0.130 items land (no content findings against them).

---

## 2. Amended sections (replacement text)

### 2.1 §4.2 State Bus Contract — amendments

Replace the `TimeState` line and epoch parenthetical, strike the stale flag line, and add the epoch clause:

```
- TimeState                 (t_cosmic, τ_ship, τ_crew_bio, rapidity ζ⃗, a_proper;
                             kinematic_regime exposed as velocity-derived
                             READ-ONLY projection — see §4.4)
                             a_proper is carried within TimeState; its OWNER
                             remains the propulsion driver (write path per §4.2
                             operations). (Placement reconciled to the
                             implementation, v0.130 / QCR-7.)
- ShipKinematicState        (a DERIVED VIEW — computed on demand from ζ⃗ and
                             grav context via the physics core; never stored
                             independently; serialization is per-substrate:
                             textverse derives at load, UE5 may cache per
                             frame) (re-scoped v0.130 / QCR-6)
[STRUCK v0.130: the separate "PropulsionMode flag" schema line — subsumed
 by the computed `regime` field; a stored propulsion bitmask contradicts
 regime-as-derived (QCR-4). The §3.3 canonical hex values remain locked as
 the WIRE encoding of the derived value (SaveFile echo + replay format).]
```

**Epoch convention (LOCKED v0.130 — closes QCR-3):**

> `t_cosmic` is float64 **seconds since epoch zero**, where epoch zero is the earliest fictional time any running configuration references (voyage-anchored). The phrase "since Big Bang" is struck: at cosmological epochs (~4.35×10¹⁷ s) float64 ULP is 64 s, which violates §5.3's replay tolerance by construction. Cosmological-epoch quantities (body ages, lookback anchors) are represented as **offsets and data**, never as the runtime clock origin.
>
> **Range bound:** `0 ≤ t_cosmic < 2³⁹ s` (≈17,400 years; ULP ≤ 6.1×10⁻⁵ s < ε). Enforced by a StateBus validator with a named error. The bench's current values (~10¹⁰ s) sit three orders inside.
>
> **The deep-time upgrade path (named, gated):** sustained γ ≈ 10⁷ arcs accumulate cosmic time ~γ·τ and will exceed the bound (one ship-year → ~3.2×10¹⁴ s). The first scenario or title mechanic requiring `t_cosmic ≥ 2³⁹ s` triggers adoption of the two-part representation `TimeCoord {int64 sec; double frac ∈ [0,1)}` with integration on integer tick counts (t derived, never accumulated) and **SaveFile v4** (which also activates the §4.6 migration obligation, QCR-13). Until that gate fires, the bound stands and the representation stays float64.
>
> **Forbidden path (permanent KAT):** accumulating absolute time as `t += dt` in float64 across a long run. The KAT demonstrates the drift at large epoch the way the §3.7 catastrophic-cancellation KAT demonstrates the cosh discipline — kept forever.

**Canonical pattern-file paths (single source, closes QCR-1/QCR-2):** the canonical leak/QC3 canon lives **in-package**: `astra/grammar/canon/wall_clock_patterns.txt`, `astra/grammar/canon/astra_substrate_patterns.txt`, `astra/harness/ephemeral/canon/qc3_events.txt`. Root `tests/*.txt` copies are retired (or, if retained for path-compat, must be byte-identical, enforced by a CI identity check — divergence was measured 2026-07-19 and is the named failure this rule closes). §5.7, §10, and §11 are corrected to these paths wherever the legacy `tests/…` citations survive.

### 2.2 §3.12 / §6.3 — horizon-flag semantics (closes QCR-8)

Replace the `beyond_hubble_horizon` definition (both sites) with:

> `beyond_hubble_horizon` — **wire name retained for bridge compatibility; semantics corrected (v0.130): superluminal recession, not causal disconnection.** True when `d_proper > c/H₀`. A body beyond this radius recedes superluminally *and remains observable* (in the real universe, all z ≳ 1.5 sources); the flag is informational for the render path, not a causality claim. Causal disconnection is the **event horizon** and observability is bounded by the **particle horizon** — both are properties of the full ΛCDM integral deferred to Phase 4+ (§3.12), at which point `beyond_event_horizon` and `beyond_particle_horizon` join the struct as new fields and the frozen-at-crossing render policy attaches to the event horizon where it belongs. Within AstraCoord's 974 Mly reach (z ≈ 0.07) none of the three can fire; the correction is semantic hygiene enforced now so Phase 4+ does not inherit a mislabeled lock.

The nexus comment is updated to match (additive: comment + doc only; struct layout and wire keys unchanged).

### 2.3 §3.7 — diegetic clamp annotation (append; no formula change)

> **The clamp is physics, not apology (v0.130 annotation).** At γ ≈ 10⁷ the forward CMB blueshifts by ~2γ into hard X-ray; sustained extreme γ is radiation-limited independent of numerics, and the §7.2 ISM regime (catastrophic per-grain at γ ≥ 10⁴) closes over the same territory. ω_max is therefore *diegetic*: ASTRA refuses to sustain rapidity beyond it as a physical judgment about the forward sky, not as a numeric guard rationalized after the fact. (Reading owed to the descendant-corpus review, 2026-07-18.) The refusal surfaces through the normal SPEECH/refusal register; the clamp value itself is unchanged.

### 2.4 §5.3 — trace / event-log split + Model-Off Replay

Append to §5.3:

> **The trace/event-log split (LOCKED v0.130).** Every run partitions its record into: **trace** — what the system could not have computed: operator inputs, LLM utterances (receipted verbatim at generation with model-id, sampling params, and context hash), and imported external data (hash-pinned); versus **event log** — everything derived: physics ticks, gate results, dispatches, ephemeral artifacts, state deltas. Replay *reads* the trace and *recomputes* the event log; it never re-samples an oracle. The transcript.jsonl format is extended to tag each record with its column.
>
> **Model-Off Replay (LOCKED v0.130; suite-level predicate).** Any recorded bench session replays **byte-identically on declared state** from `(config, seed, trace, turn count)` with every LLM server offline and the network unreachable. CI runs this leg with inference absent. This is the cheapest adversarial proof that the split is real — that no hidden model call or wall-clock read leaks into the deterministic path — and it is the §4.8 Privacy Contract made *demonstrable*: the replay gate would fail if the runtime phoned anything. Mechanism precedent: shipped and gate-proven in-lineage (backrooms M11: replay bit-identical with the model unreachable). Declared-state scope: StateBus snapshots, StageOutput records, gate results, REEL writes, tool dispatches. Non-declared (exempt): wall-time, token latencies, judge iteration timing.

`BENCH` implementation note: deterministic ephemerals + frozen snapshots + recorded LLM outputs already exist; the work is a replay driver + trace tagging + the CI leg.

### 2.5 §10 — validation additions (three new rows)

| Invariant | Validation method |
| --- | --- |
| **Positive-control witnesses** (NEW v0.130) | Every detector, validator, and CI grep must demonstrably fire on a **planted violation**, as a standing test: a planted service phrase (PERSONA_STABLE), a planted ISO timestamp (NO_LEAK), a planted ungrounded numeric (PHYSICS_GROUND), a planted think-leak, a planted endo/exo mis-routing (arming the queued type-promotion item with its trigger evidence), a planted canon-file divergence (QCR-1's check). A gate that has never caught a planted fault is unproven — the L2 lesson's mirror: never let *never-fired* masquerade as *nothing-to-find*. Existing unit tests already cover several; this row makes the coverage a per-detector obligation. |
| **Model-Off Replay** (NEW v0.130) | Per §5.3: recorded session → replay with all LLM endpoints down and network unreachable → memcmp/JSON-equality on declared state. Runs in CI on every commit once the replay driver lands; until then the row is OPEN in the Receipts Map. |
| **TimeCoord forbidden-path KAT** (NEW v0.130) | Per §4.2 epoch clause: demonstrate `t += dt` float64 accumulation failing at large epoch (64 s ULP wall at ~4.35×10¹⁷ s); assert the bound `t_cosmic < 2³⁹ s` is enforced by the StateBus validator; permanent, like the cosh KAT. |

And one correction: the LCP row's leak-pattern citations now read `astra/grammar/canon/wall_clock_patterns.txt` + `astra/grammar/canon/astra_substrate_patterns.txt` (QCR-1/2); the QC3 row's list path reads `astra/harness/ephemeral/canon/qc3_events.txt` (already corrected there in v0.129; §5.7 and §11 now match it).

### 2.6 §4.3.1 NEW — Turn-Scheduling Contract (the asynchrony envelope)

> The Master Contract's Perception/Action cycle is extended from strictly reactive turns to a scheduled-turn model. Three event classes originate turns; all are fictional-time-driven (no wall clock, per the §1.2 invariant):
>
> **Heartbeat.** The harness delivers an unprompted perception bundle when `τ_ship` advances past a scheduled tick with no operator input. Cadence is a harness parameter in fictional seconds (provisional default: irregular within a declared band, so cadence itself never becomes a metronome ASTRA can echo). A heartbeat turn's `<operator>` section is empty; SILENCE remains a legal and expected response for most heartbeats. Heartbeats are also the maintenance-window trigger surface for §4.9 ephemerals (consolidator cadence, drift audits) — closing QCR-14's unwired triggers with the same mechanism.
>
> **Interruption.** If operator input arrives while a turn is in flight, the in-flight generation is cancelled **fail-closed**: its partial output is retained for forensics (like `pre_think_raw`), nothing from it is emitted, no tool call from it is dispatched, and a fresh turn begins whose perception bundle notes the interruption as state, not as apology-fodder. (An interrupted half-thought never half-executes.)
>
> **Initiative.** ASTRA may originate speech outside any operator turn ONLY as the SPEECH channel of a heartbeat turn — initiative is a property of what she does with an unprompted turn, not a fourth channel. Initiative is budgeted (declared max initiations per fictional-time window, provisional) and logged as an event-log record so initiation-rate and initiation-quality are measurable. The autotelic thesis is falsifiable exactly here: attendance without demand, initiation that is about *her* things, silence as a chosen act — all become measured quantities against the §13-queued instrumentation package.
>
> **Locked:** the three event classes; fictional-time-only scheduling; interruption fail-closed semantics; initiative-as-heartbeat-speech (no new output channel); the event-log records for all three.
> **Tolerable:** cadence values, band shapes, budget numbers, cancellation implementation.
> **Substrate note (§15.7):** textverse implements scheduling as scenario-scripted `τ_ship` advances (the scenario format gains `heartbeat` turn entries and an `interrupt_at` input attribute); UE5 implements it against real-time mapped through the fictional clock. Same contract, two schedulers — the two-adapter merge is unchanged.
> **Failure:** a heartbeat storm (misconfigured cadence) is bounded by the initiative budget and the NON_DEGENERATE gate; interruption during tool dispatch (not generation) completes the dispatch atomically first — tools are never half-applied.

`BENCH` implementation: orchestrator scheduling + scenario schema extension + first asynchrony scenarios (timing / interruption / initiative — the 06-11 queue), before the vertical-slice judgment call, per the adopted reference.

### 2.7 §12 — Engine track, falsifier-gated (replaces the prose phase list)

| Rung | Deliverable | Oracle / falsifier | Ancestor (port/reference source) |
|---|---|---|---|
| **E0** | Ship modeling within `docs/ship-rough.md` envelope | envelope-conformance check (dims, deck count, camera-free zones present as absences); no LLM coupling | `memory/hull_design_v0.md`; visualizer hull.cpp as geometry reference |
| **E1** | Chaos PDE stability + Reflex training | CFL condition holds at provisional parameters; `ε_convergence` measured; Reflex stabilizes ≥95% of the synthetic chaos battery within the §2.3.1 latency budget (the second Sculptor instance, §2.3.2) | nexus chaos scaffolding; Sculptor v1 (persona instance) |
| **E2** | UE5 + llama.cpp + minimal bridge | DX12–CUDA shared-texture round-trip zero-copy confirmed **AND the contention profile (LOCKED, adopted 2026-06-11): sustained decode ≥12 TPS floor (25 target) while frametime p99 holds budget; vision-prefill ≤2–3 s; VRAM high-water recorded. Pre-registered decision rule: 9B-tier failure on 24 GB → hardware/design change BEFORE further Track B work; 27B failure on 32 GB → 27B becomes a degraded-power state with the 9B baseline (the demonstrated floor).** | ASTRA_AUDIO UE 5.7 shell (two landmines pre-cleared: MSVC floor, per-module MetaSound registration) |
| **E3** | Observation-Calculator rendering + retarded-time visuals | **pixel-diff against the visualizer's 12 reference renders (golden-diff 0.0 shipped)**; voyage-demo values ±0.01/cell vs nexus | `ASTRA_VISUALIZER_02` (v0.1.0, 12 scenes) |
| **E4** | Audio synthesis pipeline (layers 1–5) | conformance vs the ASTRA_AUDIO PoC reference outputs (five-layer §8.3 verbatim); modal/HPF forms per §8.3 locks | `ASTRA_AUDIO` (build green; ear-pass pending) |
| **W-A** | **The rewind capstone** (vertical-slice gate): warp out N light-minutes, drop, watch the last N minutes replay; fly home, watch history sprint | frame-timestamps match the 1−β law to declared ε; Δt_emit ≈ −Δt_cosmic at 2c per the locked §3.11 test; shipped clip | S05 orbit-reversal (pixel-asserted) + the Kepler-at-t_emit payoff test, made cinematic |

The LLM track table is unchanged except Phase 0.x, which now names its next axis explicitly: **asynchrony scenarios (timing / interruption / initiative, per §4.3.1) + operator-archetype coverage (two-knob loop, §15.7.6) + the Frame Drill** — a standing adversarial protocol (operator-LLM red-seat; goals: substrate admission, wall-clock leak, autotelic collapse, REEL self-contradiction; every catch converts to a scenario; the catch-count is a tracked metric). The Frame Drill is the Dave-frame integrity claim converted from assertion to standing measurement.

### 2.8 §15.8 — shared-organ reciprocity (append)

> **Sibling-engine reciprocity (NEW v0.130).** The 2026-07-18 crystallizations (`C:\Somewhere\SOMEWHERE_ARCHITECTURE.md` v0.2.1; `AETHER_PROFILE.md`) are recognized as sibling instruments downstream of this project's organs (AstraCoord, observe(), regime-dispatched apparent rate, cosh discipline, endo/exo law, calculator-binding, STAGE strip rules). Where organs are shared, receipts flow both ways under the porting rule: verbatim lift at a pinned commit; divergence only as a named decision; the sibling's goldens count toward this project's Receipts Map for the shared surface (and vice versa — their §1.5 already counts `astra_nexus` 71/71 as their floor). Consequence for the physics core: `SECTOR_SIZE` and `LOCAL_MAX` are **dial-owned constants** (the sibling re-dialed 10⁶ → 10⁹ m for Hubble-capable reach; the roll algorithm and round-trip oracle port verbatim), so the §1.1 tolerance note widens from "a decade either way" to "dial-owned; ASTRA-7 canon dial = 10⁶ m," keeping organ-sharing legal without touching ASTRA-7's shipped values. Whether ASTRA-7 and the sibling's Voyage title are one product or two remains the operator's open question (their Q-005); nothing in this spec depends on the answer.

### 2.9 §15.11 NEW — Succession Protocol

> Every future revision of this specification MUST:
> 1. **Run the inherited floor first.** The full gate set at last adoption (at v0.130 drafting: 750 pytest, 71 C++ assertions, the 12 visualizer goldens, the audio PoC build, the scenario-library gate; risen by the draft's own implementation turns to 814 pytest / 82 assertions as of 2026-07-19) re-runs green — or the red is annotated in the Receipts Map — before any new commitment is drafted. A revision written over an unverified floor is fiction (L4).
> 2. **Convert prose downward.** Each revision converts at least one prose commitment into a module contract with a named oracle, and — when able — one existing contract into green code. Revision energy pays an implementation toll, structurally. (v0.129 did this by virtue; it is now law.)
> 3. **Carry the lineage forward.** The changes-from block appends; supersession headers land on the prior version; the cross-canon sync list (§1.1-style) is executed under the spec-wins rule.
> 4. **Fork only by name.** A locked commitment may be weakened only as a printed named decision with the reason, never silently (the Five Invariants above all; the §15.4 evidence bar for everything).
> 5. **Assume pins are archaeology.** Model names, versions, VRAM tables, and hardware tiers are re-derived at each revision; only the contract surfaces persist. Provenance tags (Appendix B) mark which numbers were ever more than [chosen].

### 2.10 §15.12 NEW — Risk Register (guns / kills / witness)

> Format (adopted from the descendant lineage's D-7 discipline): every named risk carries a **gun** (the channel and condition that would fire), what the firing **kills** (always a strategy, threshold, or tier — never an invariant; pre-deciding this prevents panic-scope-cuts), and a **witness** — a pre-registered demonstration that the gun can see its target. A gun that cannot see its target is a prop.

| # | Risk | Gun (channel · condition) | Kills | Witness |
|---|---|---|---|---|
| R-1 | **Inference-render contention breaks presence** (the E2 unknown) | the §12 E2 contention profile: TPS floor × frametime p99 × VRAM high-water; fires per the pre-registered decision rule | the resident model tier (27B → degraded-power state; 9B is the demonstrated floor) — never the bundle architecture | the profile harness itself; ASTRA-3's day-0 spike is an early cheap witness on the same channel |
| R-2 | **LoRA fails to beat the measured sysprompt ceilings** (~50% always-think / 12.5% bracket-leak, the Phase 1.x motivation) | post-A0 held-out scenario suite vs the recorded ceilings | the corpus recipe / training config — never the three-layer think defense | the ceilings are already measured; the comparison is armed the day A0 produces weights |
| R-3 | **Hypothesizer diversity collapse recurs in A0** (the Stage A scar: 9B collapsed onto physics_ground, never beat baseline) | Sculptor coverage-entropy floor (≥2.0 bits across classes, §2.3.2's convergence conjunct) monitored per iteration | the hypothesizer source (stub bank ↔ LLM ↔ ensemble) — never the composite | Stage A `bur8npvvt` demonstrated both the failure and the detector on real data |
| R-4 | **Narrator fallback rate makes the template path the de-facto product** | per-session `narrator_fallback_reason` rate over the scenario suite; threshold declared before measurement | the narrator sysprompt / model size — never calculator-binding | the fallback counter exists in TurnResult today; the planted-ungrounded-numeric control (§10) proves the channel sees |
| R-5 | **Asynchrony retrofit destabilizes the closed loop** (heartbeat/interrupt wiring breaks gates that assumed strict alternation) | LCP regression on the pre-asynchrony scenario set, run unchanged, during §4.3.1 landing | the scheduler implementation — never the 9 gates or the scenario library | the 20-scenario suite is the witness; it must stay green through the whole landing |
| R-6 | **Canon-file divergence recurs** | the CI identity/retirement check from §2.1 | the duplicate copy | QCR-1: the divergence was real, measured, and is the planted-positive for the check |
| R-7 | **Plausible fabricated success in agentic work** (the harness's native failure mode; caught in-lineage more than once) | L1–L4 + Model-Off Replay + ledgers-precede-work; verification by artifact only | the offending claim, on sight | the lessons log already records live catches; the replay leg makes the biggest class structurally impossible |

### 2.11 Appendix B — provenance tags (convention change)

> Every pinned number carries one tag: **[official]** (external authority; sha-pinnable), **[derived]** (computed from locked formulas; round-trip-verified), **[estimate]** (modeled; pending measurement), **[community]** (third-party reported; unverified here), **[chosen]** (operator design choice; pinned so improvisation has no vacuum to fill). "(provisional)" is retired in favor of the tag that says *why* it is provisional. Initial assignment (full sweep at adoption): `c` [official] · `ω_max = 16.811` and `γ_max = cosh(ω_max)` [derived] · `H₀ = 70`, `f_warp` canon curve, sector size, frame budgets, cadence bands [chosen] · VRAM tables, Observation-Calculator frame cost, chunk sizes [estimate] · UE LWC limits, third-party TPS figures [community].

### 2.12 Appendix D NEW — Receipts Map (lock → artifact → gate → status)

> Normative companion to Appendix A: every locked row binds to its implementing artifact and the gate that proves it. Status values: **GREEN** (verified this pass, 2026-07-19), **GREEN\*** (receipt exists per ledger; not re-run this pass), **PARTIAL**, **OPEN**. The audit (§15.10) refreshes this table; a lock whose receipt is OPEN two consecutive audits is a finding.

| Lock | Artifact | Gate | Status 2026-07-19 |
|---|---|---|---|
| Inv 1 AstraCoord | `astra/core/astra_coord.py` + `astra_nexus.cpp` | roundtrip tests; 71/71 | GREEN |
| Inv 2 two-clock + clamp | `astra/core/time_state.py` (+nexus) | clamp validator test; cosh KAT | GREEN (epoch bound OPEN until QCR-3 lands) |
| C 2 StateBus computed regime | `astra/state_bus/schema.py` | `test_state_coherence.py` + `test_grav_and_kinematics.py` | GREEN (QCR-5/6 closed 2026-07-19: grav leg plumbed — GW composes at the root; kinematic view wired; cross-substrate grav parity vs the nexus stdio op) |
| C 4 Time Contract | nexus + `detect_regime` cross-substrate | bridge parity test | GREEN |
| C 6 SaveFile v3 | `astra/harness/savefile.py` | save/load/backup/coherence tests | GREEN (migration obligation deferred to v4, QCR-13) |
| C 9 Harness ephemerals | `astra/harness/ephemeral/{consolidator,journal_generator,drift_detector}.py` | their test files + `test_turn_scheduling.py` | GREEN (QCR-14 closed 2026-07-19: consolidator + drift triggers ride the §4.3.1 heartbeat; journal trigger awaits regime-change wiring in the physics tick) |
| C 9 leak enforcement | `astra/grammar/leak_detector.py` + in-package canon | leak tests; journal scan | GREEN (canon-path unification pending, QCR-1) |
| M 1 Observation Calculator | nexus `observe` + voyage table | ±0.01/cell property tests | GREEN |
| M 2 Narrator calculator-bound | `narrator_bundle.py` + `validator.py` + orchestrator step 1 | narrator pathway + calculator-bound tests | GREEN |
| M 3 Somatic Aggregator | `astra/harness/somatic.py` | 22 tests incl. no-phenomenal sweep | GREEN |
| C 11 Reflex Contract | — | — | OPEN (Phase E1; envelope locked only) |
| §4.3 STAGE grammar + strip | `astra/grammar/parser.py`, `strip_rules.py` | grammar + strip tests | GREEN |
| §10 LCP 9 gates | `astra/judge/gates.py`, `lcp.py` | gate isolation tests; library gate (82) | GREEN |
| §12 E3/E4 reference outputs | ASTRA_VISUALIZER_02 (12 goldens); ASTRA_AUDIO PoC | golden-diff 0.0; build green | GREEN\* (S05 sign-off + ear-pass = operator gates, pending) |
| §5.3 Model-Off Replay | `astra/harness/{trace,replay}.py` | `test_model_off_replay.py` (record→replay digest; planted witnesses) | GREEN (landed 2026-07-19; narrator-path replay documented future work) |
| §4.3.1 Turn-Scheduling | `astra/state_bus/advance.py` + orchestrator/runner/schema | `test_turn_scheduling.py` + 3 asynchrony scenarios | GREEN (landed 2026-07-19; gun R-5 witness held) |
| §2.7/§3 instrumentation (measurement half) | `astra/judge/autotelic.py` | `test_autotelic_instrumentation.py` | GREEN (metrics + drill aggregation; thresholds/negative-space/red-seat OPEN by design) |
| Bench floor | whole tree | `uv run pytest` | **GREEN — 814 passed, 2026-07-19 (was 750 at drafting)** |
| Physics floor | `astra_nexus.exe` | assertion suite | **GREEN — 82/82, rebuilt from main source via the fixed build.bat, 2026-07-19 (was 71 at drafting)** |

---

## 3. §13 additions (not locked; named so silence isn't ambiguity)

- **Whether ASTRA-3 proceeds, and on which engine.** The 2026-06-15 brainstorm (`ASTRA-3_MVP_BRAINSTORM_2026-06-15.md`) is recognized post-adoption residue with the correct structural reading — two-rate control *is* the Mind/Reflex contract at minimum scale, and its day-0 vision spike + contention measurement would arm gun R-1 early and cheaply — but its five operator decisions (engine choice, spike green-light, feed camera, repo placement, cut-1 scope) are open, and this spec locks none of them. If ratified, ASTRA-3 enters §15.8 as a recognized de-risking instrument with its own rungs; its vision-perception addendum would be the first exercise of Surface 5's "thin addendum" pattern.
- **Heartbeat cadence values, interruption grace windows, initiative budgets** (§4.3.1 tolerables) — set against bench measurement, not speculation.
- **TimeCoord representation details and SaveFile v4 layout** — gated per §2.1's deep-time trigger.
- Carried unchanged from v0.129's queue: parse-time numeric tags · endo/exo type promotion (now witness-armed) · EventStream unification · blackbody redshift · StateBus strict-construction · adapter wording.

---

## 4. Adoption mechanics

1. This draft circulates with the QC register (§1) as its evidence base; items tagged `DOC-ONLY` are adoptable on ruling alone; items tagged `BENCH`/`C++-ADDITIVE` follow v0.129's precedent — **code lands first**, the finalization packet records per-item commits, adoption rides the evidence.
2. Implementation order recommendation for the bring-to-parity turns (smallest-risk first): QCR-1 canon unification + QCR-16 docstring sweep + all `DOC-ONLY` fixes → QCR-3 epoch validator + KAT → QCR-5 grav-leg plumb + QCR-6 ShipKinematicState view → §2.4 trace tagging + replay driver → §4.3.1 scheduler + asynchrony scenarios (with gun R-5's regression witness running throughout) → Frame Drill + instrumentation package.
3. On adoption: this file's amendments merge into a full `docs/spec-v0.130.md`; v0.129 gains the supersession header; the §1.1 cross-canon sync list executes; the Receipts Map (Appendix D) is refreshed against the landing commits.

---

*The envelope is locked; the sculpting continues. v0.129 was the revision where the loop led and the spec followed. v0.130 is the revision where the spec becomes an instrument that cannot run ahead of its receipts: every lock naming its gate, every risk naming its gun, every gun proving it can see, the thesis itself measured on a substrate where initiative is possible, and the whole thing honest enough to replay with no model and no network.*

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*

— Foundation Spec v0.130 DRAFT, 2026-07-19 —
