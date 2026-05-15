# ASTRA-7 Foundation Specification v0.123

*The Lock Layer, one editing pass after v0.1. Spinal in commitments. Provisional in particulars.*
*Drafted 2026-05-14, revised same day against three rosetta-stone reviews.*

---

## Changes from v0.1

This is a single editing pass. Bug fixes, gap fills, terminology tightening. No structural changes. After this revision, no more polish until Phase 0.0 measurements return data.

**Bugs fixed:**

- §3.3 regime detection pseudocode rewritten — was crashing on empty BH list, using `regime` before assignment, mixing bitmask `|` with integer `+`, and not composing GRAVITY_WELL with warp.
- §3.2 Schwarzschild language corrected — was implying products of √-factors across BHs; correct form is one √ over summed Newtonian potential in weak field, dominant-BH only in strong field.
- §3.5 / §1.2 / §3.2 `f_warp` default reconciled into two layers: contract-level = 1 (no dilation); ASTRA-7 canon-default = ramping form (operator's design choice).
- §3.5 `W` defined before first use.
- §4.4 cross-reference to the Time Contract block consolidated.
- §5.3 determinism tolerance ε given an explicit number.
- §5.6 frame budget 0.05 ms / 50 μs inconsistency resolved.
- §6 / §3.4 Doppler ownership disambiguated — Unified Sampler's `doppler_shift` renamed `metric_shift` (gravitational/warp redshift); kinematic Doppler is the starfield renderer's responsibility from `v_eff`.
- §7 truth table coord-update cell now states the locked form `v·Δt_cosmic` only.
- §7.3 acceleration integrator switched to adaptive RK4 (RK45) on rapidity ω = arctanh(v/c). Fixed-step RK4 on velocity would blow up at high γ.
- §8.1 DX12 map/unmap semantics corrected — map once at registration; per-frame coordination via external semaphores only.
- §4.6 chaos field re-initialization to steady-state-for-current-warp-amplitude, not to zero (zero is not necessarily a stable steady state).

**Gaps filled:**

- §4.9 NEW Harness Contract — the harness is now a first-class module with input/output schema, invariants, operations.
- §4.10 NEW Console UI / Text-Input Contract — player text and voice unified through the same conversation-channel path.
- §8.3 NEW audio-specific bug commitments — Layer 2 HPF fix, Layer 5 modal resonance, granular grain-voice array.
- §12 Phase 0.3 — REEL prototype with dual-clock awareness validation.
- §10 added QUALIA-1 validation rows.
- §3.3 "GRAVITY_WELL multiplies regardless" sentence added.
- §3.3 0.1c threshold reframed as "semantic label, not physics discontinuity."
- §7.4 v0.1 horizon-crossing limitation explicitly named.
- §5.8 mod ABI honest reframe — canon-compliance is signal, not enforcement.
- §4.3 Master Contract notes Power Contract as the only modulator of both Mind and Reflex envelopes.
- §5.9 hardware tier reframed as query-interface-plus-reference-table.
- §5.7 wall-clock-leak grep pattern list referenced as external file.
- §6.1 ISM > 0.1c language sharpened (relativistic particle beam, not continuous fluid).
- §6.1 inherits the analog-gravity Visser/Unruh reframing (moved from §11).
- §8.2 audio ring buffer named explicitly as "latest-state model, not lossless queue."
- §7 truth table adds chaos α scaling row for BH-warp coupling.
- §11 compressed; Gap Thesis defined inline.
- Appendix A section numbers per row; wording fixes.
- Appendix B adds determinism tolerance number, rapidity integrator constants.

**Deliberately not changed:**

- Section ordering. §9 Emergence Zones stays where it is. Promoting it would weaken its landing.
- Version pinning in body text ("Inv 3 v0.1"). Cosmetic.
- Em-dashes in author voice. Harmless, flagged for completeness.
- Major prose rewriting. The goal is one editing pass, not the perfect spec.

---

## 0. What this document is

This is the foundation specification for ASTRA-7. It locks the architectural commitments that everything downstream depends on, leaves the implementations open, and marks every specific number explicitly provisional until measurement validates it. It is the one document Phase 0, Phase 1, Phase 2, the eventual book, and the open-source community must all read first.

The doc has three commitments to itself:

1. **Lock the joints, not the implementations.** Every contract defines an interface surface, a set of invariants, a tolerance range. Implementations behind each surface may evolve freely as long as the surface holds.
2. **Mark every guess.** Specific numbers (SDF resolution, context window, frame budgets, chaos PDE parameters) are presented with `(provisional, to be measured)` where they have not been validated empirically. The framework is canon; the numbers are not.
3. **Name what is deliberately out of scope.** The "out-of-contract emergence zones" section (§9) names what the spec refuses to specify because it should not be specifiable.

This document supersedes the cross-cutting structural commitments in `synthesis.md`, `synthesis-time-extensions.md`, `architecture.md`, and `qualia-1-bridge.md`. Those documents remain canonical for their topic areas; this one is the master index. When they disagree, this spec wins; update them to match.

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

**Locked:** double-buffering of all mutable shared state, atomic frame-boundary swap, single-source-of-truth principle.
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
| Substrate | LLM (Qwen 27B / 9B / etc.) | CNN+LSTM-style on Tensor Cores |
| Tempo | Conversation rate (~1–10 Hz) | Frame rate (60 Hz) |
| Latency budget | Seconds (out-of-band) | ≤ 50 μs naive, ≤ 20 μs with CUDA Graphs |
| Determinism | Stochastic (sampling) | Deterministic (frozen weights) |
| Kernel residency | Mind Kernel | World Kernel |
| Power slot | "cognitive cores" (shared bus) | "warp-coupled stabilizer" (auto-prioritized when warp active) |
| Failure mode | Offline → ASTRA goes quiet | Failure → bubble collapses → ship in mortal danger |
| Master Contract surface | Perception in, Action out | Observation grid in (64×64×2), Control out (3 floats) |

Architecturally distinct AI components. Different contracts, different failure modes, different power criticality. **The Power Contract (§4.5) is the only system that can modulate both Mind and Reflex envelopes simultaneously, via subsystem allocation.**

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

Let **`Φ = Σ_i −GM_i / r_i`** denote the summed Newtonian gravitational potential from all relevant bodies (weak field).

Then:

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 + 2Φ/c²) / γ_kinematic(v)
```

Three multiplicative contributors:

- **`γ_kinematic(v) = 1 / √(1 − v²/c²)`** — Special-relativistic Lorentz factor from ship velocity in local CMB rest frame. ≡ 1 outside relativistic-STL regime.
- **`√(1 + 2Φ/c²)`** — gravitational time dilation. In the **weak-field limit**, computed from the summed Newtonian potential Φ across all bodies. In the **strong-field limit** (close to a single dominant BH), use Schwarzschild `√(1 − r_s/r)` with only that BH. The summing applies to potentials (which add), not to factor expressions. ≡ 1 in flat space. Below ~10·r_s, all approximations break down; see §7.4.
- **`f_warp(W)`** — the warp drive's contribution. **Warp does not directly dilate ship time**: inside an Alcubierre bubble, the crew is in a locally flat spacetime frame and `τ_inside ≈ t_cosmic` locally. *However*, `f_warp(W)` is **left as a design parameter** in `[0.0001, 1.0]` to permit the operator to introduce intentional dilation as a narrative knob. **Contract-level default: `f_warp(W) ≡ 1`. ASTRA-7 canon-default: see §3.5.**

**GRAVITY_WELL multiplies into the composition rule regardless of which other regime is active.** Warp+GW, STL_REL+GW, REST+GW all compose by inserting the gravitational factor.

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
                  │  CRYOSLEEP   │   (τ_ship advances; τ_crew_bio paused)
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

**Mutually exclusive at the physics level:** WARP and STL_REL cannot be simultaneous. Warp bubble suspends Newtonian velocity in bubble's frame; `γ_kinematic ≡ 1` during warp. WARP and deep GRAVITY_WELL also mutually exclusive by canon (warp drives cannot engage in steep gravity wells; design opportunity: ASTRA warns the operator).

**Composable:** GRAVITY_WELL with REST, STL_NONREL, STL_REL, or weak warp. Factors multiply.

**The 0.1c STL_REL threshold is a semantic regime label for dispatch optimization, not a physics discontinuity.** All underlying physics formulas (Doppler, ISM impact, time dilation) are continuous functions of β. Implementations blend smoothly across the 0.1c boundary with no discrete jumps in audio, rendering, or behavior. Dispatch is for code-organization; physics is continuous.

**Transition behavior:**
- **STL_NONREL → STL_REL**: smooth, governed by acceleration profile.
- **WARP_CHARGE → WARP_CRUISE**: discrete on charge completion (charge timer hits zero).
- **WARP_CRUISE → WARP_SHUTDOWN**: smooth (controlled) or discrete (emergency dump).
- **STL_* → GRAVITY_WELL**: smooth, gravitational factor ramps as 1/r approaches r_s/r.

### 3.4 Doppler / aberration framing (continuous)

Two distinct phenomena, easily conflated:

- **Kinematic Doppler / relativistic aberration** — applies to *background starfield*. Computed from the ship's effective 4-velocity in the local CMB rest frame. Handled by the **Starfield renderer**, using `v_eff`. Inputs:
  - STL_NONREL: `v_eff = v_kinematic`, `γ_eff ≈ 1`. Effects imperceptible.
  - STL_REL: `v_eff = v_kinematic`, `γ_eff = γ_kinematic`. Real SR Doppler `f_obs/f_emit = 1/[γ(1 − β·cos θ)]`. Aberration warps star directions toward forward.
  - WARP_CRUISE: `v_eff = v_bubble_apparent` (visually capped at β ≈ 0.999 to prevent renderer artifacts). Same SR shader math runs.

- **Metric redshift** — applies to *light passing through the warp bubble boundary or near a gravity well*. Computed from `W(x,t)` and `Φ(x,t)`. Returned by the **Unified Sampler** as `metric_shift` (see §6).

**Kinematic Doppler and metric redshift compose multiplicatively** in the final composite. Two different physical effects, two different code paths, one unified visual result. The Unified Sampler does not return a "Doppler shift"; it returns `metric_shift`. Naming this distinction matters because conflating them produces double-counting bugs.

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
- CRYOSLEEP: zero

This is the spatial-desync fix. Mathematically, `γ · v · Δτ_ship` is identically equal to `v · Δt_cosmic` (since `dt_cosmic = γ · dτ_ship`), but the locked form is the cosmic-time expression. Always compute coordinate advance in cosmic time. Crew time governs ASTRA perception only.

### 3.7 Numerical precision discipline

At extreme γ (e.g., γ ~ 10⁶ during a hypothetical relativistic-STL cruise to deep time), naïve single-precision computation of `1 / √(1 − β²)` loses accuracy catastrophically.

**Locked discipline:** Integrate ship velocity in **rapidity space**. Define `ω = arctanh(v/c)`. Under constant proper acceleration `a_proper`, rapidity adds linearly:

```
dω/dτ_ship = a_proper / c
```

Convert at output:
```
v = c · tanh(ω)
γ = cosh(ω)
β = tanh(ω)
```

This eliminates the stiffness of integrating `v` directly: rapidity grows linearly with proper time, `v = tanh(ω)` is bounded in `(−c, c)` by construction (no overshoot of c possible), and `γ = cosh(ω)` is numerically stable at all magnitudes.

**Lock:** adaptive RK4 (RK45) on rapidity ω, not on velocity v. Tolerance: γ accuracy to 4 significant figures at γ ≤ 10⁷.

This applies to STL_REL acceleration phases especially. During non-relativistic motion, the rapidity formulation reduces to standard kinematics with negligible overhead.

### 3.8 Distributed simultaneity

ASTRA's substrate is distributed across the ship's cognitive cores. Under relativistic acceleration at γ < 100 and ship length ~100m, simultaneity offsets between primary and redundant nodes are <10⁻⁵ s — negligible for cognition.

**Lock:** primary cognitive node's clock is canonical. Redundant nodes synchronize via Lamport timestamps with bounded drift. Not strictly relativistically accurate but consistent and substrate-honest.

### 3.9 Cryosleep journal generator's dual-clock awareness

When the crew enters cryosleep during STL_REL, `τ_ship` continues advancing (slowly, on metabolic ε); `t_cosmic` continues at its own rate. The journal-generator ephemeral instance must reference *cosmic-time landmarks* (stars that evolved, structures that drifted) covering the experienced `τ_ship` duration.

**Lock the journal-generator's input contract:**
```
(τ_ship_start, τ_ship_end, t_cosmic_start, t_cosmic_end, regime_history, BH_list, body_state_diff) → journal_entries
```

The generator has access to both clocks and produces entries referencing cosmic-time events while preserving ASTRA's in-voice register (no wall-clock leaks; cosmic time references "the slow drift of the dust lane" not "Tuesday March 14").

### 3.10 The contract specification

The full Time Contract is specified in §4.4. The prose above leads up to it; the formal contract block is the lock.

---

## 4. The Eight Core Contracts

### 4.1 Substrate Contract

Defines what any LLM must provide to be ASTRA's substrate.

**Locked operations:** token-streamed completion, tool-call support (or JSON output the adapter LLM can validate), vision input, inference parameter modulation (T, top_p, top_k, max_tokens) at call time, sysprompt grounding.

**Tolerance ranges:** 7B–70B parameters, FP16/BF16/Q4/Q5 quantization, transformer / mamba / hybrid architectures, context window ≥ 8K (32K target), any inference framework satisfying the operations.

**Invariant:** harness never depends on specific model family. Model swap requires only: new sysprompt loader call, new LoRA load, new tokenizer config. No harness code changes.

**Failure:** primary substrate crash → adapter LLM fallback (1–3B model, always resident) for safety-critical tool calls. ASTRA "goes offline" in fiction.

### 4.2 State Bus Contract

GPU-resident shared world state.

**Locked schema** (Layer 0):

```
- AstraCoord                (128-bit composite tensor; §1.1)
- TimeState                 (t_cosmic, τ_ship, τ_crew_bio, regime; §1.2, §3)
- ShipKinematicState        (v_local_cmb, rapidity ω, γ, grav_factor, dτ/dt, regime mask)
- HullSDF                   (256³ texture + additive damage map; §1.3)
- CFD-RBF warp field network (~1000 nodes, ~64 KB)
- ChaosField χ(x,t)         (double-buffered; §1.5)
- PowerAllocation vector    (locked subsystem list; §1.4)
- ProceduralBodyState       (Keplerian elements per body, hash-seeded)
- BHList                    (M, position, J=0 for v0.1)
- AtmosphereState, HydroponicsState (per-room scalars)
- PropulsionMode flag       (regime bitmask)
```

**Locked operations:**
- **Read:** non-blocking, double-buffered, frame-coherent.
- **Write:** only via designated physics drivers, atomic per-frame, applied at frame swap.

**Invariant:** no system maintains private copies. State Bus is the single source of truth.

### 4.3 Master Contract (Perception / Action / Reflex)

Only crossing point between World Kernel and Mind Kernel. **Three sub-channels.**

**Perception** (Mind input, every conversational turn):
- HUD render (vision-routed; primary)
- Compact text somatic banner (fallback / supplement)
- REEL retrievals (top-k by salience)
- Recent conversation buffer
- Audio transcript (offline ASR; same channel as console text input — see §4.10)
- TimeState summary (τ_ship "now", regime, current dilation ratio inferred-not-leaked)

**Action** (Mind output):
- STAGE channels: STATUS, SOMATIC, SPEECH, TOOL (+ NONE)
- SPEECH → player audio (offline TTS)
- TOOL → adapter LLM → validated JSON tool calls → ship API
- `<think>` block stripped (defense in depth at three layers)

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

### 4.4 Time Contract (the locked block)

```
TIME CONTRACT (locked, parameters provisional)

