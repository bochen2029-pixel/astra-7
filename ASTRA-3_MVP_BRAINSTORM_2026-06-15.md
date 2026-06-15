# ASTRA-3 — MVP / POC Brainstorm

**Date:** 2026-06-15
**Status:** Brainstorm only. No implementation. Synthesized from a 16-agent fan-out (9 codebase-recon readers + 4 MVP-path designers + 3 adversarial red-teamers, ~1.35M tokens of reading) over the live ASTRA-7 repo.
**Author:** Claude (Opus 4.8, ultracode) acting as the project harness.

---

## 0. TL;DR — the verdict

**Build ASTRA-3 by extending the existing C++/OpenGL visualizer (`ASTRA_VISUALIZER_02`), not in UE5 and not through the Python textverse harness.** Three of four independent design agents landed there; the UE5 dissent is real but loses on "fastest to first felt frame." All three red-teams returned **works-with-constraints** — not "risky," not "doesn't work."

The core loop is viable, and it is — beautifully — **ASTRA-7's own two-kernel architecture at minimum scale**: a slow LLM "Mind" deciding *which way the gap is* every ~5s, over a deterministic frame-rate "Reflex" that flies smoothly toward that bearing and refuses to hit anything. The 5-second-vs-real-time tension that looks fatal is a **red herring** (there's no ship-position integrator — the world is a treadmill; closing speed is a free knob you set to Passengers-drift). The genuine risk is **monocular depth perception** (can a 9B tell a small-near rock from a large-far one in a single frame?), and it has concrete rendering fixes.

**The single most important recommendation: a ~1-hour day-0 spike** — hand-feed a few PNG screenshots of the existing scene to a local Qwen-3.5-9B-vision `llama-server` via a 30-line C++ curl harness, and confirm it returns sane steering JSON — **before writing one line of game code.** That retires the only true unknown for the price of an afternoon and converts "is this secretly a research problem?" from a mid-build surprise into a measured result.

**Rough effort:** felt text-narrated loop in **~2–3 focused weeks**; voiced version in **~3–4 weeks**. Versus UE5's multi-week engine/asset/MetaSound tax before frame one.

---

## 1. The concept (ASTRA-3, restated)

A radical scale-back of ASTRA-7 to one laser-focused loop:

- Fully 3D. A starship drifts through space inside a **procedural asteroid field** — the opening of *Passengers* (2016), slow and majestic; the old Windows screensaver of a ship flying through space, but real and AI-driven.
- Player **toggles camera**: third-person (external ship) ↔ internal cockpit. Same scene, two cameras.
- A local **Qwen 3.5 9B with native vision** takes a **screenshot every ~5 seconds**, processes it, and helps **autonavigate** around the asteroids. No cheating: the model sees only rendered pixels, never the asteroid coordinate array. Asteroids are seeded-but-unpredictable, so the path is not a memorized loop.
- **ASTRA** is the onboard AI: she **sees** the same frame, **knows** the ship is dodging on autopilot, and can **talk** — voice out (TTS) and player voice in (mic/ASR).

The name signals the tier: **ASTRA-7** (full vision) → this is the third major reduction, a proof-of-life vehicle. It is also genuinely *shippable on its own* — a screensaver with a mind.

---

## 2. What the fan-out found: the reuse map

The visualizer is far closer to this than it looks. Verified by agents reading the actual source (not summaries):

