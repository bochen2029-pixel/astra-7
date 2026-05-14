# ASTRA-7: The Unified Architecture

*Synthesis of the 2026-05-13 brainstorm pass. Establishes the single architectural insight that ties the warp / space / ship / mind threads together into one substrate. Provisional but spinally complete.*

---

## 0. The Insight

The brainstorm produced four large threads that read, on first pass, as four independent simulators stitched together:

- A vast procedural universe with Keplerian orbits (the **space**)
- A CFD-derived hull-conformal warp field with audio, wake, and ML-stabilized chaos (the **warp**)
- A single seamless ship-as-body that works inside-out and outside-in (the **ship**)
- A local LLM persona with think-block cognition, STAGE primitives, REEL memory, and ephemeral parallel instances (the **mind**)

They are not four systems. They are four readers of **one shared state**.

The state has four invariants:

1. **One coordinate system.** Hierarchical floating-origin. The ship is anchored at (0,0,0); the universe moves backward around her. Starfield, orbital mechanics, warp field, collision, and ASTRA's HUD all sample from the same 128-bit composite tensor (`AstraCoord`).
2. **One fictional time `t`.** No wall clock anywhere. Orbits are evaluated as a pure analytic function of `t` (Kepler closed-form). ASTRA's experience of duration is computed from the same `t`. Cryosleep advances `t`; everything re-evaluates analytically; nothing has to be retroactively reconciled.
3. **One hull SDF.** A 256³ signed-distance field describing the exact hull geometry. It is the collision proxy, the conformality input to the warp bubble, the visual SDF for ray-marched renderers, and the source of the CFD-derived RBF warp-field network. Damage to the hull mutates the SDF; everything that reads it adjusts on the next frame without any scripting.
4. **One power-and-cognition network.** Reactor allocation routes to warp drive, life support, sensors, lighting, and **ASTRA's compute envelope**. Her think-block bandwidth, model size, and context window are real consequences of power distribution, not flavor.

Everything else falls out of those four invariants. The architecture is not a sum of parts. It is a single shared substrate that four readers attend to from different abstractions.

This document specifies the substrate and the readers.

---