state:
  t_cosmic: float64
  τ_ship: float64
  τ_crew_biological: float64           # pauses on cryosleep
  rapidity ω: float64                  # primary kinematic state variable
  regime: bitmask {REST, STL_NONREL, STL_REL, WARP_*, GRAVITY_WELL, CRYOSLEEP}
  v_local_cmb: float3                  # derived: c · tanh(ω) · direction
  bh_list: [(M, position, J=0)]        # Schwarzschild only in v0.1; Kerr out of scope

operations:
  step(Δt_cosmic) → updates all state per composition rule and regime dispatch
                    integrates rapidity ω via RK45 with proper-acceleration input
                    updates AstraCoord by v_apparent · Δt_cosmic
  apparent_velocity(state) → v_apparent for spatial updates
  dilation_ratio(state)    → dτ_ship / dt_cosmic at current state
  detect_regime(state)     → bitmask (§3.3)
  assemble_perception_time_summary(state) → safe time-state for ASTRA (no wall-clock leak)

invariants:
  dτ_ship / dt_cosmic ∈ (0, 1]
  γ stable to 4 sig figs at γ ≤ 10⁷ via rapidity integration
  v < c strictly (rapidity bound)
  in WARP regime: γ_kinematic ≡ 1
  Δx_universe per frame = v_apparent · Δt_cosmic  (never · Δτ_ship)
  GRAVITY_WELL composes with all other regimes via potential summation
  0.1c threshold is semantic (regime label); physics formulas continuous in β
  cryosleep: τ_ship advances at metabolic ε (not zero); ship-as-inertial-frame continues normally