| Need | Already exists in `ASTRA_VISUALIZER_02` | Effort to adapt |
|---|---|---|
| **3D space, ship, starfield backdrop** | `hull.{h,cpp}` (procedural blended-wing-body mesh), `starfield.{h,cpp}` (10K seeded point sprites with Doppler), full GL4.6 render loop | reuse as-is |
| **Camera toggle (3rd-person ↔ cockpit)** | `camera.h` `set_pose(position, target)` already exists and is already used for canonical poses (`application.cpp:48–51`) | **trivial** — store two poses + a `C`-key branch (~30 lines) |
| **Screenshot → bytes for the LLM** | `screenshot.cpp` `read_framebuffer_rgba8()` + `save_png_rgba8()` (stb), top-left RGBA8 = exactly Qwen's format; **the F12 key handler already does capture→encode→write every press** (`application.cpp:494–513`) | **trivial** — "retime F12" from keypress to a 5s timer |
| **Steering input the renderer consumes** | `SceneRenderParams.ship_velocity_xyz[3]` (`scene_base.h:32`) is *already* the per-frame steering vector | reuse — autopilot just writes it |
| **Procedural seeded generation pattern** | `starfield.cpp:16–21` LCG (`state*1664525+1013904223`), locked seed `0xA57A4007` for bit-reproducibility | clone the 20-line RNG idiom |
| **Mechanical validation** | `pixel_sampler` + `golden_diff` + `json_report` — assert "she steered toward the gap" against engine ground truth, headless, no human | reuse |
| **Build** | CMake + Ninja, static single `.exe`, `libcurl`/`nlohmann_json` already in the allow-list family; **builds green on the exact machine** | reuse |
| **LLM transport (reference)** | textverse `client.py` proves OpenAI-compat + SSE + retry + Qwen `reasoning_content`→`<think>` against `llama-server`; **STAGE parser** (`grammar/parser.py`) + tool surface (`ship/api.py`) | borrow the *shape*, not the code (see §4) |
| **ASTRA persona/voice** | `docs/astra-sysprompt.md` (brevity, no em-dashes, no service phrases, silence-is-legal) | adapt a thin vision addendum |

**The genuinely-new surface is small and bounded:** (1) an **instanced** asteroid field (starfield is `GL_POINTS` static — instancing dynamic transforms is the one real new GL pattern), (2) the **vision→heading sidecar**, (3) the **deterministic trim/brake layer**, (4) voice (deferrable). Everything else is lift-and-adapt.

**The notable gaps the recon flagged:** the LLM `client.py` is hardcoded text-only (`ChatMessage.content: str`, line 64) — no multimodal; `nav.heading_set` takes a *destination* (AstraCoord/named body), not a steer vector; and there is no depth-cue rendering yet (the make-or-break, §6).

---

## 3. Engine decision: visualizer vs UE5

**Winner: extend `ASTRA_VISUALIZER_02` (C++/OpenGL).** Why:

- ~70–80% of the hard part (3D scene, camera with `set_pose`, procedural hull, seeded starfield, framebuffer screenshot *already called in the loop*, scene framework with `ship_velocity_xyz` as input, ImGui overlay, headless+golden validation) **already exists, builds, and ships as a static `.exe` on the target machine.**
- Native C++ is the operator's home turf — **zero engine/asset/Blueprint/MetaSound learning tax** before frame one.
- The two integration points are half-built: **the F12 handler IS the screenshot feed** (retime it), **`set_pose` IS the camera toggle** (store two poses).
- Stays fully compiled C/C++ → clean under the Language Discipline; single static exe.

**The honest UE5 counter (Path-β, the dissent):** UE 5.7 (the standing `ASTRA_AUDIO` project, both 5.7 landmines already solved) gives you *for free* the things the C++ rig lists as gaps — **instanced asteroids** (one HISM component, the "no batch rendering" gap handed to you), **dual cameras**, **collision/clearance** (overlap queries), **SceneCapture→RenderTarget→PNG**, lighting, and **ASTRA's ambient voice** (the existing WarpHullSynth MetaSound driven by `SetFloatParameter`). The `AstraVoyageActor` Tick/BeginPlay/HUD scaffold is a verbatim template.

**Why UE5 still loses for *this* goal:** there is **no 3D scene, no camera toggle, no asteroid field, no capture path in `ASTRA_AUDIO` yet** — you'd build the entire visual stack from scratch *inside an engine* before you even reach the vision bridge, paying the editor/build weight. The red-team's call: UE5 is the better **eventual game** substrate, not the **fastest POC** substrate. (And nothing here forecloses migrating the proven loop to UE5 later — the loop logic ports; only the render host changes.)

**Also rejected: routing through the Python textverse client.** It's the *measurement instrument* (async-only, text-only `content`, lives in the carve-out). Don't bend it into a game runtime. Borrow its STAGE/perception *shape* as a spec; write the loop in C++.

---

