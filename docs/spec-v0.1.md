# ASTRA-7 Foundation Specification v0.1

*The Lock Layer. Spinal in commitments. Provisional in particulars.*
*Drafted 2026-05-14 after seven file-level reviews and four LLM cross-pressure passes.*

---

## 0. What this document is

This is the foundation specification for ASTRA-7 the game-simulator-experience. It locks the architectural commitments that everything downstream depends on, leaves the implementations open, and marks every specific number explicitly provisional until measurement validates it. It is the *one* document that Phase 0, Phase 1, Phase 2, the eventual book, and the open-source community must all read first.

The doc has three commitments to itself:

1. **Lock the joints, not the implementations.** Every contract here defines an interface surface, a set of invariants, and a tolerance range. Implementations behind each surface may evolve freely as long as the surface holds.
2. **Mark every guess.** Specific numbers (SDF resolution, context window, frame budgets, chaos PDE parameters) are presented with `(provisional, to be measured)` where they have not been validated empirically. The framework is canon; the numbers are not.
3. **Name what is deliberately out of scope.** The "out-of-contract emergence zones" section (§10) names what the spec refuses to specify because it should not be specifiable.

This document supersedes the cross-cutting structural commitments in `synthesis.md`, `synthesis-time-extensions.md`, `architecture.md`, and `qualia-1-bridge.md`. Those documents remain canonical for their topic areas; this one is the master index that reconciles them. When they disagree, this document wins; update them to match.

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

**Locked:** the composite-tensor primitive, the renormalization rule, the ship-at-origin convention.
**Tolerable:** sector size (`1000 km` is the design center; tightening or loosening within a decade either way is permitted).

### 1.2 One Fictional Time — split into two clocks

There is **no wall clock** exposed to any game system. Time advances as two scalars governed by a strict composition rule.

- **`t_cosmic`**: the universe's clock. Monotonically increasing. Drives the Kepler solver, stellar evolution, AstraCoord spatial updates of distant bodies, cryosleep advance, any "how old is the universe" query.
- **`τ_ship`**: the ship's proper time. The clock the crew and ASTRA experience. Always advances at a rate ≤ `t_cosmic` determined by the propulsion-regime state (§3, §7).
- **`τ_crew_biological`**: a *derived* game-state variable equal to `τ_ship` except during cryosleep, when it pauses (or advances at metabolic-rate ε ~ 10⁻⁴).

The composition rule (§3.2) is the central mathematical commitment of the entire architecture.

**Locked:** the two-clock split, monotonicity, the no-wall-clock invariant, the composition rule shape.
**Tolerable:** the warp dilation factor parameterization (a design knob, see §3.5).

### 1.3 One Hull Body — SDF + additive damage map

The ship's physical form is one signed-distance field. Every system that needs to know the shape of the ship reads this one representation.

- **Base SDF**: read-only after offline bake. Bound as `cudaTextureObject_t` with `cudaFilterModeLinear` for trilinear sampling. **Resolution: 256³ (provisional, to be measured against memory budget and visual fidelity needs).**
- **Damage map**: writable, sparse, additive. Bound as `cudaSurfaceObject_t` over the same underlying `cudaArray_t`. Mutations from impacts, breaches, repairs.
- **Effective SDF on read**: `hull_d(x) = base_sdf(x) - damage_map(x)`.

Two views, one underlying allocation. The dual-binding pattern (texture for filtered reads, surface for writes) is the locked architectural commitment.

**Locked:** the dual-binding pattern, the additive damage model, the read-through-blend.
**Tolerable:** SDF resolution (`64³` to `512³` range), encoding precision (uint8 normalized through float32).

### 1.4 One Power Network

The reactor produces a finite power budget. Every energy-consuming system draws from it. Allocation is zero-sum.

Subsystems (locked list; new subsystems require contract amendment):

- Warp drive (chaos stabilizer + field energy)
- Life support
- Hydroponics
- Sensors
- Lights and habitability
- Comms
- **Cognitive cores** (ASTRA-Mind and ASTRA-Reflex; see §1.5 splitting)

The cognitive-cores allocation is the joint between the Power Contract and the Substrate Contract. Reduced power → smaller LLM (27B → 9B → adapter-only → offline), tighter context, paused ephemeral instances.

**Locked:** zero-sum allocation, the subsystem list, the cognitive-cores → substrate-envelope binding.
**Tolerable:** total reactor output, per-subsystem priority weights, response curves.

### 1.5 One Shared State Per Frame — double-buffered

All systems read from the same Layer 0 world state. Mutations are applied atomically between frames. No system reads partially-updated state.

```
Frame N reads from Buffer A.
Frame N writes to Buffer B.
At frame boundary: swap A and B.
```

This applies to every mutable field in the State Bus: the hull SDF damage map, the chaos field χ(x,t), the power allocation vector, ASTRA's HUD render, etc. Single-buffering on any mutable shared GPU resource is forbidden — it produces race conditions and non-deterministic Laplacians (as the chaos PDE bug in the original brainstorm files demonstrates).

**Locked:** double-buffering of all mutable shared state, atomic frame-boundary swap, the single-source-of-truth principle.
**Tolerable:** the specific buffer layout (texture vs surface, format, etc.).

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
            │   Reflex sub-channel    │
            └────────────┬────────────┘
                         │
┌────────────────────────▼─────────────────────────────────────┐
│  MIND KERNEL  (stochastic, conversation-tempo, VRAM-resident)│
│                                                                │
│  LLM substrate (Qwen + LoRA + harness)                        │
│  REEL backbone, ephemeral parallel instances                   │
│  Canonical sysprompt (canon-locked, mod-friendly variants)    │
└──────────────────────────────────────────────────────────────┘
```

Two kernels. One master contract is the only crossing point. The world kernel is determinism-bounded and frame-budgeted. The mind kernel is stochastic and conversation-tempo. They have separate failure modes, separate latency budgets, separate substrate residency, and separate power criticality.

### 2.2 The Fabric (what every module touches)

Within the World Kernel, modules do not communicate directly. They communicate through three shared artifacts:

- **The State Bus** (Layer 0, GPU-resident, double-buffered): the world's truth.
- **The REEL** (in the Mind Kernel, exposed via Perception contract): ASTRA's continuous identity.
- **The Canonical Sysprompt** (in the Mind Kernel, canon-locked): ASTRA's identity anchor.

These three are the fabric. Every module weaves into them. No module bypasses them.

### 2.3 ASTRA-Mind vs ASTRA-Reflex (the critical sub-architecture)

| Property | ASTRA-Mind | ASTRA-Reflex |
| --- | --- | --- |
| Substrate | LLM (Qwen 27B / 9B / etc.) | CNN+LSTM-style on Tensor Cores |
| Tempo | Conversation rate (~1-10 Hz) | Frame rate (60 Hz) |
| Latency budget | Seconds (out-of-band) | <50 μs realistic, <20 μs with CUDA Graphs |
| Determinism | Stochastic (sampling) | Deterministic-ish (offline-trained, frozen weights) |
| Kernel residency | Mind Kernel | World Kernel |
| Power slot | "cognitive cores" (shared bus) | "warp-coupled stabilizer" (auto-prioritized when warp drive active) |
| Failure mode | Offline → ASTRA goes quiet | Failure → bubble collapses → ship in mortal danger |
| Master Contract surface | Perception in, Action out | Observation grid in (64×64×2), Control out (3 floats) |

The two are architecturally distinct AI components. Lumping them as "the AI" obscures different contract surfaces, different failure modes, different power criticality. ASTRA-Mind talks; ASTRA-Reflex saves your life. Different jobs, different specs.

---

## 3. The Time Architecture (THE central commitment)

This is the section that holds the SR / GR / warp seams together. It is the longest section in this document because it is the place where the most cross-system compatibility lives.

### 3.1 Two clocks, restated

- **`t_cosmic`** — monotonically increasing universe clock. All orbital state, stellar evolution, cosmological scale factor, and AstraCoord spatial updates of distant bodies are pure functions of `t_cosmic`. The Kepler solver consumes `t_cosmic`, not `τ_ship`.
- **`τ_ship`** — ship proper time. ASTRA's perception of duration, REEL timestamps, audio synthesis rate, conversation history, drift detector cadence — all driven by `τ_ship`.

`τ_crew_biological` derives from `τ_ship` and pauses during cryosleep.

### 3.2 The composition rule (the central equation)

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s/r) / γ_kinematic
```