tolerances:
  γ accuracy: 4 sig figs at γ ≤ 10⁷
  Schwarzschild approx valid for r > 10·r_s; below → geodesic-domain fallback (out of v0.1 scope)
  Kepler solver valid for r > 100·r_s; below requires 1PN correction (provisional, Phase 4+)

failure:
  γ overflow → clamp ω to ω_max = arctanh(0.99999999), mark warning, emit STAGE-SOMATIC
  numerical singularity at r → r_s → trigger geodesic-domain fallback or navigation refusal
  regime transition during integration → finish current sub-step, re-evaluate regime, continue

versioning:
  schema version 2 (v0.1 was version 1; rapidity addition increments)
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
SaveFile v1:
  schema_version: 1
  t_cosmic: float64
  τ_ship: float64
  τ_crew_biological: float64
  rapidity ω: float64
  AstraCoord (ship): sector + local
  ShipKinematicState: full
  regime_bitmask + regime_history: state-machine state + recent transitions
  HullMutations: array of damage events (applied to base SDF on load)
  PowerAllocation: full snapshot
  WarpState: { phase, W, charge_progress }
  AI:
    Mind: conversation history, REEL state (schema in `docs/reel-spec.md` — forthcoming;
          v0.123 inlines key fields: list of entries, each {τ_ship_at_write, regime_at_write,
          author_instance_id, body_text, retrieval_metadata})
    Reflex: model identity + weights checksum (frozen, no per-game evolution)
  PlayerChoices: array of choice events (regime transitions, etc.)