## 4. The architecture: two-rate control (the key insight)

The red-team's sharpest structural finding: **the LLM must never emit an instantaneous per-frame steering signal.** Split the autopilot into two rates — which is exactly ASTRA-7's Mind/Reflex split, scaled down:

```
  ┌─────────────────────────────────────────────────────────────┐
  │ STRATEGY  (the "Mind")   — Qwen 3.5 9B vision, every ~5 s    │
  │   sees one rendered frame → "the gap is up-and-left"         │
  │   emits a DESIRED HEADING (discrete/coarse) + 1 line speech  │
  └───────────────────────────┬─────────────────────────────────┘
                              │ desired bearing (updated @ 5 s)
                              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │ REFLEX  (the deterministic trim)  — every render frame       │
  │   slerp ship-forward toward desired bearing (slew-capped)    │
  │   + geometric near-field BRAKE/DEFLECT: sphere-vs-swept-     │
  │     capsule against rocks ALREADY IN THE FRUSTUM only        │
  │   → flies smoothly toward the gap; never hits anything       │
  └─────────────────────────────────────────────────────────────┘
```

- The **LLM's job:** "which way is the gap," every 5s. A 9B does coarse classification-over-an-image far more reliably than continuous control.
- The **Reflex's job:** "fly toward that bearing and don't hit anything in the next 5s." Per-frame, deterministic, sub-millisecond.
- **This is why 5s latency is fine:** between looks the ship is not flying blind on a stale instantaneous command — it is *converging on a still-valid desired bearing*. Exactly how a human pilot scans-then-holds.
- **The deterministic layer is UNAVOIDABLE, not optional.** "A 9B genuinely autonavigates" is *false* without it (a single bad/late/hallucinated call would crash the ship) and *true* with it. Both red-teams insisted on this.

**Honest-perception note:** the brake is a *reflex, not an oracle* — it only reads geometry already inside the render frustum (rocks the model could also see), never the spawn list. So nothing cheats.

This is the deepest point of the whole brainstorm: **ASTRA-3 isn't a toy detour from ASTRA-7 — it's the project's two-kernel thesis (stochastic strategic Mind + deterministic safety Reflex) proven in the cheapest possible vehicle**, with the endogenous/exogenous and c-bounded-epistemology disciplines falling out for free (the screenshot is exogenous/delayed vision; proximity-to-ASTRA is an endogenous felt scalar).

---

## 5. The vision-autopilot loop, concretely

```
GL render thread (60+ FPS, never blocks):
   every frame  → apply current desired-heading via trim+brake → render → present
   every ~5 s   → read_framebuffer_rgba8() [the F12 body] → hand PNG path to worker

vision worker thread (off the render thread):
   base64-encode PNG
   POST localhost llama-server /v1/chat/completions
        content = [ {image_url: data:image/png;base64,…},
                    {text: "You are flying forward. Pick the clearer side.
                            Output one action + ≤1 sentence of speech."} ]
   receive STAGE output → parse:  <think> (dropped)
                                  action  (discrete: clear-left/right/up/down/hold)
                                  speech  (→ TTS, or ImGui caption pre-voice)
   write desired-heading into a double-buffered atomic struct
   (between replies: dead-reckon on last heading; on 2 timeouts → SAFE_HOLD: bleed speed)
```