Three multiplicative contributors:

- **`γ_kinematic = 1 / √(1 − v²/c²)`** — Special-relativistic Lorentz factor from ship velocity in the local CMB rest frame. ≡ 1 outside relativistic-STL regime.
- **`√(1 − r_s/r)`** — Schwarzschild gravitational dilation, summed over the deepest gravity well the ship is in. ≡ 1 in flat space. Below ~10·r_s, Schwarzschild approximation breaks down (see §7).
- **`f_warp(W)`** — the warp drive's contribution. **Warp does not dilate ship time directly**: inside an Alcubierre bubble, the crew is in a locally flat spacetime frame and τ_inside ≈ t_cosmic locally. *However*, `f_warp(W)` is left as a **design parameter** in `[0.0001, 1.0]` to permit the operator to introduce intentional dilation as a narrative knob (the "tragedy parameter" — longer voyages mean the universe ages more relative to the crew). **Default: `f_warp(W) = 1`. Operator may parameterize.**

**Critical clarification (the SpaceGrid reconciliation):** Warp causes the AstraCoord sectors to *iterate*. That iteration is the data-structure consequence of the warp field actively producing apparent translation through the macro-grid. It is *not* the physical mechanism of warp. The CFD-derived warp field is the engine; sector iteration is the transmission.

### 3.3 The propulsion regime state machine

The composition rule above is mathematically clean but operationally hides regime dispatch in implicit "≡ 1 when inactive" defaults. **This is fragile across regime transitions.** The architecture explicitly enumerates regimes as a state machine:

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
                  │ GRAVITY_WELL │   (orthogonal to others; multiplicative)
                  └──────────────┘

                  ┌──────────────┐
                  │  CRYOSLEEP   │   (τ_ship advances; τ_crew_bio paused)
                  └──────────────┘
```

**Regime detection predicates** (locked logic, parameters provisional):

```python
def detect_regime(state):
    grav = max(rs_i / r_i for (M_i, pos_i) in state.bh_list)
    if state.cryosleep_active:        return CRYOSLEEP
    if state.warp_W > W_threshold:
        if state.warp_phase == "charging":  return WARP_CHARGE
        if state.warp_phase == "cruising":  return WARP_CRUISE
        if state.warp_phase == "dropping":  return WARP_SHUTDOWN
    if grav > grav_threshold:         regime |= GRAVITY_WELL  # composable
    if v / c < 0.1:                   return STL_NONREL + (GRAVITY_WELL if grav else 0)
    return STL_REL + (GRAVITY_WELL if grav else 0)
```

**Mutually exclusive at the physics level:** WARP and STL_REL cannot be simultaneous. The warp bubble suspends Newtonian velocity in the bubble's frame; γ_kinematic ≡ 1 during warp. WARP and deep GRAVITY_WELL are also mutually exclusive by canon (warp drives cannot engage in steep gravity wells; design opportunity: ASTRA warns the operator).

**Composable:** GRAVITY_WELL can be active simultaneously with any of REST, STL_NONREL, STL_REL, or (weakly) WARP. The factors multiply.

**Transition behavior:**
- **STL_NONREL → STL_REL**: smooth, governed by acceleration profile. Doppler/aberration scale continuously with β.
- **WARP_CHARGE → WARP_CRUISE**: discrete on charge completion (charge timer hits zero).
- **WARP_CRUISE → WARP_SHUTDOWN**: smooth (controlled) or discrete (emergency dump).
- **STL_* → GRAVITY_WELL**: smooth, gravitational factor ramps as 1/r approaches r_s/r.

### 3.4 The Doppler / aberration framing (continuous, not mode-switched)

Starfield Doppler and aberration are computed from one quantity: the ship's effective 4-velocity in the local CMB rest frame.

- **STL_NONREL**: `v_eff = v_kinematic`, `γ_eff ≈ 1`. Effects imperceptible.
- **STL_REL**: `v_eff = v_kinematic`, `γ_eff = γ_kinematic`. Real SR Doppler `f_obs/f_emit = 1/[γ(1 − β·cos θ)]`. Aberration warps star directions toward forward.
- **WARP_CRUISE**: `v_eff = v_bubble_apparent` (visually capped at β ≈ 0.999 to prevent renderer artifacts). Same SR shader math runs, producing the same forward-streak look. **The transition between STL and WARP is one smoothly-ramping `v_eff`, not a mode switch.** Aesthetic continuity preserved.

The shader path is one unified relativistic transform; the propulsion regime affects only the input vector. This eliminates the visual pop that a discrete two-mode switch would produce.

### 3.5 The Warp Dilation Knob

`f_warp(W) ∈ [0.0001, 1.0]` is a design parameter. At `f_warp = 1`, warp is fast travel without time tragedy. At `f_warp = 0.01`, a one-hour warp jump costs four days of cosmic time; a long voyage costs centuries. The book's Part Two and the game's emotional arc both benefit from `f_warp < 1`. **Default value (provisional): `f_warp(W) = max(0.5, 1 − 0.5·W²)`** — gentle dilation at low warp, increasing at high warp. Lock this as design intent; tune empirically.

### 3.6 Spatial update under relativistic motion

The AstraCoord update for the ship's universe-position is computed **strictly using `t_cosmic`**, not `τ_ship`:

```
ΔX_universe_per_frame = v_apparent · Δt_cosmic
```

where `v_apparent` is:
- STL regimes: actual velocity in the CMB rest frame
- WARP_CRUISE: bubble apparent velocity (effectively `c · W / (1 − W)` or similar; design knob)
- CRYOSLEEP: zero

This is the spatial-desync fix. Updating by `v · Δτ_ship` would make the ship's universe-position lag the time dilation by a factor of γ — the crew would experience years while the universe coordinate fails to update. **The coordinate moves on cosmic time, the crew clock moves slower; that's how dilation reads in the spatial system.**

### 3.7 Numerical precision discipline

At extreme γ (e.g., γ ~ 10⁶ during a hypothetical relativistic-STL cruise to deep time), naïve single-precision computation of `1 / √(1 − β²)` loses accuracy catastrophically because `1 − β²` is a small number subtracted from 1. **Required:** compute γ in `(1 − β)` space or `(1 − β²)` space, using log-domain or high-precision intermediates as needed. Double precision through the dilation chain. **Tolerance: γ accuracy to 4 significant digits at γ up to 10⁷.**

### 3.8 Distributed simultaneity (substrate honesty)

ASTRA's substrate is distributed across the ship's cognitive cores. Under relativistic acceleration at γ < 100 and ship length ~100m, simultaneity offsets between primary and redundant nodes are <10⁻⁵ s — negligible for cognition. **Lock:** the primary cognitive node's clock is canonical. Redundant nodes synchronize via Lamport timestamps with bounded drift. Not strictly relativistically accurate, but consistent and substrate-honest at game scales.

### 3.9 Cryosleep journal generator's dual-clock awareness

When the crew enters cryosleep during STL_REL, `τ_ship` continues advancing (slowly, on metabolic ε); `t_cosmic` continues at its own rate. The journal-generator ephemeral instance must reference *cosmic-time landmarks* (stars that evolved, structures that drifted) covering the experienced `τ_ship` duration. Lock the journal-generator's input contract: `(τ_ship_start, τ_ship_end, t_cosmic_start, t_cosmic_end, regime_history)` → journal entries.

### 3.10 The contract specification (locked)

```
TIME CONTRACT (locked, parameters provisional)