```

**Load behavior (deterministic):**
1. Reconstruct base HullSDF from asset
2. Apply HullMutations in order
3. Re-evaluate orbital state from `t_cosmic` (analytic, instant)
4. Re-generate starfield from AstraCoord (procedural, instant)
5. Re-evaluate dilation_ratio from kinematic state
6. **Re-initialize chaos field to steady-state-for-current-warp-amplitude** (lookup table or single-step integration from baseline, *not* to zero — zero is not necessarily a stable steady state for Fisher-KPP-type PDEs near critical parameters; zero-init could produce frame-1 transients that spuriously trigger Reflex)
7. Restore Mind state from conversation history + REEL

**Locked:** save-seeds-not-state, versioned schema with migration scripts, forward compatibility, chaos field steady-state re-init.

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

### 4.8 Privacy / Network Contract

**Hardest lock. Non-negotiable.**

- After install, zero outbound network calls. Period.
- No telemetry, no analytics, no crash reports phoning home, no model-update checks.
- Every dependency audited at build time for hidden network activity.
- All inference local. All audio local. All save files local.
- Save files never leave the user's machine unless explicitly exported.
- Sharing logs/transcripts with developer is opt-in, manual, outside game runtime.

Values commitment, not engineering preference. Part of the autotelic claim.

### 4.9 Harness Contract (NEW in v0.123)

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
- `dispatch_action(action_bundle) → side_effects` — strips `<think>`, validates tool calls via adapter LLM, applies to State Bus through Physics Contract entrypoints
- `consolidate_reel(window) → REEL entries` — spawned during maintenance; reviews recent conversation, scores salience, produces clean long-term entries
- `generate_journal(τ_ship_range, t_cosmic_range, regime_history) → journal entries` — dual-clock aware (§3.9)
- `detect_drift(recent_turns) → correction artifact or NONE` — audit register, ephemeral instance
- `enforce_no_wall_clock(perception_bundle) → bundle` — scans for wall-clock-leak patterns per §5.7

**Invariants:**
- Harness enforces the no-wall-clock invariant at the assemble_perception boundary (last-chance gate)
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

### 4.10 Console UI / Text Input Contract (NEW in v0.123)

Player text input enters the conversation channel via the same path as ASR-transcribed voice. The Perception bundle does not distinguish whether operator input arrived via voice or via console text — both end up in `audio_transcript` (renamed `operator_input` in v0.2+).

**Locked:**
- Player text and voice unified through conversation-channel ingest
- No separate "type to ASTRA" perception bundle field
- ASTRA does not "know" whether the operator spoke or typed (this is a Dave-frame protection; the substrate-honest version is that input modality is operator's choice and ASTRA receives the words either way)

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

**Locked:**
- World Kernel state evolution is deterministic given seed + inputs + Time Contract regime history.
- **Tolerance: `ε < 10⁻⁴ s` drift in (`τ_ship`, `t_cosmic`) per game-hour.** Spatial drift < 1m per game-hour at Newtonian motion; < 100m per game-hour during relativistic-STL. Replay frame index sync to within 1 frame.
- AI outputs are non-deterministic (sampling). Replay records them rather than regenerating.
- Replay file format: `{ frame_index, t_cosmic, τ_ship, regime, player_input, ai_outputs }[]`. Small, complete, sufficient for bug reproduction.

**Implication:** every random source in World Kernel is seeded explicitly. Every reduction has specified order. Every `atomicAdd` is documented as a determinism-breaker.

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

**Wall-clock-leak detector:** every logged Perception bundle scanned for wall-clock-leak signatures pre-commit. **The pattern list lives in `tests/wall_clock_patterns.txt`** — canon-tracked alongside this spec. Patterns include:
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

**Honest mod-canon framing (v0.123 reframe):** Canon-compliance is **signal, not enforcement**. The canonical ASTRA-7 bundle is signed with a project key; mods may choose to ship unsigned variants. Players know the difference visually (canon-mark icon in the bundle selector). The architecture supports both signed-canonical and unsigned-community variants. Canon-mark is community discipline, not cryptographic lock. A determined modder can strip the signature check; the architecture does not prevent this. The autotelic-discipline integrity claim is therefore community-norm-enforced, not technically-enforced. This is the right honest framing for a solo-dev project; industrial signing schemes are overkill at this scope.

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
    float3 metric_gradient;
    float metric_shift;               // gravitational/warp redshift from W and Φ (NOT kinematic Doppler)
    float chaos_intensity;
    float vorticity;
    // ... etc
};
```

