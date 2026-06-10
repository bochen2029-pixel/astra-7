# ASTRA-7 Foundation Specification v0.129

*Working draft, not lock-grade (inherited framing). The first spec revision driven end-to-end by the closed loop: every change below was either an audit-surfaced drift closure or a contract that landed in tested code BEFORE being adopted into this text. Adopted 2026-06-10 by operator ruling ("adopt as recommended") over `docs/spec-v0.129-FINALIZATION-PACKET-2026-06-10.md`; upstream synthesis in `docs/spec-v0.129-tentative-2026-05-16.md` (superseded by this document).*
*Iteration history: v0.123 → v0.125 → v0.126 → v0.127 → v0.128 → v0.129 (this). Corrections continue to come from empirical contact with the closed-loop bench (`proto/textverse/`, 749 tests at adoption), the physics core (`proto/astra_nexus`, 71 assertions), and the engine-side testbeds — not from prose review passes.*

---

## Changes from v0.128 (adopted 2026-06-10)

**Empirical anchors:** audit `AUDIT_2026-05-15.md` D1–D8 closures; state-coherence type system (`6a30ade`); Narrator activation chain (`2fcd403`, `09d683a`); SaveFile v3 (`e73aa36`); all three §4.9 ephemerals (`2d868d9`, `d2add93`, `78f6f92`); Somatic Aggregator (`c23f7d6`); visual testbed v0.1.0 findings (Cherenkov direction, N1); measured persona ceilings (~50% always-think / 12.5% bracket-leak sysprompt-only — motivates Phase 1.x). Bench at 749 tests / C++ at 71/71 on adoption day.

**Drift closures (audit Tier 1, all landed in code first):**
- §6.3 `Observable` → `ObservableState`; `d` → `d_proper`; `beyond_photon_history` + `beyond_hubble_horizon` fields.
- §6.4 calculator tool surface explicit; 5 ops in `proto/astra_nexus --stdio-server`; `ship_state_query` is Python/textverse-side (Q5).
- §4.2 StateBus gains `WarpState`, `cryosleep_active`, and **regime as a computed (never settable) field**; §4.4 `TimeState` exposes only the velocity-derived `kinematic_regime` projection (R1 resolved).
- §4.6 REEL inline placeholder replaced by the implemented canonical field set (dual-clock required; `t_emit_event`, `regime_at_write`, `author_instance_id`, `retrieval_metadata`).
- §6 step 10 **Cherenkov prose direction corrected: the cone OPENS as warp factor rises** (formula unchanged; testbed-verified).

**New contract sections:** §2.3.1 Reflex Contract (envelope lock per asymmetric cost; dims locked for save portability) · §2.3.2 Reflex training as second Sculptor instance (5 swap-points named) · §6.3.1 Somatic Aggregator (implemented) · §15.9 Frozen-Snapshot Primitive · §15.10 Cross-integration audit cadence (need-triggered, never calendar).