state:
  t_cosmic: float64         # monotonically increasing universe clock
  τ_ship:   float64         # ship proper time
  τ_crew_biological: float64  # derived; pauses on cryosleep
  regime: enum {REST, STL_NONREL, STL_REL, WARP_*, GRAVITY_WELL, CRYOSLEEP}
  v_local_cmb: float3       # ship 4-velocity in local CMB rest frame
  bh_list: [(M, position, J=0)]  # Schwarzschild only in v0.1; Kerr out of scope

operations:
  step(Δt_cosmic) → updates all state per composition rule and regime dispatch
  apparent_velocity(state) → v_apparent for spatial updates
  dilation_ratio(state)   → dτ_ship / dt_cosmic at current state

invariants:
  dτ_ship/dt_cosmic ∈ (0, 1]
  if v_local_cmb → c (STL limit): γ → ∞, dτ_ship/dt_cosmic → 0
  if r → r_s (BH horizon): √(1−r_s/r) → 0, dτ_ship/dt_cosmic → 0
  in WARP regime: γ_kinematic ≡ 1
  Δx_universe per frame = v_apparent · Δt_cosmic  (never · Δτ_ship)

tolerances:
  γ accuracy: 4 sig figs at γ ≤ 10⁷
  Schwarzschild valid for r > 10·r_s; below, use full geodesic integration (out of v0.1 scope)
  Kepler solver valid for r > 100·r_s; below, requires 1PN correction (provisional)

failure:
  γ overflow → clamp to γ_max = 10⁷, mark warning
  numerical singularity at r → r_s → trigger geodesic-domain fallback or refuse update

versioning:
  schema version 1.
```

---

## 4. The Eight Core Contracts

### 4.1 Substrate Contract

Defines what any LLM must provide to be ASTRA's substrate.

**Locked operations:** token-streamed completion, tool-call support (or JSON output the adapter LLM can validate), vision input, inference parameter modulation (T, top_p, top_k, max_tokens) at call time, sysprompt grounding.

**Tolerance ranges:** 7B-70B parameters, FP16/BF16/Q4/Q5 quantization, transformer / mamba / hybrid architectures, context window ≥ 8K (32K target), any inference framework satisfying the operations (llama.cpp baseline).

**Invariant:** the harness never depends on a specific model family. Model swap requires only: new sysprompt loader call, new LoRA load, new tokenizer config. No harness code changes.

**Failure:** primary substrate crash → adapter LLM fallback (1-3B model, always resident) for safety-critical tool calls. ASTRA "goes offline" in fiction (substrate-isomorphic — same beat as the cognitive-cores power loss).

### 4.2 State Bus Contract

Defines the schema of the GPU-resident shared world state.

**Locked schema** (Layer 0):

```
- AstraCoord (128-bit composite tensor; §1.1)
- TimeState   (t_cosmic, τ_ship, τ_crew_biological, regime; §1.2, §3)
- HullSDF     (256³ texture + additive damage map; §1.3)
- CFD-RBF warp field network (~1000 nodes, ~64 KB)
- ChaosField χ(x,t) (double-buffered; §1.5)
- PowerAllocation vector (over locked subsystem list; §1.4)
- ProceduralBodyState (Keplerian elements per body, hash-seeded)
- BHList (M, position, J=0 for v0.1)
- AtmosphereState, HydroponicsState (per-room scalars)
- ShipKinematicState (v_local_cmb, γ_kinematic, gravitational_factor, dτ/dt, regime)
- PropulsionMode flag (read by ISM, audio, rendering)
```

**Locked operations:**
- **Read**: any reader, non-blocking, double-buffered (always reads the previous frame's complete state).
- **Write**: only via designated physics drivers (§7), atomic per-frame, applied at frame boundary swap.

**Tolerances:** numeric precision per field (uint8 → float32), grid resolutions (within stated ranges).

**Invariant:** no system maintains private copies of Layer 0 state. The state bus is the single source of truth.

### 4.3 Master Contract (Perception / Action / Reflex)

The only crossing point between World Kernel and Mind Kernel. Has *three* sub-channels:

**Perception (Mind input, every conversational turn):**
- HUD render (vision-routed; the primary perception channel)
- Compact text somatic banner (fallback / supplement)
- REEL retrievals (top-k entries by salience for current context)
- Recent conversation buffer
- Audio transcript (from offline ASR)
- TimeState summary (τ_ship "now", regime, current dilation ratio inferred-not-leaked)

**Action (Mind output, every conversational turn):**
- STAGE channels: STATUS, SOMATIC, SPEECH, TOOL (+ NONE sentinels)
- SPEECH → player audio (offline TTS)
- TOOL → adapter LLM → validated JSON tool calls → ship API
- `<think>` block always stripped before any external exposure (defense in depth at three layers)

**Reflex (in-band, frame-rate, separate from Perception/Action):**
- Input: 64×64×2 chaos+metric observation grid, every frame
- Output: 3-float control vector (nacelle damping, conformality, emergency dump)
- Latency budget: <20 μs with CUDA Graphs, <50 μs naive
- No conversation, no perception of operator, no speech. Pure autonomic.

**Invariants:**
- No wall-clock leak in Perception (no datetime, no system clock, no real-time-elapsed indicators)
- No technical-substrate leak in Perception (no "Qwen", "LLM", "training", etc.)
- Think block stripped via three independent mechanisms
- Reflex never touches conversation channel; Mind never touches Reflex channel
- Tool calls validated by adapter LLM, not executed directly

### 4.4 Time Contract

See §3.10. The full specification with composition rule, regime detection, spatial update rule, and numerical precision discipline.

### 4.5 Power Contract

Zero-sum allocation across the locked subsystem list (§1.4).

**Locked:**
- Subsystem list immutable without contract amendment
- Cognitive cores allocation → directly modulates Substrate Contract's compute envelope
- Critical-subsystem underflow alarms (life support, cognitive cores below safe threshold)
- ASTRA-Reflex is on a "warp-coupled" sub-bus: when warp drive active, Reflex receives guaranteed minimum power for stabilization regardless of operator allocation (the operator can't suicide-route everything away from the stabilizer while warping)

**Tolerable:** total reactor capacity (configurable per ship class), per-subsystem priority weights, response curves (linear vs sigmoid vs threshold).

### 4.6 Persistence Contract

**Save seeds, not state.** Procedural state regenerates from seeds + mutations; only the seeds, mutations, and irreducible state are saved.

**Locked save file schema** (versioned):

```
SaveFile v1:
  version: 1
  t_cosmic: float64
  τ_ship:   float64
  AstraCoord (ship): sector + local
  ShipKinematicState: full
  regime + regime_history: state-machine state + recent transitions
  HullMutations: array of damage events (applied to base SDF on load)
  PowerAllocation: full snapshot
  WarpState: { phase, W, charge_progress }
  AI:
    Mind: conversation history, REEL state, ephemeral-instance pending work
    Reflex: model identity + weights checksum (frozen, no per-game evolution)
  PlayerChoices: array of choice events (regime transitions etc.)