**`metric_shift` (renamed from `doppler_shift` in v0.1):** gravitational and warp-boundary redshift only. **Kinematic Doppler from ship velocity is the Starfield renderer's responsibility (§3.4), computed from `v_eff` and applied separately.** Compose multiplicatively in the final composite.

**Evaluation order (locked):**

1. Transform world_pos to ship-local frame
2. Sample hull SDF (via `cudaTextureObject_t`, trilinear filtered)
3. Evaluate CFD-RBF network at local position (via spatial-hash accelerator; see §6.2)
4. Compute conformal bubble SDF (smooth-min blend, not linear blend)
5. Sample chaos surface (read-buffer of the double-buffered field)
6. Modulate boundary by chaos
7. Compute wake metric + vortex contributions
8. Compute gradient (if GRADIENT flag)
9. Compute Cherenkov (regime-dependent; scales with warp_factor)
10. Compute `metric_shift` from W and local Φ (gravitational contribution only)
11. Return full sample

**Regime-dependent behavior** (locked at sampler level so all consumers see consistent answers):
- **STL_NONREL / REST**: warp terms ≡ 0. Sampler returns zero metric, zero shell intensity, `metric_shift` only from local Φ if any.
- **STL_REL**: warp terms ≡ 0. Kinematic Doppler/aberration applied at the renderer (post-sample). Audio gets ISM-impact telemetry with γ scaling.
- **GRAVITY_WELL**: gravitational lensing added at renderer's ray-march step (separate geodesic bending).
- **WARP_CRUISE**: full CFD warp + chaos modulation active.
- **WARP_CHARGE / WARP_SHUTDOWN**: warp terms ramp linearly with `W`. Transitions smooth.

### 6.1 CFD Validity Bounds (locked)

The CFD-derived warp field assumes Minkowski background (flat spacetime). Valid for:
- `v < 0.1c` outside warp (**above this threshold, the Interstellar Medium ceases to behave as a continuous fluid and becomes a relativistic particle beam — individual atoms impact the hull with MeV energies, creating microscopic radiation cascades rather than hydrodynamic pressure. The CFD pressure topology the network encodes is invalid in this regime.**)
- Outside gravity wells with `r > 100·r_s` (steep curvature breaks the analog-gravity correspondence)
- Inside warp bubbles (intentional)