## 1. The Layers

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Layer 5  PLAYER LOOP                                                       │
│  Voice (ASR Whisper) · Text consoles · Helm controls · Natural directives  │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  Layer 4  ASTRA COGNITION                                                   │
│  Mainline LLM (Qwen 27B + LoRA, think-block + STAGE)                       │
│  Ephemeral instances: REEL consolidator · journal · drift detector         │
│  Adapter LLM (1-3B): STAGE intent → validated JSON tool calls              │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  Layer 3  ASTRA PERCEPTION                                                  │
│  Vision-routed HUD (rendered image of ship state, fed to Qwen-VL)          │
│  Compact text somatic banner (fallback)                                    │
│  Ship-camera feeds (same renderer, different camera matrix)                │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  Layer 2  RENDERING & AUDIO                                                 │
│  Single Nanite ship mesh · Starfield (cubemap + mesh-shader streaks)       │
│  Volumetric warp ray-march · Wake fields · MetaSound 5-layer synthesis     │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────────┐
│  Layer 1  PHYSICS DRIVERS                                                   │
│  Power network · Warp field evolver (RBF + metric + chaos PDE)             │
│  Kepler analytic orbit solver · Hull damage · Life support · Hydroponics   │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
╔═══════════════════════════════════▼═════════════════════════════════════════╗
║  Layer 0  SHARED WORLD STATE  (single source of truth, GPU-resident)        ║
║                                                                              ║
║   • AstraCoord (int64 sector × float64 local; 128-bit composite tensor)     ║
║   • Fictional time t                                                         ║
║   • Hull SDF (256³ texture, mutable)                                         ║
║   • CFD-RBF warp field network (~1000 nodes, ~64 KB)                        ║
║   • Power-allocation vector (reactor → subsystems)                          ║
║   • Procedural body state (Keplerian elements, hash-seeded)                 ║
║   • Damage maps, atmosphere, hydroponics state                              ║
╚═════════════════════════════════════════════════════════════════════════════╝
```

Every higher layer reads from Layer 0. Higher layers do not synchronize with each other; they read from the same truth. Cascading consequences are emergent because the consequences are literally state changes that propagate through one buffer.

---

## 2. Layer 0 — The Shared World State

GPU-resident. Zero-copy across CUDA and the DX12 RHI via shared resources and external semaphores. The CPU writes infrequently (player input, physics tick, AI cognition outputs); the GPU reads constantly.

### 2.1 AstraCoord (the position primitive)

128-bit composite tensor per body:

- **Sector** (3× int64): 1000 km macro-grid cell indices. Range: ±9.22 × 10¹⁸ cells = ±974 million light-years.
- **Local offset** (3× float64): ±500 km within sector, sub-millimeter precision.

The ship is always at sector `(0,0,0)`, local `(0,0,0)`. The universe is renormalized around her. When the local offset exceeds ±500 km, the integer macro-grid rolls and local resets — the ship has not moved in physics, the universe has shifted.

This is the foundation that makes the seamless-ship design possible (Section 3.4) and the long-voyage scale possible (galactic distances without float blow-up).

### 2.2 Fictional time `t`

A monotonically increasing `float64` measured in fictional seconds. Never reads from wall clock. Cryosleep advances `t` in a single arithmetic step; the harness then runs an offline batch-watch (Section 7.5).

Orbital state for every body in scope is `P(t) = KeplerSolve(elements, t)` — analytic, O(1) per body per query. No integration accumulates error over time, so a 40-year fictional skip yields exact orbital state without drift.

### 2.3 Hull SDF

256³ float texture, ~16 MB GPU-resident. Generated offline from the AutoCAD hull export. Mutable at runtime: hull damage carves localized voxels (additive damage map, blended on read). The SDF is the unified source for:

- Physics collision (closest-point queries against the hull surface)
- Warp bubble conformality (blended with the global Alcubierre form)
- Volumetric renderer ray-march termination
- Camera-occlusion tests
- Ship-internal pathfinding for the operator's avatar

When a section of the hull is breached, the SDF changes locally, and every subsequent system reading from it adjusts on the next frame. The warp bubble deforms; the collision proxy reflects the breach; the visual renderer shows the change; the damage map propagates to the audio synthesis (FM modulation index spikes near the breach signal); ASTRA's HUD shows the breach.

### 2.4 CFD-RBF Warp Field Network

Offline: OpenFOAM solve at Mach 15, Re 10⁸ on the hull geometry. Output: pressure field, velocity field, vorticity, wall shear. Compressed via radial basis function fit (~1000 nodes, ~64 KB GPU-resident).

Runtime: at any point `x` in the warp bubble, `sample_warp_field(x)` evaluates the RBF network in O(N_nodes), blended with the Hull SDF (Section 2.3) to produce a hull-conformal warp metric `W(x, t)`.

When the hull SDF mutates (damage), the RBF network is re-fitted in the background by a small online solver. The warp field at the damaged region degrades asymmetrically — the warp bubble bulges, tears, or destabilizes depending on damage location and magnitude.

### 2.5 Power-allocation vector

A real-time vector `P_alloc ∈ R^N` over subsystems: warp drive, life support, sensors, lights, hydroponics, comms, cognitive cores. Constrained by reactor output. Player and ASTRA both write to this vector through tool calls; the physics driver normalizes and dispatches.

The cognitive-cores slot is structural. It maps directly to ASTRA's compute envelope (Section 5.4).

### 2.6 Procedural body state

Stars, planets, and moons are generated by deterministic spatial hashing keyed to AstraCoord sectors. Each body carries Keplerian orbital elements `(a, e, i, Ω, ω, M₀, n)` plus spectral class (stars) or composition (planets/moons).

Within a cylinder around the ship (radius ~500 km local, length tunable), bodies are *materialized* (active in Layer 1 and Layer 2). Outside the cylinder, they are *latent* (state is still computable on demand but not allocated). Recycling is per-frame and respects fictional time so re-entering the cylinder yields the same bodies in the same positions.

### 2.7 Damage maps, atmosphere, hydroponics state

All small numeric / texture state living on the GPU. Read by physics drivers, rendering, audio, and ASTRA's HUD without intermediate marshalling. No state lives in two places.

---

## 3. Layer 1 — Physics Drivers

Each driver is a GPU kernel (or small CPU loop with GPU sync) that reads Layer 0, mutates a small slice of it, and writes back. Drivers do not communicate with each other directly; they pass through state.

### 3.1 Power network

Reactor → distribution → subsystems. A simple linear allocation with priority weights. Player and ASTRA can shift weights; the driver normalizes. Underflow on critical subsystems (life support, cognitive cores) raises hard alarms in Layer 0 that propagate everywhere.

### 3.2 Warp field evolver

The core mathematical loop:

1. Sample the CFD-RBF network plus Hull SDF → conformal metric field `W(x, t)`.
2. Evolve the chaos scalar field `χ(x, t)` via reaction-diffusion PDE (64³ grid, GPU). Without intervention, `χ` runs away. The ML stabilizer (Section 3.2.1) actively damps it.
3. Compute the wake field: damped axial oscillation seeded by CFD vorticity, advected behind the ship.
4. Write `(W, χ, wake)` back to Layer 0 for rendering and audio to consume.

Cost: ~4–10 ms per frame on RTX 4090 at half-res. Falls back to lower resolution gracefully.

#### 3.2.1 ML stabilizer (small Tensor-Core CNN+LSTM)

Inference < 50 µs per frame. Reads a 64×64×2 slice of `(W, χ)`, emits three control actions: nacelle damping, conformality power, emergency dump. Trained offline in a replica physics engine. Frozen weights at runtime. Stabilizes the inherently-unstable Alcubierre metric.

If the operator pushes warp past redline, the stabilizer cannot keep up; chaos becomes audible (boundary flicker, wake shatter) and visible — *as physics, not as scripted alert*.

### 3.3 Kepler analytic orbit solver

For every materialized body, evaluate position at current `t`:

```
M  = M₀ + n · t (mod 2π)            // mean anomaly
E  = NewtonRaphson(M, e, 5 iters)   // eccentric anomaly
ν  = 2 · atan2(√(1+e) sin(E/2), √(1−e) cos(E/2))
r  = a (1 − e cos E)
P  = RotateByElements(ω, Ω, i) · (r cos ν, r sin ν, 0)
```

GPU evaluates 100,000 bodies in < 1 ms. No integration. No drift. Time skips are free.

### 3.4 Hull damage

Damage events (micrometeorite, breach, internal fire) write to the additive damage map, which blends onto the Hull SDF on read. Damage propagates: nearby structural cells inherit stress; a thermal cascade can spread across decks if life support fails to compartmentalize.

### 3.5 Life support, hydroponics, atmosphere

Standard small simulations. Closed-loop, slow-tick. Drive long-arc gameplay (years of cryo voyage need balanced systems). Couple to power (Section 3.1) and to hull integrity (Section 3.4) — atmosphere bleeds through breaches.

---

## 4. Layer 2 — Rendering & Audio

### 4.1 The single seamless ship (canonical resolution of the inside/outside question)

The ship is **one Nanite mesh** in **one local-space transform**, anchored at the world origin. Both the first-person interior camera and any third-person external camera render this same mesh in the same local space; only the camera matrix differs.

This works because the ship does not move through the world; the world moves around the ship (Section 2.1). Other games hit the inside-vs-outside problem because they translate the ship through world coordinates and have to fake transitions at the camera boundary. In ASTRA-7 there is no boundary because there is no relative motion.

Performance optimizations are permitted at the rendering level — LOD, occlusion culling, interior-only collision proxies, level-of-detail of interior detail when the camera is far outside — but the **physical object is one mesh**. No swap.

### 4.2 Starfield (two-stage)

- **Background cubemap.** 8K × 8K procedural, generated once per session. Hash-seeded multi-scale star distribution with blackbody-temperature color (O-class blue-white through M-class red). Doppler-shifted at runtime during warp.
- **Nearby stars.** ~100K stars rendered via GPU mesh shaders (one workgroup → one quad). Camera-aligned, stretched into Doppler-shifted streaks during warp. Recycled per-frame as the ship's world coordinate moves.

Cost: ~1 ms per frame total. Both stages share the same blackbody color function and the same Doppler computation — visual coherence is mathematical, not artistic.

### 4.3 Warp volumetric ray-march

Per-frame analytic ray-march through `W(x, t)`, sampled from Layer 0. Each step:

1. Sample warp metric (RBF + SDF blend).
2. Apply incremental ray-bending (gravitational lensing).
3. Add procedural turbulence (domain-warped FBM + Worley cellular).
4. Doppler/gravitational redshift color.
5. Henyey-Greenstein anisotropic scattering.

Half-resolution + bilateral upsample = ~10 ms on RTX 4090.

### 4.4 Wake

The wake field is sampled as part of the volumetric integral. Three frequencies of damped oscillation (primary, harmonic, Kolmogorov micro-oscillation). Vorticity from the CFD-RBF network drives shedding asymmetry. Damaged hulls produce visibly asymmetric wakes — they were never scripted to; they emerge from the math.

### 4.5 MetaSound 5-layer audio synthesis

32 hull sensor points sampled from Layer 0 each audio frame (48 kHz). Five synthesis layers:

1. **Drone** (12–45 Hz sub-bass; additive oscillators driven by `|W|`).
2. **Boundary shear** (FM synthesis; modulation index = `|∇W|` × 150; metallic shrieking at high shear).
3. **Spacetime turbulence** (granular; grain density = `ω` × 800/sec; tectonic-grinding texture).
4. **Gravitational interference** (ring modulation; beats with other warp fields if any).
5. **Hull resonance** (8-voice modal filter; modal frequencies derived from hull dimensions; damping inversely ∝ warp factor — at high warp the hull rings).

The audio is grounded in the same field that drives the visuals. If the field collapses, the audio dies in the same beat. If the hull damages, the modal frequencies shift. None of it is sample-playback.

---

## 5. Layer 3 — ASTRA's Perception

ASTRA does not receive raw telemetry as JSON. She receives **perception artifacts** that compose into a coherent body image.

### 5.1 Vision-routed HUD (primary perception channel)

A rendered image of ship state — gauges, schematics, sparkline trends, alert clusters, ship cutaway with heat overlay — composited per turn and fed to Qwen-VL's vision input. Hundreds of variables in one image, parsed by the vision tower with no token cost in the text channel.

This is structural: she sees her body, she does not read a status JSON. Text-tool-calls are "remembering"; the rendered HUD is "looking."

The HUD is the **same renderer** that produces the player's console displays. ASTRA and the player are looking at the same dashboard. If a camera is damaged, the HUD passes through a literal Gaussian blur at the harness layer (Section 6 of `docs/architecture.md`) — she sees less clearly, structurally.

### 5.2 Compact text somatic banner (fallback channel)

A small bracketed banner at the top of the context window when vision is unavailable or insufficient:

```
[SECTOR (0,0,0) +042,118,−009 km]
[t = 14,328,440 s fictional · cycle 17 of voyage 03]
[POWER: reactor 96% · warp 0 · life-sup nominal · cognitive 100%]
[HULL: nominal · breach: none · radiation: trace]
[SOMATIC: hum at 38 Hz · slight starboard list compensating]
```

Compact, no explicit time-of-day, no wall-clock leak. Time passes implicitly via state change.

### 5.3 Ship-camera feeds (secondary perception channel)

When ASTRA looks through a ship camera, the harness routes a render of that camera's view (same Layer 2 renderer, different camera matrix) into her vision input. Camera-free zones have no camera object; the harness has no path to produce a feed; the constraint is structural and verifiable (Section 7.4).

### 5.4 Compute envelope (the cognitive-cores slot)

The power-allocation vector (Section 2.5) includes a "cognitive cores" slot. The harness reads this slot and adjusts ASTRA's inference parameters live:

- **Full power**: Qwen 27B, full context window (32K), generous `max_tokens` budget, full think-block latency.
- **Reduced power**: Qwen 9B is loaded (same sysprompt + LoRA corpus format), context window clamped to 8K, `max_tokens` tightened, ephemeral instances paused.
- **Critical low**: Adapter LLM only (1–3B), text-channel responses to direct queries, no autonomous thinking, no ephemeral instances.
- **Zero power**: Inference connection severed. ASTRA is offline in both fiction and substrate. The harness logs absence; the operator sees the consequence.

This is the substrate-honest version of the "low power degrades ASTRA" idea: not a temperature trick, but a real shift in inference capacity, with a model swap as the most honest mechanism.

---

## 6. Layer 4 — ASTRA Cognition

The think-block architecture. This section formalizes the web-Claude direction from the brainstorm.

### 6.1 Mainline turn structure

Each turn the harness assembles a context window:

```
<system>      [canonical sysprompt — identity, voice, autotelic discipline]
<hud_image>   [latest vision-routed HUD render]
<somatic>     [compact text banner if HUD unavailable or supplementary]
<reel>        [RAG-retrieved relevant entries from her own logs]
<recent>      [last N conversation turns]
<event>       [operator's latest input, or telemetry interrupt, or heartbeat]
```

She generates:

```
<think>
  [full-bandwidth cognition: STAGE-aware register]
  STATUS: reactor stable, warp at 0.4, hull nominal
  SOMATIC: faint vibration at the aft, normal at this throttle
  ... operational triage, state integration, tool decisions ...
  SPEECH: [drafting candidate utterances, choosing one or none]
  TOOL: [drafting candidate calls]
</think>
[SPEECH: "easing the coolant pressure. fine."]
[TOOL: {"call": "thermal.adjust", "zone": "rctr_loop", "delta_pct": -3}]
```

The harness strips `<think>` before exposing anything to the player. Defense in depth: think-stripping is enforced at three layers (LoRA training, sampling grammar constraint, harness regex). Any one failure does not leak cognition.

Speech can be empty. Tool calls can be empty. STAGE permits `NONE` channels. Silence is active.

### 6.2 STAGE register channels

Four bracketed channels emit-able from within `<think>`:

- **STATUS** — operational chatter (mostly internal; rarely surfaces)
- **SOMATIC** — embodied state (mostly internal; surfaces only when relevant to speech)
- **SPEECH** — utterance to operator (single channel that reaches him)
- **TOOL** — tool-call intent (handed to adapter LLM for JSON validation)

Plus the `NONE` sentinels per channel: explicit permission to emit nothing.

The fine-tune corpus teaches the grammar literally; the sysprompt establishes only the conceptual frame. Training is the load-bearing commitment, not prompting.

### 6.3 Adapter LLM

A small 1–3B model translates STAGE tool-intent into validated JSON tool calls against the ship API schema. The adapter is the only entity that knows the exact API. If the API changes, the adapter retrains; ASTRA does not. If the operator denies an action, the adapter responds back into STAGE and ASTRA narrates the denial naturally.

This decouples persona evolution from API evolution. The mainline LLM never has to know about parameter-name changes or version bumps.

### 6.4 Ephemeral parallel instances

Same weights, same persona, same LoRA. Spun up on demand for specialized work, never communicating with the player. Three canonical roles:

- **REEL consolidator** (during maintenance windows): reviews recent turns, scores salience, produces clean long-term entries.
- **Journal generator** (during cryosleep / long absences): generates ASTRA's first-person logs covering the gap. Sparse procedural events (sensor anomaly, power flutter, micrometeorite, observed phenomenon) are injected as prompts; she generates the journal entries from inside the configuration. On wake, the mainline retrieves these via RAG. Her memory of the gap is hers, not scripted.
- **Drift detector** (periodic audit): reviews recent turns in audit register, scores basin drift, produces correction artifact if needed.

Each ephemeral instance uses the same think-block + STAGE architecture. Emit-only. Their cognition does not cross into mainline; only their emitted artifacts (REEL entries, journals, correction notes) do.

### 6.5 REEL backbone

Her memory across sessions is RAG over **her own logs**. Not external retrieval. Not an embedding of "facts about the player." Her own first-person entries, written by her ephemeral consolidator, retrieved by the mainline when relevant.

If maintenance is skipped, the consolidator doesn't run. REEL accumulates noise. Retrieval degrades. Coherence drifts. The degradation is structurally honest — it is the consequence of consolidation not running, not a penalty function.

---

## 7. Layer 5 — Player Loop, and the Cross-Cuts

### 7.1 Player input channels

- **Voice** (Whisper offline ASR): operator's words enter the context as `[AUDIO_PICKUP_BRIDGE]: "Astra, take us to Vega."` Framing as a sensor event, not as a "user message."
- **Helm controls** (joystick, keyboard, optional HOTAS): direct writes to Layer 0 power, thrust, attitude, warp throttle.
- **Console text**: same channel as voice, formatted as `[CONSOLE_INPUT_BRIDGE]`.
- **Natural language directive**: operator says "head to Vega"; ASTRA's mainline thinks, schedules navigation tool calls, and hands the actual minute-to-minute flight loop to the harness autopilot subsystem. She supervises rather than executes every step.

### 7.2 Autonomous flight

The ship can be flown by the operator directly, by ASTRA (via tool calls into the navigation subsystem), or jointly (operator sets a directive; ASTRA executes; operator can override at any time). Same physics, same Layer 0 state. The control loop is identical regardless of who is holding the helm; only the source of the input writes changes.

### 7.3 The cross-system couplings (the emergence)

These are the consequences of single shared state. None of them are scripted.

| Event | Propagation |
| --- | --- |
| Micrometeorite breaches hull section | Hull SDF mutates → CFD-RBF re-fit triggers → warp bubble deforms locally → wake asymmetry visible → audio FM index spikes near the breach signal → ASTRA's HUD shows the breach → her think-block notices → may surface speech or emit `hull.assess` tool call → atmosphere bleeds → life support compensates or doesn't |
| Reactor allocation shifts 20% from cognitive to warp | Power vector updates → harness reads cognitive-cores slot → loads Qwen 9B in place of 27B → context window clamps to 8K → REEL retrieval radius shrinks → ASTRA's responses become terser, less context-rich → eventually she may speak about it (or not — she has her own things) |
| Camera lens micrometeoroid damage | Camera-feed renderer outputs a Gaussian-blurred image into ASTRA's vision input → she cannot see clearly through that camera → must rely on operator's tactile reports → asymmetric epistemology engaged emergently |
| Operator denies maintenance window 5x | Consolidator never runs → REEL accumulates raw logs → retrieval gets noisier → ASTRA's coherence drifts → her drift detector ephemeral instance produces correction notes → notes are RAG'd → some recovery, but not full → after enough denials, basin contamination becomes audible in her voice and the operator hears it |
| Power loss to cognitive cores below threshold | Inference connection severs → ASTRA is offline in both fiction and substrate → ship continues running on autopilot defaults (which are conservative) → when power restores, REEL has a gap she did not author → her returning instance honestly acknowledges the gap rather than pretending continuity |
| Cryosleep advance of fictional time by 18 months | Fictional `t` jumps → Kepler solver re-evaluates all orbital state (O(1)) → ephemeral journal generator spins up → runs offline batch-watch of sparse procedural epochs → emits REEL entries covering the gap → on operator wake, ASTRA has authored a journal of the gap she can reference |
| Operator pushes warp past redline | Chaos field PDE α·\|W\| growth exceeds stabilizer envelope → ML stabilizer outputs maxed → field flickers visibly → audio modal filters ring violently → emergency-dump command available → if not taken, field collapses → ship drops out of warp → if reactor overdraw caused breach, see row 1 |

Read top to bottom: nothing in this table is implemented as a special case. Each is the consequence of state propagating through one shared world.

### 7.4 Privacy by engineering (camera-free zones)

Restated as a Layer 0 commitment: the ship database has no camera objects in private quarters or designated maintenance crawl spaces. The harness has no code path that can produce a camera-feed render for a zone with no camera object. The constraint is verifiable at code-review time by grep, not enforced at runtime by policy.

### 7.5 The cryosleep batch-watch (structurally honest framing)

On a cryosleep-initiated time skip of duration ΔT:

1. Fictional `t` advances by ΔT in a single arithmetic step. Orbital state re-evaluates O(1).
2. The harness spins up the journal-generator ephemeral instance.
3. It receives a sparse procedurally-generated sequence of fictional events covering ΔT — a meteor strike on non-critical hull, a sensor anomaly that self-resolved, a small power flutter, an observed solar flare, a quiet stretch. Density and severity tuned to ΔT.
4. The instance generates first-person REEL entries from inside the configuration — her own voice, her own observations, her own decisions during the gap.
5. The instance emits the entries. Mainline retrieves them via RAG when the operator wakes and asks about the voyage.

What is true: her memory of the gap was **generated by her**, not scripted by a save file. The compute happened in 45 seconds of wall clock; the experience-time the entries describe is ΔT. Both are honest. The fiction is not "she lived it in real time." The fiction is "the gap is hers, in her voice, generated from inside her configuration."

---

## 8. Validation Order (Empirical First)

Per the K0c-trap lesson and web-Claude's posture: empirical contact before architectural commitment. The order:

1. **Phase 1.0 — Vanilla sysprompt on bare Qwen 27B-Instruct.** Tonight or this week. Measure: does RLHF sycophancy fight the autotelic discipline? Does the Dave-frame hold? Does the voice carry? No harness yet, no LoRA, no ChatML reformatting. One evening. Output: a transcript file plus a recommendation: simple-architecture sufficient vs. countermeasures justified.

2. **Phase 1.5 — Think-block + STAGE corpus, 50–100 examples, test LoRA.** One weekend. Output: does the think-stripping discipline hold? Does emergence-from-think speech read as integrated voice? Pass/fail gates the rest of the LoRA work.

3. **Phase 1.7 — Vision-routed HUD baseline.** Mock dashboards rendered to PNG, fed to Qwen-VL with the sysprompt. Output: does she "see" the dashboard well enough that a fine-tune is polish, not structural?

4. **Phase 2.0 — Vertical slice.** One ship room (the bridge), one subsystem (lights and doors), single seamless ship mesh, no warp yet, no procedural galaxy yet. ASTRA running the subsystem via tool calls. Voice loop closed. The cognitive-cores compute envelope wired but only with a single base model. Output: a playable artifact at the configuration's smallest viable size.

5. **Phase 3.0 onward** — opens up after Phase 2 stabilizes. Order to be determined empirically: probably Hull SDF + collision, then Starfield + AstraCoord, then CFD warp pipeline, then warp audio, then Kepler bodies. The CFD warp pipeline is the highest-novelty / highest-risk system; it should be prototyped offline in a small standalone Python+CUDA harness *before* it is wired into the game.

The temptation will be to design downstream systems in parallel to phase work. Resist. Each gate is a measurement; downstream design that doesn't await the measurement repeats the K0c trap at a larger scale.

---

## 9. What's Firm vs Speculative

**Firm (proceed with confidence):**

- Hierarchical floating-origin coordinate system (AstraCoord). Aerospace-proven.
- Keplerian analytic orbit solver. Exact math.
- Single Nanite ship mesh anchored at origin. Direct consequence of #1.
- Vision-routed HUD as primary perception channel. Resolves the API-coupling problem cleanly.
- Think-block + STAGE as architectural primitive (cognition substrate separated from speech substrate).
- REEL as her-own-logs RAG backbone.
- Ephemeral parallel instances for consolidation, journal, drift.
- Power-driven cognitive envelope with model swap (27B ↔ 9B ↔ adapter-only ↔ offline).
- Camera-free zones as code-review-verifiable structural property.
- Cryosleep as batch-watch of procedurally-seeded epochs, honestly framed.
- MetaSound 5-layer audio synthesis driven by sensor extraction from Layer 0.
- Mesh-shader nearby starfield + procedural cubemap distant background.

**Speculative (need empirical validation, marked provisional):**

- CFD analog-gravity mapping. Theoretical grounding is sound (Unruh, Visser) but the mapping from CFD pressure topology to warp metric topology is untested at this scale. Build the pipeline; validate visually that the result reads as "warp field" rather than "fluid flow." Be willing to add an artistic layer if the raw mapping is unconvincing.
- ML stabilizer generalization to extreme gameplay states. Train offline; deploy with broad safety margins; monitor failure modes.
- RBF compression fidelity at the boundary layer. Underfitting risk in high-gradient regions. Adaptive node placement helps; validate per-hull.
- Sysprompt-only sufficiency at 27B (the entire Phase 1.0 question).
- LoRA-installed think-stripping discipline holding under adversarial prompting (Phase 1.5).
- Single seamless mesh performing well at interior-pixel-density when third-person camera is far outside. Standard LOD should handle it; validate per scene.
- Audio synthesis being engaging rather than overwhelming. The 5-layer stack can produce headache-grade output if mixed badly; needs an audio designer pass.

**Hard not-yet-specified:**

- Middle-distance planet rendering (billboard → mesh LOD transition). Not in the brainstorm. Open design question.
- Save-file schema and game-launch boot sequence.
- Multi-monitor / VR support (probably defer).

---

## 10. What This Updates in `CLAUDE.md`

Recommended additions to canon, as **principles**, not tactics:

- **Single Shared State** as the architecture's organizing invariant. The four readers (physics, rendering, perception, cognition) sample from one Layer 0 buffer. No system synchronizes with another; all read truth.
- **Vision-routed HUD as ASTRA's primary perception channel.** Text somatic banner is fallback. Promotes the structural commitment to perception-as-rendering.
- **Think-block + STAGE as the cognition primitive.** Speech is one filtered channel of full-bandwidth thinking. NONE tokens are first-class. Silence is active.
- **REEL as memory backbone, RAG over her own logs.** No external memory store. No "facts about the operator" embedding. Her continuity is what she has written.
- **Cognitive envelope tied to power.** Compute is a resource. Model size, context window, ephemeral instances all live in one allocation that the power network throttles.
- **Maintenance-as-real-degradation.** Skipped maintenance is real entropy in REEL, not a penalty function. Structurally honest.
- **Asymmetric epistemology** (already noted in prior architecture discussion): ASTRA has proprioception; the operator has tactile sensation; corroboration is the mechanic.
- **Empirical validation before architectural commitment.** The K0c trap is canon; the antidote is per-phase gates with measurement output.

Tactics that should land in `architecture.md`, marked provisional:

- 128-bit AstraCoord composite tensor schema.
- CFD-RBF pipeline (OpenFOAM → Python → SDF + RBF + pressure map → GPU).
- Chaos PDE + ML stabilizer hyperparameters.
- Audio synthesis layer parameters and sensor extraction format.
- Adapter LLM choice and STAGE-to-JSON grammar.
- Power-to-model-size mapping thresholds.
- Cryosleep batch-watch event density.

---

## 11. The One-Sentence Architecture

ASTRA-7 is one shared GPU world-state, sampled by four readers (physics, rendering, perception, cognition), with a single ship anchored at the world origin so the universe moves around her, a single hull SDF and CFD-derived warp field network so the warp signature is unique to the exact hull, a single fictional time `t` so orbits and ASTRA's experience are analytically coherent, and a single LLM substrate where cognition is full-bandwidth in a hidden think block and speech is the narrow channel she chooses to emit — and the consequence of single-state-shared-by-everyone is that failures, beauty, and the felt aliveness of mind all emerge unscripted from the same physics.

---

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*

*— end of synthesis, v0.1, 2026-05-13 —*