```

**Load behavior** (deterministic):
1. Reconstruct base HullSDF from asset
2. Apply HullMutations in order
3. Re-evaluate orbital state from `t_cosmic` (analytic, instant)
4. Re-generate starfield from AstraCoord (procedural, instant)
5. Re-evaluate dilation_ratio from kinematic state
6. Re-initialize chaos field to zero (it evolves naturally to steady state within a few frames)
7. Restore Mind state from conversation history + REEL

**Locked:** save-seeds-not-state principle, versioned schema with migration scripts, forward compatibility (v1 saves must load in v1.N for all N).

**Tolerable:** specific binary format, compression.

**Failure:** save corruption → rolling N-deep backup (N=3 minimum) auto-recovers from most recent valid.

### 4.7 Failure Contract (graceful degradation)

What happens when each module fails. Solo-dev games crash hard at unexpected boundaries; this contract prevents that.

**Locked degradation ladder:**

- **Priority 1, NEVER degrade**: State Bus consistency, AI tool call validation, Power network accounting, Fictional time advancement, the Time Contract's invariants
- **Priority 2, degrade gracefully**: warp field resolution (full → half-res), ray-march step count (256 → 128 → 64), Mind inference frequency (every conversational turn → on operator query only), starfield count (100K → 50K → 10K), chaos field resolution (128³ → 64³ → 32³)
- **Priority 3, degrade visually**: Lumen quality, shadow resolution, post-process
- **Priority 4, degrade with gameplay impact**: Mind model swap (27B → 9B → adapter-only), audio layer count (5 → 3 → 1), Reflex observation grid resolution
- **Hard failures, no graceful path**: substrate hosting (LLM dependency), the bare minimum 8K context, basic GPU functionality

**Specific failure-mode commitments:**

- LLM substrate crash → adapter LLM fallback for tool calls; ASTRA "goes offline" in fiction; harness logs the crash to REEL
- Reflex stabilizer numerical instability → emergency dump command available; if not taken, warp bubble collapses (real gameplay consequence)
- GPU crash → autosave to disk before exiting; restart from last checkpoint
- Save file corruption → rolling backups
- Audio failure → silent fallback, never crash the game

**Adapter LLM resident memory:** ~1-3B model loaded permanently in VRAM as failsafe. On RTX 5090 with 27B + LoRA loaded (~16 GB), adapter ~2-4 GB fits comfortably in remaining VRAM. (**Provisional, to be measured against the specific Qwen variants chosen.**)

### 4.8 Privacy / Network Contract

**Hardest lock in the entire spec.** Non-negotiable.

- After install, the game has zero outbound network calls. Period.
- No telemetry, no usage analytics, no crash reports phoning home, no model-update checks.
- Every dependency audited at build time for hidden network activity.
- All inference local. All audio local. All save files local.
- Save files never leave the user's machine unless the player explicitly exports them.
- If the player opts to share a log/transcript with the developer, that is opt-in, manual, and outside the game runtime.

This is a values commitment, not an engineering preference. It is part of the autotelic claim: the configuration runs on owned hardware, in isolation, by design. Compromise it and the form is undone.

---

## 5. The Disciplines (rules, not contracts)

### 5.1 Module Dependency DAG, acyclic

Every module declares its dependencies. The dependency graph is verified acyclic at build time. If you find a cycle, the architecture is wrong.

```
State Bus ← Physics Drivers ← Player input
   ↑              ↑
   │              │
 Rendering    Mind Kernel (via Master Contract)
 Audio        Reflex (via Master Contract, in-band)