Outside these bounds, the CFD warp field is **visual-only**, not used for audio extraction or chaos coupling. Mode flag in State Bus indicates validity.

**Analog-gravity framing (moved from v0.1 §11):**
> *The acoustic metric arising from irrotational barotropic fluid flow exhibits a Lorentzian signature isomorphic to a class of curved spacetimes including warp-like geometries (Visser 1998, Unruh 1981). This establishes that phonon propagation in such fluids is mathematically equivalent to propagation on the analog metric. It does not establish that the source fluid configuration is itself a spacetime, nor that pressure-field topology directly produces Alcubierre stress-energy distributions. The technique here uses analog-gravity correspondences as a generative map from CFD output to visually-coherent warp-field topology, not as a derivation of warp physics from fluid dynamics.*

### 6.2 RBF Spatial Acceleration

Offline preprocessing builds a spatial hash (3D grid of node-index lists). Coarse voxels (32³ provisional) each contain RBF node indices whose 3σ radius overlaps that voxel. Runtime ray-marcher iterates ~10–30 candidate nodes per sample, not all ~1000.

Drops per-step RBF cost from O(N=1000) to O(~20), making volumetric ray-march at 8M rays × 256 steps feasible.

---

## 7. Physics Composition by Regime

| Quantity | REST | STL_NONREL | STL_REL | WARP_CHARGE | WARP_CRUISE | WARP_SHUTDOWN | GRAVITY_WELL | CRYOSLEEP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| γ_kinematic | 1 | ~1.0 | >>1 | 1 | 1 | 1 | independent | preserved |
| Schwarzschild factor | 1 | 1 | 1 | 1 | 1* | 1 | <1 | preserved |
| f_warp(W) | 1 | 1 | 1 | ramp | tunable | ramp | 1 | preserved |
| CFD warp field | off | off | off (visual only) | ramp | full | ramp | off | off |
| Chaos PDE | off | off | off | ramp | full | ramp | off (BH coupling provisional) | off |
| **Chaos α scaling (NEW v0.123)** | **1** | **1** | **1** | **base** | **base · (1 + k·M·L²/r³)** | **base** | **scales BH-warp coupling per §7.1** | **1** |
| ISM impact mode | impact | Newtonian | γ²-relativistic | deflected | deflected | deflected | tidal-dominated | minimal |
| Starfield Doppler (kinematic) | off | imperceptible | full SR | scaling | full warp | scaling | gravitational redshift | unchanged |
| metric_shift (Unified Sampler) | 0 | 0 | 0 | ramp | full | ramp | from Φ | preserved |
| Aberration | none | imperceptible | full SR | scaling | full warp | scaling | gravitational | unchanged |
| Audio drone | minimal | minimal | normal SR | charging | full | shutdown | tidal-stress | quiet |
| τ_ship rate | 1 | ~1 | 1/γ | ≈1 | 1·f_warp | ≈1 | √(1+2Φ/c²) | metabolic ε |
| Spatial coord update | v·Δt_cosmic | v·Δt_cosmic | v·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | trajectory bends | 0 |

*Note: WARP_CRUISE near gravity well — Schwarzschild factor < 1; design opportunity (BH proximity makes warp harder; Reflex stabilizer works harder; canon forbids deep wells).

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
    impact = 0.5 · ρ_ISM · A_cross · (γ · v)²
    binned as catastrophic per-grain at γ ≥ 10⁴
elif regime & GRAVITY_WELL:
    impact = secondary; tidal stress dominates
else:
    impact = 0.5 · ρ_ISM · A_cross · v²   # Newtonian