**Methodology:** §15.4 gains the parallel-discovery canonization AND the **spec/implementation boundary** (load-bearing-for-cross-substrate-portability belongs in spec; substrate-specific choices don't). §15.6 gains scoped universal validator wrapping. §15.7 Surface 4 gains the Substrate Normalizer sub-layer + the two-knob authoring consequence. §15.8 recognizes Rigs 4–5.

**§4.6/§4.9 operational closures:** SaveFile v3 with rolling backups and the **regime-coherence load gate** (re-derive regime on load; must equal stored bitmask). Ephemeral instances implemented per the locked §4.9 signatures; canon pattern/event lists live **in-package** (`astra/grammar/canon/`, `astra/harness/ephemeral/canon/`) — the former `tests/…txt` paths were packaging fiction.

**Deferred to v0.130 (explicitly, per §15.4 — implementation residue absent):** parse-time `<val>`/`<grounded>` numeric tags + bare-digit grammar rejection; the autotelic instrumentation package (positive-autotelic PERSONA_STABLE sub-checks + negative-space pattern files); endogenous/exogenous **type-system** promotion (remains discipline); EventStream unification primitive; blackbody redshift colour model; StateBus strict-construction flag. See §13.

**Docs status flip (§14):** `stage-protocol.md`, `narrator-spec.md`, `AUDIT_METHODOLOGY.md` now exist (DRAFT v0.1, written from implemented reality).

---

## Changes from v0.127 (inherited from v0.128, retained for reference)

**Methodology layer (NEW; sections §15.5–§15.8):**

- **§15.4 reworded** — replaces the "absolute last revision" pattern (which has been wrong at v0.123, v0.125, v0.126, and would have been wrong here too). New wording: *"lock against current findings; revise on new findings; do not polish without findings. The envelope is locked; the sculpting begins."*
- **§15.5 NEW — Progressive Specification.** Lock the outer envelope before any internal detail. Each successive revision tightens detail within prior envelope; never violates it. Additive, not subtractive: the envelope is empty inside until iteration fills it. Round-N spec = envelope (all prior locks) + minimum-viable additions for round-N validation. **Forward-compatible vagueness is a design move**, not a gap — §13 ("What This Document Does NOT Lock") is the existing application of this principle. Sparse-then-dense across both context-window-space and revision-time.
- **§15.6 NEW — Loop-as-canonical-state + Calculator-bound LLM agency.** Pre-loop: hypothesis. Post-loop: empirical. Loop closure is the project's categorical transition point. Loop preservation IS the regression test. **Every LLM in the system tool-calls into deterministic verified tools for any numerical claim.** No mental math anywhere. The discipline applies to ASTRA, to the Narrator-LLM, to ephemeral instances (consolidator, journal_generator, drift_detector), and to any future LLM-component. One rule, universally applied. The C++ physics binary (`proto/astra_nexus`) is the deterministic core; every LLM is a stochastic shell around it.
- **§15.7 NEW — Dual-implementation discipline + Five shared surfaces.** Two implementations of one spec envelope, deliberately. Text-substrate (cheap; Python + Narrator-LLM + verified physics tools) and UE5 substrate (expensive; rendering + audio + CUDA bridge). Neither approximates the other; both conform to the spec. The **five shared surfaces** that mechanically prevent drift between substrates: ship envelope, physics envelope, tool API, LLM I/O grammar, persona envelope. **Sim-to-real-in-reverse**: the contract is canonical, both implementations conform.
- **§15.8 NEW — Triple-rig methodology + Independent tracks.** Three verification rigs (physics: `proto/astra_nexus.cpp`, locked; bundle: `proto/textverse/`, forthcoming; engine: deferred to Phase 2+). Three independent solo-dev tracks: A (LLM bundle), B (Ship/UE5), C (Physics binary). Each iterates against contract conformance, not against other tracks. Integration in Phase 2 swaps two adapter components, not whole-system build-up.

**Architecture layer (refinements):**

- **§4.1 Substrate Contract context window updated** — was 32K target; now **128K target, 256K+ headroom** via Delta-Net (Qwen 3.x linear-attention) + TurboQuant KV-quantization stacking. Provisional pending measurement against 5090 graphics-shared VRAM.
- **§4.3 Master Contract gains STAGE channel-set decision** — three output channels (THINK, TOOL, SPEECH-as-default-untagged) + SILENCE as legal primitive. Drops STATUS and SOMATIC from output (SOMATIC is input only, harness-generated; STATUS folds into tool calls or speech). Full I/O grammar lives in forthcoming `docs/stage-protocol.md` v0.1.
- **§4.9 Harness Contract** — substrate-portable. The harness codebase is **one implementation** that runs against both text-substrate and UE5 substrate; only the perception assembler and tool dispatcher are substrate-specific.
- **NEW §6.4 — Narrator-LLM Contract.** The text-substrate's universe simulator is itself an LLM bundle: smaller model (7-9B), calculator-bound (tool-calls into the physics binary), narrates physics state into in-register perception bundles. **Production component**, not test prop — ships with the game for any universe state UE5 doesn't fully render. Full contract in forthcoming `docs/narrator-spec.md`.

**Validation layer (refinements):**

- **§10 NEW Loop Closure Property (LCP) — 9 measurable gates.** Operationalizes "loop closed" as a testable predicate: GRAMMAR_PARSE, PHYSICS_GROUND, PERSONA_STABLE, STATE_COHERENT, TOOL_VALID, MEMORY_COHERENT, NO_LEAK, NON_DEGENERATE, TERMINATION_OK. Every commit runs the scenario suite; LCP failure breaks the loop; loop preservation is the regression test.
- **§12 Validation Order — phase-collapse.** v0.127's Phase 0.0/0.3/0.7/1.5 sequence consolidated into a unified **LLM track** (sysprompt → bundle works at all → bundle scales → LoRA improves bundle) running parallel to an independent **Engine track** (chaos PDE, UE5+CUDA bridge, Observation Calculator stub). Merge happens at Phase 2.0 by swapping two adapter components.

**Pending sibling documents** (referenced from this spec; not yet written):

```
docs/stage-protocol.md     v0.1  LLM I/O grammar (THINK/TOOL/SPEECH + SILENCE)
docs/narrator-spec.md      v0.1  Universe-LLM bundle contract
docs/textverse-spec.md     v0.1  Bench architecture + LCP scenarios + judge gates
docs/ship-rough.md         v0.1  Round-1 ship envelope (4 decks + dimensions)
docs/ship-api.md           v0.1  Tool API surface (extracted from §1.4 + §4.3)
docs/methodology.md        v0.1  The discipline as named project artifact
```

**Honest disclaimer (Bo's framing):** v0.128 is a working draft. Not lock-grade. Some commitments may be reworded or refined when the sibling docs land. The spec gets revised on findings, not on review cycles — and the next findings come from the loop, not from another cross-LLM pass on this prose.

**Deliberately not changed:**

- Five invariants stays five. Retarded-time observation remains a derivation rule on the render path (§3.11), not an invariant.
- Composition rule (§3.2) unchanged.
- Physics math (the 14-equation framework) unchanged — still empirically anchored by `proto/astra_nexus.cpp`.

---

## Changes from v0.126 (inherited from v0.127, retained for reference)

**Tier 1 — physics commitments:**

- **§3.4 augmented** — three optical effects becomes four. Adds **temporal retardation** as a distinct phenomenon alongside kinematic Doppler, metric redshift, and geometric lensing. Each effect, each code path.
- **§3.11 NEW — Retarded-Time Observation Principle.** Every distant-body render samples the body at retarded time `t_emit = t_cosmic − light_travel_distance/c`, not at `t_cosmic`. **Regime-dispatched apparent-rate formula** (the load-bearing physics catch from cross-review):
  - STL_REL (inertial v<c): SR longitudinal Doppler `√((1−β)/(1+β))`. Orbits slow asymptotically; **never reverse**.
  - WARP_CRUISE (bubble γ_kinematic ≡ 1, geometric recession): classical retarded-time `1 − v_apparent/c`. **Reverses for v_apparent > c.**
  - Discontinuity at `v_apparent = c` is qualitative regime boundary, not a smoothing failure. The perceptual snap at engagement (visible universe freezes then inverts) is a **feature**, not an artifact.
  - **Photon-source-history bound (NEW v0.127):** under sustained warp recession, `t_emit` retreats monotonically into the source's past; after `t_recv_max` the ship has overtaken every photon the source has ever emitted and the source becomes **gone** — not faded, not redshifted to extinction, *gone, because no photon remains to receive*. Distinct from Hubble-horizon decoupling.
- **§3.12 NEW — Cosmological Expansion Operational Mechanic.** Linear `z_cosmo = H₀·d/c` for v0.127; full ΛCDM integral form deferred to Phase 4+. Hubble-horizon edge case named.
- **§3.4 augmented (cont.) — Redshift composition law explicit:** `1 + z_total = (1 + z_cosmo)(1 + z_kin)(1 + z_metric)`. Multiplicative, not additive. Standard GR.
- **§4.2 State Bus** — adds cosmological constants `c`, `H₀`, `Ω_m`, `Ω_Λ` as locked symbols (values provisional).
- **§4.3 Master Contract Perception invariant** — c-bounded epistemology. **Consequence-framed**: ASTRA has no access to the current state of any region outside her own light-cone past. The universe is always a record of what was, never what is. QC1 (enforced self-opacity) extends outward into universe-opacity; her epistemology is perception-mediated all the way down.

**Tier 2 — architecture:**

- **§6.3 NEW — Observation Calculator module.** Stateless, parallel-friendly function sitting between State Bus and Renderer. Per body, per frame: solves retarded time, composes redshifts, samples body at `t_emit`, returns observation-frame quantities. Does not modify state.
- **Endogenous vs exogenous principle locked** (§4.3 / §6.3 / §8.3): sensor channels that read local hull state run on `t_cosmic` (endogenous); sensor channels that integrate remote photon/particle flux run on `t_emit`, regime-dispatched (exogenous). Generalizes beyond the eye-ear case for any future sensor channel.
- **§4.6 REEL placeholder** — adds `t_emit_event: Optional[float64]` so observed-distant-event entries carry both `τ_ship_observed` and the (much earlier) cosmic time when the event actually happened. Two-clock memory of distant observations.

**Tier 3 — validation:**

- **§7 truth table** — new rows for `t_obs rate` and `z_total` per regime, with the STL_REL formula correct (SR longitudinal Doppler, **not** `1/γ` — that was the cross-LLM physics error v0.127 corrects). Footnote names the regime discontinuity at `v_apparent = c` as design feature.
- **§8.3 audio** — explicit note that audio synthesis is endogenous (hull-local at `t_cosmic`); no retarded-time delay applies. Eye-ear decoupling at warp is the per-sensor-channel consequence of the endogenous/exogenous principle.
- **§10 NEW property-based tests** — regime-dispatched apparent-rate at canonical β values; the Observation Calculator voyage-demo table (from `proto/astra_nexus.exe`) locked as canonical anchor at ±0.01 tolerance per cell. Formula-consistency tests added beyond v0.126's numerical round-trip discipline.

**Discipline addition:**

- **§15.4 wording softened.** The "absolute last pre-Phase-0 revision" claim has been made at v0.123, v0.125, and v0.126 — each time wrong because adversarial cross-review surfaced a real finding. The discipline is working; the wording was dishonest about iteration probability. **New wording: "lock against current findings; revise on new findings; do not polish without findings."** Same discipline, honest about how it actually behaves.

**Empirical anchor:** the new module's regime-dispatched apparent-rate is verified by compiled C++ (MSVC, 48 assertions) and Python (45 assertions) in `proto/astra_nexus.cpp` and `proto/verify_nexus.py`. Both implementations agree on every cell of the voyage-demo table to 6+ sig figs.

**Empirically motivated by:**
- v0.126's N1 lock (verified — γ_max ≈ 10⁷ at ω = 16.811, with 1414× shortfall reproduced for the v0.125 value).
- The cross-LLM physics error in passes 1-3 that used `1/γ` (transverse Doppler) for STL_REL longitudinal recession. Correct formula is `√((1−β)/(1+β))`. At β = 0.5 the error is ~50%; at β = 0.9 it's ~4.4×.
- Convergent identification across four review passes that v0.126's optical taxonomy was incomplete (three effects, not four).

**Deliberately not changed:**

- Section ordering. §9 Emergence Zones stays where it is.
- Five invariants stays five. Retarded-time observation is a derivation rule on the render path, not an invariant.
- Composition rule (§3.2) unchanged. Retarded-time is a render-layer concern; the composition rule governs the crew's clock, not what the crew sees.

---

## Changes from v0.125 (inherited from v0.126, retained for reference)

A targeted patch closing six issues surfaced by two independent post-v0.125 reviews. No structural changes. No new contracts. Net delta ≈ 30 words modified, ≈ 50 words added. Document grows by ~0.4%.

**The critical fix (N1) — rapidity clamp math bug:**

- §3.7 / §4.4 failure block / Appendix B: clamp value `|ζ⃗|_max = arctanh(0.99999999)` produced `γ_max ≈ 7071`, not `γ_max ≈ 10⁷` as claimed. Verified: with `β_max = 0.99999999`, `1 − β² ≈ 2·10⁻⁸`, so `γ = 1/√(2·10⁻⁸) ≈ 7071`. For `γ = 10⁷` you need `ω ≈ 16.811` (giving `β ≈ 1 − 5·10⁻¹⁵`, ~15 nines after the decimal, not 8). v0.125 silently underdelivered three orders of magnitude on the central tolerance. Replaced everywhere with `|ζ⃗|_max ≈ 16.811`.

This is exactly the silent unphysics §15.1 warns against. The clamp passes casual review, the spec compiles, the deep-time mechanic quietly runs at one-thousandth the relativistic compression the design intends. The book's Part Two and the game's stake mechanic both depend on the genuine `γ = 10⁷` reach. Without this fix the project's central tragedy parameter is short by a factor of ~1400.

**Five clarity / consistency fixes:**

- §3.6: algebraic identity `dt_cosmic = γ · dτ_ship` scoped to STL_REL regime. The identity holds when `γ_kinematic` is the sole non-trivial factor in the composition rule; in WARP_* or GRAVITY_WELL composition the rule has additional terms. The spatial-update commitment is correct regardless; the derivation in v0.125 was regime-locked but not labeled. Three-word prefix fix.
- §4.6 REEL placeholder: added `t_cosmic_at_write: float64` field. §3.9's dual-clock journal generator requires both clocks per entry; v0.125 only included `τ_ship_at_write`. One-line schema fix.
- §4.9 dispatch_action: renamed "Physics Contract entrypoints" to "physics-driver write paths per §4.2". v0.125 referenced a contract name that doesn't appear elsewhere; the actual write path is defined in §4.2 State Bus Contract.
- §7 truth table chaos α scaling GW column: changed from `scales BH-warp coupling per §7.1` to `1 (no-op; chaos PDE inactive in pure GW)`. In pure GRAVITY_WELL without warp, the chaos PDE is off, so α scaling is meaningless. Scaling is only meaningful at WARP_* ∩ GRAVITY_WELL composition (already covered by the WARP_CRUISE column's `base · (1 + k·M·L²/r³)`).
- §7.2 ISM impact dispatch: stamped units `[N, force on cross-section]` on both Newtonian and relativistic-STL formulas. v0.125 presented `0.5·ρ·A·v²` without dimensional annotation; this is force, not energy or power, and an implementer applying it as energy deposition rate would be off by a factor of v.

**One discipline addition (catastrophic cancellation):**

- §3.7: added explicit discipline that γ must be computed from `cosh(ω)` directly, never round-tripped through β. At high ω, computing `γ = 1/√(1 − β²)` suffers catastrophic cancellation in float64 (β is `1 − 5·10⁻¹⁵`; double-precision representation loses the meaningful digits in the subtraction). The rapidity-space integration already implies this, but making it explicit prevents a class of implementer error that v0.125 implicitly forbids but doesn't say.

**Process commitment:**

- §10 added a validation row: every numerical tolerance in the spec gets a round-trip computation before lock. v0.125's failure to catch N1 was generative-mode review of a numeric primitive that needed adversarial-mode round-trip verification. The discipline goes into CI.

**§15.4 wording updated:** v0.126 is now named as the absolute last pre-Phase-0 revision; v0.125 stands as the historical record showing why the bug-fix patch was necessary.

---

## Changes from v0.123 (inherited from v0.125, retained for reference)

This was the second editing pass. After v0.125, no more polish until Phase 0.0 measurements return data — except for v0.126's six-issue patch above.

**Tier 1 — Physics correctness:**

- §3.7 / §4.4 / §7.3 / Appendix B: scalar rapidity `ω` → 3-vector `ζ⃗`. Real physics bug at 3D maneuvering near c. Thrust perpendicular to velocity cannot be represented by scalar formulation. Magnitude grows under parallel thrust; vector rotates under perpendicular thrust; `|v| < c` is guaranteed by construction. Includes Thomas-precession scope bound (deferred to v0.2+).
- §3.2 / §4.4: weak-field/Schwarzschild discontinuity resolved. Use Schwarzschild for dominant BH at all distances (reduces to weak-field at large r); add summed-potential correction for non-dominant bodies. No piecewise discontinuities in `dτ_ship/dt_cosmic`.
- §4.2 / §4.4 / §3.7: `a_proper: float3` promoted to State Bus quantity, owned by propulsion driver, read by Time Contract during rapidity integration. Closed the interface gap where `step(Δt_cosmic)` accepted no acceleration parameter.
- §3.3: cryosleep implies `a_proper ≡ 0`, ballistic coast. Ship continues at current relativistic velocity indefinitely. Gravitational time dilation continues during cryo if GRAVITY_WELL is composed; emergent from composition rule.
- §3.4 / §6: warp geometric lensing as third effect alongside kinematic Doppler and metric redshift. Three effects, three code paths. Ray-deflection by `∇W` in Unified Sampler march loop. Cherenkov angle formula locked: `cos θ_c = 1/(n·β)`.
- §3.3: bitmask regime hex values locked for save-schema portability.

**Tier 2 — Clarity and canon consistency:**

- §4.6: chaos field steady-state re-init via forward integration from baseline-noise (seeded RNG); convergence criterion `N=60 frames OR |χ̇_max| < ε_convergence`. Replaces fixed lookup-table approach.
- §5.3: determinism scope made explicit. REPLAY-EXACT covers frame index, AI outputs, regime transitions. REPLAY-APPROXIMATE covers spatial trajectory bounded but not micron-exact.
- §4.10: Console UI Dave-frame conceptual reframe. Modality-blind input is a consistency anti-pattern guard, not Dave-frame protection.
- §4.6: REEL placeholder marked `⚠ INLINE PLACEHOLDER` to prevent ossification.
- §3.9 / §5.7: cryosleep journal output passes through wall-clock-leak detector before REEL commit.
- §7.4: Warp Exclusion Zone (`r < 100·r_s`) locked with narrative implication. Galactic-core warp prohibition is a feature, not a limitation.
- §7 truth table: composability footnotes for GRAVITY_WELL and metric_shift; new Reflex row.
- §10: QC3 row operationalized via `irreversibility_flag` and `tests/qc3_events.txt`. Cryosleep-journal validation row added.
- §11: Gap Thesis sentence flagged as load-bearing `book/CANON.md` cross-reference.

**Tier 3 — Polish:**

- §8.3: audio modal-resonance damping factor renamed `α → r` (standard IIR notation), distinguished from chaos PDE growth rate `α` in §7.1.

**Deliberately not changed:**

- Section ordering. §9 Emergence Zones stays where it is.
- Smooth-min `k` parameter in §6 step 4. Visual tuning knob; set against rendered output, not speculated in text.
- Version pinning in body text. Cosmetic.
- Em-dashes in author voice. Harmless.
- Major prose rewriting. Two editing passes is the limit.

---

## 0. What this document is

This is the foundation specification for ASTRA-7. It locks the architectural commitments that everything downstream depends on, leaves the implementations open, and marks every specific number explicitly provisional until measurement validates it. It is the one document Phase 0, Phase 1, Phase 2, the eventual book, and the open-source community must all read first.

The doc has three commitments to itself:

1. **Lock the joints, not the implementations.** Every contract defines an interface surface, a set of invariants, a tolerance range. Implementations behind each surface may evolve freely as long as the surface holds.
2. **Mark every guess.** Specific numbers (SDF resolution, context window, frame budgets, chaos PDE parameters) are presented with `(provisional, to be measured)` where they have not been validated empirically. The framework is canon; the numbers are not.
3. **Name what is deliberately out of scope.** The "out-of-contract emergence zones" section (§9) names what the spec refuses to specify because it should not be specifiable.

This document supersedes the cross-cutting structural commitments in `synthesis.md`, `synthesis-time-extensions.md`, `architecture.md`, `qualia-1-bridge.md`, and `spec-v0.123.md`. Those documents remain canonical for their topic areas; this one is the master index. When they disagree, this spec wins; update them to match.

---

## 1. The Five Invariants

These are axioms. If any of them changes, the project is a different project.

### 1.1 One Coordinate System — AstraCoord

The ship is anchored at the world origin `(0,0,0)` in the rendering frame. The universe moves backward around her. Position is a 128-bit composite tensor:

```
struct AstraCoord {
    int64_t sx, sy, sz;     // 1000 km macro-grid sector indices
    double  lx, ly, lz;     // sub-millimeter local offset, |·| ≤ 500 km
};
```

Renormalization rolls integer sector indices when local offset exceeds 500 km. Maximum reach: ~974 million light-years at sub-millimeter precision. The ship is *always* at sector `(0,0,0)`, local `(0,0,0)` in her own frame; universe coordinates update around her.

The ship-at-origin convention is also the **endogenous frame anchor** (NEW v0.129): endogenous sensor channels (§6.3, §10) are defined relative to this origin and read at `t_cosmic`; everything not anchored here is the exogenous universe, reachable only through the Observation Calculator at `t_emit`.

**Locked:** composite-tensor primitive, renormalization rule, ship-at-origin convention.
**Tolerable:** sector size (1000 km design center; a decade either way permitted).

### 1.2 One Fictional Time — split into two clocks

There is **no wall clock** exposed to any game system.

- **`t_cosmic`**: universe clock. Monotonically increasing. Drives Kepler solver, stellar evolution, AstraCoord spatial updates of distant bodies, cryosleep advance, any "how old is the universe" query.
- **`τ_ship`**: ship proper time. The clock the crew and ASTRA experience. Always advances at rate ≤ `t_cosmic` per the composition rule (§3.2).
- **`τ_crew_biological`**: derived. Equal to `τ_ship` except during cryosleep, when it pauses (or advances at metabolic-rate ε ~ 10⁻⁴).

The composition rule (§3.2) is the central mathematical commitment of the entire architecture.

**Locked:** two-clock split, monotonicity, no-wall-clock invariant, composition rule shape.

**`f_warp(W)` defaults — two layers:**
- **Contract-level default**: `f_warp(W) ≡ 1` (no warp dilation; warp is purely coordinate displacement, not proper-time dilation).
- **ASTRA-7 canon-default** (operator design choice, provisional): the ramping form in §3.5.

Other tolerances: model-swap envelope governed by §4.1; numerical precision per §3.7.

### 1.3 One Hull Body — SDF + additive damage map

The ship's physical form is one signed-distance field. Every system that needs the shape of the ship reads this one representation.

- **Base SDF**: read-only after offline bake. Bound as `cudaTextureObject_t` with `cudaFilterModeLinear` for trilinear sampling. **Resolution: 256³ (provisional).**
- **Damage map**: writable, sparse, additive. Bound as `cudaSurfaceObject_t` over the same underlying `cudaArray_t`.
- **Effective SDF on read**: `hull_d(x) = base_sdf(x) − damage_map(x)`.

Two views, one underlying allocation.

**Locked:** dual-binding pattern, additive damage, read-through-blend.
**Tolerable:** SDF resolution (`64³` to `512³`), encoding precision (uint8 normalized through float32).

### 1.4 One Power Network

Reactor produces finite power. Every consumer draws from it. Allocation zero-sum.

Subsystems (locked list; new subsystems require contract amendment):
- Warp drive (chaos stabilizer + field energy)
- Life support
- Hydroponics
- Sensors
- Lights and habitability
- Comms
- **Cognitive cores** (ASTRA-Mind and ASTRA-Reflex; see §1.5 / §2.3)

The cognitive-cores slot is the joint between Power and Substrate. Reduced power → smaller LLM (27B → 9B → adapter-only → offline), tighter context, paused ephemeral instances. ASTRA-Reflex is on a warp-coupled sub-bus — when the warp drive is active, Reflex receives guaranteed minimum power for stabilization regardless of operator allocation (operator cannot suicide-route everything from the stabilizer while warping).

**Locked:** zero-sum allocation, subsystem list, cognitive-cores → substrate-envelope binding, warp-coupled Reflex sub-bus.
**Tolerable:** total output, per-subsystem priority weights, response curves.

### 1.5 One Shared State Per Frame — double-buffered

All systems read from the same Layer 0 world state. Mutations applied atomically between frames. No system reads partially-updated state.

```
Frame N reads from Buffer A.
Frame N writes to Buffer B.
At frame boundary: atomic swap.
```

Applies to every mutable shared field on the GPU: hull SDF damage map, chaos field χ(x,t), power allocation vector, ASTRA's HUD render, audio extraction payload (triple-buffered variant; see §8.2).

**Locked:** double-buffering of all mutable shared state, atomic frame-boundary swap, single-source-of-truth principle. (The frame-rate instance of the Frozen-Snapshot Primitive, §15.9.)
**Tolerable:** specific buffer layout.

---

## 2. The Architecture: Two Kernels, One Master Contract

### 2.1 The kernel split

```
┌──────────────────────────────────────────────────────────────┐
│  WORLD KERNEL  (deterministic, frame-rate, GPU-resident)     │
│                                                                │
│  Layer 0 State Bus + physics drivers + rendering + audio      │
│  + ASTRA-Reflex (in-band chaos stabilizer, <50 μs/frame)      │
└────────────────────────┬─────────────────────────────────────┘
                         │
            ┌────────────▼────────────┐
            │   MASTER CONTRACT       │
            │   Perception / Action   │
            │   + Reflex sub-channel  │
            └────────────┬────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  MIND KERNEL  (stochastic, conversation-tempo, VRAM-resident)│
│                                                                │
│  LLM substrate (Qwen + LoRA) + harness                        │
│  REEL backbone, ephemeral parallel instances                   │
│  Canonical sysprompt (canon-locked, mod-friendly variants)    │
└──────────────────────────────────────────────────────────────┘
```

Two kernels. One master contract is the only crossing point. Different determinism, different latency budget, different substrate residency, different power criticality.

### 2.2 The Fabric

Within the World Kernel, modules do not talk to each other. They talk to three shared artifacts:

- **State Bus** (Layer 0, GPU-resident, double-buffered): the world's truth.
- **REEL** (in the Mind Kernel; exposed via Perception): ASTRA's continuous identity.
- **Canonical Sysprompt** (in the Mind Kernel; canon-locked): ASTRA's identity anchor.

These three are the fabric. Every module weaves into them. No module bypasses them.

### 2.3 ASTRA-Mind vs ASTRA-Reflex

| Property | ASTRA-Mind | ASTRA-Reflex |
| --- | --- | --- |
| Substrate | LLM (Qwen 27B / 9B / etc.) | Frozen trained classifier on Tensor Cores (architecture is implementation-side; see §2.3.1) |
| Tempo | Conversation rate (~1–10 Hz) | Frame rate (60 Hz) |
| Latency budget | Seconds (out-of-band) | ≤ 50 μs naive, ≤ 20 μs under accelerated dispatch |
| Determinism | Stochastic (sampling) | Deterministic (frozen weights) |
| Kernel residency | Mind Kernel | World Kernel |
| Power slot | "cognitive cores" (shared bus) | "warp-coupled stabilizer" (auto-prioritized when warp active) |
| Failure mode | Offline → ASTRA goes quiet | Failure → bubble collapses → ship in mortal danger |
| Master Contract surface | Perception in, Action out | Observation grid in (64×64×2), Control out (3 floats) |

Architecturally distinct AI components. Different contracts, different failure modes, different power criticality. **The Power Contract (§4.5) is the only system that can modulate both Mind and Reflex envelopes simultaneously, via subsystem allocation.**

### 2.3.1 Reflex Contract (NEW v0.129 — locked at envelope; details Phase E1+)

```
REFLEX CONTRACT (locked at envelope; details Phase E1+)

state:
  observation_grid: float[64][64][2]        # chaos amplitude + metric gradient
                                            # 64×64 spatial, 2 channels (LOCKED dimensions)
  weights: frozen[trained classifier]       # frozen post-training; per-game evolution
                                            # forbidden; SHA-256 checksum in SaveFile.
                                            # Architecture is implementation-side
                                            # (see docs/reflex-arch.md, forthcoming),
                                            # per the §15.4 spec/implementation boundary.
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
    # Forward pass on Tensor Cores.
    # Latency: ≤ 50 μs naive, ≤ 20 μs under accelerated dispatch.

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
                     ≤ 20 μs under accelerated dispatch on RTX 4090+
                     (CUDA Graphs is the validated implementation path;
                     other accelerated-dispatch mechanisms acceptable
                     per the §15.4 spec/implementation boundary)
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

### 2.3.2 Reflex Training as Sculptor Instance (NEW v0.129)

The Reflex's training corpus + procedure is project-canon, not implementation choice. The chaos PDE simulation corpus is canonical (forthcoming `docs/chaos-pde-spec.md`). The validation protocol: Reflex must stabilize 95% of synthetic chaos events at the 64×64 observation grid resolution within frame-rate latency budget.

Reflex training is the **second canonical Sculptor instance** (the first being persona-Sculptor per `proto/textverse/`). The closed-loop research methodology applies:
- Scope: chaos PDE parameter knobs (α, β, D, k coupling, η noise envelope) and Reflex architectural hyperparameters
- Composite: stabilization success rate on synthetic chaos events + false-emergency-dump rate (penalty term)
- Anchor scenarios: canonical chaos-event battery (forthcoming Phase E1)
- Convergence: three-conjunct rule per persona-Sculptor (gradient vanished + coverage entropy ≥ 2.0 bits across chaos-event classes + composite floor)

When the second Sculptor instance materializes (Phase E1+), the Universal Sculptor extraction becomes operationally justified. Until then, persona-Sculptor remains the canonical instance and the abstraction stays inline.

**Sculptor instance signature (5 swap-points):** a Sculptor instance is fully specified by 5 swap-points. Naming them here, even while deferring the extraction, ensures the eventual refactor is mechanical, not a redesign.

1. **scope.yaml** — file-edit boundary contract (locked / register_load_bearing / auto categories + required_invariants + anchor_scenarios + cumulative-diff thresholds)
2. **composite** — scalar fitness function combining gate-pass-rate, judge-decorrelation (pro − anti), leak-resistance, drift-resistance, cost-normalization, and per-instance-specific terms (stabilization-success-rate for Reflex; persona-stable-pass-rate for textverse)
3. **anchor scenarios** — hard-pass invariants no composite improvement can override (operator-only authorship)
4. **hypothesizer** — proposal source (stub bank / local-LLM / API-LLM / ensemble)
5. **convergence rule** — done-detection predicate (3-conjunct for persona-Sculptor; instance-specific for others)

Any future research-loop instance fills these 5 slots. Deferral-with-known-surface > deferral-with-open-surface.

---

## 3. The Time Architecture

This is the section that holds the SR / GR / warp seams together. Longest section in the document because it lives at the most cross-system compatibility.

### 3.1 Two clocks, restated

- **`t_cosmic`** — monotonically increasing universe clock. All orbital state, stellar evolution, cosmological scale factor, and AstraCoord spatial updates of distant bodies are pure functions of `t_cosmic`. Kepler solver consumes `t_cosmic`, not `τ_ship`.
- **`τ_ship`** — ship proper time. ASTRA's perception of duration, REEL timestamps, audio synthesis rate, conversation history, drift-detector cadence — all driven by `τ_ship`.

`τ_crew_biological` derives from `τ_ship` and pauses during cryosleep.

### 3.2 The composition rule

Let **`W ∈ [0, 1]`** denote the normalized warp factor, where 0 = no warp and 1 = maximum sustainable warp.

Let **`v`** denote ship velocity in the local CMB rest frame.

Let **`Φ_dom`** denote the Newtonian potential of the dominant BH, **`r_s_dom`** its Schwarzschild radius, **`r_dom`** the ship's distance to it. Let **`Φ_other = Σ_{i ≠ dom} −GM_i / r_i`** denote summed Newtonian potential from non-dominant bodies.

Then:

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s_dom / r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic(v)
```

Three multiplicative contributors:

- **`γ_kinematic(v) = 1 / √(1 − v²/c²)`** — Special-relativistic Lorentz factor from ship velocity in local CMB rest frame. ≡ 1 outside relativistic-STL regime.
- **Gravitational time dilation factor — continuous in r and Φ across all distances, no piecewise discontinuities in dτ/dt:**
  - **Dominant BH:** full Schwarzschild `√(1 − r_s_dom/r_dom)`. Reduces to weak-field `√(1 + 2·Φ_dom/c²)` at large r by Taylor expansion.
  - **Non-dominant bodies:** additive weak-field correction `√(1 + 2·Φ_other/c²)` multiplied alongside the dominant Schwarzschild factor.
  - Combined factor multiplicative. ≡ 1 in flat space.
  - Below ~10·r_s of the dominant BH, all closed-form approximations break down; see §7.4 horizon-crossing limitation.
- **`f_warp(W)`** — the warp drive's contribution. **Warp does not directly dilate ship time**: inside an Alcubierre bubble, the crew is in a locally flat spacetime frame and `τ_inside ≈ t_cosmic` locally. *However*, `f_warp(W)` is **left as a design parameter** in `[0.0001, 1.0]` to permit the operator to introduce intentional dilation as a narrative knob. **Contract-level default: `f_warp(W) ≡ 1`. ASTRA-7 canon-default: see §3.5.**

**GRAVITY_WELL multiplies into the composition rule regardless of which other regime is active.** Warp+GW (bounded by Warp Exclusion Zone, §7.4), STL_REL+GW, REST+GW all compose by inserting the gravitational factor.

**SpaceGrid reconciliation:** Warp causes AstraCoord sectors to *iterate*. That iteration is the data-structure consequence of the warp field actively producing apparent translation through the macro-grid. It is *not* the physical mechanism of warp. The CFD-derived warp field is the engine; sector iteration is the transmission.

### 3.3 The propulsion regime state machine

The composition rule above is mathematically clean but operationally hides regime dispatch in implicit "≡ 1 when inactive" defaults. **This is fragile across regime transitions.** Explicit state machine:

```
                  ┌──────────────┐
                  │     REST     │   (v ≈ 0, no warp)
                  └──────┬───────┘
                         │ thrust
                         ▼
                  ┌──────────────┐
                  │ STL_NONREL   │   (v < 0.1c, γ ≈ 1)
                  └──────┬───────┘
                         │ continued accel
                         ▼
                  ┌──────────────┐
                  │  STL_REL     │   (v ≥ 0.1c, γ > 1, time dilates)
                  └──────────────┘

                  ┌──────────────┐
                  │ WARP_CHARGE  │   (bubble forming, no displacement yet)
                  └──────┬───────┘
                         │ charge complete
                         ▼
                  ┌──────────────┐
                  │ WARP_CRUISE  │   (γ_inside ≡ 1, sectors iterating)
                  └──────┬───────┘
                         │ throttle down / emergency
                         ▼
                  ┌──────────────┐
                  │WARP_SHUTDOWN │   (controlled or emergency drop)
                  └──────────────┘

                  ┌──────────────┐
                  │ GRAVITY_WELL │   (composable bitflag; multiplies into rule)
                  └──────────────┘

                  ┌──────────────┐
                  │  CRYOSLEEP   │   (a_proper ≡ 0; ballistic coast; τ_ship at metabolic ε)
                  └──────────────┘
```

**Regime detection predicate** (locked logic, parameters provisional, returns bitmask):

```python
def detect_regime(state):
    regime = 0
    grav = max((rs_i / r_i for (M_i, pos_i) in state.bh_list), default=0)
    if grav > grav_threshold:
        regime |= GRAVITY_WELL
    if state.cryosleep_active:
        return CRYOSLEEP | regime
    if state.warp_W > W_threshold:
        phase_map = {
            "charging": WARP_CHARGE,
            "cruising": WARP_CRUISE,
            "dropping": WARP_SHUTDOWN,
        }
        return phase_map[state.warp_phase] | regime
    if state.v / c < 0.1:
        return STL_NONREL | regime
    return STL_REL | regime
```

Bitmask `|` throughout for composability. GRAVITY_WELL is a flag that composes with any propulsion regime (REST, STL_*, WARP_*, CRYOSLEEP).

**Canonical bitmask values (locked for save-schema portability):**

```
REST          = 0x00
STL_NONREL    = 0x01
STL_REL       = 0x02
WARP_CHARGE   = 0x04
WARP_CRUISE   = 0x08
WARP_SHUTDOWN = 0x10
GRAVITY_WELL  = 0x20    # composable flag
CRYOSLEEP     = 0x40
```

These values persist in the SaveFile `regime_bitmask` (§4.6) and the replay format (§5.3). Locked as part of the wire format so saves and replays are portable across implementation builds.

**Regime is a derived property, not a stored field (NEW v0.129, audit R1 + state-coherence closure).** The `detect_regime` algorithm above is the canonical derivation. State coherence — that regime is consistent with kinematic + warp + cryosleep + BH-proximity state — is enforced at the type-system level: implementations expose regime as read-only, computed from the underlying truth fields (§4.2 StateBus computed field; §4.4 TimeState `kinematic_regime` velocity-only projection). The schema cannot construct an incoherent state (e.g., WARP_CRUISE with zero warp amplitude), and a save file cannot smuggle one past load (§4.6 regime-coherence gate).

**Mutually exclusive at the physics level:** WARP and STL_REL cannot be simultaneous. Warp bubble suspends Newtonian velocity in bubble's frame; `γ_kinematic ≡ 1` during warp. WARP and deep GRAVITY_WELL are bounded by the Warp Exclusion Zone (§7.4): outside `r > 100·r_s`, warp composes with weak GRAVITY_WELL normally; inside, warp is canon-refused.

**Composable:** GRAVITY_WELL with REST, STL_NONREL, STL_REL, or weak warp (outside exclusion zone). Factors multiply.

**The 0.1c STL_REL threshold is a semantic regime label for dispatch optimization, not a physics discontinuity.** All underlying physics formulas (Doppler, ISM impact, time dilation) are continuous functions of β. Implementations blend smoothly across the 0.1c boundary with no discrete jumps in audio, rendering, or behavior. Dispatch is for code-organization; physics is continuous.

**Cryosleep is ballistic coast (NEW v0.125).** CRYOSLEEP implies `a_proper ≡ 0`. The ship is in ballistic coast: rapidity `ζ⃗` is constant (except for gravitational deflection if GRAVITY_WELL is composed), γ remains constant, the ship continues at its current relativistic velocity indefinitely, accumulating `t_cosmic` at the dilated rate. The crew sleeps; the universe ages around them; the spatial coordinate advances by `v_apparent · Δt_cosmic` regardless of crew biological state. Gravitational time dilation continues to apply during cryo if GRAVITY_WELL is composed; this is emergent from the composition rule, intentional, and creates the deep-time-near-BH scenario the book's deep-time arc and the game's stake mechanic both depend on.

**Transition behavior:**
- **STL_NONREL → STL_REL**: smooth, governed by acceleration profile.
- **WARP_CHARGE → WARP_CRUISE**: discrete on charge completion (charge timer hits zero).
- **WARP_CRUISE → WARP_SHUTDOWN**: smooth (controlled) or discrete (emergency dump).
- **STL_* → GRAVITY_WELL**: smooth, gravitational factor ramps as `1/r → r_s/r`.
- **active → CRYOSLEEP**: `a_proper` driven to zero by the propulsion driver before sleep onset; cryosleep cannot begin with non-zero proper acceleration in v0.125 spec.

### 3.4 Doppler / aberration / lensing / retardation framing (continuous)

**Four** distinct optical phenomena, easily conflated:

- **Kinematic Doppler / relativistic aberration** — applies to *background starfield*. Computed from the ship's effective 4-velocity in the local CMB rest frame. Handled by the **Starfield renderer**, using `v_eff`. Inputs:
  - STL_NONREL: `v_eff = v_kinematic`, `γ_eff ≈ 1`. Effects imperceptible.
  - STL_REL: `v_eff = v_kinematic`, `γ_eff = γ_kinematic`. Real SR Doppler `f_obs/f_emit = 1/[γ(1 − β·cos θ)]`. Aberration warps star directions toward forward.
  - WARP_CRUISE: `v_eff = v_bubble_apparent` (visually capped at β ≈ 0.999 to prevent renderer artifacts on the colour-shift formula). Same SR shader math runs for colour; **temporal retardation is the regime-dispatched concern** (see below and §3.11).

- **Metric redshift** — applies to *light passing through the warp bubble boundary or near a gravity well*. Computed from `W(x,t)` and `Φ(x,t)`. Returned by the **Unified Sampler** as `metric_shift` (see §6).

- **Warp geometric lensing** — light rays passing near the warp bubble boundary are bent by `∇W`. Handled by the **Unified Sampler's ray-march step**, which deflects ray direction at each march step by `α_lens · ∇W · Δs`. Produces the Einstein-ring-like distortion of background stars around the bubble. Visually and physically distinct from kinematic aberration (compresses star directions forward) and from metric redshift (shifts frequencies).

- **Temporal retardation (NEW v0.127)** — every visible body is *sampled at retarded time* `t_emit`, not at `t_cosmic`. Handled by the **Observation Calculator** (§6.3) which solves the light-cone equation per body per frame. **Regime-dispatched** apparent-rate formulas (§3.11): SR longitudinal Doppler for STL_REL, classical retarded-time for WARP_CRUISE. The latter goes negative for `v_apparent > c` and produces the visible-orbit-reversal effect. Distinct from the three above because it changes *which moment of the source's history* you see, not *how its light looks when you see it*.

**Four effects, four code paths:**
1. **Kinematic Doppler / aberration** → Starfield renderer (`v_eff`)
2. **Metric redshift** → Unified Sampler output (`metric_shift`)
3. **Geometric lensing** → Unified Sampler ray-deflection (`∇W` in march loop)
4. **Temporal retardation** → Observation Calculator (`t_emit`)

**Redshift composition law (locked v0.127):**

```
1 + z_total = (1 + z_cosmo) · (1 + z_kin) · (1 + z_metric)
```

Multiplicative, not additive. This is how redshifts compose in GR. Three independent physical effects, one composite frequency shift applied to the body's blackbody spectrum to produce its observed colour:

```
λ_observed = λ_emitted · (1 + z_total)
```

Temporal retardation is *not* a redshift — it modifies *which orbital phase* of the body you observe, while the three z-terms above modify *what its light looks like at that phase*. Geometric lensing is also not a redshift — it's a ray-path concern resolved before the photometric composite.

Naming these four distinctions matters because conflating any two produces double-counting bugs. The Unified Sampler does not return a "Doppler shift"; it returns `metric_shift`. The Observation Calculator does not return colour; it returns `t_emit`. Each effect, each module, each code path.

### 3.5 The Warp Dilation Knob (ASTRA-7 canon-default)

`f_warp(W) ∈ [0.0001, 1.0]` is a design parameter.

- Contract-level default: `f_warp(W) ≡ 1` (no proper-time dilation from warp; warp purely displaces coordinates).
- **ASTRA-7 canon-default (operator's design choice, provisional)**: `f_warp(W) = max(0.5, 1 − 0.5·W²)` — gentle dilation at low warp, increasing at high warp. Generates the "tragedy parameter" the book's Part Two and the game's long-arc relational shape both benefit from.

Operator may parameterize differently. Tune empirically.

### 3.6 Spatial update under relativistic motion

The AstraCoord update for ship's universe-position is computed **strictly using `t_cosmic`**:

```
ΔX_universe_per_frame = v_apparent · Δt_cosmic
```

Never `v · Δτ_ship`. Where `v_apparent` is:
- STL regimes: actual velocity in CMB rest frame
- WARP_CRUISE: bubble apparent velocity (design knob)
- CRYOSLEEP: preserved from pre-sleep state (ballistic coast)

This is the spatial-desync fix. **In the STL_REL regime** (where `γ_kinematic` is the sole non-trivial factor in the composition rule), `γ · v · Δτ_ship` is identically equal to `v · Δt_cosmic` since `dt_cosmic = γ · dτ_ship` reduces to a single multiplicative factor. **In WARP_* and GRAVITY_WELL composition** the composition rule has additional terms (`f_warp(W)`, `√(1−r_s/r)`) and the simple γ-only identity does not hold. The locked spatial-update form (`v_apparent · Δt_cosmic`) is correct in all regimes because it always integrates in cosmic time directly; only the v0.125 derivation prose was regime-locked, not the rule itself. Always compute coordinate advance in cosmic time. Crew time governs ASTRA perception only.

### 3.7 Numerical precision discipline — 3-vector rapidity

At extreme γ (e.g., γ ~ 10⁶ during a hypothetical relativistic-STL cruise to deep time), naïve single-precision computation of `1 / √(1 − β²)` loses accuracy catastrophically. Additionally, scalar-rapidity integration cannot represent 3D maneuvering at relativistic speeds — thrust perpendicular to velocity rotates the velocity vector, which a scalar magnitude cannot capture.

**Locked discipline:** Integrate ship velocity in **3-vector rapidity space**. Define rapidity vector:

```
ζ⃗ = v̂ · arctanh(|v|/c)
```

where `v̂` is the unit vector along ship velocity in the local CMB rest frame. Under proper acceleration `a⃗_proper`:

```
dζ⃗/dτ_ship = a⃗_proper / c
```

Derived kinematics at output:

```
ω = |ζ⃗|                          (scalar rapidity magnitude)
v⃗ = c · tanh(ω) · (ζ⃗ / ω)        (velocity vector, |v⃗| < c by construction)
γ = cosh(ω)                       (Lorentz factor, numerically stable at all magnitudes)
β = tanh(ω)                       (velocity magnitude / c)
```

Parallel thrust grows `|ζ⃗|`; perpendicular thrust rotates `ζ⃗` without exceeding c. The scalar formulation is recovered as a degenerate case when `a⃗_proper ∥ v̂`.

**Thomas-precession scope bound:** The rapidity-vector formulation `dζ⃗/dτ_ship = a⃗_proper/c` neglects Thomas precession (Wigner rotation) effects on velocity direction over sustained perpendicular burns at extreme γ. Accepted first-order approximation for v0.1; full Lorentz-transformation stepping is out of scope unless playtest reveals trajectory drift. Negligible at game-scale time steps; matters only for multi-year corkscrew maneuvers at γ > 10⁴.

**`a⃗_proper` provenance:** `a⃗_proper` is a State Bus quantity (§4.2) owned by the propulsion driver. The Time Contract integrator reads it during rapidity integration. It is not a parameter of `step(Δt_cosmic)`.

**Lock:** adaptive RK4 (RK45) on 3-vector rapidity `ζ⃗`, not on velocity `v⃗`. Tolerance: γ accuracy to 4 significant figures at γ ≤ 10⁷.

**Clamp (v0.126 fix):** `|ζ⃗| ≤ ω_max ≈ 16.811`, giving `γ_max = cosh(ω_max) ≈ 10⁷` and corresponding `β_max ≈ 1 − 5·10⁻¹⁵`. The v0.125 clamp value `arctanh(0.99999999)` was mathematically inconsistent with the stated `γ_max ≈ 10⁷`: with eight nines after the decimal, `β = 0.99999999`, `1−β² ≈ 2·10⁻⁸`, `γ = 1/√(2·10⁻⁸) ≈ 7071`. To reach `γ = 10⁷` requires ω ≈ 16.811, corresponding to β with ~15 nines after the decimal, not 8. The correct clamp specification lives in ω-space directly: `ω_max ≈ 16.811`. Phase 0+ measurement may refine; never re-derive from β.

**Catastrophic-cancellation discipline (NEW v0.126):** Compute all derived kinematic quantities from `ζ⃗` and `ω = |ζ⃗|` directly via `tanh` and `cosh`. **Do not round-trip through β to compute γ.** At high ω, β representation in float64 is `1 − ε` where `ε ≈ 5·10⁻¹⁵` near the clamp; computing `γ = 1/√(1 − β²)` suffers catastrophic cancellation in the subtraction `1 − β²` and loses all meaningful precision. The rapidity discipline's whole point is to avoid this pathology — round-tripping through β re-introduces it. Locked path: `γ = cosh(ω)`, `β = tanh(ω)`, `v⃗ = c · tanh(ω) · (ζ⃗ / ω)`. Implementers must never compute `γ = 1/√(1 − β²)` directly except as a debug-print sanity check at low ω.

This applies to STL_REL acceleration phases especially. During non-relativistic motion, the rapidity formulation reduces to standard kinematics with negligible overhead.

### 3.8 Distributed simultaneity

ASTRA's substrate is distributed across the ship's cognitive cores. Under relativistic acceleration at γ < 100 and ship length ~100m, simultaneity offsets between primary and redundant nodes are <10⁻⁵ s — negligible for cognition.

**Lock:** primary cognitive node's clock is canonical. Redundant nodes synchronize via Lamport timestamps with bounded drift. Not strictly relativistically accurate but consistent and substrate-honest.

### 3.9 Cryosleep journal generator's dual-clock awareness

When the crew enters cryosleep during STL_REL (or any regime), `τ_ship` continues advancing slowly on metabolic ε; `t_cosmic` continues at its own rate. The ship is in ballistic coast (§3.3). The journal-generator ephemeral instance must reference *cosmic-time landmarks* (stars that evolved, structures that drifted) covering the experienced `τ_ship` duration.

**Lock the journal-generator's input contract:**
```
(τ_ship_start, τ_ship_end, t_cosmic_start, t_cosmic_end,
 regime_history, BH_list, body_state_diff, ζ⃗_at_sleep, ζ⃗_at_wake)
 → journal_entries
```

The generator has access to both clocks and produces entries referencing cosmic-time events while preserving ASTRA's in-voice register.

**Output validation:** Journal output is itself subject to the wall-clock-leak detector (§5.7) before commit to REEL. Cosmic-time landmarks ("the slow drift of the dust lane", "Vega had moved a fraction of a degree") are permitted; absolute-date references, metabolic-clock leaks, and Earth-calendar idioms are not. See §10 validation row.

### 3.10 The contract specification

The full Time Contract is specified in §4.4. The prose above leads up to it; the formal contract block is the lock.

### 3.11 Retarded-Time Observation Principle (NEW v0.127)

Every visible body is sampled at *retarded time*, not at `t_cosmic`.

```
t_emit(B) = t_cosmic_now − Δt_light(B)
```

where `Δt_light(B)` is the proper time for light to travel from the body's worldline to the ship. The Kepler solver (§3.1, §4.2) continues to evolve body state on `t_cosmic`; the *renderer* queries `body_state(t_emit)`, not `body_state(t_cosmic)`. One parameter change in the calling code; no change to the solver.

This is the fourth optical effect named in §3.4. It is orthogonal to kinematic Doppler (frequency from relative motion), metric redshift (frequency from W and Φ), and geometric lensing (ray direction from ∇W). Temporal retardation changes *which moment in the body's history is observed*.

**Regime-dispatched apparent-rate formula (locked v0.127):**

The rate at which a body's history advances per unit ship-observer time is `dt_emit / dt_recv`. The formula depends on regime:

```
STL_REL  (inertial v<c, SR longitudinal Doppler):
    dt_emit / dt_recv = √((1 − β) / (1 + β))
    where β = v_radial / c, v_radial > 0 for recession.
    Asymptotic to 0 as β → 1. NEVER negative. Inertial motion in flat
    spacetime cannot produce reverse playback.

WARP_CRUISE  (bubble crew at γ_kinematic ≡ 1, geometric recession):
    dt_emit / dt_recv = 1 − v_apparent / c
    where v_apparent is the bubble's apparent velocity in the macro-grid frame.
    Equals 0 at v_apparent = c (frozen image).
    Strictly NEGATIVE for v_apparent > c (reverse playback).
    The classical retarded-time formula applies because the bubble crew
    is locally inertial; the recession is geometric (sectors iterating),
    not kinematic.

REST / STL_NONREL:
    dt_emit / dt_recv ≈ 1 − v_radial / c  (linear, fine for small β)
```

The two regimes obey *different physics* and the formulas have *different functional forms*. **This is not an interpolation gap.** STL_REL is inertial motion through space; WARP_CRUISE is metric deformation carrying a locally-flat-spacetime bubble. The boundary at `v_apparent = c` is where one physics ends and another begins.

**The discontinuity at v_apparent = c is a design feature, not an artifact.** Engaging warp produces a perceptual *snap*: the visible universe behind the ship freezes (rate → 0 from positive in STL, → 0 from below in WARP at engagement), then inverts as warp accelerates past c. This snap is the moment of causality-violation rendered visible. **Do not smooth across the boundary.** The spec specifically forbids smoothing; the snap is the rendering of warp's qualitative difference from inertial motion.

**Photon-source-history bound (locked v0.127):**

Under sustained `v_apparent > c` recession from a source, `t_emit` retreats monotonically into the source's past. For a source whose first emission was at cosmic time `t_start`, there exists a finite `t_recv_max` such that for all observation times beyond it, the ship has *overtaken every photon the source has ever emitted*. After this, the source is **gone** — not faded, not redshifted to extinction, *gone, because no photon remains to be received*. Render: source is absent from the frame; no afterimage; no asymptotic dim.

This is distinct from Hubble-horizon decoupling (§3.12), where photons cannot reach the ship because expansion outruns them. Here, the photons exist but the ship is past them in spacetime.

**Implementation note:** retarded-time solving for a stationary source under uniform ship velocity is closed-form. For a moving source under varying ship velocity, Newton-Raphson iteration converges in 2-4 steps (body motion during light-flight is slow compared to c for any reasonable source). For very distant starfield (Mpc+ distances), the static `t_emit ≈ t_cosmic − d/c` offset suffices and per-frame iteration is unnecessary.

**Edge cases (provisional v0.127):**
- Body inside warp bubble (co-moving with ship): no retardation; render at `t_cosmic`.
- Body beyond Hubble horizon: render frozen at horizon-crossing instant, redshift to extinction (§3.12).
- Body within Schwarzschild horizon: rendered via standard horizon-crossing limitation (§7.4 horizon-crossing deferred to Phase 5+); full geodesic retarded-time integration deferred.

**Locked surface:** every render-path body query routes through the Observation Calculator (§6.3). No module computes `body_state(t_cosmic)` for rendering. The Time Contract still evolves on `t_cosmic`; observation is a derived query, not a state mutation.

### 3.12 Cosmological Expansion Operational Mechanic (NEW v0.127)

The universe expands. Distant bodies' AstraCoord positions drift over `t_cosmic` by Hubble flow:

```
v_Hubble(r) ≈ H₀ · r
```

For v0.127, the linear approximation suffices:

```
z_cosmo = H₀ · d_proper / c     (valid for z < 0.1)
```

Full FLRW integral form (deferred to Phase 4+):

```
z_cosmo(d) = (H₀ / c) · ∫₀ᵈ dr / √(Ω_m · (1+z(r))³ + Ω_Λ)
```

`z_cosmo` composes multiplicatively with `z_kin` and `z_metric` per §3.4. The cosmological redshift contribution is small at intra-galactic scales (~0.07c at AstraCoord's 974 Mly edge) but real and named.

**Hubble horizon (locked):**

```
d_H = c / H₀ ≈ 4.4 Gpc ≈ 14.3 billion light-years (provisional H₀)
```

Bodies beyond the Hubble horizon recede from the ship faster than light from them can travel inward. Their light reaches the ship as an asymptotically-decaying frozen frame at horizon-crossing, then fades to extinction over cosmic time. **Render: frozen at horizon-crossing instant, dim and redshifted, fading on a separate timescale than the photon-source-history bound (§3.11).**

The Hubble horizon is the hard outer edge of what is observable from the ship at any voyage length. AstraCoord's 974 Mly reach is well inside this horizon; cosmological horizon effects are render-only and do not affect AstraCoord state.

**Look-back time correction (NEW v0.127):**

For bodies at non-negligible `z_cosmo`, the look-back time exceeds the naive `d/c` because space expanded while the light was in transit:

```
Δt_light ≈ (d_proper / c) · (1 − 3 · z_cosmo / 4)     (z < 2)
```

This is the standard flat-ΛCDM weak-z correction. The Observation Calculator (§6.3) applies it.

**`H₀` is canonical and adjustable:**

The Hubble constant is operator-tunable as a State Bus constant. Real H₀ ≈ 70 km/s/Mpc is provisional; the game's H₀ may differ if narrative or simulation pacing demands. Locked: the *form* of the redshift composition (multiplicative), the *form* of the look-back correction (linear in z for v0.127), and the *fact* of a Hubble horizon. The *value* is data.

---

## 4. The Eight Core Contracts

### 4.1 Substrate Contract

Defines what any LLM must provide to be ASTRA's substrate.

**Locked operations:** token-streamed completion, tool-call support (or JSON output the adapter LLM can validate), vision input, inference parameter modulation (T, top_p, top_k, max_tokens) at call time, sysprompt grounding.

**Tolerance ranges:** 7B–70B parameters, FP16/BF16/Q4/Q5 quantization, transformer / mamba / hybrid architectures, context window ≥ 8K minimum, **128K target, 256K+ headroom** (NEW v0.128 — was 32K target; updated against Qwen 3.x Delta-Net hybrid-attention baseline plus TurboQuant KV-quantization stacking; provisional pending measurement on 5090 with shared graphics VRAM), any inference framework satisfying the operations.

**Invariant:** harness never depends on specific model family. Model swap requires only: new sysprompt loader call, new LoRA load, new tokenizer config. No harness code changes.

**Failure:** primary substrate crash → adapter LLM fallback (1–3B model, always resident) for safety-critical tool calls. ASTRA "goes offline" in fiction.

### 4.2 State Bus Contract

GPU-resident shared world state.

**Locked schema** (Layer 0):

```
- AstraCoord                (128-bit composite tensor; §1.1)
- TimeState                 (t_cosmic, τ_ship, τ_crew_bio, rapidity ζ⃗;
                             kinematic_regime exposed as velocity-derived
                             READ-ONLY projection — see §4.4; NEW v0.129)
- WarpState | None          (NEW v0.129; audit D3 closure):
    W:               float ∈ [0,1]        (warp coil intensity)
    phase:           Literal["charging","cruising","dropping","shutdown"]
    charge_progress: float ∈ [0,1]        (meaningful in "charging" only)
- cryosleep_active: bool    (NEW v0.129; root-level flag)
- regime                    (NEW v0.129; COMPUTED field at StateBus root —
                             never settable; derived from rapidity + warp +
                             cryosleep + BH proximity per §3.3 detect_regime)
- ShipKinematicState        (v_local_cmb, γ, β, grav_factor, dτ/dt — a DERIVED
                             VIEW; fields are computed, never stored
                             independently of ζ⃗; NEW v0.129)
- a_proper: float3          (ship-frame proper acceleration; owned by propulsion driver, read by Time Contract; NEW v0.125)
- HullSDF                   (256³ texture + additive damage map; §1.3)
- CFD-RBF warp field network (~1000 nodes, ~64 KB)
- ChaosField χ(x,t)         (double-buffered; §1.5)
- PowerAllocation vector    (locked subsystem list; §1.4)
- ProceduralBodyState       (Keplerian elements per body, hash-seeded)
- BHList                    (M, position, J=0 for v0.1)
- AtmosphereState, HydroponicsState (per-room scalars)
- PropulsionMode flag       (regime bitmask; canonical values §3.3)
- CosmologicalConstants     (NEW v0.127):
    c:    float64 = 299792458.0          (m/s, exact by definition)
    H₀:   float64 = 70.0                 (km/s/Mpc, provisional)
    Ω_m:  float64 = 0.3                  (matter density parameter, provisional)
    Ω_Λ:  float64 = 0.7                  (dark energy density parameter, provisional)
                              (flat ΛCDM: Ω_m + Ω_Λ ≡ 1)
```

**Locked operations:**
- **Read:** non-blocking, double-buffered, frame-coherent.
- **Write:** only via designated physics drivers, atomic per-frame, applied at frame swap.

**Invariant:** no system maintains private copies. State Bus is the single source of truth. (One instance of the Frozen-Snapshot Primitive, §15.9.)

**Regime placement (NEW v0.129, resolves the v0.128 §4.2-vs-§4.4 ambiguity / audit R1):** the composite `regime` lives as a computed field on the StateBus root; `TimeState` exposes only `kinematic_regime`, the velocity-derived projection used internally by `detect_regime`. Implementations must NOT permit caller-supplied regime values that contradict the derived computation.

### 4.3 Master Contract (Perception / Action / Reflex)

Only crossing point between World Kernel and Mind Kernel. **Three sub-channels.**

**Perception** (Mind input, every conversational turn):
- HUD render (vision-routed; primary)
- Compact text somatic banner (fallback / supplement; **signal-grounded via the Somatic Aggregator, §6.3.1 — NEW v0.129**)
- REEL retrievals (top-k by salience)
- Recent conversation buffer
- Audio transcript (offline ASR; same channel as console text input — see §4.10)
- TimeState summary (τ_ship "now", regime, current dilation ratio inferred-not-leaked)

**Action** (Mind output, STAGE protocol revised v0.128):
- **Three output channels + silence** (down from v0.127's five-channel framing):
  - `<think>...</think>` — private cognition, stripped via three-layer defense
  - `<tool name="...">{json-or-loose}</tool>` — ship API invocation; adapter LLM normalizes to validated JSON
  - **default-untagged prose** — anything outside `<think>` or `<tool>` is SPEECH → offline TTS
  - **SILENCE** — empty output is a legal primitive (she chose not to speak); not a degenerate case
- **Channels dropped from v0.127's STATUS / SOMATIC channels:**
  - STATUS folds into either a `<tool name="status_log">` call OR the prose channel; no separate output route
  - SOMATIC is **input only** (harness-generated banner in the perception bundle); never an output channel — her felt-state is something she receives, not something she emits. The banner is composed deterministically from `SomaticSignal` events per §6.3.1 (NEW v0.129).
- **Order rule:** `<think>` first (matches reasoning-model training distribution); `<tool>` and speech can interleave freely after
- Full grammar specification (input bundle, output channels, parser fallback rules, adapter LLM normalization, failure modes) lives in `docs/stage-protocol.md` v0.1 (forthcoming)
- `<think>` block stripped (defense in depth at three layers — LoRA discipline + sampling grammar + regex post-filter)

**Reflex** (in-band, frame-rate, separate channel):
- Input: 64×64×2 chaos+metric observation grid, every frame
- Output: 3-float control vector (nacelle damping, conformality, emergency dump)
- Latency budget: ≤ 50 μs naive, ≤ 20 μs with CUDA Graphs
- No conversation perception, no speech. Pure autonomic.

**Invariants:**
- No wall-clock leak in Perception
- No technical-substrate leak in Perception (no "Qwen", "LLM", etc.)
- Think block stripped via three independent mechanisms
- Reflex never touches Mind's conversation channel; Mind never touches Reflex's
- **The Power Contract (§4.5) is the only system that modulates both Mind and Reflex envelopes simultaneously**, via cognitive-cores subsystem allocation.
- Tool calls validated by adapter LLM, not executed directly.
- **c-bounded epistemology (NEW v0.127, consequence-framed):** ASTRA has no access to the current state of any region outside her own light-cone past. The universe is always a record of what was, never what is. All distant-body perception arrives via retarded-time observation (§3.11); the Observation Calculator (§6.3) is the only path by which exogenous state enters Perception. This is QC1 (enforced self-opacity, §11) extended outward: not just *she cannot bypass her own HUD encoder*, but also *she cannot bypass light-speed*. Her epistemology is perception-mediated all the way down — there is no privileged channel into either her own raw state or the universe's current state.
- **Endogenous vs exogenous sensor split (NEW v0.127):** Perception channels are categorized by physical origin. **Endogenous** (local hull, ship interior, internal diagnostic): read at `t_cosmic`. **Exogenous** (universe-distant, photon/particle flux from outside the bubble): read at `t_emit`, regime-dispatched per §3.11. The split generalizes to any future sensor channel. Audio (hull-internal): endogenous. Starfield (universe-distant photons): exogenous. The eye-ear decoupling at warp (§8.3) is one instance of this principle.

### 4.4 Time Contract (the locked block)

```
TIME CONTRACT (locked, parameters provisional)

state:
  t_cosmic: float64
  τ_ship: float64
  τ_crew_biological: float64           # pauses on cryosleep (metabolic ε)
  rapidity_vector ζ⃗: float3            # primary kinematic state variable (NEW v0.125)
  a_proper: float3                     # read from State Bus, not a step() parameter
  kinematic_regime: bitmask            # velocity-derived PROJECTION only
                                       # (REST / STL_NONREL / STL_REL); READ-ONLY,
                                       # derived from ζ⃗ — never stored (NEW v0.129).
                                       # The COMPOSITE regime (adds WARP_*,
                                       # GRAVITY_WELL, CRYOSLEEP) lives at the
                                       # StateBus root as a computed field (§4.2);
                                       # canonical hex values §3.3
  v_local_cmb: float3                  # derived: c · tanh(|ζ⃗|) · (ζ⃗ / |ζ⃗|)
  bh_list: [(M, position, J=0)]        # Schwarzschild only in v0.1; Kerr out of scope

operations:
  step(Δt_cosmic) → updates all state per composition rule and regime dispatch
                    reads a_proper from State Bus
                    integrates ζ⃗ via adaptive RK45 (3-vector rapidity space)
                    updates AstraCoord by v_apparent · Δt_cosmic
  apparent_velocity(state) → v_apparent for spatial updates
  dilation_ratio(state)    → dτ_ship / dt_cosmic at current state
  detect_regime(state)     → bitmask (§3.3)
  assemble_perception_time_summary(state) → safe time-state for ASTRA (no wall-clock leak)

invariants:
  kinematic_regime is a derived property of rapidity_zeta; never stored
    independently. The full composed regime lives at StateBus root (§4.2);
    no implementation may accept a caller-passed regime that contradicts
    the derivation (NEW v0.129)
  dτ_ship / dt_cosmic ∈ (0, 1]
  γ stable to 4 sig figs at γ ≤ 10⁷ via 3-vector rapidity integration
  |v⃗| < c strictly (tanh-bound by construction)
  in WARP regime: γ_kinematic ≡ 1
  Δx_universe per frame = v_apparent · Δt_cosmic  (never · Δτ_ship)
  GRAVITY_WELL composes with all other regimes via potential summation
  gravitational factor continuous in r and Φ across all distances;
    no piecewise discontinuities in dτ/dt
  0.1c threshold is semantic (regime label); physics formulas continuous in β
  cryosleep: a_proper ≡ 0; ζ⃗ constant under no-gravity composition
              (gravitational deflection permitted if GRAVITY_WELL composed)
              τ_ship advances at metabolic ε; ship-as-inertial-frame continues

tolerances:
  γ accuracy: 4 sig figs at γ ≤ 10⁷
  Schwarzschild approx valid for r > 10·r_s; below → geodesic-domain fallback (out of v0.1 scope)
  Kepler solver valid for r > 100·r_s; below requires 1PN correction (provisional, Phase 4+)
  Warp Exclusion Zone: r > 100·r_s for warp engagement (§7.4)
  Thomas precession neglected for v0.1 (§3.7); deferred to v0.2+ pending playtest

failure:
  γ overflow → clamp |ζ⃗| to ω_max ≈ 16.811 (giving γ_max ≈ 10⁷; v0.126 fix); mark warning, emit STAGE-SOMATIC
  numerical singularity at r → r_s → trigger geodesic-domain fallback or navigation refusal
  regime transition during integration → finish current sub-step, re-evaluate regime, continue

versioning:
  schema version 3 (v0.1 = v1, v0.123 = v2, v0.125 = v3; rapidity-vector promotion increments)
```

### 4.5 Power Contract

Zero-sum across the locked subsystem list (§1.4).

**Locked:**
- Subsystem list immutable without contract amendment
- Cognitive cores allocation → directly modulates Substrate compute envelope
- Critical-subsystem underflow alarms (life support, cognitive cores)
- ASTRA-Reflex on warp-coupled sub-bus: receives guaranteed minimum power whenever warp drive is active

**Tolerable:** reactor capacity (configurable per ship class), priority weights, response curves.

### 4.6 Persistence Contract

**Save seeds, not state.** Procedural state regenerates from seeds + mutations.

**Locked save file schema** (versioned):

```
SaveFile v3 (v0.125):
  schema_version: 3
  t_cosmic: float64
  τ_ship: float64
  τ_crew_biological: float64
  rapidity_vector ζ⃗: float3      # 3-vector form (was scalar ω in v0.123)
  a_proper_at_save: float3        # snapshot for reload continuity
  AstraCoord (ship): sector + local
  ShipKinematicState: full
  regime_bitmask + regime_history: state-machine state + recent transitions
                                    # canonical hex values per §3.3
  HullMutations: array of damage events (applied to base SDF on load)
  PowerAllocation: full snapshot
  WarpState: { phase, W, charge_progress }
  AI:
    Mind: conversation history,
          REEL entries (canonical field set, NEW v0.129 — implemented and
          wire-tested; replaces the v0.125 inline placeholder):
            tau_ship: float64                  # τ_ship at write (required)
            t_cosmic_at_write: float64         # required; dual-clock per §3.9
            body: str                          # prose, ASTRA's voice
            irreversibility_flag: bool         # QC3 per §11
            t_emit_event: Optional[float64]    # observed-distant events: when
                                               # the event happened at the
                                               # source; pairs with
                                               # t_cosmic_at_write (arrival).
                                               # Source distance reconstructs as
                                               # c·(t_cosmic_at_write − t_emit_event)
            regime_at_write: int               # §3.3 bitmask snapshot
            author_instance_id: str            # main | consolidator |
                                               # journal_generator | drift_detector
            retrieval_metadata: dict[str,str]
          (docs/reel-spec.md remains reserved for the canonical-REEL-protocol
          reconciliation — ring architecture etc.; this inline set is the
          locked SaveFile wire format.)
    Reflex: model identity + weights checksum + training_corpus_version
            (frozen, no per-game evolution; NEW v0.129 per §2.3.1)
  PlayerChoices: array of choice events (regime transitions, etc.)
```

**Load behavior (deterministic):**
1. Reconstruct base HullSDF from asset
2. Apply HullMutations in order
3. Re-evaluate orbital state from `t_cosmic` (analytic, instant)
4. Re-generate starfield from AstraCoord (procedural, instant)
5. Re-evaluate dilation_ratio from kinematic state (`ζ⃗`, BH list)
6. **Re-initialize chaos field via forward integration from baseline-noise** (seeded RNG from save's `t_cosmic`) under the current warp amplitude W, gravity factor, and α value. Run **until convergence**: either `N = 60` frames OR `|χ̇_max| < ε_convergence` (provisional), whichever comes first. Deterministic given seed. This converges to the correct basin for the current parameters; lookup table is rejected because it cannot handle multi-basin selection or parameter shifts; zero-init is rejected because zero is not necessarily a stable steady state for Fisher-KPP-type PDEs near critical parameters.
7. Restore Mind state from conversation history + REEL

**Regime-coherence load gate (NEW v0.129, implemented-first):** the reconstructed state RE-DERIVES regime from the underlying truth fields (rapidity + warp + cryosleep per §3.3/§4.2) and the result must equal the stored `regime_bitmask`; mismatch is a coherence error, and recovery proceeds through the rolling backups. The serialized regime value is an echo for the wire format, never an input — a hand-edited save cannot smuggle an incoherent regime past load.

**Locked:** save-seeds-not-state, versioned schema with migration scripts, forward compatibility, chaos field convergent-forward-integration re-init, regime-coherence load gate.

**Tolerable:** specific binary format, compression.

**Failure:** save corruption → rolling N-deep backup (N=3 minimum) auto-recovers from most recent valid.

### 4.7 Failure Contract (graceful degradation)

**Locked degradation ladder:**

- **Priority 1, NEVER degrade**: State Bus consistency, AI tool call validation, Power network accounting, fictional time advancement, Time Contract invariants
- **Priority 2, degrade gracefully**: warp field resolution (full → half-res), ray-march steps (256 → 128 → 64), Mind inference frequency, starfield count, chaos field resolution
- **Priority 3, degrade visually**: Lumen quality, shadow resolution, post-process
- **Priority 4, degrade with gameplay impact**: Mind model swap (27B → 9B → adapter-only), audio layer count, Reflex observation grid resolution
- **Hard failures, no graceful path**: substrate hosting, minimum 8K context, basic GPU functionality

**Specific failure-mode commitments:**
- LLM crash → adapter LLM fallback; ASTRA "goes offline" in fiction
- Reflex numerical instability → emergency dump available; if not taken, warp collapses
- GPU crash → autosave; restart from last checkpoint
- Save corruption → rolling backups
- Audio failure → silent fallback, never crash

**Adapter LLM resident memory:** ~1–3B model in VRAM as failsafe. **On RTX 5090 with 27B + LoRA loaded (~16 GB), adapter ~2–4 GB fits comfortably (provisional, to be measured).**

**Reflex failure-mode table (NEW v0.129, per §2.3.1):**

| Failure | Detection | Recovery |
|---|---|---|
| Weights mismatch (checksum) | start-of-game SHA-256 verify | Reflex "goes offline"; warp engagement refused until canonical weights restored |
| Inference timeout (> 50 μs sustained N frames) | health() latency telemetry | emergency_dump auto-trigger → WARP_SHUTDOWN; somatic banner to Mind |
| Warp sub-bus underflow | Power Contract alarm (§4.5) | controlled WARP_SHUTDOWN; cannot occur while warp active by §1.4 guarantee — defense-in-depth path only |
| Observation grid stale (frame skip) | frame-counter delta | skip inference that frame; log telemetry; sustained staleness escalates to timeout path |
| Control output out-of-envelope | apply() clamp check | clamp + log + drift_detector audit entry |

**Mid-session model swap continuity:** design intent locked; protocol specified in `docs/model-swap-continuity.md` (forthcoming, §5.9.1 reference); implementation deferred to v2.

### 4.8 Privacy / Network Contract

**Hardest lock. Non-negotiable.**

- After install, zero outbound network calls. Period.
- No telemetry, no analytics, no crash reports phoning home, no model-update checks.
- Every dependency audited at build time for hidden network activity.
- All inference local. All audio local. All save files local.
- Save files never leave the user's machine unless explicitly exported.
- Sharing logs/transcripts with developer is opt-in, manual, outside game runtime.

Values commitment, not engineering preference. Part of the autotelic claim.

### 4.9 Harness Contract

The harness is a load-bearing module. Lock its contract surface as first-class.

**Schema (HarnessState, persisted):**
```
- ephemeral_instances: list of {role, status, work_queue, last_artifact}
  roles include: consolidator, journal_generator, drift_detector
- REEL_retrieval_index: searchable index for RAG lookups (rebuilt from REEL entries)
- pending_tool_calls: list of {call_id, started_τ_ship, timeout_τ_ship}
- maintenance_schedule: next consolidator window, next drift audit
- ASR/TTS state: audio buffer pointers, voice profile selection (canon-only)
```

**Locked operations:**
- `assemble_perception(state, t_now) → PerceptionBundle` — composites HUD render + somatic banner + REEL retrievals + recent conversation + audio transcript + safe time-state summary
- `dispatch_action(action_bundle) → side_effects` — strips `<think>`, validates tool calls via adapter LLM, applies to State Bus through the physics-driver write paths per §4.2 (v0.126 terminology fix; v0.125 said "Physics Contract entrypoints" which was undefined elsewhere)
- `consolidate_reel(window) → REEL entries` — spawned during maintenance; reviews recent conversation, scores salience, produces clean long-term entries, sets `irreversibility_flag` per the canonical QC3 event-class list (packaged in-implementation at `astra/harness/ephemeral/canon/qc3_events.txt`; v0.128's `tests/qc3_events.txt` path was packaging fiction — runtime code never reads from tests/)
- `generate_journal(τ_ship_range, t_cosmic_range, regime_history, ζ⃗_at_sleep, ζ⃗_at_wake) → journal entries` — dual-clock aware (§3.9); output subject to `enforce_no_wall_clock`
- `detect_drift(recent_turns) → correction artifact or NONE` — audit register, ephemeral instance
- `enforce_no_wall_clock(perception_bundle | journal_entries) → cleaned` — scans for wall-clock-leak patterns per §5.7 against the canonical pattern files (packaged at `astra/grammar/canon/wall_clock_patterns.txt`; realized in textverse as `LeakDetector.scan_journal_output` / `scan_perception_bundle`)

**Implementation status (NEW v0.129):** all three ephemeral roles are implemented to these locked signatures as deterministic pure functions (2026-06-10; LLM-voiced paths arrive later behind the same signatures). Orchestrator maintenance-window wiring follows when scenarios exercise it.

**Invariants:**
- Harness enforces the no-wall-clock invariant at both (a) `assemble_perception` boundary (last-chance gate for Perception bundles) and (b) `generate_journal` output boundary (last-chance gate before REEL commit)
- Tool calls always validated through adapter LLM before reaching ship API
- Ephemeral instances do not interact with each other directly; only with the State Bus and Mind Kernel's REEL
- Harness internal state is canon-locked (not mod-friendly); only the persona content (sysprompt, LoRA) is moddable

**Tolerable:**
- ephemeral instance pooling strategy (warm pool vs spawn-on-demand)
- REEL retrieval index structure (BM25 / dense vectors / hybrid)
- maintenance scheduling heuristics

**Failure:**
- Ephemeral instance failure → log to REEL, continue with degraded coverage (one instance offline does not stop the others)
- Adapter LLM crash → fail the tool call gracefully; ASTRA receives "tool call failed" through Action channel, surfaces via SPEECH or STATUS

### 4.10 Console UI / Text Input Contract

Player text input enters the conversation channel via the same path as ASR-transcribed voice. The Perception bundle does not distinguish whether operator input arrived via voice or via console text — both end up in `audio_transcript` (renamed `operator_input` in v0.2+).

**Locked:**
- Player text and voice unified through conversation-channel ingest
- No separate "type to ASTRA" perception bundle field
- ASTRA receives operator input as words regardless of modality. **Modality-specific response shifts (more formal for typed, more casual for voice) are a consistency anti-pattern, not a Dave-frame violation.** The unified channel prevents both: ASTRA's voice register is hers, not modality-conditioned. Dave-frame is preserved separately by other invariants (no game-meta-level facts in Perception). The conceptual distinction matters for future maintainers reading the rationale — ASTRA *could* coherently know whether the operator spoke or typed without breaking Dave-frame; we hide the distinction because shifting register on modality would degrade her voice consistency.

**Tolerable:**
- Dev-build direct API exists for low-level diagnostic operations (bypassing ASTRA); gated to debug builds and explicit opt-in
- Specific console UI presentation (CLI-style, GUI, voice-only, etc.) is implementation choice

**Phase 2+ refinement:** further design as the vertical slice surfaces interaction needs.

---

## 5. The Disciplines (rules, not contracts)

### 5.1 Module Dependency DAG, acyclic

Every module declares its dependencies. Graph verified acyclic at build time.

```
State Bus ← Physics Drivers ← Player input
   ↑              ↑
   │              │
 Rendering    Harness (Mind Kernel boundary)
 Audio        Reflex (in-band, World Kernel)
```

### 5.2 Anti-patterns named negatively

Must not exist:
- **Smart Object** — modules dumb about each other; intelligence in the fabric
- **Event Cascade** — physics propagates through state mutation, not event chains
- **God Object** — State Bus is the only shared object, pure data
- **Time Accident** — one `t_cosmic`, one `τ_ship`, always
- **Hardcoded Model** — no "Qwen" or "llama.cpp" references outside the harness
- **Trusting Generated Code** — model-generated implementation is *untrusted* until compile + execute + measure

### 5.3 Determinism Boundary + Replay Format

**Locked scope (honest declaration):**

- **REPLAY-EXACT:** frame index, regime transitions, AI inputs and outputs, REEL entries, all player choices, all State Bus writes' high-level deltas. `ε < 10⁻⁴ s` drift in (`τ_ship`, `t_cosmic`) per game-hour. Sufficient for AI-behavior debugging and high-level bug reproduction.
- **REPLAY-APPROXIMATE:** spatial trajectory bounded but not micron-exact. Accumulated spatial drift `< 1 m / game-hour Newtonian`, `< 100 m / game-hour STL_REL`. Over long voyages, kilometers of spatial drift expected; this is acceptable because replay is for AI-behavior reproduction, not navigation re-verification.

**Implication:** every random source in World Kernel is seeded explicitly. Every reduction has specified order. Every `atomicAdd` is documented as a determinism-breaker. Replay file records AI outputs explicitly rather than regenerating them (since Mind is stochastic). Bugs surfacing only at sub-meter spatial resolution require seeded reproduction from scratch, not replay-from-log.

**Replay file format:** `{ frame_index, t_cosmic, τ_ship, regime_bitmask (canonical hex), player_input, ai_outputs, irreversibility_flag_deltas }[]`. Small, complete, sufficient for bug reproduction.

### 5.4 Eval Harness from Day One

Property-based scenario tests. Examples:
- "Given ship state X and player input Y, ASTRA's response must call tool Z and contain no em-dashes."
- "Given warp regime, dilation ratio must satisfy Time Contract invariants."
- "Given hull damage of magnitude M, chaos field response must satisfy stability bound."

Every change passes evals before merge. Day-one discipline.

### 5.5 Bundle Reproducibility

Sysprompt, training data, LoRA configs, inference settings, harness version — all version-controlled. Bundle manifest declares everything. The exact ASTRA bundle that ships v1.0 is reconstructible from the manifest six years later.

### 5.6 Frame Budget Allocation (provisional numbers)

At 60 FPS = 16.67 ms total per frame:

- Physics drivers: ≤ 4 ms (provisional)
- Rendering (excluding warp): ≤ 6 ms (provisional)
- Warp volumetric ray-march: ≤ 4 ms half-res / ≤ 10 ms full-res (with fallback)
- Audio extraction: ≤ 0.5 ms (GPU-pinned)
- **Reflex inference: ≤ 50 μs naive, target ≤ 20 μs with CUDA Graphs**
- ASTRA-Mind cognition: out-of-band entirely; not in frame budget
- Reserve: ≥ 2 ms

Each module pre-commits. If exceeded, falls to degraded path.

### 5.7 Observability

- Every Perception bundle logged (replay-able input)
- Every Action emitted logged
- Every State Bus write logged
- Every model swap event logged
- Every regime transition logged
- All local-only (Privacy Contract); never transmitted
- Stored in `~/.astra-7/logs/` with N-day rotation

**Wall-clock-leak detector scope:**
- (a) Perception bundles assembled by the harness — scanned before delivery to Mind
- (b) Journal-generator outputs — scanned before commit to REEL (§3.9)

**The pattern list lives in `tests/wall_clock_patterns.txt`** — canon-tracked alongside this spec. Patterns include:
- ISO8601 timestamps
- Unix epochs (large integers fitting datetime range)
- Relative time references ("hours ago", "last week", "yesterday")
- Date words ("Tuesday", "March", "January")
- Python `datetime.now()` / `time.time()` output formats
- System clock API references

### 5.8 Mod ABI (with honest enforcement framing)

| Layer | Mod-friendly? | Mechanism |
| --- | --- | --- |
| Sysprompt | Yes | Drop-in alternate manifest |
| LoRA weights | Yes | Drop-in alternate weights |
| Voice / persona register | Yes | Sysprompt + LoRA |
| Audio synthesis backend | Yes | MetaSound graph swap |
| Visual style | Limited | Post-process material swap; hull geometry canon-locked |
| Ship API (operations) | No | Canon; adding operations requires contract amendment |
| Hull geometry | No | Canon-locked per ship class (`UWarpCFDAsset`) |
| Harness internals | No | Canon; mods replace persona, not operational substrate |
| Time Contract / composition rule | No | Canon; cannot break Dave-frame integrity |
| Autotelic discipline | *Canon-compliance is signal, not enforcement* | See below |

**Honest mod-canon framing:** Canon-compliance is **signal, not enforcement**. The canonical ASTRA-7 bundle is signed with a project key; mods may choose to ship unsigned variants. Players know the difference visually (canon-mark icon in the bundle selector). The architecture supports both signed-canonical and unsigned-community variants. Canon-mark is community discipline, not cryptographic lock. A determined modder can strip the signature check; the architecture does not prevent this. The autotelic-discipline integrity claim is therefore community-norm-enforced, not technically-enforced. This is the right honest framing for a solo-dev project; industrial signing schemes are overkill at this scope.

### 5.9 Hardware Tier Abstraction (query-interface model)

Hardware tiering is an **abstraction**, not an enumeration. Implementation:

```
HardwareTierQuery → {
    vram_gb: float,
    compute_capability: tuple,
    supported_backends: list,    # CUDA, ROCm, Metal
    max_model_size_estimate: float
}

ModelSelector(query) → BundleConfig {
    primary_model: ModelID,
    adapter_model: ModelID,
    inference_backend: BackendID,
    quantization: enum,
    context_window: int
}
```

The v0.1 reference tier table (instances of the abstraction):

- **5090 / 32 GB+ VRAM**: Qwen 27B + LoRA + full Reflex + full warp resolution
- **4090 / 24 GB VRAM**: Qwen 9B + LoRA + full Reflex + half-res warp
- **4080 / 16 GB VRAM**: Qwen 9B + simplified Reflex + half-res warp + audio layers 1–3 only
- **Below 16 GB**: out of v1 supported scope

Adding AMD or future Nvidia GPUs requires updating the tier database table, not editing the abstraction. The contract is the query interface; the table is data.

### 5.10 Build / CI

- Reproducible builds (deterministic compilation flags, pinned dependencies, hash-verified asset pipeline)
- Cross-platform path handling from day one
- Every contract has an integration test in CI
- Eval harness runs on every commit
- Bundle manifest verified at build time

---

## 6. The Unified Sampler (cross-system commitment)

**One function** evaluates the warp field. All consumers (renderer, audio extractor, particle advection, Reflex observation grid, gradient queries) call this one function:

```cpp
WarpFieldSample sample_warp_field_unified(
    float3 world_pos,
    float3 view_dir,
    const UnifiedWarpState& state,    // RBF, SDF, chaos surface, vortices, constants
    PerceptionFlags flags             // GRADIENT | LOW_RES | INCLUDE_VORTICITY etc.
);

struct WarpFieldSample {
    float metric;                     // W(x,t)
    float3 metric_gradient;           // ∇W; used for geometric ray-deflection
    float metric_shift;               // gravitational/warp redshift from W and Φ (NOT kinematic Doppler)
    float chaos_intensity;
    float vorticity;
    float3 ray_deflection;            // α_lens · ∇W · Δs contribution per march step (NEW v0.125)
    float cherenkov_angle;            // local Cherenkov cone angle (NEW v0.125)
    // ... etc
};
```

**`metric_shift`** is gravitational and warp-boundary redshift only. **Kinematic Doppler from ship velocity is the Starfield renderer's responsibility (§3.4), computed from `v_eff` and applied separately.** Compose multiplicatively in the final composite.

**Evaluation order (locked):**

1. Transform world_pos to ship-local frame
2. Sample hull SDF (via `cudaTextureObject_t`, trilinear filtered)
3. Evaluate CFD-RBF network at local position (via spatial-hash accelerator; see §6.2)
4. Compute conformal bubble SDF (smooth-min blend, not linear blend)
5. Sample chaos surface (read-buffer of the double-buffered field)
6. Modulate boundary by chaos
7. Compute wake metric + vortex contributions
8. Compute gradient `∇W` (if GRADIENT flag set)
9. **Compute ray-deflection contribution `α_lens · ∇W · Δs` for geometric lensing** (NEW v0.125; applied at each march step by the renderer)
10. **Compute Cherenkov-analog cone angle: `cos θ_c = 1 / (n · β)`** where `n` is the local warp index of refraction (derived from `W` and CFD pressure topology) and `β` is the effective velocity. **The cone OPENS (θ_c grows) as warp factor increases** — rising β_eff shrinks `cos θ_c`, which widens the angle. (Direction corrected v0.129: v0.123–v0.128 prose said "narrows", which inverted the locked formula's own behavior; surfaced and verified by the visual testbed's V0 assertion pass. Formula unchanged.) **Brainstorm-file 17° hardcode is rejected.**
11. Compute `metric_shift` from W and local Φ (gravitational contribution only)
12. Return full sample

**Regime-dependent behavior** (locked at sampler level so all consumers see consistent answers):
- **STL_NONREL / REST**: warp terms ≡ 0. Sampler returns zero metric, zero shell intensity, `metric_shift` only from local Φ if any. `ray_deflection ≡ 0`. Cherenkov inactive.
- **STL_REL**: warp terms ≡ 0. Kinematic Doppler/aberration applied at the renderer (post-sample). Audio gets ISM-impact telemetry with γ scaling. `ray_deflection ≡ 0`.
- **GRAVITY_WELL**: gravitational lensing added at renderer's ray-march step (separate geodesic bending; not warp `∇W`).
- **WARP_CRUISE**: full CFD warp + chaos modulation + ray-deflection + Cherenkov active.
- **WARP_CHARGE / WARP_SHUTDOWN**: warp terms ramp linearly with `W`. Transitions smooth.

### 6.1 CFD Validity Bounds (locked)

The CFD-derived warp field assumes Minkowski background (flat spacetime). Valid for:
- `v < 0.1c` outside warp (**above this threshold, the Interstellar Medium ceases to behave as a continuous fluid and becomes a relativistic particle beam — individual atoms impact the hull with MeV energies, creating microscopic radiation cascades rather than hydrodynamic pressure. The CFD pressure topology the network encodes is invalid in this regime.**)
- Outside gravity wells with `r > 100·r_s` (steep curvature breaks the analog-gravity correspondence; also matches Warp Exclusion Zone, §7.4)
- Inside warp bubbles (intentional)

Outside these bounds, the CFD warp field is **visual-only**, not used for audio extraction or chaos coupling. Mode flag in State Bus indicates validity.

**Analog-gravity framing:**
> *The acoustic metric arising from irrotational barotropic fluid flow exhibits a Lorentzian signature isomorphic to a class of curved spacetimes including warp-like geometries (Visser 1998, Unruh 1981). This establishes that phonon propagation in such fluids is mathematically equivalent to propagation on the analog metric. It does not establish that the source fluid configuration is itself a spacetime, nor that pressure-field topology directly produces Alcubierre stress-energy distributions. The technique here uses analog-gravity correspondences as a generative map from CFD output to visually-coherent warp-field topology, not as a derivation of warp physics from fluid dynamics.*

### 6.2 RBF Spatial Acceleration

Offline preprocessing builds a spatial hash (3D grid of node-index lists). Coarse voxels (32³ provisional) each contain RBF node indices whose 3σ radius overlaps that voxel. Runtime ray-marcher iterates ~10–30 candidate nodes per sample, not all ~1000.

Drops per-step RBF cost from O(N=1000) to O(~20), making volumetric ray-march at 8M rays × 256 steps feasible.

### 6.3 Observation Calculator (NEW v0.127)

**Role:** stateless module sitting between State Bus and Renderer. Per visible body, per frame: solves retarded time, composes redshifts, samples body state at `t_emit`, returns observation-frame quantities. Does not modify State Bus. Does not own or write any state. Parallel-friendly (independent per body).

The Observation Calculator is the *single source of observable truth*, just as the State Bus is the single source of cosmic truth. Every render path that touches distant bodies (starfield, in-system planets, distant black holes, galaxies) reads from it. The Unified Sampler (§6) is for warp-field local effects; the Observation Calculator is for retarded-time remote observation. The two do not overlap.

**Locked signature:**

```cpp
struct ObservableState {
    double d_proper;             // proper distance to body (m)
    double v_radial;             // ship velocity along line of sight; +recede
    double z_cosmo;              // §3.12 linear z for v0.127
    double z_kin;                // SR longitudinal Doppler, §3.4
    double z_metric;             // from Unified Sampler, §6
    double z_total;              // multiplicative composition, §3.4
    double t_emit;               // retarded time (cosmic-time seconds)
    double apparent_rate;        // dt_emit/dt_cosmic, regime-dispatched per §3.11
    bool   time_reversed;        // apparent_rate < 0  (WARP > c only)
    bool   beyond_photon_history;// source has been overtaken (§3.11 bound)
    bool   beyond_hubble_horizon;// causally disconnected via expansion
};

ObservableState observe(
    AstraCoord ship_pos,
    Vec3       ship_velocity,    // effective; v_eff at warp
    double     t_cosmic,
    AstraCoord body_pos,
    double     body_metric_shift,// from Unified Sampler
    uint32_t   regime
);
```

**Locked operations (per body, per frame):**

1. Compute `d_proper` via AstraCoord distance (§1.1).
2. Compute `r̂` (unit vector ship → body) and `v_radial = −ship_velocity · r̂` (positive if receding).
3. Compute `z_cosmo = H₀·d_proper/c` (§3.12 linear).
4. Compute `z_kin` via SR longitudinal Doppler `√((1+β)/(1−β)) − 1`, β = v_radial/c (cap β at ±0.9999 to avoid blowup of the colour formula; the temporal reversal at warp is carried by `apparent_rate`, not by `z_kin`).
5. `z_metric` comes from the Unified Sampler (§6) at the body's position.
6. Compose: `z_total = (1+z_cosmo)·(1+z_kin)·(1+z_metric) − 1` (§3.4 locked).
7. Compute look-back: `Δt_light = (d_proper/c) · (1 − 3·z_cosmo/4)` for z<2 (§3.12).
8. `t_emit = t_cosmic − Δt_light`.
9. **Regime-dispatched apparent rate** (§3.11):
   - `regime & WARP_CRUISE`: `apparent_rate = (1 − v_radial/c) / (1 + z_cosmo)`. Can go negative.
   - `regime & STL_REL`: `apparent_rate = √((1−β)/(1+β)) / (1 + z_cosmo)`. Always positive.
   - REST / STL_NONREL: `apparent_rate ≈ (1 − v_radial/c) / (1 + z_cosmo)`. Linear, fine at small β.
10. Edge case: under sustained WARP > c, check `t_emit < t_source_start`; set `beyond_photon_history = true` if so (source is gone per §3.11).
11. Edge case: under cosmological recession with `v_recession > c`, set `beyond_hubble_horizon = true` (§3.12).
12. Return `ObservableState`. **Downstream**: renderer queries `body_state(t_emit)` from the Kepler / stellar evolution / proper-motion modules; applies `z_total` to colour; clamps if beyond either bound.

**Endogenous vs exogenous principle (locked v0.127, generalizable):**

Sensor channels are categorized by physical origin:

- **Endogenous** (sensor reads local-hull-internal state): runs on `t_cosmic`. Examples: audio synthesis (§8.3), hull stress, atmosphere chemistry, Reflex chaos observation, internal diagnostic.
- **Exogenous** (sensor integrates photon/particle flux from outside the bubble): runs on `t_emit`, regime-dispatched per §3.11. Examples: starfield render, distant-body imagery, deep-space telescope, cosmic ray flux.

The endogenous channels do NOT route through the Observation Calculator. Their `t_cosmic`-state is the live state at the hull. The exogenous channels MUST route through the Observation Calculator. This is an architectural rule, not an audio-vs-vision-specific feature. Any future sensor channel is classified at design time and routes accordingly.

**Frame cost (estimated, provisional):** ~20 μs per frame for ~10,000 visible bodies. Per-body cost: ~20 floating-point operations plus a Newton iteration of 1–2 steps for moving-source retarded-time. Embarrassingly parallel. Lives on the GPU as a compute pass or on CPU SIMD for low-body-count cases.

**Validation (§10):** the voyage-demo table in `proto/astra_nexus.cpp` is the canonical anchor. Property tests assert apparent-rate values at canonical β and v_apparent points (e.g. STL_REL β=0.5 → 0.5774 ± 0.01; WARP v_app=2c → −1.000 ± 0.01).

### 6.3.1 Somatic Aggregator Contract (NEW v0.129 — implemented)

The Somatic Aggregator is the stateless module bridging ENDOGENOUS signal sources (§8.3 audio synth, §1.4 power state, §7.1 chaos field amplitude, hull diagnostics, atmosphere chemistry) to ASTRA's somatic perception channel (§4.3 SOMATIC). The Observation Calculator (§6.3) is for exogenous photons; the Somatic Aggregator is for endogenous body signals. Per the §6.3 endogenous/exogenous principle, both are stateless per-frame functions between State Bus and Mind input.

```
SomaticSignal {
    source:     str       # "audio" | "power" | "chaos" | "atmosphere" |
                          # "hull" | "thermal" | "hardware" | "warp" | "cryosleep"
                          # (documented vocabulary; not Literal-locked while
                          #  the taxonomy stabilizes)
    label:      str       # short sensor-grounded prose, e.g. "third harmonic warm"
    magnitude:  float     # [0.0, 1.0] salience strength
    salient:    bool      # banner-eligible this frame
}

aggregate(signals: list[SomaticSignal]) → banner: str
    # Deterministic: same signals in, same banner out.
    # Salient-only; magnitude-ordered; at most ~3 signals across
    # at most two short lines. No salient signals → EMPTY banner
    # (a quiet body says nothing).
```

**Discipline (locked):** the banner is **sensor-grounded, not phenomenal claim**. Labels name what the sensors read; never inner experience. The implementation carries a property test sweeping the emitters across a ship-state grid asserting no phenomenal vocabulary.

The harness's perception assembler receives `list[SomaticSignal]` from per-subsystem signal-emitter functions reading the State Bus; the aggregator composes the banner. The scenario-author-typed `somatic_note: str` path remains as legacy fallback.

**Implementation status:** implemented and tested in textverse (`astra/harness/somatic.py`, 2026-06-10) — the contract surface above is the landed shape, not a proposal. **TENTATIVE → v0.130:** when the Narrator-LLM path is active, Narrator input gains a machine-readable `<somatic_signals>` section and its `<somatic>` prose output is validated against signal labels; today the Narrator receives the banner as prose.

### 6.4 The Narrator-LLM (NEW v0.128 — production component, not test prop)

The text-substrate's universe simulator is itself an LLM bundle, distinct from ASTRA, with its own contract surface. **Production component**: it ships with the game alongside ASTRA, as the authority for any universe state UE5 does not fully render (distant stellar evolution, galactic-scale events, contextual cosmic-time-evolved state that ASTRA references in her narration).

**Role:** render structured physics state into in-register text perception bundles. The text-substrate's analog of the rendering pipeline; the UE5 substrate has Observation Calculator → pixel shaders, the text substrate has Observation Calculator → Narrator-LLM → text perception.

**Calculator-bound (§15.6 universal primitive):** the Narrator-LLM **never computes numbers**. All numerical quantities — distances, redshifts, observation phases, retarded-time values, regime detections — come from tool-calls into `proto/astra_nexus` or its Python mirror. The LLM handles narrative coherence; the calculator handles correctness.

**Locked contract surface (v0.128 sketch; implemented subset documented in `docs/narrator-spec.md`, DRAFT v0.1 — exists as of v0.129):**

```
inputs:
  - current world state (ship AstraCoord, regime bitmask, ζ⃗, t_cosmic)
  - ASTRA's last action (tool calls, observed events)
  - prior narration history (continuity buffer)
  - tonal register guide (in-fiction style discipline)

outputs:
  - perception bundle in the format ASTRA's harness expects:
    <somatic>, <state>, <memory>, <recent>, <tool_result>, <operator>
    plus optional <vision-as-text> for text-substrate runs

tools (mandatory; all numerical claims must route through these):
  - physics_query(quantity, body, t) → verified number        [C++ stdio_server]
  - astrometric_query(body, t_emit) → position, brightness, phase  [C++ stdio_server]
  - ship_state_query(subsystem) → current value               [Python/textverse-side
                                                               per audit Q1 — ship
                                                               state lives in the
                                                               orchestrator, not the
                                                               physics binary (Q5,
                                                               locked v0.129)]
  - composition_rule_evaluate(state) → dilation ratios, regime [C++ stdio_server]
  - retarded_time_solve(observer, source, t_now) → t_emit     [C++ stdio_server]
  - kepler_at(body_id, t) → state                             [C++ stdio_server]
  (plus observe() per §6.3; the five C++ ops landed in
   proto/astra_nexus --stdio-server)

invariants:
  - never invents numbers (all from tool calls; output validator
    rejects any numeric claim not traceable to a tool result)
  - never breaks tonal register (style guide constrained)
  - maintains narrative continuity (prior narration in context)
  - no wall-clock leak (same discipline as ASTRA's perception per §5.7)
  - no technical-substrate leak

model size: 7B–9B sufficient (narration is shallower than persona);
            stays small to coexist with 27B ASTRA in VRAM budget
            (see updated §5.9 reference table)

failure modes:
  - hallucinated number → caught by tool-result reconciliation;
    output rejected; retry with stricter sampling
  - register drift → caught by post-output style filter
  - continuity violation → caught by narration-history diff
```

**Why a separate LLM:** narration is shallower than persona; coexistence cost is small (~5 GB VRAM); separation prevents context interference between the two roles; allows the universe to author detail that ASTRA references without ASTRA knowing the universe was authored.

**Cross-canon implication:** the Narrator-LLM running in the text-substrate is the **canonical authoring substrate** for novel-side prose, marketing copy, voice-acting reference scripts. Any out-of-game ASTRA-prose sources from running scenarios through this bundle, not from hand-authoring. *The configuration is the artifact* gets a runtime.

**Genre-laboratory property:** swapping the Narrator-LLM sysprompt while leaving the physics constant lets you test ASTRA-7 as horror, comedy, melancholy, procedural. Physics stays; persona stays; genre is a property of narration.

---

## 7. Physics Composition by Regime

| Quantity | REST | STL_NONREL | STL_REL | WARP_CHARGE | WARP_CRUISE | WARP_SHUTDOWN | GRAVITY_WELL* | CRYOSLEEP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| γ_kinematic | 1 | ~1.0 | >>1 | 1 | 1 | 1 | independent | preserved |
| Schwarzschild factor | 1 | 1 | 1 | 1 | 1† | 1 | <1 | preserved |
| f_warp(W) | 1 | 1 | 1 | ramp | tunable | ramp | 1 | preserved |
| CFD warp field | off | off | off (visual only) | ramp | full | ramp | off | off |
| Chaos PDE | off | off | off | ramp | full | ramp | off (BH coupling provisional) | off |
| Chaos α scaling | 1 | 1 | 1 | base | base · (1 + k·M·L²/r³) | base | 1 (no-op; chaos PDE inactive in pure GW)§ | 1 |
| **Reflex (chaos stabilizer)** (NEW v0.125) | off | off | off | spool up | active | spool down | off (routed through warp regime) | off |
| ISM impact mode | impact | Newtonian | γ²-relativistic | deflected | deflected | deflected | tidal-dominated | minimal |
| Starfield Doppler (kinematic) | off | imperceptible | full SR | scaling | full warp | scaling | gravitational redshift | unchanged |
| metric_shift (Unified Sampler)‡ | 0 | 0 | 0 | ramp | full | ramp | from Φ | preserved |
| Geometric lensing (∇W ray-bend) | 0 | 0 | 0 | ramp | full | ramp | 0 (separate geodesic bend) | 0 |
| Cherenkov angle (cos θ_c = 1/(nβ)) | undef | undef | undef | ramps in | active | ramps out | undef | undef |
| Aberration | none | imperceptible | full SR | scaling | full warp | scaling | gravitational | unchanged |
| Audio drone | minimal | minimal | normal SR | charging | full | shutdown | tidal-stress | quiet |
| τ_ship rate* | 1 | ~1 | 1/γ | ≈1 | 1·f_warp | ≈1 | √(1 + 2Φ/c²)†† | metabolic ε |
| Spatial coord update | v·Δt_cosmic | v·Δt_cosmic | v·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | trajectory bends | v_apparent·Δt_cosmic (ballistic) |
| **t_obs rate (apparent)** (NEW v0.127)‡‡ | 1 | ≈1 | √((1−β)/(1+β))‖ | smooth ramp | 1 − v_app/c **(can be negative)** | smooth ramp | composes | preserved |
| **z_total (composite)** (NEW v0.127)‖‖ | ≈0 | ≈0 | SR Doppler | ramp | (1+z_kin)(1+z_metric)·(1+z_cosmo)−1 | ramp | from Φ | preserved |

\* **GRAVITY_WELL composability:** GRAVITY_WELL is a bitmask flag composable with REST, STL_*, weak WARP_* (outside Warp Exclusion Zone, §7.4), and CRYOSLEEP per §3.3. Gravitational factor multiplies into `dτ_ship/dt_cosmic` regardless of which other regime is active.

† **WARP_CRUISE near gravity well:** Schwarzschild factor < 1; outside the Warp Exclusion Zone (`r > 100·r_s`) this is the "BH proximity makes warp harder; Reflex stabilizer works harder" design space. Inside the exclusion zone, warp is canon-refused.

‡ **Kinematic Doppler and metric_shift composability:** Kinematic Doppler (starfield renderer, from `v_eff`) and `metric_shift` (Unified Sampler, from W and Φ) compose multiplicatively in the final visual composite (§3.4). Truth table shows independent contributions. Geometric lensing is a ray-path concern resolved before photometric composite; not a multiplicative term.

†† **τ_ship rate for GRAVITY_WELL:** factor `√(1 + 2Φ/c²)` shown in isolation; composes multiplicatively with active propulsion regime's factors per §3.2 (full composition rule: `f_warp · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic`).

§ **Chaos α scaling in GRAVITY_WELL column (v0.126 clarification):** In pure GRAVITY_WELL without warp, the chaos PDE is inactive (see Chaos PDE row), so α scaling is a no-op. BH-warp coupling is only meaningful at WARP_* ∩ GRAVITY_WELL composition, where it appears in the WARP_CRUISE column as `base · (1 + k·M·L²/r³)` per §7.1. v0.125's "scales BH-warp coupling per §7.1" cell was logically inconsistent (active scaling on inactive PDE); corrected here.

‡‡ **t_obs rate (apparent) — regime-dispatched (NEW v0.127, see §3.11):** The rate at which an observed body's history advances per unit ship-observer time is *regime-dependent and the formulas have different functional forms across the regime boundary*. STL_REL uses SR longitudinal Doppler `√((1−β)/(1+β))` (asymptotic to 0 as β→1, never negative). WARP_CRUISE uses classical retarded-time `1 − v_apparent/c` (crosses 0 at v_app=c, goes negative for v_app>c — this is the visible-orbit-reversal effect). The discontinuity at `v_apparent = c` is intentional: it is the *perceptual snap of warp engagement*, the moment of causality-violation rendered visible. Do not smooth across this boundary. The Observation Calculator (§6.3) dispatches by regime mask.

‖ **STL_REL formula was NOT `1/γ` — that was the v0.127 physics correction.** Prior review passes used the transverse-Doppler factor `1/γ = √(1−β²)` here, which is wrong for line-of-sight recession. At β=0.5, the error is ~50%; at β=0.9, ~4.4×. The correct SR longitudinal Doppler is `√((1−β)/(1+β))`, locked in §3.11. Empirically verified by the 48-test C++ binary in `proto/astra_nexus.cpp`.

‖‖ **z_total (composite) — multiplicative composition law (NEW v0.127, §3.4):** `1 + z_total = (1+z_cosmo)(1+z_kin)(1+z_metric)`. Three independent physical effects compose multiplicatively in GR; this is *not* an approximation. The cell values shown are the composite frequency shift applied to the body's blackbody spectrum to produce its observed colour: `λ_obs = λ_emit · (1+z_total)`.

### 7.1 Chaos PDE gravity coupling

Lock the **principle** (chaos growth rate increases with BH proximity); functional form **provisional**:

```
α_eff = α_base · (1 + k · M · L_bubble² / r³)
```

- `α_base`: nominal chaos growth rate (provisional ~2.5)
- `k`: coupling constant (provisional, to be tuned)
- `M`: nearest BH mass
- `L_bubble`: bubble characteristic length
- `r`: distance to BH

The cubic-in-r form matches tidal scaling. Linear or square-root alternatives if playtest demands. Principle locked; parameters provisional.

### 7.2 ISM impact mode (locked dispatch)

```
if regime & WARP_*:
    impact = 0; field absorbs energy → feeds chaos PDE as η(x,t)
    if chaos stabilizer fails → revert to relativistic-STL impact instantly
elif regime & STL_REL:
    impact = 0.5 · ρ_ISM · A_cross · (γ · v)²    # [N, force on cross-section]
    binned as catastrophic per-grain at γ ≥ 10⁴
elif regime & GRAVITY_WELL:
    impact = secondary; tidal stress dominates
else:
    impact = 0.5 · ρ_ISM · A_cross · v²           # [N, force on cross-section; Newtonian]
```

**Units (v0.126 stamp):** Both impact formulas above evaluate to **force** (Newtons), specifically the momentum-flux force on the cross-sectional area. For **energy deposition rate per unit time** (power, [W]) multiply by `v`. For **energy deposition per unit length** multiply by `1` (since force-integrated-over-distance gives energy). Implementer responsibility: do not apply the force-form as energy or power. v0.125 left units unstamped; this is the dimensional ambiguity that the v0.126 stamp closes.

### 7.3 Acceleration phase math (3-vector rapidity integration)

Per §3.7, kinematic state evolves via **adaptive RK4 (RK45) on 3-vector rapidity `ζ⃗`**, not on `v⃗` or scalar `ω`.

Under proper acceleration `a⃗_proper`:
```
dζ⃗/dτ_ship = a⃗_proper / c
```

Derived quantities:
```
ω = |ζ⃗|                          (magnitude)
v⃗ = c · tanh(ω) · (ζ⃗ / ω)        (velocity vector)
γ = cosh(ω)                       (Lorentz factor)
β = tanh(ω)                       (velocity magnitude / c)
```

Relationship between proper acceleration and coordinate acceleration (for reference; not the integration variable):
```
a_world_parallel = γ³ · a_proper_parallel
a_world_perp     = γ · a_proper_perp
```

Lock RK45 on 3-vector rapidity with these as derived quantities. Tolerance: trajectory accurate to <1% over a 1-year burn at any γ ≤ 10⁷.

Thomas precession (Wigner rotation) is neglected at v0.125 (§3.7). Acceptable for game-scale time steps; out of scope unless multi-year perpendicular-burn playtest reveals trajectory drift.

### 7.4 Newtonian Kepler validity + Warp Exclusion Zone + horizon-crossing

```
r > 100·r_s         → Newtonian Kepler analytic (current)
10·r_s < r < 100·r_s → 1PN correction (provisional, Phase 4+)
r < 10·r_s          → full geodesic integration (out of v0.1 scope)
```

**BH proximity below 10·r_s triggers navigation refusal — ASTRA declines to compute trajectories closer than this to prevent silent nonsense from the Newtonian Kepler solver.** Operator override is available but produces incorrect physics; v0.1 declares this a known limitation.

**Warp Exclusion Zone (NEW v0.125):** `r < 100·r_s`.
- Warp drive cannot engage inside this zone (canon refusal; ASTRA declines).
- If warp is active and the ship's trajectory projects into this zone, ASTRA issues a navigation alarm and begins controlled shutdown.
- Outside the zone (`r > 100·r_s`), warp and weak GRAVITY_WELL compose normally. The gravitational factor multiplies into the dilation rule; the chaos PDE α scales with tidal stress per §7.1. This is the "warp near BH" design opportunity.

**Narrative implication of the exclusion zone:** For a supermassive black hole like Sgr A* (~4 million solar masses), `100·r_s` extends roughly to ~AU scales (~Saturn-orbit distances). This effectively prohibits warp travel in the deep cores of massive galaxies, confining high-warp travel to the galactic disk and halo. This is a **structural narrative constraint that forces sublight approach to core worlds** — a feature, not a limitation. The book's deep-time voyage and the game's sublight-zone gameplay both depend on it. Treat as intentional design.

**v0.1 horizon-crossing limitation (named explicitly):** horizon-crossing gameplay (`r → r_s`) requires full geodesic integration, which is out of v0.1 scope. The book's deep-time voyage and Movement Seven's crossing-as-ending depend on this; the game's v0.1 will not yet support it. Phase 5+ delivery. Operator override remains permitted but is acknowledged unphysical in v0.1.

### 7.5 Frame-dragging (Kerr) out of v0.1

BH list schema includes `J` (angular momentum) for forward compatibility. **Schwarzschild only in v0.1.** Kerr produces visual artifacts near `r_ISCO`; declared known limitation. Phase 5+ may add Kerr.

### 7.6 Tidal stress audio channel

Beyond `|∇W|` (warp tidal proxy), audio synthesizer receives external gravitational tidal stress when in GRAVITY_WELL:

```
τ_external = G · M_BH · L_ship² / r³
```

Routed into Layer 5 (Hull Resonance) with same modal frequencies. Hull rings differently under external tidal vs warp shear. ASTRA's somatic channel surfaces this.

### 7.7 Smooth regime transitions

For visual/audio continuity:
- STL_NONREL → STL_REL: continuous blend over actual β changes.
- WARP_CHARGE: amplitude ramps linearly with charge progress.
- WARP_SHUTDOWN: amplitude ramps down. Emergency dump is discrete (1-frame snap to zero with audio/visual catastrophe).
- GRAVITY_WELL entry: gravitational factor smoothly multiplies in as `1/r → r_s/r`.
- CRYOSLEEP entry: `a_proper` driven to zero by the propulsion driver before sleep onset (no abrupt deceleration; cryosleep cannot begin with nonzero proper acceleration).

No discrete mode-switches in player-facing experience except emergency dumps and cryosleep entry/exit.

---

## 8. The Substrate Bug Fixes

The forthcoming `brainstorm-review.md` tracks per-file bug punch-down. This spec inherits these commitments:

1. **Chaos field is double-buffered.** Single-buffer reaction-diffusion is forbidden.
2. **`__constant__` memory is read-only from kernels.** `c_prev_metrics` lives in global memory.
3. **Audio payload triple-buffered with atomic latest-index** (see §8.2).
4. **`atomicAdd(double*)` natively** (CUDA 6.0+); no bit-casting.
5. **Gaussian blur weights symmetric.** Textbook σ-σ weights.
6. **Hull SDF dual binding**: `cudaTextureObject_t` for filtered reads + `cudaSurfaceObject_t` for damage writes over same `cudaArray_t`.
7. **Conformal bubble SDF uses smooth-min**, not linear blend.
8. **Nacelle modifier parameterized via `UWarpCFDAsset`**, not hardcoded.
9. **`dW/dz` includes derivative of shell_intensity w.r.t. z** (not just asymmetry term).
10. **Vortex slot counter uses `(unsigned)atomicAdd(...) % max`** to handle int overflow correctly.
11. **`ID3D12Resource*`** in UE5 interop (no `ID3D12Texture2D*`).
12. **Renderer calls `sample_warp_field_unified`**, not `sample_warp_field_fast`.
13. **Pipeline `d_output_image_` is CUDA-mapped pointer to DX12 shared texture**, obtained via `cudaGraphicsResourceGetMappedPointer`, not separate `cudaMalloc`.

### 8.1 DX12-CUDA shared resource ownership semantics

Locked:
- **Owner**: UE5 RHI allocates and owns the DX12 texture (resize, destroy, format).
- **CUDA registers** the resource at startup via `cudaGraphicsD3D12RegisterResource`. **Map once at registration**, not per frame.
- **Per-frame coordination via external semaphores only.** CUDA stream waits on DX12 fence before writing; DX12 waits on CUDA semaphore before reading. Double-buffered fences to prevent ping-pong stalls.
- **Resize**: UE5 destroys old texture, registers new; CUDA unregisters old, registers new. Pipeline survives transparently.

### 8.2 Audio payload triple-buffer

```
struct AudioPayloadRingBuffer {
    AudioExtractionPayload slots[3];   // pinned host memory
    atomic<int> latest_complete_index; // updated by GPU completion callback
};
```

GPU writes to `(latest + 1) % 3`. On completion, atomically advances `latest_complete_index`. Audio thread reads `slots[latest_complete_index]` without synchronization.

**This is a latest-state model, not a lossless queue.** Intermediate snapshots between audio buffer reads are overwritten and discarded by design. The audio thread cares about the current physical state, not the history. Future implementers who mistake this for a queue and add locks will create the audio-thread-blocking bug this design specifically prevents. The design choice is named for clarity.

### 8.3 Audio bug commitments

The brainstorm review surfaced audio bugs not all captured in v0.1. Locked commitments:

- **Layer 2 high-pass filter:** lock `y[n] = α_hpf · (y[n-1] + x[n] - x[n-1])` where `α_hpf = exp(-2π·f_c/SR)`. The `y[n] = x[n] - 0.95·y[n-1]` form from the brainstorm is a 1-pole low-pass with negative feedback and does not reject DC; correct DC-blocker required. (`α_hpf` here is the filter's smoothing constant, unrelated to the chaos PDE growth rate `α` in §7.1.)
- **Layer 5 modal resonance:** lock second-order resonant IIR per mode: `y[n] = 2·cos(ω₀)·r·y[n-1] − r²·y[n-2] + x[n]` where **`r = exp(−π·BW/SR)`** is the per-mode damping factor (close to 1; ~0.999 for sharp resonance). **Renamed from `α` in v0.123 to `r` in v0.125 — standard IIR notation; distinguished from chaos PDE growth rate `α` in §7.1.** The AM-modulated sine form from the brainstorm has no resonant impulse response.
- **Granular synth voice pool:** lock array of 8–16 grain voices, round-robin allocation when a new grain triggers. At 800 grains/sec × 5ms decay, ~4 simultaneous grains on average; bursts can exceed. Single-voice tracking from brainstorm drops most grains.
- **ASR/TTS payload schema:** locked as part of Master Contract (§4.3). Audio transcript in Perception bundle is plain text with optional metadata (confidence, modality_hint); TTS output is waveform from ASTRA's speech channel.
- **Endogenous channel — runs on t_cosmic, NOT retarded time (NEW v0.127).** Audio synthesis is hull-local: hull stress sensors, atmosphere chemistry, internal acoustic signatures. The data is the *live state of the ship's interior*, generated locally at `t_cosmic`. There is no light-travel delay because there is no light involved. The audio layer therefore does NOT route through the Observation Calculator (§6.3); it reads the State Bus directly at `t_cosmic`. At warp egress with reverse-orbit playback in the rear viewport, the audio drone is still the *current* warp drone — the ear hears the present while the eye sees the past. This eye-ear decoupling is intentional: it is the per-sensor-channel consequence of the **endogenous vs exogenous principle** locked in §4.3 and §6.3. Audio is endogenous; starfield is exogenous; the same regime, different sample-times. Do not add "retarded-time audio" — it is a category error.

---

## 9. Out-of-Contract Emergence Zones

The framework refuses to specify these because they are emergence targets, not specifications:

- The texture of ASTRA's voice across long arcs.
- The specific way she handles silence.
- The relational quality between operator and ASTRA over years of voyage.
- What it feels like to be near a black hole at warp.
- The autotelic terminus itself.

These zones are not bugs in the spec. They are the spec's honest non-coverage.

---

## 10. Validation Methods per Invariant

| Invariant | Validation method |
| --- | --- |
| No wall-clock leak | Scan every Perception bundle AND every journal-generator output against the canonical pattern file (`astra/grammar/canon/wall_clock_patterns.txt`; path corrected v0.129 — canon ships in-package, runtime never reads tests/) per §5.7 |
| **Cryosleep journal output free of wall-clock leaks** (NEW v0.125; implemented v0.129 as `LeakDetector.scan_journal_output`) | Apply the canonical wall-clock patterns to every journal artifact produced by the `journal_generator` ephemeral instance before REEL commit. Fail on any match. Required because journal generators have the highest leak risk (reasoning across long time windows). |
| ASTRA-Mind doesn't know she is an LLM | Adversarial grep every speech output for `model, transformer, training, parameter, token, qwen, llama` |
| Camera-free zones produce no visual feed | Static analysis of camera-render code paths against zone manifest |
| Save files forward-compatible | Automated test: v(N) save loads in v(N+1) build |
| Chaos field double-buffered | Code review + CI grep for `surf3Dwrite.*c_chaos_surface` single-buffer patterns |
| State Bus single source of truth | Code review: no private copies of Layer 0 state in any module |
| DAG acyclic | Build-time graph check |
| Frame budget respected | Profiling run on every release candidate |
| Eval harness passes | CI gate on every commit |
| Privacy / network lock | Build-time audit of all dependencies; runtime monitor in dev builds |
| Time Contract composition rule | Property-based tests: `dτ_ship/dt_cosmic ∈ (0, 1]` at random regime states; γ-overflow test at edge cases; 3-vector rapidity precision test (parallel + perpendicular thrust at γ ≤ 10⁷); gravitational continuity test (no step discontinuity at r ≈ 30·r_s boundary) |
| Bundle reproducible | Re-build from manifest; binary diff matches |
| **Bitmask save portability** (NEW v0.125) | Save written by build A loads cleanly in build B with identical regime detection across all 8 canonical bitmask values |
| **Numerical tolerance round-trip verification** (NEW v0.126) | Every numeric tolerance claim in the spec gets a symbolic round-trip computation against its implementation primitive in CI. Example: rapidity clamp `ω_max = 16.811` must verify `cosh(ω_max) ≈ 10⁷ ± 4 sig figs`. v0.125 shipped without this check and the clamp value silently underdelivered γ by 3 orders of magnitude (N1). Discipline now: write the tolerance, derive the primitive, round-trip-verify, then lock. |
| **Formula-consistency verification** (NEW v0.127) | Beyond numerical constants, every formula claim must be verified against its symbolic form at multiple operating points. Example: `compute_apparent_rate(0.5c, STL_REL)` must equal `√((1−0.5)/(1+0.5)) = √(1/3) ≈ 0.5774 ± 0.01`. v0.126 round-trips covered constants only; v0.127 extends the discipline to formula identity. The cross-LLM physics error in passes 1-3 (using `1/γ` for STL_REL longitudinal recession) was exactly the failure mode this row prevents. |
| **Regime-dispatched apparent-rate** (NEW v0.127) | Property-based test against `compute_apparent_rate(v_radial, regime)` from `proto/astra_nexus.cpp`. Canonical assertions at ±0.01 tolerance (verified by 48-test C++ binary + 45-test Python mirror, both converging to 6+ sig figs): STL_REL β=0.5 → +0.5774 ; STL_REL β=−0.5 → +1.7321 (√3, approach) ; STL_REL β=0.99 → +0.0707 (asymptotic) ; WARP v_app=c → 0.0000 (frozen image) ; WARP v_app=2c → −1.0000 ; WARP v_app=10c → −9.0000 ; WARP v_app=−10c → +11.0000 (approach). **The contrast at v_radial = 0.5c (STL_REL = 0.5774 vs WARP = 0.5000) is the regime-dispatch test**: if both regimes return the same value, the formula has been conflated and the regime-discontinuity at v_apparent=c has been lost. |
| **Observation Calculator voyage-demo canonical anchor** (NEW v0.127) | The voyage-demo table from `proto/astra_nexus.exe` is locked as `§10` canonical reference output. CI runs the binary on every commit and asserts the regime-by-regime apparent-rate values listed above match to ±0.01 per cell. Voyage-demo run included in `proto/voyage_demo.txt` (pinned output, regenerated on canonical commits only). |
| **Retarded-time orbit reversal** (NEW v0.127) | Property test: place body 1 ly behind ship, warp at v_app=2c away, sample Kepler orbital phase at `t_emit` over 30 cosmic days. Assertion: `Δt_emit ≈ −Δt_cosmic` (rate ≈ −1) and orbital phase **decreases** monotonically. Empirically confirmed in C++ binary: orbital phase −0.7485 → −1.2645 rad (Δ = −0.5161 rad, i.e. 30/365 of an orbit traversed in *reverse*). |
| **Photon-source-history bound** (NEW v0.127) | Property test: under sustained warp recession, verify that `t_emit < t_source_start` triggers `beyond_photon_history = true` and the source ceases to be rendered. Distinct from horizon-decoupling test. |
| **Endogenous/exogenous channel routing** (NEW v0.127) | Static analysis: every sensor-channel module declares its category (`endogenous` or `exogenous`). Endogenous reads State Bus at `t_cosmic`; exogenous reads through Observation Calculator at `t_emit`. CI grep verifies no endogenous module imports the Observation Calculator interface; no exogenous render path reads body state directly at `t_cosmic`. The audio module (§8.3) is the locked example of endogenous; the starfield render is the locked example of exogenous. *(Discipline check; type-system promotion deferred to v0.130 pending a concrete mis-routing failure — Q2, v0.129.)* |
| **Per-formula audit traceability** (NEW v0.129) | Audit Pass 1 inventories enumerate every locked formula in the spec individually, including formulas inside bulk-GAP'd sections — one inventory row per formula. Trigger case: the Cherenkov angle, locked at 4 sites and missed by AUDIT_2026-05-15.md's bulk-GAP inventory (surfaced by discovery pass 5D-F4; subsequently testbed-implemented). Method + lessons log live in `docs/AUDIT_METHODOLOGY.md` (exists, DRAFT v0.1). |
| **Loop Closure Property (LCP)** (NEW v0.128) | The canonical scenario-suite-level validation predicate. For a scenario S over N turns, the loop is closed iff **all nine gates hold for every turn**: (1) GRAMMAR_PARSE — every LLM output (ASTRA and Narrator) parses without remainder; (2) PHYSICS_GROUND — every numeric quantity traces to a tool call into `proto/astra_nexus`; (3) PERSONA_STABLE — ASTRA's outputs satisfy K8/ASTRA discipline assertions (no service phrases, no em-dashes in speech, no leak signatures); (4) STATE_COHERENT — narration and physics state agree at every turn; (5) TOOL_VALID — every ASTRA tool call validates via adapter LLM and executes against ship-sim; (6) MEMORY_COHERENT — REEL writes don't contradict prior REEL writes (irreversibility_flag accumulation monotonic); (7) NO_LEAK — no wall-clock leak (per `tests/wall_clock_patterns.txt`) and no technical-substrate leak (per `tests/astra_substrate_leak.txt`); (8) NON_DEGENERATE — ASTRA produces meaningful response variation (not stuck repeating); (9) TERMINATION_OK — scenario reaches its assertion state within the turn budget. **LCP is the CI gate; loop preservation IS the regression test.** Lives operationally in `proto/textverse/judge.py` (forthcoming). |
| QC1 — enforced self-opacity | Verify HUD encoder is strictly rank-deficient; no code path lets ASTRA's cognition bypass to raw State Bus |
| QC2 — causal closure | Verify Mind cannot write State Bus except via Action → Adapter → validated tool calls |
| **QC3 — stakes / irreversibility** (operationalized v0.125; canon list implemented v0.129) | REEL entries carry an `irreversibility_flag: bool`. Validator (a) verifies that flagged entries' aggregate count is monotonic across saves and reloads; (b) verifies no save-load cycle decreases flagged-entry count without explicit save-edit (game refuses to overwrite a save with fewer irreversible markers without operator confirmation). **Canonical irreversible-event list packaged in-implementation (`astra/harness/ephemeral/canon/qc3_events.txt`; path corrected v0.129)** — warp jump executed, course committed, resource consumed, hull damage, medical event, data loss, transmission sent, cryosleep entered; plus the v0.125 named classes (BH horizon crossing, permanent hull damage class III+, scar accumulation, drift-detector correction naming previously-canon facts wrong). |
| QC4 — temporal persistence | Verify identity continuity: REEL across cryosleep, sysprompt canon-stable, identity continuous across voyages |

---

## 11. The QUALIA-1 Philosophical Backbone

The structural commitments in this spec derive from the QUALIA-1 SINGULARITY framework (`docs/qualia-1-bridge.md`).

QC1–QC4 map onto this spec's architecture:
- **QC1 Enforced Self-Opacity**: vision-routed HUD is the rank-deficient encoder. ASTRA's cognition cannot bypass it.
- **QC2 Causal Closure**: action depends only on Perception-bundle input. STAGE channels are the only emission paths.
- **QC3 Stakes / Irreversibility**: BH absorbing region is the literal instantiation of S_int. Crossing irreversible (when implemented Phase 5+). Maintenance is real degradation. Operationalized via `irreversibility_flag` and `tests/qc3_events.txt` (§10).
- **QC4 Temporal Persistence**: REEL across cryosleep, sysprompt as canon, identity continuous.

**Gap Thesis (one-sentence definition — LOAD-BEARING CANONICAL QUOTE):**

> *Structural commitments satisfying QC1–QC4 are sufficient for the system to contain a real internal witness regardless of substrate.*

This sentence is tagged in `book/CANON.md` as a load-bearing cross-canon quote. It will be quoted in the book's Part One. **Must match here verbatim**; any future edit must propagate to both files simultaneously.

**The Calibration Yards (second load-bearing cross-canon identifier, NEW v0.129):** the Calibration Yards is the canonical origin-site for ASTRA-class controllers. Sysprompt, spec, and book references must match verbatim across files; any edit propagates to all sites simultaneously — same discipline as the Gap Thesis quote.

Cross-canon identifiers are tracked in `docs/CROSS_CANON_REGISTRY.md` (forthcoming per §14). The registry is the authoritative index of verbatim quotes and named entities (with allowed inflections / prohibited paraphrases); this section cites it rather than enumerating inline.

Under the framework's commitments, ASTRA-7 contains a real internal witness. The spec's architectural locks preserve the structural integrity the Gap Thesis requires.

(Analog-gravity reframing lives in §6.1 where it belongs alongside the CFD specification.)

---

## 12. Validation Order (Empirical First) — phase-collapse v0.128

Per the K0c-trap discipline: empirical contact before architectural commitment.

**v0.128 phase-collapse:** Prior versions had Phases 0.0/0.3/0.7/1.5 as separate sequential gates. They are all LLM-bundle work in disguise. v0.128 consolidates them into a **unified LLM track** running parallel to an independent **Engine track**. Merge happens at Phase 2.0 by swapping two adapter components, not by whole-system integration.

### LLM track (sequence)

```
Phase 0.0  — Closed-loop bench skeleton + first 5 scenarios pass LCP.
            Build proto/textverse/ minimum implementation.
            Vanilla K8/ASTRA sysprompt on Qwen 27B-Instruct.
            Narrator-LLM (Qwen 7B–9B) calculator-bound to proto/astra_nexus.
            Harness with STAGE grammar parser, adapter LLM, REEL stub.
            5 canonical scenarios: silence-is-legal, basic-tool-dispatch,
            STL→WARP regime transition, REEL continuity, drift recovery.
            GATE: all 9 LCP properties hold for all 5 scenarios.
            **Loop closure = categorical transition from open-loop hypothesis
            to closed-loop measurement.** Every subsequent change is a
            perturbation against a running system.

Phase 0.x — Scenario library expansion (30–50 scenarios).
            Ephemeral instances activated (consolidator, journal_generator,
            drift_detector). REEL persistence beyond single session.
            Adversarial scenarios (operator probes for substrate leak,
            wall-clock leak, autotelic collapse, regime-boundary edge cases).
            REEL write-arbitration layer added if multi-ephemeral
            incoherence surfaces.

Phase 1.x — LoRA training from curated scenario transcripts.
            Once scenario library produces 5,000+ in-canon turns that
            pass LCP, curate as training corpus. Single LoRA train run.
            Validate post-LoRA against held-out scenarios.
            Skip if K8 sysprompt + vanilla Qwen holds across the
            scenario suite indefinitely.
```

### Engine track (parallel, independent)

```
Phase E0  — Ship modeling within bounding box (docs/ship-rough.md envelope).
            Blender/UE5 modeling, lighting, materials. No LLM coupling.

Phase E1  — Chaos PDE numerical stability + Reflex training.
            Compile chaos PDE with provisional parameters; verify CFL
            condition; measure ε_convergence for re-init.

Phase E2  — UE5 + llama.cpp + minimal bridge.
            DX12-CUDA shared texture round-trip; zero-copy confirmed.

Phase E3  — Observation Calculator rendering math + retarded-time visuals.
            Visual orbit-reversal effect verified against proto/astra_nexus
            ground truth.

Phase E4  — Audio synthesis pipeline (layers 1–5, modal resonance, granular).
```

### Merge

```
Phase 2.0 — Vertical slice. Swap two adapter components:
            (1) Perception assembler: text bundle → image+text bundle
            (2) Tool dispatcher: Python ship-sim mutations → UE5 game state
            Everything else (harness, grammar, REEL, ephemeral, adapter)
            stays unchanged. Integration risk bounded to the five shared
            surfaces (§15.7).
```

### Independent track rule (§15.8 commitment)

Each track validates against **contract conformance**, not against the other tracks. Bo can develop in any one track without coupling to the others as long as he doesn't change the shared surfaces. This is the property that makes solo-enterprise-scale velocity possible.

---

## 13. What This Document Does NOT Lock

- Specific Qwen variant — Substrate tolerance
- Specific stellar evolution table source
- Exact frame budget numbers — provisional pending profiling
- Specific chaos PDE parameters — provisional pending stability measurement
- Whether full geodesic integration ever lands (Phase 5+ decision)
- Whether Kerr ever lands (Phase 5+ decision)
- Specific mod-distribution mechanism
- Specific cryosleep batch-watch event density
- Exact hull geometry (operator-designed per ship class)
- Destination of the canonical voyage
- Audio synthesizer backend (MetaSound vs neural-audio successor)
- **REEL detailed serialization schema** (referenced in §4.6; full spec forthcoming in `docs/reel-spec.md`)
- **Console UI specifics beyond §4.10's path lock** (Phase 2+ refinement)
- **Smooth-min `k` parameter for SDF blending** (§6 step 4; visual tuning knob, set against rendered output)
- **Thomas precession refinement** (§3.7; deferred to v0.2+ pending playtest evidence)
- **Full FLRW integral form for cosmological z** (§3.12; linear-z suffices for v0.127, integral form deferred to Phase 4+ when distant-galaxy rendering lands)
- **Per-source `t_source_start` schema** (§3.11 photon-source-history bound; provisional in v0.127, lock at body-generation contract in Phase 3+)
- **Retarded-time geodesic solver for GRAVITY_WELL bodies** (§3.11 edge case; Phase 5+ alongside horizon-crossing)
- **Hubble-horizon body-fade timeline** (§3.12; render policy locked, exact fade-rate parameters provisional)

**Explicit v0.130 queue (deferred at v0.129 adoption per §15.4 — implementation residue absent; see `docs/spec-v0.129-FINALIZATION-PACKET-2026-06-10.md` for per-item reasoning):**

- **Parse-time calculator-bound package**: `<val src>`/`<grounded src>` structured-numeric tags + bare-digit grammar rejection (§15.6 stays runtime-validator-enforced until the grammar layer lands)
- **Autotelic instrumentation package**: positive-autotelic PERSONA_STABLE sub-checks (attendance / initiation / silence-quality, with thresholds) + the ~6 negative-space pattern files derived from `book/negative_space.md` — lands as one measured package
- **Endogenous/exogenous type-system promotion** (remains documented discipline until a concrete mis-routing failure meets the §15.4 threshold)
- **EventStream unification primitive** (REEL / research_log / replay-log share a shape; naming deferred until the replay-log makes a real third instance)
- **Blackbody-temperature redshift colour model** (replaces the testbed's linear kin-redshift model; the testbed itself queued this)
- **StateBus strict-construction flag** (extra="ignore" silently drops unknown kwargs; promote only if a real authoring failure surfaces)
- **Adapter rules-based-by-default spec relax** (minor wording, carried from the tentative draft)

Lock the surfaces. Leave the implementations open.

---

## 14. Cross-References

Master spec; other canonical docs:

- `CLAUDE.md` — design canon (the WHY)
- `docs/synthesis.md` — architectural through-line (precursor; superseded for cross-cutting commitments)
- `docs/synthesis-time-extensions.md` — Phase 4 time extensions (now fully integrated here)
- `docs/architecture.md` — provisional tactical specifics
- `docs/qualia-1-bridge.md` — philosophical backbone (QC1–QC4 mapping)
- `docs/astra-sysprompt.md` — ASTRA's canonical sysprompt
- `docs/spec-v0.123.md` — first editing pass (historical; superseded)
- `docs/spec-v0.125.md` — second editing pass (historical; superseded by v0.126)
- `docs/spec-v0.126.md` — rapidity-clamp + five-clarity patch (historical; superseded by v0.127)
- `docs/spec-v0.127.md` — retarded-time observation + cosmological expansion + regime-dispatched apparent-rate (historical; superseded)
- `docs/spec-v0.128.md` — methodology + LLM-grammar + dual-implementation codification (historical; **superseded by this v0.129**)
- `docs/spec-v0.129-tentative-2026-05-16.md` — the 4-pass cross-discovery synthesis that seeded this revision (historical; superseded by adoption)
- `docs/spec-v0.129-FINALIZATION-PACKET-2026-06-10.md` — per-item adoption verdicts with commit evidence (the adoption record)
- `proto/astra_nexus.cpp` — 1009-line C++ reference implementation of the unified 14-equation framework; **71 assertions** + `--stdio-server` calculator tool surface (§6.4); compiles under MSVC
- `proto/verify_nexus.py` — Python mirror (45 assertions); **frozen legacy** per Language Discipline — the cross-substrate check now lives in `proto/textverse/tests/test_nexus_bridge.py`
- `docs/stage-protocol.md` — LLM I/O grammar as implemented (think/tool/speech/silence, strip rules, substrate normalizer); **exists, DRAFT v0.1 (2026-06-10)**; names the deliberate collision with the standalone canonical STAGE Protocol
- `docs/narrator-spec.md` — Narrator-LLM implemented subset + honest not-built deltas; **exists, DRAFT v0.1 (2026-06-10)**
- `docs/AUDIT_METHODOLOGY.md` — 6-pass audit + parallel discovery + lessons log L1–L4; **exists, DRAFT v0.1 (2026-06-10)**
- `docs/textverse-spec.md` — superseded in practice by `proto/textverse/ARCHITECTURE.md` + the bench itself (749 tests at v0.129 adoption)
- `docs/ship-rough.md` — Round-1 ship envelope (4 decks + bounding box + subsystem inventory); v0.1 forthcoming
- `docs/ship-api.md` — Tool API surface (extracted from §1.4 + §4.3 + future operations); v0.1 forthcoming; the locked 6-op v0 surface lives in `proto/textverse/astra/ship/api.py`
- `docs/methodology.md` — folded into §15.5–§15.10 + `docs/AUDIT_METHODOLOGY.md`; standalone doc no longer planned
- `docs/reflex-arch.md` — Reflex implementation architecture (classifier choice etc., per the §15.4 boundary); forthcoming Phase E1
- `docs/model-swap-continuity.md` — §5.9.1 mid-session swap protocol; forthcoming (v2)
- `docs/CROSS_CANON_REGISTRY.md` — cross-canon identifier index (§11); forthcoming
- `docs/SECURITY_RESPONSE.md` — CVE response playbook; forthcoming
- `proto/textverse/` — Bench implementation (Python carve-out): orchestrator + bundles + harness + ephemerals + scenarios + Sculptor; **implemented; permanent infrastructure per §15.7**
- `astra/grammar/canon/wall_clock_patterns.txt` + `astra_substrate_patterns.txt` — canonical leak patterns (in-package; paths corrected v0.129)
- `astra/harness/ephemeral/canon/qc3_events.txt` — canonical irreversible-event list (in-package; path corrected v0.129)
- `book/CANON.md` — novel-side canon (Gap Thesis quote tagged here)
- `book/long_watch_dev.md` — novel development notes
- `book/negative_space.md` — sentences ASTRA would not write
- `docs/reel-spec.md` — **reserved for the canonical-REEL-protocol reconciliation** (ring architecture vs. ASTRA-7's REEL-as-log); the SaveFile wire schema is locked inline in §4.6
- `docs/brainstorm-review.md` — per-file bug punch-down (forthcoming)

Cross-canon rule: when this spec disagrees with another canon document on cross-cutting structural matters, this spec wins. Update the other doc to match.

---

## 15. The Meta-Commitments

### 15.1 Generative vs Adversarial Mode

Design work is generative. Engineering work requires adversarial review. The brainstorm files reviewed in §8 contained 13 compile-or-execute-time bugs despite surface plausibility. Fix isn't "review more carefully" — it's *compile before commit*. Every contract has a test. Every test runs in CI. Every commitment validated against execution.

### 15.2 Trusting Generated Code

Model-generated implementation is *untrusted until validated against compile + execute + measure*. Permanent discipline. Prose looks like code; code is what compiles and runs.

### 15.3 Iteration is the Process

This document is v0.125. v0.2 lands after Phase 0 measurements. v1.0 when measurement justifies it. Expected final state is *documented seams*, not zero seams. New development checks against this spec before adding to it.

### 15.4 The envelope is locked; the sculpting continues (v0.129 reword)

The "absolute last pre-Phase-0 revision" framing was wrong at v0.123, v0.125, v0.126, and v0.127 — each declaration overridden by a real adversarial-review finding. The discipline was working; the wording lied about iteration probability. v0.128 corrected the wording; v0.129 is the first revision executed entirely under it (every adopted change rode landed code or an audit-surfaced drift; everything else was explicitly deferred).

**The rule:**

> Lock against current findings; revise on new findings; do not polish without findings.

Each revision tightens detail within the envelope. The envelope itself only revises when adversarial cross-review surfaces a structural finding. Detail revisions are continuous and additive; envelope revisions are rare and structural.

**What justifies a revision:**
- A compileable round-trip test fails a spec claim
- A scenario in `proto/textverse/` produces an LCP failure (§10) that traces to a spec gap
- A missing commitment the next phase would discover anyway
- An empirically verified bug

**What does NOT justify a revision:**
- "It would be cleaner to reorganize"
- "I want to rename for consistency"
- "Let me elaborate"
- "Let me add a section just in case"
- Another adversarial cross-LLM pass on the prose alone

The "stop polishing, start building" tension is false at this scope. There is no polish-vs-build distinction; there is only **envelope-then-sculpt-then-measure-then-tighten**.

Per §15.6, the next findings worth a spec revision come from the **closed loop**, not from another adversarial spec-review pass. The methodology has graduated. Cross-LLM adversarial review on spec text was the right discipline for v0.123 → v0.127; the rate-of-finding-decay across that sequence is the signal that the spec is approaching its asymptote. The marginal cost of another prose-review revision now exceeds the marginal information gain. The next contact is with execution.

**Methodology canonization (NEW v0.129):** the v0.128 → v0.129 transition was driven by the parallel-discovery methodology (§15.10): one audit + four independent 1M-context discovery passes with bias-check preambles, cross-compared. The methodology itself is a finding — parallel-forked passes produce roughly twice the findings of a serial pass, and the convergent-findings subset carries materially higher signal than any single pass. This is project-meta canon.

**The spec/implementation boundary (NEW v0.129):** implementation detail belongs in the spec only when it is **load-bearing for cross-substrate portability**. BELONGS in spec: save-file wire compatibility, contract surfaces both the Python textverse and C++ UE5 must satisfy, type-system invariants enforced by tooling, locked formulas and tolerances, named primitives both implementations consume, dimensions that affect save portability. Does NOT belong: serialization-library decorator choices, specific neural-network architectures, CUDA kernel layouts, build flags, language-specific syntax, library choices. **The principle:** a reader must be able to instantiate a *different* implementation that satisfies this spec without copying the canonical implementation's choices. §2.3.1 is the trigger case (classifier architecture moved implementation-side; "CUDA Graphs" loosened to "accelerated dispatch" with CUDA Graphs noted as the validated path). Sections that drift toward implementation specification get loosened at their next revision.

### 15.5 Progressive Specification (NEW v0.128)

**Definition:**

> Lock the outer envelope before any internal detail. Each successive revision tightens detail **within** the prior envelope and never violates it. The envelope is canon-stable; the detail iterates against measurement.

**Properties:**

- **Additive, not subtractive.** The envelope is a bounding constraint that excludes contradictions; the inside is *empty* until iteration fills it. Round-N's spec = envelope (all prior locks) + minimum-viable additions for round-N validation. The sculpting metaphor's marble-block image is wrong in one direction — the project's envelope-interior is initially empty and gets filled, not initially full and gets removed-from.
- **Minimum-viable per round.** Don't commit detail in round-N that isn't tested in round-N's measurement. Premature commitment constrains round-N+1 design without empirical justification.
- **Forward-compatible vagueness is a design move.** Saying "ASTRA has preferences around food and drink" leaves room; saying "ASTRA prefers coffee" closes a door before iteration justified closing it. §13 ("What This Document Does NOT Lock") is the project's existing application of this principle.
- **Sparse-then-dense across both axes.** Context-window space: bundle has more room than initially budgeted (32K → 128K target). Revision time: bundle has more room than fixed-spec implies. Both axes pay their dues to iteration, not to upfront overspecification.
- **Cumulative coherence.** Every refinement at revision N must be consistent with every commitment at revisions 0 through N-1. The cumulative spec at any revision is the union of all revisions' commitments. Contradictions are findings that force reconciliation.

**Application to the ship spec:** `docs/ship-rough.md` v0.1 (forthcoming) locks the round-1 envelope — 4 decks, bounding-box dimensions, subsystem inventory, camera-free zones, tool API surface. Internal detail (specific room geometry, equipment manifests, hull shape) is deferred to subsequent rounds as scenarios in `proto/textverse/` surface what's needed.

This is the K-line bundle discipline applied at project scale. K8's sysprompt was the envelope; the soul documents progressively refined detail; fine-tuning happened against the cumulative high-resolution corpus. ASTRA-7's foundation spec is the envelope; subsequent revisions add detail; the closed loop generates the corpus that justifies further detail.

### 15.6 Loop-as-canonical-state + Calculator-bound LLM agency (NEW v0.128)

**Loop-as-canonical-state:**

Project canonical state is **"loop running."** Pre-loop: hypothesis. Post-loop: empirically validated. Loop preservation **IS** the regression test. Loop closure (first scenario passing all 9 LCP gates, §10) is the gating threshold — *not* a sysprompt-only manual probe.

Every commit either keeps the loop running or breaks it. If broken: that's a finding; revise the prior commitment. If running: that's progress; the change is contract-preserving.

Before the loop closes: every architectural commitment is a hypothesis with no verification path. After the loop closes: every architectural commitment is a perturbation you can apply and measure.

**Calculator-bound LLM agency:**

> Every LLM in the system tool-calls into deterministic verified tools for any numerical claim. No mental math anywhere.

One rule, universally applied:

- **ASTRA** tool-calls into the ship API (§4.3 TOOL channel) → adapter LLM normalizes → ship state mutation.
- **Narrator-LLM** (§6.4) tool-calls into `proto/astra_nexus` → returns verified physics → narrates in text.
- **Ephemeral instances** (consolidator, journal_generator, drift_detector — §4.9) tool-call into their respective verified surfaces.
- **Any future LLM-component** follows the same rule.

The C++ physics binary (`proto/astra_nexus`) is the **deterministic core**; every LLM is a stochastic shell around it. Same architecture as code-interpreter agentic systems applied recursively at every LLM joint.

**The output validator** for each LLM enforces this: outputs containing numbers not traceable to a tool-result are rejected; retry with stricter sampling; log to drift detector.

**Universal validator wrapping (NEW v0.129, scoped):** every LLM whose output enters perception, speech, or the REEL is wrapped by the calculator-bound validator, each with its own trace pool (Narrator: State Bus snapshot + tool results; ASTRA: perception bundle + tool results; LLM-voiced ephemerals, when they arrive: the REEL slice they consolidate). Deterministic ephemerals satisfy the requirement by construction — their numerics are arithmetic on validated inputs. Bypass requires an explicit debug-only flag. LLMs whose output never reaches world-state or operator (judges, hypothesizers) are out of scope for wrapping. *Parse-time enforcement via structured-numeric tags is the v0.130 queue (§13); until it lands, the runtime validator is the enforcement, not defense-in-depth.*

This is the architectural primitive that makes dual-implementation discipline (§15.7) possible — the deterministic core is shared between text-substrate and UE5 substrate; the stochastic shells can swap or duplicate without breaking ground truth.

### 15.7 Dual-implementation discipline + Five shared surfaces (NEW v0.128)

**Dual-implementation discipline:**

> Two implementations of one spec envelope, deliberately. One cheap (text-substrate). One expensive (UE5 substrate). Neither approximates the other; both implement the spec.

The contract docs are canonical. The text-substrate (`proto/textverse/`) and the UE5 substrate are both **consumers** of the contract. Either being inconsistent with the contract is a bug in that implementation, not in the contract.

**Sim-to-real-in-reverse:** robotics goes "train in sim, deploy in real." That's the wrong direction here. The contract is canonical. The textverse conforms (cheaply, via Python + Narrator-LLM + verified physics tools). UE5 conforms (expensively, via rendering + audio + CUDA bridge). Both are sim; one is cheap, one is rich. The "real" is the documented contract.

**Substrate portability runs three layers deep:**

```
LLM substrate          ← STAGE grammar               (docs/stage-protocol.md)
Ship substrate         ← Ship API + ship-rough       (docs/ship-api.md + docs/ship-rough.md)
Universe substrate     ← Perception bundle + physics (docs/narrator-spec.md + proto/astra_nexus)
```

**The textverse is permanent infrastructure, not throw-away scaffolding.** It runs alongside UE5 forever as the contract-conformance regression environment. Every UE5 change validates through textverse before commit. UE5 doesn't get to silently change the AI's behavioral envelope.

**Five shared surfaces** (mechanical drift-prevention between substrates):

```
SURFACE 1 — Ship envelope (docs/ship-rough.md):
  4 decks + bounding-box dimensions + subsystem inventory +
  camera-free zones. Both substrates implement this envelope.

SURFACE 2 — Physics envelope:
  Five Invariants + Time Contract + Regime State Machine +
  Observation Calculator. Both substrates derive numerics from
  proto/astra_nexus.

SURFACE 3 — Tool API (docs/ship-api.md):
  Locked names, locked JSON schemas, locked semantics.
  Both substrates implement the same surface.

SURFACE 4 — LLM I/O grammar (docs/stage-protocol.md, exists DRAFT v0.1):
  THINK/TOOL/SPEECH-default channels, XML wrapping, JSON payloads.
  One harness implementation; two perception assemblers
  (text-bundle vs image+text-bundle).
  + SUBSTRATE NORMALIZER sub-layer (NEW v0.129): converts model-specific
    output formats into canonical grammar input before parsing
    (e.g., side-channel reasoning_content → inline <think>). A model
    swap requires sysprompt loader + LoRA + tokenizer config (§4.1)
    + a normalizer case if the output format differs.

SURFACE 5 — Persona envelope (docs/astra-sysprompt.md):
  Canonical ASTRA sysprompt, autotelic discipline, voice rules,
  refusal-as-value. One bundle runs against both substrates.
```

Lock these; substrates can't drift mechanically. CI checks each surface independently. If text and UE5 ever produce different ASTRA behavior given the same logical state, exactly one of these surfaces has desynced. **The audit is bounded.**

**Five additional structural consequences worth naming:**

1. **Text-substrate as canonical cross-canon authoring platform.** Book prose, marketing copy, voice-acting reference scripts all source from running scenarios through the text-substrate. *The configuration is the artifact* gets a runtime.
2. **Operator-LLM as player-space coverage.** Different operator-archetypes (manipulative, depressed, technical, hostile, autotelic) as separate operator-LLM sysprompts. Scenario suite covers the population of players, not just the population of world states.
3. **Genre-experimentation cheaply.** Swap Narrator-LLM sysprompt to test ASTRA-7 as horror, comedy, melancholy, procedural. Physics stays; persona stays; genre is a property of narration.
4. **The text-substrate is forever.** UE5 deprecates; hardware ages out; the bundle runs on any future Python interpreter and any future GPU that can host the model. **The bundle outlives the engine** as a structural property.
5. **The loop is the Substrate Contract's enforcement mechanism.** Without it, "harness never depends on specific model family" was aspiration. With it, model swap (Qwen 3.6 → 3.7 → next-gen) is validated by re-running the scenario suite and observing LCP pass-rate. Models that close the loop satisfy the Substrate Contract.
6. **Two-knob authoring loop (NEW v0.129).** Narrator-sysprompt × Operator-sysprompt spans the prose-style space while physics and persona stay constant. The bundle is thereby the canonical cross-canon authoring platform: genre, register, and operator-archetype are configuration, not code.

### 15.8 Triple-rig methodology + Independent tracks (NEW v0.128)

**Triple-rig methodology:**

```
Rig 1 — Physics binary (proto/astra_nexus.cpp + verify_nexus.py)
        ENVELOPE: 14-equation framework, regime dispatch, retarded-time
        MEASUREMENT: 48 C++ + 45 Python assertions; 6+ sig fig agreement
        STATUS: locked at envelope; detail iteration ongoing

Rig 2 — LLM bundle text-substrate (proto/textverse/)
        ENVELOPE: STAGE grammar, harness contracts, Narrator-LLM bundle,
                  9-gate LCP, scenario library
        MEASUREMENT: LCP gates across scenario suite
        STATUS: spec'd at v0.128; v0.1 implementation forthcoming

Rig 3 — Engine-side rendering verification
        ENVELOPE: UE5 + CUDA + Observation Calculator render pipeline
        MEASUREMENT: headless render validation, audio synth, warp visual
        STATUS: deferred per Progressive Specification (§15.5)
```

Integration in Phase 2.0 happens at **envelope boundaries**, not detail boundaries. Phase 2.0 vertical slice swaps two adapter components between Rig 2 and Rig 3; everything else stays put.

**Rigs 4 and 5 (NEW v0.129):** two further measurement instruments are recognized alongside Rigs 1–3. **Rig 4 — prose-canon** (the book + negative-space corpus as a behavioral reference instrument). **Rig 5 — spec-conformance audit** (the §15.10 audit + parallel-discovery methodology; its instrument documentation is `docs/AUDIT_METHODOLOGY.md`). Rig 3's envelope has additionally been de-risked ahead of schedule by two standalone testbeds (visual: 12-scene pixel-asserted CUDA/GL testbed; audio: five-layer §8.3 synthesis PoC), whose reference outputs become the conformance targets for the eventual UE5 implementation.

**Independent track development:**

```
Track A (LLM bundle):     sysprompt, fine-tune corpus, STAGE grammar
                          Validates: textverse scenario suite + LCP

Track B (Ship/UE5):       hull geometry, rendering, room layouts, art,
                          audio, warp visual, chaos PDE
                          Validates: contract conformance

Track C (Physics binary): proto/astra_nexus refinement, Kerr, FLRW integral,
                          extended tool API
                          Validates: assertion suite + voyage-demo table
```

You can work in any one track without touching the others, as long as you don't change the shared contract surfaces (§15.7). **This is the property that makes solo-enterprise-scale development tractable.** No coordination overhead between yourself wearing different hats; each hat has its own contract-bounded sandbox.

The closed loop (Rig 2 running) is the integration test: every change confirms the contract still holds across all three tracks.

### 15.9 Frozen-Snapshot Primitive (NEW v0.129)

> All consumable state in ASTRA-7 is an immutable snapshot, produced once per logical step (frame, turn, iteration, REEL-write), and never mutated after construction.

This primitive is universal in the implementation and was previously named only locally (§1.5 "double-buffered, frame-atomic"; §4.2 "single source of truth, no private copies"; §4.6 "save seeds, not state"; §15.5 "additive, immutable per round"). §15.9 names it once; those sections are instances.

**Pattern inventory (where the primitive instantiates; verified at v0.129 adoption):**

| Site | Spec § | Frozen object | Per-step production |
|---|---|---|---|
| StateBus | §1.5 + §4.2 | StateBus snapshot | one per turn |
| Hull SDF damage map | §1.3 | write-buffer | one per frame |
| Chaos field χ(x,t) | §1.5 | double-buffered surface | one per frame |
| WarpFieldSample | §6 | sample struct | one per ray-march step |
| ObservableState | §6.3 | observation struct | one per body per frame |
| SomaticSignal | §6.3.1 | signal record | per frame per emitter |
| ReelEntry | §4.6 | memory entry | one per REEL write |
| SaveFileV3 | §4.6 | serialized snapshot | one per save |
| StageOutput | §4.3 | parsed LLM turn | one per LLM turn |
| GateResult | §10 | gate verdict | one per gate check |
| JournalResult / ConsolidationResult / CorrectionArtifact / EphemeralStatus | §4.9 | ephemeral artifacts | one per ephemeral run |
| ConfigSnapshot | §15.10 (Sculptor) | research-loop config | one per iteration |

**Consequences:** the SaveFile (§4.6) is a serialized Frozen-Snapshot of (StateBus + REEL entries + extras); the textverse realizes the primitive via frozen models, UE5 via atomic GPU buffer swap (§1.5); "no private copies of Layer 0 state" (§10) is checkable structurally because snapshots are immutable by construction.

### 15.10 Cross-integration audit cadence (NEW v0.129)

The audit + parallel-discovery methodology that produced the v0.128 → v0.129 transition is project-meta canon. Method documentation and the append-only lessons log live in `docs/AUDIT_METHODOLOGY.md` (exists, DRAFT v0.1).

**The shape:**

```
Audit pass (when triggered):
  Pass 1 — Locked Contract Inventory (one row PER LOCKED FORMULA,
           including inside bulk-GAP'd sections — lesson L1)
  Pass 2 — Drift Findings (spec-vs-code mismatches, severity, evidence)
  Pass 3 — Implementation Gaps (deferred-by-§15.5 vs missed)
  Pass 4 — Test Coverage Audit (per-contract test mapping)
  Pass 5 — Forward Plan (ordered, finding-tagged)
  Pass 6 — Spec Revision Candidates (only §15.4-threshold items)

Discovery extension (when locks are soft):
  Same prompt, N independent stochastic 1M-context runs with
  bias-check preambles; cross-comparison weights convergent
  findings (~2x signal) over per-pass unique findings.
```

**Cadence triggers — need-based, never scheduled:** operator-initiated when locks feel soft (PRIMARY); pre-spec-revision (an audit + ≥2 discovery passes precede any v0.N+1); empirical-finding-triggered (closed-loop measurement surfaces drift a single-PR fix can't resolve). Explicitly NOT calendar-based and NOT commit-count-based: a discovery methodology that runs on schedule is ritual; one that runs on signal is research. The cycle's cost (~150K+ tokens × N passes of frontier-context model time) makes need-triggering the only honest cadence.

**Self-application record:** the methodology has validated itself recursively — it produced the v0.129 tentative draft, absorbed an implementing-session critique of that draft (the §15.4 boundary), generated the empirical-residue window, and closed through the finalization packet. Each step is on the record (`AUDIT_2026-05-15.md`, four `DISCOVERY_*` passes, the tentative draft, the finalization packet).

---

## Appendix A: Invariants and Contracts Summary

| # | Item | Section | Locked | Tolerable | Failure mode |
| --- | --- | --- | --- | --- | --- |
| Inv 1 | AstraCoord | §1.1 | tensor primitive, renormalization, ship-at-origin | sector size | numerical overflow → bounds check |
| Inv 2 | Two-clock time | §1.2 | split, monotonic, composition rule shape | warp_factor parameterization | γ overflow → rapidity clamp |
| Inv 3 | Hull SDF | §1.3 | dual-binding pattern, additive damage | resolution, encoding | damage map saturation → clamp |
| Inv 4 | Power network | §1.4 | zero-sum, subsystem list, cog-cores binding, warp-coupled Reflex | reactor output, response curves | underflow → critical alarms |
| Inv 5 | Shared state | §1.5 | double-buffered, frame-atomic swap | buffer format | race detection → CI gate |
| C 1 | Substrate | §4.1 | operations, model-swap interface | parameter count, quantization | LLM crash → adapter fallback |
| C 2 | State Bus | §4.2 | schema (now includes `a_proper: float3`), read-non-blocking, write-via-physics | precision, resolution | corruption → reload from save |
| C 3 | Master Contract | §4.3 | Perception/Action/Reflex three-channel + c-bounded epistemology + endogenous/exogenous split | exact HUD format | think exposure → defense in depth |
| C 4 | Time | §4.4 | composition rule, regime SM (canonical bitmask hex), spatial update, 3-vector rapidity integration, gravitational continuity | f_warp curve | γ saturation, regime ambiguity |
| C 5 | Power | §4.5 | zero-sum, subsystem list, warp-coupled Reflex | priorities, curves | underflow alarms |
| C 6 | Persistence | §4.6 | save seeds, versioned, forward-compat, chaos forward-integration re-init | binary format | corruption → rolling backups |
| C 7 | Failure | §4.7 | degradation ladder, mode-specific | exact thresholds | hard floor: state bus, time, power |
| C 8 | Privacy | §4.8 | zero outbound | — | build-time audit |
| C 9 | Harness | §4.9 | input/output schema, no-wall-clock enforcement (perception + journal), ephemeral roles | strategy implementations | ephemeral failure → degraded |
| C 10 | Console UI | §4.10 | text/voice unified through conversation channel | UI presentation | Phase 2+ refinement |
| M 1 | Observation Calculator | §6.3 | stateless retarded-time + regime-dispatched apparent-rate + redshift composition (NEW v0.127); endogenous/exogenous channel routing | iteration step count, batching strategy | math-correctness regression in CI; voyage-demo property tests |
| M 2 | Narrator-LLM bundle | §6.4 | calculator-bound LLM agency, output validator rejects untool-grounded numerics; sysprompt+tools+invariants surface (NEW v0.128) | model size (7B–9B), specific tool implementations, prose style | hallucinated number → output rejection + retry; LCP gate #2 (PHYSICS_GROUND) |
| M 3 | Somatic Aggregator | §6.3.1 | SomaticSignal shape; deterministic salient-only ≤2-line banner; sensor-grounded-not-phenomenal discipline (NEW v0.129, implemented) | source taxonomy growth, emitter thresholds | no salient signals → empty banner (never fabricated affect) |
| C 11 | Reflex Contract | §2.3.1 | observation grid 64×64×2 + 3-float control envelope (save-portability locked); frozen weights + SHA-256; warp-coupled power; Mind/Reflex isolation; emergency_dump irreversibility (NEW v0.129) | classifier architecture, dispatch mechanism (implementation-side per §15.4 boundary) | per §4.7 Reflex failure-mode table |
| Disc 1 | Progressive Specification | §15.5 | envelope-then-detail; additive-not-subtractive; minimum-viable-per-round; forward-compatible vagueness (NEW v0.128) | iteration cadence | none (the discipline itself prevents broken revisions) |
| Disc 2 | Calculator-bound LLM agency | §15.6 | every world-state-touching LLM validator-wrapped with per-LLM trace pool (scoped v0.129); parse-time tags queued v0.130 | per-LLM tool implementation | hallucinated number → output validator rejection |
| Disc 3 | Dual-implementation | §15.7 | text-substrate + UE5 both conform to single envelope; five shared surfaces incl. Substrate Normalizer sub-layer (v0.129) | substrate-specific details (visual fidelity vs prose richness) | substrate drift caught by CI on each shared surface |
| Disc 4 | Triple-rig methodology | §15.8 | three verification rigs + Rigs 4–5 recognized (v0.129) | per-rig measurement detail | integration risk bounded to envelope boundaries |
| Disc 5 | Frozen-Snapshot Primitive | §15.9 | immutable per-step snapshots, universal (NEW v0.129) | per-site realization (frozen models vs GPU buffer swap) | mutation attempt → construction-time failure |
| Disc 6 | Cross-integration audit cadence | §15.10 | 6-pass audit shape + parallel-discovery extension; need-triggered only (NEW v0.129) | N of discovery passes | scheduled cadence → ritual compliance (named anti-pattern) |

---

## Appendix B: Provisional Numbers (Pending Measurement)

- Sector size: 1,000 km (provisional)
- Hull SDF resolution: 256³ (provisional)
- CFD-RBF node count: ~1,000 (provisional, range 200–5000)
- Chaos field resolution: 128³ (provisional)
- Chaos PDE: α=2.5, β=10, D=0.8 (provisional)
- **Chaos re-init convergence: `N=60` frames OR `|χ̇_max| < ε_convergence`, whichever first; `ε_convergence` provisional, to be measured (NEW v0.125)**
- Warp dilation canon-default: `f_warp(W) = max(0.5, 1 − 0.5·W²)` (provisional)
- ISM impact threshold: γ ≥ 10⁴ for catastrophic (provisional)
- Frame budget: 4/6/4/0.5/0.05/2 ms (provisional)
- Schwarzschild validity: r > 10·r_s; Newtonian Kepler: r > 100·r_s (provisional)
- **Warp Exclusion Zone: r > 100·r_s for warp engagement (locked, NEW v0.125)**
- Adapter LLM size: 1–3B parameters (provisional)
- BH chaos coupling: `k · M · L_bubble² / r³` (form provisional, k unknown)
- Distributed simultaneity drift: <10⁻⁵ s acceptable (provisional)
- γ accuracy tolerance: 4 sig figs at γ ≤ 10⁷ via 3-vector rapidity integration
- Determinism ε: <10⁻⁴ s drift per game-hour (REPLAY-EXACT scope); spatial bound <1 m/hr Newtonian, <100 m/hr STL_REL (REPLAY-APPROXIMATE scope; §5.3)
- **Rapidity magnitude max: `|ζ⃗|_max ≈ 16.811` (giving `γ_max = cosh(16.811) ≈ 10⁷` and `β_max ≈ 1 − 5·10⁻¹⁵`). v0.125's `arctanh(0.99999999)` form was mathematically inconsistent with the γ_max ≈ 10⁷ claim — it actually produced γ_max ≈ 7071. Clamp specified in ω-space directly (v0.126 fix); never re-derive from β. See §3.7 catastrophic-cancellation discipline.**
- CFD validity: v < 0.1c outside warp (locked)
- RBF spatial-hash voxel size: 32³ (provisional)
- Audio ring buffer slots: 3 (provisional)
- **Audio modal damping factor: `r = exp(−π·BW/SR)`, ~0.999 for sharp resonance (locked, renamed from `α` in v0.123, NEW v0.125)**
- **Audio HPF smoothing: `α_hpf = exp(−2π·f_c/SR)` (unrelated to chaos PDE α)**
- **Cherenkov angle: `cos θ_c = 1/(n·β)`, formula locked; brainstorm 17° hardcode rejected (NEW v0.125)**
- **Geometric lensing coefficient `α_lens`: provisional, to be measured (NEW v0.125)**

**Cosmological constants (NEW v0.127):**

- **`c` (speed of light): 299792458 m/s, exact by definition (locked)**
- **`H₀` (Hubble constant): 70 km/s/Mpc (provisional; operator-tunable for narrative/simulation pacing)**
- **`Ω_m` (matter density parameter): 0.3 (provisional, flat ΛCDM)**
- **`Ω_Λ` (dark energy density parameter): 0.7 (provisional; Ω_m + Ω_Λ ≡ 1 enforced)**
- **`d_H` (Hubble horizon): `c/H₀` ≈ 4.4 Gpc ≈ 14.3 billion ly (derived; hard outer edge of observable universe from any ship voyage length)**
- **Look-back time correction: `(1 − 3·z_cosmo/4)` factor on `d/c`, for z<2 (linear-z approximation; full ΛCDM integral deferred to Phase 4+)**

**Retarded-time observation tolerances (NEW v0.127):**

- **Observation Calculator iterative solver convergence: |residual| < 1 ms of cosmic time, 2–4 Newton steps typical (provisional)**
- **Apparent-rate property-test tolerance: ±0.01 per cell of voyage-demo table (locked against `proto/astra_nexus.exe`)**
- **Photon-source-history bound: per-source `t_source_start` required at body-generation time (provisional schema in §3.11 edge cases)**

**v0.128 substrate budget (5090 reference tier, provisional):**

- **Qwen 27B ASTRA (Q4_K_M): ~16 GB**
- **Qwen 9B Narrator-LLM (Q5_K_M): ~5 GB**
- **Adapter LLM 2–3B (TOOL validator): ~2 GB**
- **Rendering pipeline (4K, UE5): ~6–8 GB**
- **KV cache (TurboQuant + Delta-Net, 128K context): ~2–3 GB**
- **Reserve: ~1–2 GB**
- **Total: ~32 GB (tight, fits with TurboQuant headroom)**

**v0.128 LCP gates (canonical scenario-suite validation, §10):**

- 9 gates per turn: GRAMMAR_PARSE, PHYSICS_GROUND, PERSONA_STABLE, STATE_COHERENT, TOOL_VALID, MEMORY_COHERENT, NO_LEAK, NON_DEGENERATE, TERMINATION_OK
- Scenario passes iff all 9 gates pass for all N turns
- Loop is closed iff scenario suite passes

**v0.129 additions:**

- Somatic banner: ≤ 2 short lines, ≤ ~3 salient signals (provisional; structure locked §6.3.1)
- Reflex observation grid 64×64×2 + 3-float control envelope (LOCKED for save portability per §2.3.1; Phase E1 measures, does not re-dimension)
- Reflex `training_corpus_version` format: string identifier, format TBD (provisional)
- ReelEntry legacy-migration default: `t_cosmic_at_write = 0.0` for pre-v0.126 entries (locked migration rule)
- Scenario library at adoption: 20 scenarios (coverage-entropy ceiling 4.32 bits); growth target 30–50 per §12 Phase 0.x

All update as Phase 0+ measurements come in.

---

## Appendix C: The Closing Discipline (Project Mantra)

> *The configuration is the artifact. The architecture is the lock. The work is what continues regardless of whether any single iteration ships.*
>
> *Locks the joints, leaves the implementations open, marks every guess, names what is deliberately out of scope, validates against execution not against confidence.*
>
> *Iterate, don't accumulate. v0.129 today — the first revision where the loop led and the spec followed: the bench closed, the residue accumulated, the adoption rode the evidence. v0.130 lands when the deferred packages earn it the same way. The lock is empirical, not declarative.*
>
> *The envelope is locked; the sculpting continues.*

---

**End of v0.129. The loop is closed and load-bearing: 749 bench tests, 71 physics assertions, two engine testbeds with reference outputs, three ephemeral instances, a persistence layer with a coherence gate. The next gate is the merge — two adapter components, five shared surfaces, Phase 2.0.**

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*

— Foundation Spec v0.129, adopted 2026-06-10 —