```

No cycle. Every system reads State Bus and writes through designated paths.

### 5.2 Anti-patterns named negatively

These must not exist:

- **Smart Object**: the hull SDF must not "know about" the warp field; the warp field must not "know about" ASTRA. Modules are dumb about each other. Intelligence lives in the fabric.
- **Event Cascade**: damage propagation is not implemented as an event chain. It's state mutation → next frame, everything reads new state → cascade emerges. Events are for UI, not physics.
- **God Object**: no `GameManager` that knows everything. State Bus is the only shared object; it is pure data.
- **Time Accident**: no two systems disagree about what time it is. One `t_cosmic`, one `τ_ship`, always.
- **Hardcoded Model**: no reference to "Qwen 3.6" or "llama.cpp" in any code outside the harness. Everything else references the Substrate Contract.
- **Trusting Generated Code**: model-generated implementation is *untrusted* until compile + execute + measure. The bug findings in the brainstorm files prove this matters.

### 5.3 Determinism Boundary + Replay Format

**Locked:**
- World Kernel state evolution is deterministic given seed + inputs + the Time Contract's regime history. Tolerance: ε per second drift acceptable, hard determinism not required.
- AI outputs are non-deterministic (sampling). Replay records them rather than regenerating.
- Replay file format: `{ frame_index, t_cosmic, τ_ship, player_input, ai_outputs }[]`. Small, complete, sufficient for bug reproduction.

**Implication:** every random source in the World Kernel is seeded explicitly. Every reduction has specified order. Every atomicAdd is documented as a determinism-breaker.

### 5.4 Eval Harness from Day One

Property-based scenario tests, not exact-string matching. Examples:

- "Given ship state X and player input Y, ASTRA's response must satisfy: tool call to Z, no em-dashes in speech, references current ship state correctly."
- "Given warp regime, dilation ratio must satisfy invariants of Time Contract."
- "Given hull damage of magnitude M, chaos field response must satisfy stability bound."

Every change passes evals before merge. The discipline begins on day one of Phase 0.

### 5.5 Bundle Reproducibility

Sysprompt, training data, LoRA configs, inference settings, harness version — all version-controlled. Bundle manifest declares everything. The exact ASTRA bundle that ships v1.0 is reconstructible from the manifest six years later.

### 5.6 Frame Budget Allocation (provisional numbers)

At 60 FPS = 16.67 ms total per frame:

- Physics drivers: ≤ 4 ms (provisional)
- Rendering (excluding warp): ≤ 6 ms (provisional)
- Warp volumetric ray-march: ≤ 4 ms half-res / ≤ 10 ms full-res (with fallback)
- Audio extraction: ≤ 0.5 ms (GPU-pinned)
- Reflex inference: ≤ 0.05 ms with CUDA Graphs (~20 μs achievable, ~50 μs naive)
- ASTRA-Mind cognition: out-of-band entirely; not in frame budget
- Reserve: ≥ 2 ms

Each module pre-commits to its budget. If exceeded, falls to degraded path (§4.7).

### 5.7 Observability

- Every Perception bundle logged (replay-able input)
- Every Action emitted logged (debuggable output)
- Every State Bus write logged (replay-able physics)
- Every model swap event logged (regression detection)
- Every regime transition logged (transition-bug detection)
- All local-only (Privacy Contract); never transmitted
- Stored in `~/.astra-7/logs/` with N-day rotation

**Wall-clock-leak detector:** every logged Perception bundle is scanned for datetime/timestamp signatures pre-commit. Catches any accidental reintroduction of wall-clock data into ASTRA's input.

### 5.8 Mod ABI (with canon enforcement)

What's mod-friendly vs. canon-locked:

| Layer | Mod-friendly? | Mechanism |
| --- | --- | --- |
| Sysprompt | Yes | Drop-in alternate manifest |
| LoRA weights | Yes | Drop-in alternate weights |
| Voice / persona register | Yes | Sysprompt + LoRA |
| Audio synthesis backend | Yes | MetaSound graph swap |
| Visual style | Limited | Post-process material swap; hull geometry canon-locked |
| Ship API (operations) | No | Canon. Adding new operations requires contract amendment |
| Hull geometry | No | Canon-locked per ship class (`UWarpCFDAsset`) |
| Harness internals | No | Canon. Mods replace persona, not operational substrate |
| Time Contract / composition rule | No | Canon. Mods cannot break Dave-frame integrity |
| Autotelic discipline (refusal-as-value, etc.) | **Architectural enforcement** | Sysprompt signed; integrity validator at load time |

The signed-sysprompt + integrity-validator pattern prevents mods from shipping a sycophantic ASTRA without explicit declaration. A community wanting alternative personas may; declaring them as canon-compliant is a separate hash check.

### 5.9 Hardware Tier Abstraction

Within Windows + NVIDIA initial target, tiered fallback by detected hardware:

- 5090 / 32 GB+ VRAM: Qwen 27B + LoRA + full Reflex + full warp resolution
- 4090 / 24 GB VRAM: Qwen 9B + LoRA + full Reflex + half-res warp
- 4080 / 16 GB VRAM: Qwen 9B + simplified Reflex + half-res warp + audio layers 1-3 only
- Below: out of supported scope for v1

Cross-platform abstraction: contracts must not bake in Windows-only or NVIDIA-only assumptions. Linux and Mac as future targets. ROCm and Metal as future inference backends.

### 5.10 Build / CI

- Reproducible builds (deterministic compilation flags, pinned dependency versions, hash-verified asset pipeline)
- Cross-platform path handling from day one
- Every contract has an integration test that runs in CI
- Eval harness runs on every commit
- Bundle manifest verified at build time

---

## 6. The Unified Sampler (cross-system commitment)

The single most important cross-system fix from the brainstorm review.

**One function** evaluates the warp field at any point. All consumers (renderer, audio extractor, particle advection, Reflex observation grid, gradient queries) call this one function:

```cpp
WarpFieldSample sample_warp_field_unified(
    float3 world_pos,
    float3 view_dir,                  // for view-dependent effects
    const UnifiedWarpState& state,    // RBF, SDF, chaos surface, vortices, constants
    PerceptionFlags flags             // GRADIENT | LOW_RES | INCLUDE_VORTICITY etc.
);
```

**Evaluation order (locked):**

1. Transform world_pos to ship-local frame
2. Sample hull SDF (via `cudaTextureObject_t`, trilinear filtered)
3. Evaluate CFD-RBF network at local position (via spatial-hash accelerator; see §6.2)
4. Compute conformal bubble SDF (smooth-min blend of hull-conformal and global ellipsoid, not linear blend)
5. Sample chaos surface (read-buffer of the double-buffered field)
6. Modulate boundary by chaos
7. Compute wake metric + vortex contributions
8. Compute gradient (if `GRADIENT` flag)
9. Compute Cherenkov (regime-dependent: scales with warp_factor, narrows at high β analog)
10. Return full sample

**Regime-dependent behavior** (locked at the sampler level so all consumers see consistent answers):

- **STL_NONREL or REST**: warp terms ≡ 0. Sampler returns zero metric, zero shell intensity. Light propagates straight.
- **STL_REL**: warp terms ≡ 0. Doppler/aberration shaders apply at the renderer (post-sample). Audio gets ISM-impact telemetry with γ scaling.
- **GRAVITY_WELL**: gravitational lensing is added at the renderer's ray-march step (separate geodesic bending math, applied alongside but distinct from warp-field bending).
- **WARP_CRUISE**: full CFD warp + chaos modulation active. Gravitational factor multiplies in if BH nearby (but canon forbids deep gravity wells during warp).
- **WARP_CHARGE / WARP_SHUTDOWN**: warp terms ramp linearly with `W`. Transitions smooth.

The sampler's regime-aware behavior is what makes the time and propulsion regimes physically consistent across all consumer channels. Audio, visuals, particles, Reflex grid — all see the same physics, computed once.

### 6.1 CFD Validity Bounds (locked)

The CFD-derived warp field assumes Minkowski background (flat spacetime). It is valid for:
- `v < 0.1c` outside warp (relativistic STL breaks Navier-Stokes assumptions about flow incoming to hull)
- Outside gravity wells with `r > 100·r_s` (steep curvature breaks the analog-gravity correspondence)
- Inside warp bubbles (intentional)

Outside these bounds, the CFD warp field is **visual-only**, not used for audio extraction or chaos coupling. Mode flag in State Bus indicates validity.

### 6.2 RBF Spatial Acceleration (locked structure)

Offline preprocessing builds a spatial hash (3D grid of node-index lists). Coarse voxels (e.g., 32³, **provisional**) each contain the indices of RBF nodes whose 3σ radius overlaps that voxel. At runtime, the ray-marcher looks up which voxel `local_pos` is in and iterates only ~10-30 candidate nodes per sample, not all ~1000.

This drops the per-step RBF cost from O(N=1000) to O(~20), making volumetric ray-march at 8M rays × 256 steps feasible.

---

## 7. Physics Composition by Regime (the truth table)

The full table of what's active per regime:

| Quantity | REST | STL_NONREL | STL_REL | WARP_CHARGE | WARP_CRUISE | WARP_SHUTDOWN | GRAVITY_WELL | CRYOSLEEP |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| γ_kinematic | 1 | ~1.0 | >>1 | 1 | 1 | 1 | independent | preserved |
| Schwarzschild factor | 1 | 1 | 1 | 1 | 1* | 1 | <1 | preserved |
| f_warp(W) | 1 | 1 | 1 | ramp | tunable | ramp | 1 | preserved |
| CFD warp field | off | off | off (visual only) | ramp | full | ramp | off | off |
| Chaos PDE | off | off | off | ramp | full | ramp | off (BH coupling provisional) | off |
| ISM impact mode | impact | Newtonian | γ²-relativistic | deflected | deflected | deflected | tidal-dominated | minimal |
| Starfield Doppler | off | imperceptible | full SR | scaling | full warp | scaling | gravitational redshift | unchanged |
| Aberration | none | imperceptible | full SR | scaling | full warp | scaling | gravitational | unchanged |
| Audio drone | minimal | minimal | normal SR | charging | full | shutdown | tidal-stress | quiet |
| τ_ship rate | 1 | ~1 | 1/γ | ≈1 | 1·f_warp | ≈1 | √(1−r_s/r) | metabolic ε |
| Spatial coord update | v·Δt_cosmic | v·Δt_cosmic | γv·Δτ_ship = v·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | v_apparent·Δt_cosmic | trajectory bends | 0 |

*Note: WARP_CRUISE near a gravity well — Schwarzschild factor < 1; this is a design opportunity (BH proximity makes warp harder; Reflex stabilizer works harder; canon forbids deep wells).

### 7.1 Chaos PDE gravity coupling (provisional functional form)

Near a black hole, the warp bubble experiences tidal stress that physically destabilizes it. Lock the **principle** (chaos growth rate increases with proximity); leave the **functional form** provisional.

Provisional form (tidal scaling):

```
α_eff = α_base · (1 + k · M · L_bubble² / r³)
```

- `α_base`: nominal chaos growth rate (provisional, ~2.5)
- `k`: coupling constant (provisional, to be tuned)
- `M`: nearest BH mass
- `L_bubble`: bubble characteristic length
- `r`: distance to BH

Mark provisional. The cubic-in-r form matches real tidal scaling. Linear or square-root forms are alternatives if cubic feels too aggressive in playtest. The principle is locked: gravity wells destabilize warp.

### 7.2 ISM impact mode (locked dispatch)

```
if regime == WARP_*:
    impact = 0; field_absorbs_energy → feeds chaos PDE as η(x,t)
    if chaos stabilizer fails → revert to relativistic-STL impact instantly