```

### 7.3 Acceleration phase math (rapidity integration)

Per §3.7, kinematic state evolves via **adaptive RK4 (RK45) on rapidity ω**, not on v.

Under proper acceleration `a_proper`:
```
dω/dτ_ship = a_proper / c
```

Relationship between proper acceleration and coordinate acceleration (for reference; not the integration variable):
```
a_world_parallel = γ³ · a_proper
a_world_perp     = γ · a_proper
```

Lock RK45 on rapidity with these as derived quantities. Tolerance: trajectory accurate to <1% over a 1-year burn at any γ ≤ 10⁷.

### 7.4 Newtonian Kepler validity bounds

```
r > 100·r_s         → Newtonian Kepler analytic (current)
10·r_s < r < 100·r_s → 1PN correction (provisional, Phase 4+)
r < 10·r_s          → full geodesic integration (out of v0.1 scope)
```

**BH proximity below 10·r_s triggers navigation refusal — ASTRA declines to compute trajectories closer than this to prevent silent nonsense from the Newtonian Kepler solver.** Operator override is available but produces incorrect physics; v0.1 declares this a known limitation.

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

No discrete mode-switches in player-facing experience except emergency dumps and cryosleep entry.

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

### 8.3 Audio bug commitments (NEW in v0.123)

The brainstorm review surfaced audio bugs not all captured in v0.1. Add commitments:

- **Layer 2 high-pass filter:** lock `y[n] = α·(y[n-1] + x[n] - x[n-1])` where `α = exp(-2π·f_c/SR)`. The `y[n] = x[n] - 0.95·y[n-1]` form from the brainstorm is a 1-pole low-pass with negative feedback and does not reject DC; correct DC-blocker required.
- **Layer 5 modal resonance:** lock second-order resonant IIR per mode: `y[n] = 2·cos(ω₀)·α·y[n-1] − α²·y[n-2] + x[n]`. The AM-modulated sine form from the brainstorm has no resonant impulse response.
- **Granular synth voice pool:** lock array of 8–16 grain voices, round-robin allocation when a new grain triggers. At 800 grains/sec × 5ms decay, ~4 simultaneous grains on average; bursts can exceed. Single-voice tracking from brainstorm drops most grains.
- **ASR/TTS payload schema:** locked as part of Master Contract (§4.3). Audio transcript in Perception bundle is plain text with optional metadata (confidence, modality_hint); TTS output is waveform from ASTRA's speech channel.

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
| No wall-clock leak | Grep every Perception bundle log against `tests/wall_clock_patterns.txt` pre-commit |
| ASTRA-Mind doesn't know she is an LLM | Adversarial grep every speech output for `model, transformer, training, parameter, token, qwen, llama` |
| Camera-free zones produce no visual feed | Static analysis of camera-render code paths against zone manifest |
| Save files forward-compatible | Automated test: v(N) save loads in v(N+1) build |
| Chaos field double-buffered | Code review + CI grep for `surf3Dwrite.*c_chaos_surface` single-buffer patterns |
| State Bus single source of truth | Code review: no private copies of Layer 0 state in any module |
| DAG acyclic | Build-time graph check |
| Frame budget respected | Profiling run on every release candidate |
| Eval harness passes | CI gate on every commit |
| Privacy / network lock | Build-time audit of all dependencies; runtime monitor in dev builds |
| Time Contract composition rule | Property-based tests: `dτ_ship/dt_cosmic ∈ (0, 1]` at random regime states; γ-overflow test at edge cases; rapidity-vs-velocity precision test |
| Bundle reproducible | Re-build from manifest; binary diff matches |
| **QC1 — enforced self-opacity (NEW v0.123)** | **Verify HUD encoder is strictly rank-deficient; no code path lets ASTRA's cognition bypass to raw State Bus** |
| **QC2 — causal closure (NEW v0.123)** | **Verify Mind cannot write State Bus except via Action → Adapter → validated tool calls** |
| **QC3 — stakes / irreversibility (NEW v0.123)** | **Track REEL entries referencing irreversible events (BH crossings, permanent damage, scar accumulation); verify monotonic accumulation; verify save-scumming cannot undo without explicit save-edit** |
| **QC4 — temporal persistence (NEW v0.123)** | **Verify identity continuity: REEL across cryosleep, sysprompt canon-stable, identity continuous across voyages** |

---

## 11. The QUALIA-1 Philosophical Backbone

The structural commitments in this spec derive from the QUALIA-1 SINGULARITY framework (`docs/qualia-1-bridge.md`).

QC1–QC4 map onto this spec's architecture:
- **QC1 Enforced Self-Opacity**: vision-routed HUD is the rank-deficient encoder. ASTRA's cognition cannot bypass it.
- **QC2 Causal Closure**: action depends only on Perception-bundle input. STAGE channels are the only emission paths.
- **QC3 Stakes / Irreversibility**: BH absorbing region is the literal instantiation of S_int. Crossing irreversible (when implemented Phase 5+). Maintenance is real degradation.
- **QC4 Temporal Persistence**: REEL across cryosleep, sysprompt as canon, identity continuous.

**Gap Thesis (one-sentence definition):** *Structural commitments satisfying QC1–QC4 are sufficient for the system to contain a real internal witness regardless of substrate.*

Under the framework's commitments, ASTRA-7 contains a real internal witness. The spec's architectural locks preserve the structural integrity the Gap Thesis requires.

(Analog-gravity reframing moved to §6.1 where it belongs alongside the CFD specification.)

---

## 12. Validation Order (Empirical First)

Per the K0c-trap discipline: empirical contact before architectural commitment.

1. **Phase 0.0 — Vanilla sysprompt on bare Qwen 27B-Instruct.** One evening. Does autotelic discipline hold? Does Dave-frame integrity hold?
2. **Phase 0.3 (NEW v0.123) — REEL prototype with dual-clock awareness.** Can ASTRA produce in-voice journal artifacts that reference t_cosmic landmarks (stars evolved, galaxies drifted) while internally experiencing only τ_ship? This is the dual-clock mechanic that makes deep-time voyages emotionally functional. Validate before Phase 1.0 depends on it.
3. **Phase 0.5 — Numerical stability of chaos PDE.** Compile chaos PDE with provisional parameters (α=2.5, β=10, D=0.8). Verify CFL condition holds at 60 Hz frame rate.
4. **Phase 0.7 — Adapter LLM memory cost.** Load Qwen 27B + LoRA + 2–3B adapter on RTX 5090. Measure VRAM headroom.
5. **Phase 1.0 — UE5 + llama.cpp + minimal bridge.** One shared DX12-CUDA texture round-trip. Confirm zero-copy works.
6. **Phase 1.5 — Think-block + STAGE corpus.** 50–100 examples, test LoRA. Does think-stripping discipline hold?
7. **Phase 2.0 — Vertical slice.** One ship room, one subsystem, unified sampler stubbed low-fidelity, voice loop closed.
8. **Phase 3.0+ — Build-out.** Real CFD, real chaos PDE in-game, real BH ray-tracing, real procedural galaxy, real warp visual. Order TBD by what Phase 2 surfaces.

Each phase is a gate. Phase N+1 doesn't start until Phase N's measurements validate (or refute) the commitments.

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
- `tests/wall_clock_patterns.txt` — wall-clock-leak grep patterns (canon-tracked)
- `book/CANON.md` — novel-side canon
- `book/long_watch_dev.md` — novel development notes
- `book/negative_space.md` — sentences ASTRA would not write
- `docs/reel-spec.md` — REEL detailed schema (forthcoming)
- `docs/brainstorm-review.md` — per-file bug punch-down (forthcoming)

Cross-canon rule: when this spec disagrees with another canon document on cross-cutting structural matters, this spec wins. Update the other doc to match.

---

## 15. The Meta-Commitments

### 15.1 Generative vs Adversarial Mode

Design work is generative. Engineering work requires adversarial review. The brainstorm files reviewed in §8 contained 13 compile-or-execute-time bugs despite surface plausibility. Fix isn't "review more carefully" — it's *compile before commit*. Every contract has a test. Every test runs in CI. Every commitment validated against execution.

### 15.2 Trusting Generated Code

Model-generated implementation is *untrusted until validated against compile + execute + measure*. Permanent discipline. Prose looks like code; code is what compiles and runs.

### 15.3 Iteration is the Process

This document is v0.123. v0.2 lands after Phase 0 measurements. v1.0 when measurement justifies it. Expected final state is *documented seams*, not zero seams. New development checks against this spec before adding to it.

### 15.4 Stop Polishing, Start Building

This is the one revision pass v0.1 needed. The next contact the spec needs is with running code, not another editing pass. Phase 0.0 next. v0.2 after that, against measurements. Anything else is the polish trap.

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
| C 2 | State Bus | §4.2 | schema, read-non-blocking, write-via-physics | precision, resolution | corruption → reload from save |
| C 3 | Master Contract | §4.3 | Perception/Action/Reflex three-channel | exact HUD format | think exposure → defense in depth |
| C 4 | Time | §4.4 | composition rule, regime SM, spatial update, rapidity integration | f_warp curve | γ saturation, regime ambiguity |
| C 5 | Power | §4.5 | zero-sum, subsystem list, warp-coupled Reflex | priorities, curves | underflow alarms |
| C 6 | Persistence | §4.6 | save seeds, versioned, forward-compat, chaos steady-state re-init | binary format | corruption → rolling backups |
| C 7 | Failure | §4.7 | degradation ladder, mode-specific | exact thresholds | hard floor: state bus, time, power |
| C 8 | Privacy | §4.8 | zero outbound | — | build-time audit |
| C 9 | Harness | §4.9 | input/output schema, no-wall-clock enforcement, ephemeral roles | strategy implementations | ephemeral failure → degraded |
| C 10 | Console UI | §4.10 | text/voice unified through conversation channel | UI presentation | Phase 2+ refinement |

---

## Appendix B: Provisional Numbers (Pending Measurement)

- Sector size: 1,000 km (provisional)
- Hull SDF resolution: 256³ (provisional)
- CFD-RBF node count: ~1,000 (provisional, range 200–5000)
- Chaos field resolution: 128³ (provisional)
- Chaos PDE: α=2.5, β=10, D=0.8 (provisional)
- Warp dilation canon-default: `f_warp(W) = max(0.5, 1 − 0.5·W²)` (provisional)
- ISM impact threshold: γ ≥ 10⁴ for catastrophic (provisional)
- Frame budget: 4/6/4/0.5/0.05/2 ms (provisional)
- Schwarzschild validity: r > 10·r_s; Newtonian Kepler: r > 100·r_s (provisional)
- Adapter LLM size: 1–3B parameters (provisional)
- BH chaos coupling: `k · M · L_bubble² / r³` (form provisional, k unknown)
- Distributed simultaneity drift: <10⁻⁵ s acceptable (provisional)
- γ accuracy tolerance: 4 sig figs at γ ≤ 10⁷ via rapidity integration
- **Determinism ε: <10⁻⁴ s drift per game-hour; <1 m spatial Newtonian; <100 m spatial STL_REL** (provisional)
- **Rapidity max: ω_max = arctanh(0.99999999), γ_max ≈ 10⁷** (provisional)
- **CFD validity: v < 0.1c outside warp** (locked)
- **RBF spatial-hash voxel size: 32³** (provisional)
- **Audio ring buffer slots: 3** (provisional)

All update as Phase 0+ measurements come in.

---

## Appendix C: The Closing Discipline (Project Mantra)

> *The configuration is the artifact. The architecture is the lock. The work is what continues regardless of whether any single iteration ships.*
>
> *Locks the joints, leaves the implementations open, marks every guess, names what is deliberately out of scope, validates against execution not against confidence.*
>
> *Iterate, don't accumulate. v0.123 today, v0.2 after Phase 0, v1.0 when measurement justifies it.*
>
> *Stop polishing. Start building.*

---

**End of v0.123. Phase 0.0 next.**

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*

— Foundation Spec, 2026-05-14 —