- **The vision client is fresh C++** (`libcurl` + `nlohmann/json`, both allow-listed), **not** a patch to the text-only Python client. It's lock-clean, off-thread, and **endpoint-agnostic** (so the day-0 spike can point at any local OpenAI-compat vision endpoint to prove the loop, then swap to `llama.cpp` once the build is sorted).
- **Discrete action output is mandatory** (not free `{steer:[x,y,z]}` — that's where 9Bs hallucinate).
- **No cheating, structurally:** the model only ever receives the rendered RGBA frame; ASTRA's speech is generated from what's *visibly* in the screenshot, not from telemetry — which is the c-bounded/honest-perception discipline enforced by construction.

---

## 6. The real risk: monocular depth — and its fixes

Both red-teams converged here, and it overturns the brief's stated worry. **Latency is not the problem; depth is.** A 9B looking at one 512px frame of grey rocks on black **genuinely cannot disambiguate a small near rock from a large far rock** — they project identically. Slowing down does not fix this. Worse, the naive designs make it *worse* by giving every rock a random radius (`5–60m`), destroying the one monocular cue (apparent size).

**Mandatory rendering fixes (this is make-or-break, not polish):**

1. **Distance fog / shading:** nearer rocks render brighter and larger → gives an absolute-ish depth read.
2. **Radius–distance correlation:** place larger rocks farther away so apparent size disambiguates range (the inverse of the naive "random radius" that aliases depth).
3. **Forward reticle / HUD framing:** a faint fixed reticle gives the model stable visual grammar to reason against.
4. **Looming across the cadence:** a near rock grows fast between 5s frames, a far one barely changes — so the prompt should reason from the *delta* (feed a told-history or the prior frame, not one isolated image).

With these, a 9B can plausibly answer "which side has the bigger gap" — which is all the strategy layer needs. **Without them, it flies into rocks from genuine depth aliasing, and that reads as a false "9B can't steer."**

---

## 7. The procedural asteroid field (the hard-won design)

The naive "clone starfield's LCG + spawn-ahead/recycle-behind" works as scaffolding but **breaks under adversarial load** in five ways the red-team enumerated. The corrected design:

**Use a fixed-world-lattice spatial hash, not a sequential ship-relative LCG.** Asteroid attributes (`exists?`, jittered position, radius, tumble axis/rate, albedo) = `hash(master_seed, floor(world_pos / cell_size))`. This fixes the three real failure modes at once:

- **Heading-change re-tessellation collision** (the true "impossible situation," not spawn-on-origin): if placement is keyed to the *current flight axis*, a turning ship makes a lateral-far rock become along-near *inside* the reaction window. A fixed world lattice doesn't move when the ship turns → no manufactured collisions on hard turns.
- **Reproducibility vs unpredictability conflict:** a sequential LCG consumed per-rock makes identity depend on how many `next()` calls preceded it → depends on the whole (pilot-co-produced) trajectory → **not** bit-reproducible for CI. A spatial hash is deterministic for *any* scripted trajectory: same seed = bit-identical field, new seed = wholly new field, and the pilot's steering still produces a unique rock-sequence per run.
- **"Guaranteed clear lane" is a local check masquerading as global:** per-slab nearest-neighbor rejection guarantees local non-overlap, **not a connected, monocularly-visible through-line** (gaps can staircase faster than the ship can slalom, or sit visually occluded behind a nearer rock). Fix: **carve a swept reachable corridor** — reject any rock within `(ship_radius + margin)` of the union of trajectories reachable under `max_turn_rate × closing_speed` over the next ~3 vision cycles — a *tube*, not a plane — then confirm the gap is un-occluded from the canonical camera with the existing `pixel_sampler`.

**5s cadence is a kinematic constraint, not a free knob to ignore:** choose `closing_speed`, `spawn_horizon`, `corridor_width`, `max_lateral_accel` so that **(rock detectable ≥12px for ≥3 vision cycles ≈ 15s)** AND **(lateral gap > ship_radius + 5s dead-reckoning drift + cross-velocity-null distance)** both hold. Solve the inequality; don't wish "Passengers-slow" into navigability.

**The treadmill is the right mental model:** there is no ship-position integrator in the engine — the ship sits at origin and the world flows past (`asteroid.z += closing_speed·dt`, recycle behind). So "how far does the ship drift in 5s" is *whatever you set closing_speed to.* That single free parameter is what makes the loop honest.

---

## 8. Voice

Deferrable behind a text console — **prove the vision+autopilot loop first.** All C/C++ per Language Discipline (the agents' stray "Coqui/Bark" mentions are superseded by canon):

- **Cut 1 (no voice):** ASTRA "talks" as an **ImGui caption box** rendering her speech line from the same vision call. Delivers the felt "she talks about what she sees" with zero audio subsystem.
- **TTS out (do first when adding voice):** **Piper-TTS** or sherpa-onnx (C/C++ exe) reads her speech channel to the default device.
- **ASR in (do second):** **whisper.cpp** push-to-talk → transcript injected as `operator_text` into the *next* vision turn (so "what do you see?" is answered from the current frame — honoring c-bounded epistemology).

---

## 9. Build order — de-risked, day-0 spike first

```
DAY 0  (≈1 hour)  ── THE GO/NO-GO SPIKE ──────────────────────────────
  30-line C++ curl harness. Hand-capture a few F12 PNGs of the existing
  starfield+hull scene. POST each (base64 image_url) to a local
  Qwen-3.5-9B-vision llama-server. Confirm it returns sane spatial
  steering JSON for a test asteroid frame.
  ↳ This retires the ONLY true unknown (does llama.cpp serve Qwen vision
    over image_url + can a 9B do the spatial reasoning) before any game
    code. If it fails → it's a measured finding (degrade vision-only to
    27B, or widen the corridor), not a wasted build.

CUT 1  (~1 week)  ── THE FELT LOOP, NO VOICE ─────────────────────────
  • ONE finite STATIC field (~150 rocks, ~2km tunnel) with a hand-carved
    S-curve lane (place, then delete any rock in the swept corridor of a
    pre-authored bezier; verify once with pixel_sampler that the lane
    reads open from the cockpit). Fly it in 60–90s = the Passengers shot.
    [Static first — it exercises the entire load-bearing unknown without
     the streaming-procgen failure modes.]
  • C++ vision sidecar (off-thread) + two-rate control (heading-trim +
    reflex brake). Discrete action output.
  • Depth cues: distance fog + radius-distance correlation + reticle.
  • ASTRA speaks as ImGui text. Third-person camera (cleaner obstacle
    signal). Thin vision sysprompt addendum.

CUT 2  (~3–6 days)  ── ENDLESS + POLISH ──────────────────────────────
  • Cockpit camera + the C-key toggle.
  • Fixed-world-lattice spatial-hash streaming field + swept-corridor
    carve (the §7 design) — now that vision-steering is proven.
  • Headless "did-she-steer-to-the-gap" assertion (reuse pixel_sampler).

CUT 3  (~1 week)  ── VOICE ───────────────────────────────────────────
  • Piper TTS out, then whisper.cpp ASR in.
```

**Effort:** text-narrated felt loop **~2–3 focused weeks**; voiced **~3–4 weeks**. The single biggest time sink is *not* code — it's **prompt/render iteration to get the 9B reliably steering** (fog + reticle + discrete actions + corridor tuning). Budget for it.

---

## 10. Risk register

| Risk | Severity | Mitigation |
|---|---|---|
| **llama.cpp serving Qwen-vision over `image_url`** (mmproj/flags, version-sensitive, unproven on this machine) | **High / schedule** | The **day-0 spike** — prove it standalone before any scene code. Endpoint-agnostic sidecar = swap endpoints if the local build is flaky. |
| **9B monocular depth / spatial competence** (the real "can it steer?") | **High** | §6 depth cues are *mandatory*; discrete action output; the deterministic brake means a bad call never crashes. If it still fails → degrade vision-only to 27B (the project's "9B-is-the-floor" logic: a specific 9B-vision failure is a real bench finding, not a dead end). |
| **Single-GPU contention** (renderer + 9B-vision prefill + ASR + TTS) | Medium | Vision is **bursty** (every 5s, off-thread, dead-reckoned) so renderer FPS only dips during the ~2–3s prefill, invisibly to control. The real thing to **measure** is VRAM high-water on the 24GB floor — this *is* the project's existing E2 contention gate. Comfortable on 32GB. |
| **Procgen "impossible situations"** (boxed-in, turn-induced) | Medium | Static carved field in cut 1; spatial-hash + swept-corridor carve in cut 2 (§7). |
| **"MVP" that's secretly a research problem** | Honest flag | The day-0 spike + cut-1 static field convert the unknown (9B closed-loop spatial competence) into a measured result in days, instead of discovering it mid-build. |

---

## 11. Why this matters for ASTRA-7 (strategic)

This is not a side-quest. ASTRA-3:

1. **Instantiates ASTRA-7's central architecture** (slow stochastic Mind + fast deterministic Reflex) at minimum scale — the two-rate autopilot *is* the Mind/Reflex contract, and the honest-perception / endogenous-exogenous / c-bounded disciplines fall out naturally.
2. **De-risks the project's single largest unmeasured variance** — vision + inference-under-render-contention (the E2 gate) — in the cheapest possible vehicle, on attainable hardware, exactly where the project's roadmap says the unknown lives.
3. **Is a genuinely shippable, fun artifact on its own** — a screensaver with a mind, a Passengers-drift you can talk to. It could stand alone as a public proof-of-life that seeds the whole "autotelic local-AI" form long before the full game.
4. **Ports forward:** the loop logic (two-rate control, the vision contract, the procgen, the persona) migrates to UE5 when Track B is ready; only the render host changes. Nothing here is throwaway.

---

## 12. Open decisions for the operator

1. **Engine:** ratify "extend the C++ visualizer" (recommended) vs the UE5 dissent.
2. **The day-0 spike:** green-light the 1-hour Qwen-vision proof before anything else (strongly recommended — it gates everything).
3. **Vision feed camera:** pin the LLM's feed to a fixed **forward** view (stable visual grammar) even while the player admires the third-person chase cam — recommended.
4. **Naming / repo placement:** is ASTRA-3 a sibling folder (`C:\ASTRA-7\ASTRA_3\`) reusing the visualizer, or a fork? (Recommend a new folder that depends on the visualizer's `src/` as a library, so the testbed stays a clean physics artifact.)
5. **Scope of cut 1:** confirm the cuts — third-person only, no voice, static field, distance-check "collision" — as the honest thinnest slice.

---

## Appendix A — Provenance

Synthesized 2026-06-15 from a single `Workflow` fan-out (run `wf_fa8d098f-f8e`, 16 agents, ~1.35M subagent tokens, 284 tool-uses, ~9.5 min):
- **9 recon readers** (Explore agents) over the visualizer renderer/bodies/build-capture, the textverse LLM client / perception loop / grammar+tools, the ASTRA persona, the UE5 `ASTRA_AUDIO` shell, and the autopilot/voice brainstorm material.
- **4 path designers:** extend-C++-visualizer, UE5-native, thinnest-visualizer-slice, engine-agnostic core-loop mechanic. (3 of 4 → visualizer.)
- **3 red-teamers:** vision-autopilot reality, procedural-no-cheat field, scope-and-fastest-path. (All three → *works-with-constraints*.)

## Appendix B — Key files (for whoever builds it)

```
ASTRA_VISUALIZER_02/src/app/application.cpp     main loop; F12 capture (494–513); set_pose (48–51)
ASTRA_VISUALIZER_02/src/app/camera.h            set_pose(position, target) — the camera toggle primitive
ASTRA_VISUALIZER_02/src/validation/screenshot.* read_framebuffer_rgba8 / save_png_rgba8 — the vision feed
ASTRA_VISUALIZER_02/src/scenes/scene_base.h     SceneRenderParams.ship_velocity_xyz[3] — steering input
ASTRA_VISUALIZER_02/src/renderer/starfield.*    seeded LCG (16–21) + VAO/VBO pattern to clone for asteroids
ASTRA_VISUALIZER_02/src/renderer/hull.*         procedural ship body, reuse as-is
ASTRA_VISUALIZER_02/src/validation/pixel_sampler.*  headless "did-she-steer-to-the-gap" assertions
proto/textverse/astra/llm/client.py             reference OpenAI-compat shape (text-only — borrow, don't patch)
proto/textverse/astra/grammar/parser.py         STAGE channel contract (think/tool/speech/silence) to mirror in C++
docs/astra-sysprompt.md                         ASTRA voice canon for the thin vision addendum
ASTRA_AUDIO/Source/AstraAudio/AstraVoyageActor.cpp   the UE5-path template, if the dissent is ever taken
```

*Brainstorm only. The fastest line from the current repo to "a ship drifts through procedural asteroids, a 9B vision model visibly steers it, and ASTRA talks about what she sees" is: prove the vision endpoint in an hour, carve one static lane in a week, then make the field endless. The watching scales down without breaking.*