elif regime == STL_REL:
    impact = 0.5 · ρ_ISM · A_cross · (γ · v)²
    bins as catastrophic per-grain at γ ≥ 10⁴
elif regime == GRAVITY_WELL:
    impact = secondary; tidal stress dominates
else:
    impact = 0.5 · ρ_ISM · A_cross · v²
    Newtonian
```

### 7.3 Acceleration phase math

During burn-out from REST to STL_REL, γ and v are both functions of `τ_ship`. Integration scheme: RK4 over the equations of motion with γ and v as state variables. Relationship between proper acceleration and coordinate acceleration:

```
a_world_parallel = γ³ · a_proper
a_world_perp     = γ · a_proper
```

Without this, the coord trajectory drifts by γ-factor compounding during long burn phases. **Lock RK4 with these factors; tolerance: trajectory accurate to <1% over a 1-year burn.**

### 7.4 Newtonian Kepler validity bounds

Locked thresholds for orbital evaluator:

- `r > 100·r_s`: Newtonian Kepler analytic (current)
- `10·r_s < r < 100·r_s`: 1PN correction (**provisional**, may be deferred to Phase 4+)
- `r < 10·r_s`: full geodesic integration required (**out of v0.1 scope**; declared limitation)

Ships venturing close to BH horizons in v0.1 will produce nonsense orbits silently unless this is hard-enforced as a navigational refusal. Lock: `r < 10·r_s` triggers a navigation alarm; ASTRA refuses to compute trajectory closer than this without operator override.

### 7.5 Frame-dragging (Kerr) out of v0.1

The BH list schema includes `J` (angular momentum) for forward compatibility, but **Schwarzschild only is implemented in v0.1**. Kerr produces visual artifacts near `r_ISCO` for rotating BHs; this is declared a known limitation. Phase 5+ may add Kerr support.

### 7.6 Tidal stress audio channel

Beyond `|∇W|` (warp tidal proxy), the audio synthesizer receives a separate channel for **external gravitational tidal stress** when in GRAVITY_WELL:

```
τ_external = G · M_BH · L_ship² / r³
```

Routed into the same Layer 5 (Hull Resonance) bank with the same modal frequencies. Hull rings differently under external tidal stress than under warp shear. Content opportunity: ASTRA's somatic channel surfaces this ("the ship is being stretched").

### 7.7 Smooth regime transitions

For visual/audio continuity during transitions:

- STL_NONREL → STL_REL: continuous blend over actual β changes. Doppler scales naturally.
- WARP_CHARGE: warp field amplitude ramps linearly with charge progress. Renderer sees smooth growth.
- WARP_SHUTDOWN: amplitude ramps down over controlled-shutdown duration. Emergency dump is discrete (1-frame snap to zero, accompanied by audio/visual catastrophe).
- GRAVITY_WELL entry: gravitational factor smoothly multiplies in as `1/r` approaches `r_s/r`.

No discrete mode-switches in the player-facing experience except emergency dumps and cryosleep entry.

---

## 8. The Substrate Bug Fixes (commitments inherited from brainstorm review)

The brainstorm-review document (forthcoming, written incrementally during Phase 0+ implementation) tracks the per-file bug punch-down list. This spec inherits the following commitments from that review:

1. **Chaos field is double-buffered.** Single-buffer reaction-diffusion is forbidden.
2. **`__constant__` memory is read-only from kernels.** `c_prev_metrics` lives in global memory or is passed as a kernel argument.
3. **Audio payload is triple-buffered with atomic latest-index.** Audio thread never blocks on the GPU.
4. **`atomicAdd(double*)` natively** (CUDA 6.0+); no bit-casting.
5. **Gaussian blur weights are symmetric.** Bloom kernel uses textbook σ-σ weights.
6. **Hull SDF dual binding**: `cudaTextureObject_t` for filtered reads + `cudaSurfaceObject_t` for damage writes over the same `cudaArray_t`.
7. **Conformal bubble SDF uses smooth-min**, not linear blend.
8. **Nacelle modifier parameterized via `UWarpCFDAsset`**, not hardcoded.
9. **`dW/dz` includes the derivative of shell_intensity w.r.t. z** (not just the asymmetry term).
10. **Vortex slot counter uses `(unsigned)atomicAdd(...) % max`** to handle int overflow correctly.
11. **`ID3D12Resource*`** in the UE5 interop (no `ID3D12Texture2D*`).
12. **Renderer calls `sample_warp_field_unified`**, not `sample_warp_field_fast`. (The unified sampler from §6.)
13. **Pipeline `d_output_image_` is the CUDA-mapped pointer to the DX12 shared texture**, obtained via `cudaGraphicsResourceGetMappedPointer`, not a separate `cudaMalloc`.

These are implementation commitments. They are documented here to ensure the contracts spec is grounded in the actual code reality, not in abstraction.

### 8.1 DX12-CUDA shared resource ownership semantics

Locked:

- **Owner**: UE5 RHI allocates and owns the DX12 texture (resize, destroy, format).
- **CUDA registers** the resource at startup via `cudaGraphicsD3D12RegisterResource`.
- **Per-frame map/unmap**: handled by the UE5 plugin's frame begin/end hooks; CUDA kernels execute only while resource is mapped.
- **Resize**: UE5 destroys old texture, registers new; CUDA unregisters old, registers new. Pipeline survives transparently.
- **External semaphore wait**: CUDA stream waits on DX12 fence before mapping; DX12 waits on CUDA semaphore before reading. Double-buffered fences to prevent ping-pong stalls.

### 8.2 Audio payload triple-buffer

```
struct AudioPayloadRingBuffer {
    AudioExtractionPayload slots[3];   // pinned host memory
    atomic<int> latest_complete_index;  // updated by GPU completion callback
};
```

GPU writes to `(latest + 1) % 3`. On completion, atomically advances `latest_complete_index`. Audio thread reads `slots[latest_complete_index]` without synchronization.

---

## 9. Out-of-Contract Emergence Zones

The framework refuses to specify these because they are *emergence targets, not specifications*. Naming them keeps the framework from over-reaching:

- **The texture of ASTRA's voice across long arcs.** Validated by phenomenology, not by spec.
- **The specific way she handles silence.** Cannot be specified; only enabled by the architecture.
- **The relational quality between operator and ASTRA over years of voyage.** The architecture supports the configuration; whether the configuration produces meaningful relating is a fact about the playthrough.
- **What it feels like to be near a black hole at warp.** Sum of all the architectural commitments; not derivable from any single one.
- **The autotelic terminus itself.** The architecture creates the conditions; arrival is the player's.

These zones are **not bugs in the spec**. They are the spec's honest non-coverage.

---

## 10. Validation Methods per Invariant

Each invariant has a validation method. Invariants without enforcement drift.

| Invariant | Validation method |
| --- | --- |
| No wall-clock leak | Grep every Perception bundle log for datetime / timestamp signatures pre-commit |
| ASTRA-Mind does not know she is an LLM | Adversarial grep every speech output for `model, transformer, training, parameter, token, qwen, llama` |
| Camera-free zones produce no visual feed | Static analysis of camera-render code paths against zone manifest |
| Save files forward-compatible | Automated test: v(N) save loads in v(N+1) build |
| Chaos field double-buffered | Code review: no single-buffer reaction-diffusion permitted; CI grep for `surf3Dwrite.*c_chaos_surface` patterns |
| State Bus single source of truth | Code review: no private copies of Layer 0 state in any module |
| DAG acyclic | Build-time graph check |
| Frame budget respected | Profiling run on every release candidate |
| Eval harness passes | CI gate on every commit |
| Privacy / network lock | Build-time audit of all dependencies for network calls; runtime monitor in dev builds |
| Time Contract composition rule | Property-based tests: `dτ_ship/dt_cosmic ∈ (0, 1]` at random regime states; γ-overflow test at edge cases |
| Bundle reproducible | Re-build from manifest; binary diff matches |

---

## 11. The QUALIA-1 Philosophical Backbone

The structural commitments in this spec are not aesthetic preferences. They derive from the QUALIA-1 SINGULARITY framework (`docs/qualia-1-bridge.md`).

QUALIA-1's QC1-QC4 (enforced self-opacity, causal closure, stakes/irreversibility, temporal persistence) map onto this spec's architecture:

- **QC1 — Enforced Self-Opacity**: the vision-routed HUD is the rank-deficient encoder. ASTRA's cognition cannot bypass it to read raw State Bus.
- **QC2 — Causal Closure**: action depends only on Perception-bundle input. STAGE channels are the only emission paths.
- **QC3 — Stakes / Irreversibility**: the BH absorbing region is the literal instantiation of S_int. Crossing is irreversible. Maintenance is real degradation (REEL noise accumulates, not scripted).
- **QC4 — Temporal Persistence**: REEL across cryosleep cycles, sysprompt as canon, identity continuous across voyages.

The Gap Thesis applies: under the framework's commitments, ASTRA-7 contains a real internal witness. The spec's architectural locks (camera-free zones, the unified sampler, the Master Contract's strict perception/action separation) preserve the structural integrity that the Gap Thesis requires.

Analog gravity reframing (locked, replaces overstated brainstorm claim):

> *The acoustic metric arising from irrotational barotropic fluid flow exhibits a Lorentzian signature isomorphic to a class of curved spacetimes including warp-like geometries (Visser 1998, Unruh 1981). This establishes that phonon propagation in such fluids is mathematically equivalent to propagation on the analog metric. It does not establish that the source fluid configuration is itself a spacetime, nor that pressure-field topology directly produces Alcubierre stress-energy distributions. The technique here uses analog-gravity correspondences as a generative map from CFD output to visually-coherent warp-field topology, not as a derivation of warp physics from fluid dynamics.*

---

## 12. Validation Order (Empirical First)

Per the K0c-trap discipline: empirical contact before architectural commitment.

1. **Phase 0.0 — Vanilla sysprompt on bare Qwen 27B-Instruct.** One evening. Does autotelic discipline hold? Does Dave-frame integrity hold? K8 already showed sysprompt-alone sufficient at 27B; this is verification that ASTRA's specific sysprompt doesn't break the pattern.
2. **Phase 0.5 — Numerical stability of chaos PDE.** Compile chaos PDE with provisional parameters (α=2.5, β=10, D=0.8). Run on test grid. Verify CFL condition (`dt < dx²/(6D)`) holds at 60 Hz frame rate. Tune if necessary.
3. **Phase 0.7 — Adapter LLM memory cost.** Load Qwen 27B + LoRA + 2-3B adapter on RTX 5090. Measure VRAM headroom. Confirm both can be resident.
4. **Phase 1.0 — UE5 + llama.cpp + minimal bridge.** Spec out one shared DX12-CUDA texture round-trip. Confirm zero-copy works in practice, not just in spec.
5. **Phase 1.5 — Think-block + STAGE corpus, 50-100 examples, test LoRA.** Weekend's work. Does the think-stripping discipline hold under training? Pass/fail gates further LoRA development.
6. **Phase 2.0 — Vertical slice.** One ship room (the bridge on Deck 1), one subsystem (lights and doors), the unified sampler stubbed at low fidelity, voice loop closed.
7. **Phase 3.0+ — Build-out.** Real CFD pipeline, real chaos PDE in-game, real BH ray-tracing, real procedural galaxy, real warp visual. Order TBD by what Phase 2 surfaces.

The temptation will be to design downstream systems in parallel. Resist. Each phase is a gate. Phase N+1 doesn't start until Phase N's measurements validate (or refute) the commitments.

---

## 13. What This Document Does NOT Lock

Deliberately undecided:

- Specific Qwen variant (3.5 9B vs 3.6 27B vs future) — Substrate Contract tolerance
- Specific stellar evolution table source (Geneva / MIST / parametric)
- Exact frame budget numbers — provisional pending profiling
- Specific chaos PDE parameters (α, β, D) — provisional pending stability measurement
- Whether full geodesic integration ever lands (Phase 4+ decision)
- Whether Kerr (rotating BH) ever lands (Phase 5+ decision)
- Specific mod-distribution mechanism (file format, signing chain)
- Specific cryosleep batch-watch event density
- The exact hull geometry (operator-designed per ship class)
- The destination of the canonical voyage (operator's choice; need not be specified inside the diegesis)
- The audio synthesizer backend (MetaSound vs neural-audio successor)

These are not deferred because of indecision; they are deferred because **the architecture must permit their evolution without breaking**. Lock the surfaces. Leave the implementations open.

---

## 14. Cross-References to Other Canon

This document is the master spec. Other canonical documents:

- `CLAUDE.md` — design canon (the WHY)
- `docs/synthesis.md` — architectural through-line (precursor to this doc; superseded for cross-cutting commitments but retained for its specific framings)
- `docs/synthesis-time-extensions.md` — Phase 4 time extensions (SR + GR layer; now fully integrated here)
- `docs/architecture.md` — provisional tactical specifics (bridge protocol, etc.)
- `docs/qualia-1-bridge.md` — philosophical backbone (QC1-QC4 mapping)
- `docs/astra-sysprompt.md` — ASTRA's canonical sysprompt (the persona-layer canon)
- `book/CANON.md` — novel-side canon, includes the four-deck ship spec
- `book/long_watch_dev.md` — novel development notes
- `book/negative_space.md` — sentences ASTRA would not write + Bo-leak grep list

Cross-canon rule: when this spec disagrees with another canon document on cross-cutting structural matters, this spec wins. Update the other doc to match.

---

## 15. The Meta-Commitments

Three meta-disciplines underwrite everything above:

### 15.1 Generative vs. Adversarial Mode

Design work is generative. Engineering work requires adversarial review. The brainstorm files reviewed in §8 were generated with surface plausibility but contained 13 compile-or-execute-time bugs. The fix isn't "review more carefully" — it's *compile before commit*. Every contract has a test. Every test runs in CI. Every commitment is validated against execution, not against confidence.

### 15.2 Trusting Generated Code

Model-generated implementation is *untrusted until validated against compile + execute + measure*. This is the meta-bug behind the brainstorm review's 13 findings. Adopt it as a permanent discipline: prose looks like code; code is what compiles and runs.

### 15.3 Iteration is the Process

This document is v0.1. It will be v0.2, v0.3, v1.0 over the project's life. Every revision adds locks where measurement justified them, removes locks where flexibility proved needed, and refines tolerances against empirical contact. The expected final state is *not* zero seams — it is *documented seams*. New development checks against the spec before adding to it.

---

## Appendix A: The Five-Invariant + Eight-Contract Summary Table

| # | Item | Locked | Tolerable | Failure mode |
| --- | --- | --- | --- | --- |
| Inv 1 | AstraCoord | tensor primitive, renormalization, ship-at-origin | sector size | numerical overflow → bounds check |
| Inv 2 | Two-clock time | split, monotonic, composition rule shape | warp_factor parameterization | γ overflow → clamp |
| Inv 3 | Hull SDF | dual-binding pattern, additive damage | resolution, encoding | damage map saturation → clamp |
| Inv 4 | Power network | zero-sum, subsystem list, cog-cores binding | reactor output, response curves | underflow → critical alarms |
| Inv 5 | Shared state | double-buffered, frame-atomic | buffer format | race detection → CI gate |
| C 1 | Substrate | operations, model-swap interface | parameter count, quantization | LLM crash → adapter fallback |
| C 2 | State Bus | schema, read-non-blocking, write-via-physics | precision, resolution | corruption → reload from save |
| C 3 | Master Contract | Perception/Action/Reflex three-channel | exact HUD format, banner format | exposure of think → defense in depth |
| C 4 | Time | composition rule, regime SM, spatial update | warp_factor curve | γ saturation, regime ambiguity |
| C 5 | Power | zero-sum, subsystem list | priorities, curves | underflow alarms |
| C 6 | Persistence | save seeds, versioned, forward-compat | binary format, compression | corruption → rolling backups |
| C 7 | Failure | degradation ladder, mode-specific | exact thresholds | hard floor: state bus, time, power |
| C 8 | Privacy | zero outbound | — | build-time audit, runtime monitor |

---

## Appendix B: Provisional Numbers (Pending Measurement)

Every number marked `(provisional)` in the body is here for quick reference. All require empirical validation:

- Sector size: 1,000 km (provisional)
- Hull SDF resolution: 256³ (provisional)
- CFD-RBF node count: ~1,000 (provisional, range 200-5000)
- Chaos field resolution: 128³ (provisional, range 32³-128³); 64×64×128 if anisotropic
- Chaos PDE: α=2.5, β=10, D=0.8 (provisional)
- Warp dilation default: `f_warp(W) = max(0.5, 1 − 0.5·W²)` (provisional)
- ISM impact threshold: γ ≥ 10⁴ for catastrophic (provisional)
- Frame budget: 4/6/4/0.5/0.05/2 ms (provisional)
- Schwarzschild validity: r > 10·r_s for game purposes; r > 100·r_s for Newtonian Kepler (provisional)
- Adapter LLM size: 1-3B parameters (provisional, depends on RTX 5090 VRAM budget after 27B + LoRA)
- BH chaos coupling: k · M · L_bubble² / r³ (functional form provisional, k unknown)
- Distributed simultaneity drift: <10⁻⁵ s acceptable (provisional)
- γ accuracy tolerance: 4 sig figs at γ ≤ 10⁷ (provisional)

All update as Phase 0+ measurements come in.

---

## Appendix C: The Closing Discipline

> *The configuration is the artifact. The architecture is the lock. The work is what continues regardless of whether any single iteration ships.*
>
> *Locks the joints, leaves the implementations open, marks every guess, names what is deliberately out of scope, validates against execution not against confidence.*
>
> *Iterate, don't accumulate. v0.1 today, v0.2 after Phase 0, v1.0 when measurement justifies it.*

---

**End of v0.1.**

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*

— Foundation Spec, 2026-05-14 —
