# PROPOSAL — Standalone Visual Physics Testbed for ASTRA-7

**Date:** 2026-05-16
**Status:** PROPOSAL (not canon; for operator review)
**Author:** Claude Opus 4.7 (1M context window; brainstorm + design pass)
**Read-only inputs:** `docs/spec-v0.129-tentative-2026-05-16.md`, `proto/astra_nexus.cpp`, prior DISCOVERY + AUDIT + TECHDIVE docs in this repo
**Output target:** another coding agent who will build the testbed from this spec without re-reading the full corpus

---

## 0. What this document is

ASTRA-7's `proto/astra_nexus.cpp` is a 1009-line C++ binary with 48-66 assertions proving the 14-equation framework math works at the *mathematical* level — console output, PASS/FAIL counters, voyage-demo tables. It validates that numbers are correct.

**It does not validate that the MATH MAPS TO THE INTENDED VISUAL PHENOMENA.**

The intended phenomena include:
- A violet warp bubble whose shape comes from the CFD-RBF field
- Geometric lensing of starlight through the warp gradient (∇W ray deflection)
- A Cherenkov cone at v_app > c with `cos θ_c = 1/(n·β)`
- A visible warp wake — metric_shift residual trailing behind the ship as it moves
- Retarded-time orbit reversal — a planet behind the ship appearing to run backward at v_app > c
- Doppler-shifted starfield colors at relativistic STL velocities
- Geometric lensing through a gravity well (separate from warp lensing)
- Chaos PDE instability at the bubble boundary, visible as particle artifacts
- Reflex stabilizer's effect on chaos amplitude (when warp engaged)
- Photon-source-history bound: at sustained v_app > c, a source becomes **gone** (not faded; gone)
- Hubble-horizon decoupling: bodies beyond `c/H₀` rendered frozen at horizon-cross
- Time-dilation indicator (composition rule output: dτ_ship / dt_cosmic)

**This proposal designs a Windows-11 standalone .exe that renders all of these visually so a human can see whether the math produces the right phenomena, BEFORE committing months of Phase E work to UE5 integration.**

The testbed is **engine-agnostic** — no Unreal Engine. Pure C/C++/CUDA + OpenGL + GLFW + Dear ImGui. The goal: confirm at the math-and-graphics level that the spec's commitments render correctly. UE5 integration testing is a separate, downstream step (per `DISCOVERY_2026-05-16_TECHDIVE_UE5.md`).

The testbed reuses `proto/astra_nexus.cpp` as its physics math library — the same code that passes the 48-66 assertions becomes the math behind the visuals. **If the testbed shows the wrong visuals, that's a finding** (either the math is missing something the spec wants, or the math is right and the spec needs a different formula).

This document is the design spec another coding agent will implement against. It explains WHAT to build, WHY each choice, and WHAT to render so the human eye can verify the math.

---

## 1. Scope: what gets tested visually

### 1.1 Phenomena IN scope

Per v0.128 + v0.129 spec content, render and visually verify:

| # | Phenomenon | Spec source | Acceptance criterion |
|---|---|---|---|
| P1 | Hull (the ship body) | §1.3 | Hull mesh / SDF visible at world origin (ship-at-origin per §1.1) |
| P2 | Warp bubble (CFD-RBF field) | §6 sample_warp_field_unified | Violet/blue volumetric glow with sharp boundary at high \|∇W\|; shape comes from RBF network |
| P3 | Warp wake / trail | §3.6 spatial update + §6 | Trailing residual of metric_shift behind ship as it moves; decays over τ_ship |
| P4 | Geometric ray-deflection (warp lensing) | §3.4 + §6 step 9 | Stars visibly bent around bubble; Einstein-ring at the visual periphery of the bubble |
| P5 | Cherenkov cone | §6 step 10 + §6.1 | Forward-projecting blue-cyan cone when n·β > 1; cone angle narrows as W increases |
| P6 | Chaos field χ(x,t) | §7.1 Fisher-KPP | Particle visualization at high-χ voxels; intensity tracks α_eff |
| P7 | Doppler / aberration on starfield | §3.4 SR Doppler | Stars redshift (recede)/blueshift (approach) by ship velocity; aberration warps forward |
| P8 | Retarded-time orbit reversal | §3.11 + §6.3 | Body 1 ly behind ship at WARP_CRUISE 2c: visible Kepler orbit running BACKWARD at 1x |
| P9 | Photon-source-history bound | §3.11 | At sustained v_app > c, source becomes ABSENT (no afterimage, no dim) |
| P10 | Hubble-horizon decoupling | §3.12 | Body beyond `c/H₀`: rendered frozen at horizon-cross instant, dimming over separate timescale |
| P11 | Metric redshift (color shift) | §3.4 + §6 step 11 | λ_obs = λ_emit · (1 + z_total); spectral color shift visible on bodies and starfield |
| P12 | Gravitational time dilation indicator | §3.2 composition rule | UI shows real-time dτ_ship/dt_cosmic value; updates with regime + state |
| P13 | Regime state machine | §3.3 | UI shows current regime (REST / STL_NONREL / STL_REL / WARP_CRUISE / etc.) and bitmask hex |
| P14 | Reflex control vector | §2.3.1 (v0.129) | UI shows nacelle_damping, conformality, emergency_dump; visual: chaos amplitude tracks control |
| P15 | Cherenkov cone snap at warp engagement | §3.11 perceptual-snap | At the moment v_app passes c, visible discontinuity in rear-view (apparent_rate flips from + to −) |

### 1.2 Phenomena OUT of scope (not in testbed)

| Phenomenon | Reason |
|---|---|
| LLM persona / ASTRA's voice | Track A (textverse); orthogonal to visual physics |
| Hull damage map writes | §1.3 surface writes; visual but not necessary for math validation |
| Audio synthesis (5 layers per §8.3) | Separate audio test would be a sibling testbed; not visual |
| MetaSound graph evaluation | UE5-specific; not testable engine-agnostically |
| Ship interior navigation / cabin geometry | UE5 nav-mesh territory; not physics |
| TTS / ASR | LLM-coupled; out of scope |
| Multiplayer / network | Privacy Contract §4.8 — no network anyway |
| Full Solar System physics | We need ~5-10 bodies for testing, not a planetarium |
| Save-file persistence | Not a visual concern; out of scope for testbed |
| REEL retrieval | LLM-coupled; out of scope |
| Sculptor research loop | LLM-coupled; out of scope |

### 1.3 Implementation language and platform constraints

Per CLAUDE.md hard directives (2026-05-15):

- **Language:** C++17+, C, CUDA, GLSL (shaders). NO Python in new code anywhere in this testbed. CMake is permitted as build-data.
- **Platform:** Windows 11 primary (x64 + RTX 30/40/50-series NVIDIA). Linux x86_64 acceptable second target. NO Apple/Mac/Metal/iOS/Swift/Objective-C anywhere.
- **Graphics API:** OpenGL 4.6 core profile (NOT Metal; Linux + Windows portable). CUDA-OpenGL interop is mature and well-documented. Vulkan acceptable as future Linux fallback if OpenGL deprecates.
- **No engine dependency:** no Unreal Engine, no Unity, no Godot. The testbed is a standalone executable.
- **Permitted third-party libs (all BSD/MIT or equivalent permissive):**
  - GLFW 3.x — windowing + input (Apple-tolerant code paths in dep are ignored; we don't build/ship for Apple)
  - glad 2.x — OpenGL extension loader
  - Dear ImGui (docking branch) — debug UI
  - glm — header-only math (GLSL-style C++ vectors/matrices)
  - stb_image / stb_image_write — PNG screenshot capture
  - nlohmann/json — config + scenario file parsing
  - tiny-cuda-nn (optional v2) — if hash-grid SDF is needed; can skip for v1
- **Build system:** CMake 3.24+ with FetchContent for dependency management.

### 1.4 What this testbed is NOT trying to be

- Not photorealistic. We render the math; quality is secondary to correctness.
- Not optimized for very low-end hardware. RTX 3060 is the minimum target; 4070+ recommended.
- Not a game. No win conditions, no progression, no persistence between sessions.
- Not a UE5 plugin. The eventual UE5 plugin (per TECHDIVE doc) is a separate effort.
- Not a finished product. It's a diagnostic instrument: built to test, viewed by humans, then evolved as the math evolves.

---

## 2. Why this matters (the empirical anchor)

Per spec §15.4 ("revise on findings"), the testbed surfaces findings that the math-only assertion suite cannot:

**Finding class 1 — Visual phenomena that need additional math.** The 48-66 C++ assertions don't compute Cherenkov; the 5D-F4 audit finding noted "Cherenkov formula locked at 4 spec sites, 0 code sites." The testbed will demand the Cherenkov implementation; running it will surface whether the formula `cos θ_c = 1/(n·β)` produces a visually-correct cone (and what n(W) function works).

**Finding class 2 — Math right, visuals wrong.** If `apparent_rate = 1 − v_app/c` produces correct numerics at scenario points (−9 at v_app=10c per the test suite) but visually the planet's orbit reversal looks WRONG to the human eye, that's a spec-level finding: maybe the orbit reversal needs an additional damping term, or maybe the user-facing rendering needs a different mapping.

**Finding class 3 — Math right, math missing.** The visual warp wake (P3) is not in the spec. If it's visually compelling AND physically motivated (the metric_shift residual from the ship's prior positions), the spec should add it. If it's neither, the spec stays silent.

**Finding class 4 — Spec-internal inconsistency.** The Eye-Ear Decoupling (§8.3 endogenous-audio vs §6.3 exogenous-visual at warp egress) has been treated as a "feature, not a bug." But until the testbed makes it visually concrete (rear-view shows planet running backward; audio frequency display shows current warp drone with no delay), the operator can't *see* whether the decoupling is the intended experience or whether it's jarring in a way that breaks immersion.

**Finding class 5 — Closing the audit gap from a different direction.** AUDIT_2026-05-15 noted the C++ binary's stdio_server has limited ops; v0.129 already adds 5 of 6 needed for Narrator-LLM. The testbed validates THE SAME `astra_nexus.cpp` API surface, but from the graphics-rendering direction. If both Narrator (LLM-side) and Testbed (graphics-side) consume the same ops cleanly, that's two-direction conformance verification.

**Per §15.4: this testbed IS a closed loop measurement.** Not the same closed loop as the bench (textverse's LCP gates); a parallel one (visual conformance gates).

---

## 3. Tech stack with explicit rationale

### 3.1 Why OpenGL not Vulkan or DirectX 12

OpenGL 4.6 core profile is the right choice for THIS testbed because:

- **Maturity**: well-documented, stable, predictable behavior.
- **Cross-platform**: works on Windows + Linux from one codebase.
- **CUDA interop**: `cudaGraphicsGLRegisterBuffer/Image` is the mature, well-trodden path; bug-free in 99% of CUDA versions; documented in CUDA programming guides since CUDA 4.x.
- **Simplicity**: ~50 LOC of GL setup + ~30 LOC of CUDA interop boilerplate; vs ~500 LOC for equivalent Vulkan or DX12 setup.
- **Compute shaders**: OpenGL 4.3+ supports compute shaders for non-CUDA compute work (debug overlays, post-process).
- **Engine-agnostic alignment**: avoids implying any UE5-side choice. UE5 will be DX12-CUDA (per §8.1) but the math validation doesn't need that.

NOT Vulkan because: complexity overhead is wrong for a diagnostic tool that should be implementable in ~2 weeks by a single agent. We're testing physics, not the rendering API.

NOT DirectX 12 because: Windows-only (closes off the Linux secondary target unnecessarily) and complexity rivals Vulkan.

NOT WebGPU because: still maturing as of May 2026; toolchain overhead high; CUDA interop story poor.

### 3.2 Why GLFW not SDL

GLFW is the right choice because:
- Lightweight: 1 dependency, minimal footprint.
- Focused: just windowing + input + OpenGL/Vulkan context. No audio, no networking, no joystick complexity we don't need.
- Cross-platform: Windows + Linux + (we don't ship for Mac but the lib supports it harmlessly).
- Well-supported: used by Dear ImGui's example backends.
- Permissive license (zlib).

SDL is more featureful but the features are not needed.

### 3.3 Why Dear ImGui

The de facto standard for graphics tooling UI:
- Immediate-mode (matches our per-frame physics loop)
- Renders via OpenGL backend cleanly
- Docking branch gives us multi-panel layout (left panel sliders, right panel state display, top bar scenarios)
- MIT licensed, no runtime data
- Industry standard (RenderDoc, NVIDIA Nsight, every CUDA debug tool)

No competitor at this scope.

### 3.4 Why CUDA for physics

Per spec + CLAUDE.md:
- CUDA is mandated for GPU compute (NVIDIA-only acceptable; per Platform Discipline).
- The chaos PDE step and warp-field sampling are CUDA-native in the eventual UE5 build (per TECHDIVE §5).
- Testing with CUDA NOW means the same kernels port directly to UE5's CUDA-DX12 interop later.

Pure-OpenGL-compute-shader alternative: would work but doesn't validate the CUDA pipeline. Testbed should use the actual CUDA kernels that UE5 will eventually use.

### 3.5 Why CMake + FetchContent

- CMake is permitted per Language Discipline ("CMake is the only acceptable build system that has Python adjacency, treated as data, not as a Python runtime dependency").
- FetchContent (CMake 3.11+) eliminates manual third-party setup. Reproducible builds.
- Works with MSVC (Windows) and gcc/clang (Linux).
- No vendoring of source code; everything pulled fresh per repo clone.

### 3.6 Permitted vs forbidden dependencies (explicit list)

**Permitted (canonical):**
- GLFW (windowing) — zlib license
- glad (GL loader) — public domain
- Dear ImGui (UI) — MIT
- glm (math) — MIT
- stb_image / stb_image_write — public domain
- nlohmann/json — MIT
- CUDA Toolkit 12.x — NVIDIA proprietary but runtime-redistributable
- tiny-cuda-nn (OPTIONAL v2 if hash-grid SDF needed) — BSD
- Catch2 (unit tests) — BSL-1.0
- doctest (alternative to Catch2) — MIT
- libpng / libjpeg (if PNG read is needed beyond stb) — libpng/IJG licenses
- Eigen (optional, for any linear algebra beyond glm) — MPL2

**Forbidden:**
- Python anywhere (Language Discipline)
- Apple/Mac/Metal-specific code (Platform Discipline)
- Boost (too heavy for this scope; not forbidden but discouraged)
- Qt (UI library; ImGui is the right choice)
- ANY rendering engine: Unreal, Unity, Godot, Bevy, etc.

---

## 4. Architecture and module layout

```
warp_testbed/
├── CMakeLists.txt
├── README.md
├── BUILD.md
├── third_party/                            # CMake FetchContent populates
│   └── (auto-fetched: glfw, glad, imgui, glm, stb, nlohmann_json)
├── src/
│   ├── main.cpp                            # GLFW window + scenario loop entry
│   ├── app/
│   │   ├── application.cpp                 # App lifecycle, scenario controller
│   │   ├── application.h
│   │   ├── scenarios.cpp                   # 12 predefined scenarios
│   │   ├── scenarios.h
│   │   ├── camera.cpp                      # Free-fly + scenario-locked camera
│   │   ├── camera.h
│   │   ├── input.cpp                       # Keyboard + mouse handling
│   │   ├── input.h
│   │   ├── time_step.cpp                   # Sim time vs wall time decoupling
│   │   └── time_step.h
│   ├── render/
│   │   ├── opengl_ctx.cpp                  # GL context setup, GLAD init
│   │   ├── opengl_ctx.h
│   │   ├── shader.cpp                      # Shader compile/link/uniforms
│   │   ├── shader.h
│   │   ├── volume_renderer.cpp             # Warp + chaos volume ray-march
│   │   ├── volume_renderer.h
│   │   ├── starfield.cpp                   # Point-sprite stars with Doppler
│   │   ├── starfield.h
│   │   ├── cherenkov.cpp                   # Cherenkov cone billboard
│   │   ├── cherenkov.h
│   │   ├── lensing.cpp                     # Geometric lensing post-pass
│   │   ├── lensing.h
│   │   ├── hull.cpp                        # Hull mesh / SDF render
│   │   ├── hull.h
│   │   ├── trail.cpp                       # Warp wake trail (P3)
│   │   ├── trail.h
│   │   ├── retarded_body.cpp               # Per-body retarded-time render
│   │   ├── retarded_body.h
│   │   ├── overlays.cpp                    # Debug: RBF nodes, ∇W arrows, regime
│   │   ├── overlays.h
│   │   └── interop.cpp                     # CUDA-OpenGL shared resource lifecycle
│   │   └── interop.h
│   ├── physics/
│   │   ├── astra_nexus_bridge.cpp          # Link with proto/astra_nexus.cpp
│   │   ├── astra_nexus_bridge.h
│   │   ├── chaos_pde.cu                    # Fisher-KPP step
│   │   ├── chaos_pde.h
│   │   ├── warp_field.cu                   # CFD-RBF eval + ∇W computation
│   │   ├── warp_field.h
│   │   ├── rbf_network.cpp                 # RBF data; modulation
│   │   ├── rbf_network.h
│   │   ├── reflex_stub.cpp                 # PID Reflex stub
│   │   ├── reflex_stub.h
│   │   ├── observation_calc.cu             # Per-body retarded-time on GPU
│   │   ├── observation_calc.h
│   │   ├── cherenkov_math.cpp              # cos θ_c = 1/(n·β)
│   │   ├── cherenkov_math.h
│   │   ├── wake_field.cu                   # Warp wake trail evolution
│   │   └── wake_field.h
│   ├── ui/
│   │   ├── imgui_setup.cpp                 # ImGui + GLFW + OpenGL backend wire
│   │   ├── imgui_setup.h
│   │   ├── parameter_panel.cpp             # Live tuning sliders
│   │   ├── parameter_panel.h
│   │   ├── state_display.cpp               # Physics state readouts
│   │   ├── state_display.h
│   │   ├── scenario_selector.cpp           # Top bar / hotkeys
│   │   ├── scenario_selector.h
│   │   ├── profiler.cpp                    # GPU timer queries
│   │   └── profiler.h
│   ├── data/
│   │   ├── cfd_synthesizer.cpp             # Synthesize analytic Alcubierre RBF network
│   │   ├── cfd_synthesizer.h
│   │   ├── hull_loader.cpp                 # Load OBJ or procedural box
│   │   ├── hull_loader.h
│   │   ├── starfield_loader.cpp            # Generate or load star catalog
│   │   ├── starfield_loader.h
│   │   ├── scenario_loader.cpp             # Parse scenario JSON files
│   │   └── scenario_loader.h
│   └── util/
│       ├── log.cpp                         # Structured stdout logging
│       ├── log.h
│       ├── timer.cpp                       # High-res CPU/GPU timers
│       ├── timer.h
│       ├── screenshot.cpp                  # PNG capture via stb_image_write
│       └── screenshot.h
├── shaders/
│   ├── common/
│   │   ├── constants.glsl                  # Physical constants header
│   │   ├── astra_coord.glsl                # AstraCoord helper functions
│   │   ├── redshift.glsl                   # Color shift functions
│   │   └── camera.glsl                     # View/projection helpers
│   ├── volume/
│   │   ├── raymarch.vert                   # Fullscreen quad vertex shader
│   │   └── raymarch.frag                   # Warp + chaos volume ray-march
│   ├── starfield/
│   │   ├── starfield.vert                  # Point sprite with Doppler color
│   │   └── starfield.frag                  # Apparent-rate + brightness
│   ├── cherenkov/
│   │   └── cone.frag                       # Cherenkov cone overlay
│   ├── lensing/
│   │   └── post.frag                       # Geometric lensing background sample
│   ├── hull/
│   │   ├── hull.vert
│   │   └── hull.frag                       # Substrate-style hull material
│   ├── trail/
│   │   ├── trail.vert
│   │   └── trail.frag                      # Warp wake billboards
│   ├── retarded_body/
│   │   ├── body.vert                       # Per-instance Kepler-at-t_emit
│   │   └── body.frag                       # Redshift-colored body
│   └── overlay/
│       ├── arrows.vert                     # Debug ∇W arrows
│       ├── arrows.frag
│       ├── rbf_nodes.vert                  # Debug RBF center points
│       └── rbf_nodes.frag
├── assets/
│   ├── hull/
│   │   └── astra7_lowpoly.obj              # Simple low-poly hull (10K tris)
│   ├── starfield/
│   │   └── starfield_10k.bin               # 10K stars (HD-style binary format)
│   ├── scenarios/
│   │   ├── s01_rest_baseline.json
│   │   ├── s02_stl_recede_05c.json
│   │   ├── s03_stl_recede_09c.json
│   │   ├── s04_warp_charge.json
│   │   ├── s05_warp_cruise_2c.json
│   │   ├── s06_warp_cruise_10c.json
│   │   ├── s07_warp_8000c_history_bound.json
│   │   ├── s08_warp_gravity_well.json
│   │   ├── s09_chaos_instability.json
│   │   ├── s10_hubble_horizon.json
│   │   ├── s11_split_screen_stl_vs_warp.json
│   │   └── s12_eye_ear_decoupling.json
│   └── golden/                             # Reference PNG screenshots
│       ├── s01_t0.png
│       ├── s05_t5s_warp_2c.png
│       └── ... (one per scenario per significant timestamp)
├── docs/
│   ├── DESIGN.md                           # this proposal, after implementation
│   ├── SCENARIOS.md                        # detailed scenario walkthroughs
│   ├── EXPECTED_VISUALS.md                 # acceptance criteria with reference images
│   ├── BUILD.md                            # Windows 11 build instructions
│   └── KNOWN_ISSUES.md                     # findings surfaced by testbed runs
├── tests/
│   ├── CMakeLists.txt                      # Catch2 unit tests
│   ├── test_warp_field.cpp                 # CUDA kernel unit tests
│   ├── test_chaos_pde.cpp
│   ├── test_cherenkov_math.cpp             # Validates 5D-F4 implementation
│   ├── test_observation_calc.cpp
│   ├── test_reflex_stub.cpp
│   └── test_rbf_network.cpp
└── tools/
    └── golden_diff.cpp                     # PNG diff for regression checks
```

**Module count:** ~30 C++ files + ~15 CUDA files + ~20 shader files + 12 scenario files. Estimated total: ~8,000-10,000 LOC.

**Build target:** single executable `warp_testbed.exe` (Windows) or `warp_testbed` (Linux). Plus optional `warp_testbed_tests.exe` for the Catch2 unit tests.

---

## 5. Test scenarios (the 12 visual gates)

Each scenario is a JSON file under `assets/scenarios/`, loaded via `scenario_loader`. The runtime exposes scenarios via top-bar UI selector + hotkeys 1-9 + Shift-1, Shift-2, Shift-3.

Each scenario has:
- `name`: short identifier
- `description`: 1-2 sentence purpose
- `initial_state`: regime, ship pose, body list, BH list, warp state
- `script`: sequence of `{at_time_seconds: ..., action: ...}` events
- `camera`: free / locked to specific viewpoint
- `expected_visuals`: list of acceptance criteria (for human review)

### S01 — REST baseline (sanity check)

**Initial state:** REST regime, W=0, ship at origin, one Earth-like planet 1 AU in +z, sun at +y.

**Script:** no events; runs free.

**Camera:** orbiting third-person around ship, ~50m away.

**Expected visuals:**
- Hull visible (gray composite material per Substrate aesthetic from memory/hull_design_v0.md)
- Sun visible as yellow point with halo
- Earth visible as blue dot at ~1 AU
- Starfield (10K background stars) static
- UI: regime label "REST"; dτ_ship/dt_cosmic = 1.0; γ = 1.0; W = 0
- No warp visual, no Cherenkov, no chaos

**Validates:** baseline render works; nothing breaks at trivial state.

### S02 — STL_REL recede at β=0.5

**Initial state:** STL_REL, ζ⃗ = (0, 0, atanh(0.5)) ≈ (0, 0, 0.5493), so β=0.5 in +z, γ=1.155.

**Script:** no events; coast at constant velocity.

**Camera:** ship cockpit looking backward (-z); planet behind ship.

**Expected visuals:**
- Planet behind appears redshifted (warm color); SR longitudinal Doppler `z_kin = √3 − 1 ≈ 0.732`
- Stars in rear view redshifted; stars in forward view (if camera flips) blueshifted
- Mild aberration (stars compressed toward forward direction)
- UI: regime "STL_REL"; γ=1.155; dτ/dt = 1/γ = 0.866; z_kin display = 0.732
- No warp visual

**Validates:** SR Doppler color math; aberration not gross; redshift composition.

### S03 — STL_REL recede at β=0.9

**Initial state:** ζ⃗ z-component = atanh(0.9) ≈ 1.472; γ = 2.294; β=0.9.

**Script:** none; constant.

**Camera:** ship cockpit, rear view.

**Expected visuals:**
- Planet behind dramatically redshifted (deep red); `z_kin = √19 − 1 ≈ 3.359`
- Most stars compressed into forward hemisphere (aberration)
- Rear stars mostly invisible (redshifted to IR)
- UI: γ=2.294; dτ/dt=0.436

**Validates:** more dramatic SR effects; aberration visible.

### S04 — Warp charge sequence

**Initial state:** REST, W=0, planet 1 AU behind in -z.

**Script:**
- t=0: regime → WARP_CHARGE (warp.phase = "charging")
- t=0..5s: W ramps linearly 0 → 1, charge_progress 0 → 1
- t=5s: regime → WARP_CRUISE (warp.phase = "cruising"); v_app = 2c

**Camera:** orbiting third-person, sees ship + bubble form.

**Expected visuals:**
- Bubble fades in around ship: starts as faint violet glow, grows in intensity + radius
- By t=5s: bubble fully formed at ~120m radius (CFD-RBF extent)
- Chaos field activates: faint particle artifacts at bubble boundary
- Cherenkov cone NOT YET visible (W still ramping; cos θ_c condition not met until t=5)
- UI: regime transition WARP_CHARGE → WARP_CRUISE; W ramps 0→1
- After t=5s: bubble stable; per-frame chaos modulation visible as subtle shimmering

**Validates:** warp charge ramping; bubble visualization; phase transition; chaos modulation.

### S05 — Warp cruise at v_app = 2c (orbit reversal moment)

**Initial state:** WARP_CRUISE, W=1, v_app=2c in +z, planet 1 ly behind in -z with Kepler orbit (1-year period).

**Script:** none; coast at 2c.

**Camera:** ship cockpit, rear view (-z) showing planet.

**Expected visuals:**
- Bubble stable around ship
- Planet visible behind, but its Kepler position is being sampled at t_emit
- Per spec §3.11: `apparent_rate = 1 - v_app/c = -1` → planet's orbital phase decreases monotonically
- Over 30 seconds wall-time, planet should make ~30/12 ≈ 2.5 days of REVERSE orbit motion (1 ly behind; sample at t_emit goes backward)
- **The visible orbit reversal is the canonical test of the retarded-time math**
- UI: regime "WARP_CRUISE"; v_app = 2c; apparent_rate = −1.000

**Validates:** retarded-time observation; Kepler-at-t_emit; visible time-reversal.

### S06 — Warp cruise at v_app = 10c (dramatic reversal + Cherenkov)

**Initial state:** WARP_CRUISE, W=1, v_app=10c in +z, planet 1 ly behind.

**Script:** none.

**Camera:** rear view + side view split.

**Expected visuals:**
- Planet's orbital phase runs BACKWARD at 9× speed (`apparent_rate = -9`)
- Cherenkov cone NOW visible: cos θ_c = 1/(n·β) gives a real angle; cone forward-facing
- Bubble is dimmer than at 2c (because all bodies redshifted toward extinction)
- UI: apparent_rate = −9.000; Cherenkov angle in degrees displayed

**Validates:** Cherenkov rendering (THIS IS THE 5D-F4 GAP); high-warp orbit reversal; multi-effect composition.

### S07 — Warp cruise at v_app = 8000c (photon-source-history bound)

**Initial state:** WARP_CRUISE, W=1, v_app=8000c in +z, planet 1 ly behind with t_source_start = "1000 cosmic-years ago" relative to scenario start.

**Script:** none; ship pulls away at 8000c.

**Expected visuals:**
- Initially planet visible (still receiving photons emitted in recent past)
- As scenario progresses (~few seconds wall time), `t_emit` decreases by 8000× the scenario clock
- After ~0.125 cosmic-years of t_emit retreat (1000/8000 cosmic-years), `t_emit < t_source_start`
- Planet becomes GONE (clean disappearance, no fade, no afterimage)
- UI: `beyond_photon_history = true` triggers; planet rendering culled

**Validates:** photon-source-history bound (§3.11); the "source is gone, not faded" rendering decision.

### S08 — Warp + Gravity Well composition

**Initial state:** WARP_CRUISE at v_app=2c, W=0.8, ship at r=200·r_s from a 10·M_sun BH.

**Script:** ship gradually approaches BH (closing on r ramp from 200·r_s to 150·r_s over 30s).

**Camera:** side view showing ship, BH, and bubble.

**Expected visuals:**
- Bubble visible
- BH visible as black disc with subtle gravitational lensing of background stars
- Bubble shape distorts toward BH as ship approaches (the warp interacts with gravity)
- Chaos α_eff scaling visible: `α_eff = α_base · (1 + k·M·L²/r³)` — as r decreases, α grows, chaos field intensifies
- UI: regime "WARP_CRUISE | GRAVITY_WELL"; Schwarzschild factor displayed; α_eff displayed; composition rule output: `dτ/dt_cosmic = f_warp(0.8) · √(1−r_s/r) · 1/γ_kinematic`

**Validates:** regime composition (bitmask); gravity factor; chaos coupling; gravitational lensing (separate from warp lensing).

### S09 — Chaos instability + Reflex stabilizer

**Initial state:** WARP_CRUISE at v_app=2c, W=0.95 (near max), no BH; Reflex stub active.

**Script:**
- t=0..5s: Reflex stub DISABLED; chaos field allowed to grow unstable
- t=5s: Reflex stub ENABLED; should rapidly damp chaos
- t=10..15s: chaos induced manually (slider in UI; user-driven test of recovery)

**Camera:** close-up of bubble showing chaos particles.

**Expected visuals:**
- t<5s: chaos particles increasingly visible at bubble boundary; bubble distorts; |∇W| modulates erratically
- t=5s: chaos amplitude RAPIDLY drops; particles fade; bubble returns to clean shape
- t=10+s: when user pushes chaos slider, Reflex stub re-damps it; visible feedback loop
- UI: live chaos field RMS amplitude plot (time-series); Reflex control vector display (nacelle_damping, conformality, emergency_dump)
- If chaos exceeds critical threshold: emergency_dump triggers; visual snap to STL regime (bubble disappears in 1 frame)

**Validates:** Fisher-KPP chaos PDE; Reflex stub effectiveness; emergency dump behavior (irreversibility flag).

### S10 — Hubble-horizon body

**Initial state:** REST, ship at origin, one body at d = 1.2 · c/H₀ (beyond Hubble horizon for default H₀=70 km/s/Mpc).

**Script:** none.

**Camera:** view aimed at the distant body.

**Expected visuals:**
- Body visible but rendered FROZEN (paused frame from horizon-crossing instant)
- Body color extremely redshifted (toward IR; faintly red dot)
- Body dimming on a separate timescale (per spec §3.12 "frozen at horizon-cross instant, dim and redshifted, fading on a separate timescale than the photon-source-history bound (§3.11)")
- UI: `beyond_hubble_horizon = true`; d_proper displayed in Mpc; z_cosmo displayed

**Validates:** Hubble-horizon detection; frozen-at-horizon rendering; cosmological redshift composition.

### S11 — Split-screen STL_REL vs WARP_CRUISE at same v_radial

**Initial state:** TWO ships (or split-screen): one in STL_REL at v=0.5c receding, one in WARP_CRUISE at v_app=0.5c receding, both viewing same planet.

**Script:** none; both coasting.

**Camera:** left half = STL ship rear view; right half = WARP ship rear view.

**Expected visuals:**
- LEFT (STL_REL): planet redshifted by SR Doppler; apparent_rate = √(1/3) ≈ 0.577; planet's orbit runs FORWARD at 0.577× speed
- RIGHT (WARP_CRUISE): planet redshifted by classical Doppler; apparent_rate = 1 - 0.5 = 0.500; planet's orbit runs FORWARD at 0.500× speed
- The contrast IS the regime-distinction; both rates positive (both subluminal recession); slightly different
- UI: both rates displayed; the contrast at v_radial=0.5c is the §3.11 spec test that prevents formula conflation

**Validates:** regime-dispatched apparent rate distinction; both formulas right; per spec §10 validation row "STL_REL formula was NOT 1/γ".

### S12 — Eye-ear decoupling at warp egress

**Initial state:** WARP_CRUISE at v_app=2c, planet 1 ly behind orbiting in reverse.

**Script:**
- t=0..10s: WARP_CRUISE; planet visibly running backward
- t=10s: warp.disengage(emergency); regime → STL_REL → REST over ~3s; bubble collapses
- t=10..15s: planet's orbit reverses direction (now running forward); over ~1 ly/c = 1 year scenario time, eye-time would catch up with ear-time

**Camera:** rear view of planet + UI audio frequency display.

**Expected visuals:**
- t<10s: planet running backward in rear view; UI shows warp drone frequency (audio simulated as ImGui frequency display)
- t=10s exactly: bubble collapses; UI audio shows warp-shutdown sound (immediate change); but **planet visual still shows reverse orbit for some seconds** (because eye sees photons from earlier reverse-time samples)
- t=10..13s: visual gradually transitions from reverse-orbit to forward-orbit as t_emit catches up with t_cosmic
- UI: dual display "AUDIO (t_cosmic = NOW)" and "VISUAL (t_emit = past)" with the time-gap shrinking

**Validates:** endogenous/exogenous decoupling at the user-visible level; the eye-ear mismatch as designed feature.

---

## 6. UI design

### 6.1 Layout (using Dear ImGui docking branch)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Scenario: S05 Warp Cruise 2c ▼]  [Reset]  [Pause]  60 FPS  16.2ms │  ← Top bar
├──────────┬───────────────────────────────────────┬──────────────────┤
│          │                                       │                  │
│  PARAM   │                                       │   STATE          │
│  PANEL   │           VIEWPORT                    │   DISPLAY        │
│          │                                       │                  │
│  [slider │     (the 3D render goes here)         │  Regime: WARP_   │
│   W=1.0] │                                       │  CRUISE          │
│          │                                       │  γ: 1.000        │
│  [slider │                                       │  W: 1.00         │
│   v_app  │                                       │  dτ/dt: 0.5      │
│   =2c]   │                                       │  Apparent rate:  │
│          │                                       │    -1.000        │
│  [Reflex │                                       │  Cherenkov: off  │
│   ON/OFF]│                                       │  (n·β < 1)       │
│          │                                       │                  │
│  ...     │                                       │  Per-pass timing:│
│          │                                       │  Chaos: 0.8ms    │
│  [F12    │                                       │  Warp eval:1.5ms │
│   ScrCap]│                                       │  Lensing: 0.6ms  │
│          │                                       │  ...             │
├──────────┴───────────────────────────────────────┴──────────────────┤
│ Console: [scenario loaded: s05] [Reflex enabled] [t=15.3s sim time] │  ← Status bar
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Parameter panel (left, 280px wide)

ImGui controls:
- **Scenario** dropdown (top); 12 entries
- **Regime override** dropdown (REST, STL_NONREL, STL_REL, WARP_CRUISE, ...)
- **Warp factor W** slider (0.0 — 1.0)
- **Ship velocity β** slider (0.0 — 0.9999 for STL; v_app: 0 — 100c for WARP)
- **Ship direction** vec3 input (default +z)
- **BH mass** slider (1 — 1e8 solar masses; only used in S08)
- **BH distance** slider (0 — 1000 AU; only used in S08)
- **Reflex** toggle (ON/OFF)
- **Chaos α_base** slider (0 — 5; default 2.5)
- **Chaos D** slider (0 — 2; default 0.8)
- **Cherenkov visibility** toggle
- **Show ∇W arrows** toggle (debug overlay)
- **Show RBF nodes** toggle (debug overlay)
- **Show chaos particles** toggle
- **Camera mode** radio (free / locked / split-screen)
- **Time scale** slider (0 — 100; simulation Δt multiplier; for slow-mo or fast-fwd)
- **Pause** button
- **Reset scenario** button
- **Screenshot (F12)** button

### 6.3 State display (right, 320px wide)

Live readouts:
- **Regime label + bitmask hex** (e.g., "WARP_CRUISE | GRAVITY_WELL = 0x28")
- **TimeState**:
  - t_cosmic (seconds, monotonic)
  - τ_ship (seconds)
  - τ_crew_biological (seconds)
  - dτ/dt_cosmic (the composition rule output)
- **Kinematic state**:
  - ζ⃗ (3-vector)
  - ω = |ζ⃗|
  - γ = cosh(ω)
  - β = tanh(ω)
- **Warp state**: phase, W, charge_progress
- **For each visible body** (top 5 by salience):
  - d_proper (km or AU or Mpc as appropriate)
  - v_radial (km/s or c units)
  - z_cosmo, z_kin, z_metric, z_total
  - t_emit (relative to t_cosmic, negative = past)
  - apparent_rate
  - beyond_photon_history / beyond_hubble_horizon flags
- **Cherenkov state**: n (refractive index), β_eff, n·β, cone half-angle (deg)
- **Chaos field stats**: mean, max, RMS
- **Reflex control vector**: nacelle_damping, conformality, emergency_dump
- **Per-pass GPU timing** (cuEventRecord-based):
  - Chaos PDE step (ms)
  - Warp field SVT populate (ms)
  - Warp volume ray-march (ms)
  - Lensing post-pass (ms)
  - Starfield retarded-time (ms)
  - ImGui (ms)
  - Total (ms)

### 6.4 Console / status bar (bottom)

- Scrolling log of significant events: scenario loaded, regime transitions, Reflex emergency dumps, screenshot taken, errors
- Right-aligned: current simulation time, current scenario name

### 6.5 Hotkeys

- **WASD**: camera movement (free mode)
- **Q/E**: camera up/down
- **Mouse drag**: camera look (free mode)
- **1-9**: select scenario 1-9
- **Shift-1, Shift-2, Shift-3**: select scenarios 10, 11, 12
- **Space**: pause/resume
- **R**: reset current scenario
- **F1**: toggle help overlay
- **F2**: toggle parameter panel
- **F3**: toggle state display
- **F4**: toggle debug overlays (∇W arrows, RBF nodes)
- **F5**: hot-reload shaders (development feature)
- **F11**: toggle fullscreen
- **F12**: screenshot (saves PNG + JSON state dump)
- **Esc**: quit

---

## 7. Implementation phases for the coding agent

The coding agent should implement in this order. Each phase is ~1-3 days of work; total ~2-3 weeks for a competent single agent.

### Phase 1 — Skeleton (1-2 days)

**Goal:** window opens; renders a clear color; ImGui shows a "Hello world" panel.

**Deliverables:**
- `CMakeLists.txt` with FetchContent for GLFW, glad, ImGui, glm
- `src/main.cpp` opens GLFW window 1280×720
- `opengl_ctx.cpp` initializes GL 4.6 context via glad
- `imgui_setup.cpp` initializes ImGui with GLFW + OpenGL3 backends
- Window shows clear color (background) + ImGui "Hello, ASTRA-7 Visual Physics Testbed" panel
- Builds on Windows 11 + MSVC 2022 via standard CMake

**Acceptance:** `./warp_testbed.exe` launches; window shows; ImGui responsive.

### Phase 2 — Scene framework (2-3 days)

**Goal:** free-fly camera through empty space; hull mesh rendered; basic starfield.

**Deliverables:**
- `camera.cpp`: free-fly camera with WASD + mouse-look
- `hull.cpp`: load `astra7_lowpoly.obj`; render with simple lit shader (Blinn-Phong is fine)
- `starfield.cpp`: generate 10K random stars in spherical distribution; render as point sprites
- `time_step.cpp`: simulation time decoupled from wall time; supports pause + time-scale
- Status bar shows FPS + simulation time
- Parameter panel has Pause/Reset/Camera-mode controls

**Acceptance:** can fly camera around hull in starfield; simulation time advances; can pause.

### Phase 3 — Physics math bridge (2-3 days)

**Goal:** link with `proto/astra_nexus.cpp`; expose all math via C++ API; UI shows live composition rule values.

**Deliverables:**
- `astra_nexus_bridge.cpp/h`: compile `proto/astra_nexus.cpp` as a static lib `libastra_nexus`; expose `Rapidity`, `dtau_dt_cosmic`, `compute_apparent_rate`, `observe`, `Observable`, `Regime`, etc. as C++ API
- `state_display.cpp`: ImGui panel showing TimeState, Kinematic state, regime, composition rule output
- `parameter_panel.cpp`: sliders for W, β, ship direction; updates feed into nexus bridge
- Verify: nexus bridge produces same values as standalone astra_nexus.exe (regression test)

**Acceptance:** can change W and β sliders; state display updates live with correct math; composition rule output matches C++ nexus's expected values.

### Phase 4 — CUDA-OpenGL interop foundation (2-3 days)

**Goal:** CUDA writes to a 3D texture; OpenGL renders it as a volume.

**Deliverables:**
- `interop.cpp`: CUDA-OpenGL interop manager
  - Creates GL 3D texture
  - Registers with CUDA via `cudaGraphicsGLRegisterImage`
  - Maps + unmaps per frame
- `chaos_pde.cu`: simple Fisher-KPP step kernel; writes to the shared 3D texture
- `volume_renderer.cpp`: fragment shader that ray-marches the 3D texture and renders as a translucent volume
- Test: initialize 3D texture with sinusoid; CUDA runs Fisher-KPP for N frames; OpenGL renders evolving volume

**Acceptance:** visible evolving volume (chaos field) in the scene; no crashes; no flicker.

### Phase 5 — CFD-RBF warp field (3-4 days)

**Goal:** warp bubble renders correctly from synthesized CFD-RBF network.

**Deliverables:**
- `cfd_synthesizer.cpp`: generate ~200-400 RBF nodes analytically approximating Alcubierre f(r_s) shape function
- `rbf_network.cpp`: load/save RBF network; spatial-hash builder
- `warp_field.cu`: kernel that evaluates W(x) and ∇W(x) from RBF + spatial hash; populates 3D texture
- `volume_renderer.cpp` updates: sample warp field texture; render as violet/blue volume with extinction proportional to W; emissive proportional to |∇W|
- Parameter panel: W slider feeds into RBF weight modulation
- Scenario S04 (Warp Charge) works: bubble fades in as W ramps 0→1

**Acceptance:** S01 (REST) shows no bubble; S04 shows bubble forming; S05 (Warp Cruise) shows stable bubble.

### Phase 6 — Geometric lensing (2-3 days)

**Goal:** stars visibly bent through warp gradient.

**Deliverables:**
- `lensing.cpp`: post-process pass; for each pixel, ray-march through ∇W field accumulating deflection; sample background starfield at deflected ray direction
- Shader: full-screen pass reads gbuffer + warp 3D texture (∇W); accumulates `dir += α_lens · ∇W · Δs` over ~32 steps; samples skybox cubemap at final dir; blends with bubble color
- Parameter panel: `α_lens` slider for live tuning
- Scenario S05 + S06: lensing visible; Einstein-ring style distortion at bubble boundary

**Acceptance:** with α_lens=0, no lensing; as α_lens increases, starfield distorts around bubble; at high α_lens (~5), Einstein-ring visible.

### Phase 7 — Cherenkov cone (5D-F4 implementation) (2-3 days)

**Goal:** Cherenkov cone renders at v_app > c.

**Deliverables:**
- `cherenkov_math.cpp`: compute `n_refractive(W)` and `cos θ_c = 1/(n·β)`
- `cherenkov.cpp`: render cone as forward-facing billboard or volumetric cone mesh; angle from cherenkov_math
- Shader: cone material with intensity peaking at the angle; blue-cyan color
- Parameter panel: `n_per_metric` coefficient slider; cherenkov visibility toggle
- Scenario S06 (v_app=10c): cone visible; angle narrows as W increases

**Acceptance:** at v_app < c, cone not visible; at v_app > c, cone visible; angle changes with W.

### Phase 8 — Retarded-time observation (3-4 days)

**Goal:** body behind ship visibly runs in reverse at v_app > c.

**Deliverables:**
- `observation_calc.cu`: per-body Newton iteration for t_emit; computes ObservableState with edge-case flags
- `retarded_body.cpp`: render each visible body at its `body_state(t_emit)` position; apply z_total color shift
- Scenario S05: planet behind running backward at 1x speed; S06 at 9x speed
- Scenario S07: photon-source-history triggers; body disappears cleanly
- Scenario S10: Hubble-horizon body frozen and dim

**Acceptance:** visible orbit reversal in S05; dramatic in S06; clean disappearance in S07; frozen in S10.

### Phase 9 — Warp wake trail (P3; new feature) (2-3 days)

**Goal:** ship leaves a visible trail of metric_shift residual behind it at warp.

**Deliverables:**
- `wake_field.cu`: maintain a trail buffer; each frame, write current ship position + current W; decay older entries
- `trail.cpp`: render trail as billboard sprite chain or stretched ribbon mesh; color tracks W magnitude with decay
- Parameter panel: wake decay rate slider; wake intensity slider
- Scenarios S05, S06: trail visible behind ship

**Acceptance:** ship moves through warp at v_app=2c; visible decaying trail of violet/blue extends behind; trail length tracks ship motion + decay rate.

### Phase 10 — Reflex stub + chaos modulation (2-3 days)

**Goal:** Reflex stabilizer visibly damps chaos field.

**Deliverables:**
- `reflex_stub.cpp`: simple PID controller; inputs chaos field amplitude; outputs control vector (nacelle_damping ∝ 1/(1+chaos_amplitude); emergency_dump if chaos > threshold for N frames)
- Wire Reflex output back to chaos kernel: nacelle_damping reduces chaos α_eff (proxy for stabilization)
- UI: Reflex ON/OFF toggle; control vector live display; chaos amplitude plot (time series)
- Scenario S09: chaos grows; Reflex enables; rapid damping

**Acceptance:** S09 shows chaos growth → enable Reflex → rapid damping; emergency_dump triggers visual snap if chaos exceeds threshold.

### Phase 11 — Starfield Doppler + aberration (2 days)

**Goal:** stars in starfield shift color and direction based on ship velocity.

**Deliverables:**
- `starfield.cpp` updates: per-star, compute z_kin from ship velocity dot (star direction); compute aberration-warped position
- Shader: per-star color shift via blackbody approximation; position shift via aberration formula
- Scenarios S02, S03: dramatic Doppler at β=0.5 and β=0.9

**Acceptance:** S02 shows mild aberration + redshift on rear stars; S03 shows dramatic forward-compression of starfield.

### Phase 12 — UI polish + scenario loader + screenshot (1-2 days)

**Goal:** scenarios load from JSON; F12 saves PNG + state dump; profiler displays per-pass timing.

**Deliverables:**
- `scenario_loader.cpp`: parse JSON via nlohmann/json
- All 12 scenarios authored as JSON files
- `screenshot.cpp`: F12 hotkey captures front buffer + saves PNG via stb_image_write + JSON state dump
- `profiler.cpp`: per-pass GPU timer queries via cuEvent + glFinish or OpenGL timer queries; display in state panel
- `BUILD.md` + `SCENARIOS.md` + `EXPECTED_VISUALS.md` written

**Acceptance:** dropdown selects scenarios; each scenario runs correctly; F12 produces PNG; profiler shows per-pass timing.

### Phase 13 — Polish + regression test setup (1-2 days)

**Goal:** golden screenshots; PNG diff regression test.

**Deliverables:**
- For each scenario at canonical timestamp, run + capture; save as `assets/golden/`
- `tools/golden_diff.cpp`: tool that loads scenario, runs to timestamp, captures, compares to golden via per-pixel RMSE
- `docs/EXPECTED_VISUALS.md`: written prose description of what each scenario should show, with reference PNG embedded

**Acceptance:** golden_diff tool returns 0 for all scenarios on the dev machine; documentation complete.

### Phase 14 — Documentation + handoff (1 day)

**Goal:** complete docs for handoff.

**Deliverables:**
- `README.md`: project overview, quick start
- `BUILD.md`: detailed Windows 11 build (Visual Studio 2022, CUDA Toolkit 12.x, CMake 3.24+)
- `SCENARIOS.md`: each scenario explained
- `EXPECTED_VISUALS.md`: acceptance criteria with PNGs
- `KNOWN_ISSUES.md`: findings surfaced by testbed runs (this becomes input to v0.130 spec revision)

**Acceptance:** documentation complete; another dev can clone repo + follow BUILD.md + see scenarios run.

---

## 8. Performance and quality targets

### 8.1 Performance targets

| Target | Hardware | Resolution | Notes |
|---|---|---|---|
| 60 FPS | RTX 4070 | 1080p | minimum acceptable |
| 60 FPS | RTX 4090 | 1440p | recommended target |
| 120 FPS | RTX 5090 | 1080p | upper-tier |
| 30 FPS | RTX 3060 | 1080p | low-end fallback |

Per-pass budget at 1080p on RTX 4070 (16.67 ms total budget):
- Chaos PDE step (RK2): 1.5 ms
- Warp field SVT populate: 1.5 ms
- Volume ray-march: 3-4 ms
- Lensing post-pass: 1.5 ms
- Starfield render: 1.0 ms
- Cherenkov + trail: 0.5 ms
- Hull + UI + post-process: 3.0 ms
- Reserve: ~4 ms

### 8.2 Visual quality targets

The testbed is diagnostic, not photorealistic. Quality goals:
- **Phenomena distinctness**: each effect (Cherenkov, lensing, retarded-time reversal, chaos particles) visually distinguishable from the others
- **Math correlation**: visual changes track parameter changes monotonically (slider W up → bubble visibly bigger/brighter)
- **Reproducibility**: golden screenshots regenerate to same image (within RMSE tolerance) across builds

Specifically NOT goals:
- Cinematic look
- HDR pipeline
- Real-time shadows (Lumen, RTX GI)
- DLSS / FSR upscaling
- Frame generation
- Atmospheric scattering
- Volumetric clouds
- Anti-aliasing beyond MSAA 4×

---

## 9. Risk assessment

### 9.1 Technical risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| CUDA-OpenGL interop driver bugs | Low (mature API) | Use well-tested patterns; fallback to CUDA-only render path if needed |
| RBF spatial-hash + warp field too slow at 1080p | Medium | Profile early; optimize via shared memory or reduce RBF node count |
| Cherenkov visual tuning takes many iterations | High | Make all coefficients live-tunable; budget extra time in Phase 7 |
| Retarded-time Newton iteration diverges in edge cases | Low | Clamp Newton steps; fall back to closed-form for static bodies |
| Chaos PDE numerical instability near critical α | Medium | CFL guard; explicit RK2; cap α_eff at reasonable max |
| GPU driver crashes on long runs | Low | Defensive cudaGetLastError() checks; restart cleanly on error |
| Hull mesh loader chokes on complex OBJs | Low | Use simple low-poly mesh; tinyobjloader handles most files |
| Cross-build to Linux breaks | Medium | Test Linux build in CI early; use CMake portable patterns |

### 9.2 Scope risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Phase 6 (Lensing) or Phase 8 (Retarded-time) more complex than estimated | Medium | Scope is the spec's; defer cosmetic refinement (S11 split-screen) to v1.1 |
| Eye-ear decoupling visualization (S12) hard to convey in static screenshot | Low | Defer S12 to v1.1; document in EXPECTED_VISUALS.md as "dynamic only" |
| Adding more than 12 scenarios | Medium | Hard cap at 12 for v1; v1.1 adds more |
| UI panel design takes too long to polish | Low | Use ImGui defaults; no custom styling at v1 |

### 9.3 Validation risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Visual tests subjective; can't automate | High | Golden-screenshot RMSE diffs catch regression; human review for first-time scenarios |
| Math says X, visual implies Y, operator unsure which is wrong | Medium | KNOWN_ISSUES.md log; each surfaced inconsistency becomes a spec revision candidate per §15.4 |
| Performance targets miss on some hardware | Medium | Document min-hardware in README; provide quality tier setting |

---

## 10. Decisions to lock + open questions

### 10.1 Locked design decisions (no further operator input needed)

| # | Decision | Rationale |
|---|---|---|
| L1 | OpenGL 4.6 core profile (not Vulkan/DX12) | Maturity + simplicity + CUDA interop story |
| L2 | GLFW 3.x for windowing | Lightweight, focused |
| L3 | Dear ImGui (docking branch) for UI | De facto standard |
| L4 | CUDA Toolkit 12.x (NVIDIA only) | Per Platform Discipline |
| L5 | C++17 + CUDA + GLSL only (no Python) | Per Language Discipline |
| L6 | CMake 3.24+ with FetchContent | Per Language Discipline + reproducibility |
| L7 | Link `proto/astra_nexus.cpp` as static library | Reuse existing math |
| L8 | 12 canonical scenarios | Match scenarios to spec coverage |
| L9 | PNG screenshot via stb_image_write | Simple, permissive license |
| L10 | nlohmann/json for scenario files | Permissive, header-only |
| L11 | Synthesize CFD-RBF analytically (no OpenFOAM dep) | Avoid heavyweight dep for testbed; can swap for baked CFD later |
| L12 | Reflex as PID stub (not real TensorRT inference) | Testbed validates contract, not weights |

### 10.2 Open questions for operator

**Q1 — Should the testbed integrate with the same `proto/constants.toml` proposed by attempt 2's F1 / techdive F8?**

If yes, the testbed reads cosmological constants from the same source as the C++ math binary. Cleaner; commits us to constants.toml landing first.

If no, testbed uses hardcoded duplicates of the same values; works standalone.

**Recommendation:** YES if constants.toml lands before testbed Phase 1; NO if testbed proceeds first (defer constants.toml integration to v1.1 of testbed).

---

**Q2 — Should the testbed share `WarpFieldSample` struct with the future UE5 plugin?**

If yes, the testbed's CUDA kernels output to the same struct format that UE5's eventual integration will consume. Maximum reuse downstream.

If no, the testbed uses its own internal format; UE5 plugin re-implements.

**Recommendation:** YES — define the struct once in a shared header in `proto/cuda_lib/include/astra_physics/types.h` (per techdive doc); testbed + future UE5 plugin both consume.

---

**Q3 — Is S12 (Eye-Ear Decoupling) in v1, or deferred?**

The scenario requires UI audio frequency display (simulated, not real audio). It's the spec's most subtle phenomenon. Implementing it requires +2 days.

**Recommendation:** include in v1 — it's the cleanest demonstration of §6.3 endogenous/exogenous principle; the operator's been writing about this for months in the book.

---

**Q4 — Should the testbed support a "comparison mode" where two scenarios run side-by-side (like S11)?**

Adds complexity to camera + render-target management (~2-3 days). S11 specifically calls for it.

**Recommendation:** YES — split-screen support is needed for S11; once implemented, S11 + S12 both use it. ~3 days extra work; worth it.

---

**Q5 — Should the testbed maintain a "history" timeline display (like a video editor scrubber)?**

Lets the user scrub backward in time through a scenario. Useful for capturing screenshots at the right moment.

**Recommendation:** NO at v1 — too much complexity. Add pause + reset + screenshot. v1.1 could add scrub if findings demand it.

---

**Q6 — Should the testbed be open-sourced separately from the main ASTRA-7 repo?**

The testbed is engine-agnostic; future ASTRA-7 contributors could use it without touching UE5 or the LLM bundle. Could live in its own repo `astra-7-visual-testbed` under the same org.

**Recommendation:** initially under `proto/visual_testbed/` in the main ASTRA-7 repo; split to separate repo when it stabilizes (v1.x).

---

**Q7 — What's the canonical hull mesh source?**

Two options:
- (a) Bake from `memory/hull_design_v0.md` description via a Blender script (~2 days extra work)
- (b) Use a generic low-poly placeholder for v1; commission proper hull for v1.x

**Recommendation:** (b) — placeholder for v1. The testbed is testing physics, not hull aesthetics. Hull comes in via UE5 Phase E0.

---

**Q8 — Should the testbed include audio (MetaSound-equivalent) playback to make S12 fully functional?**

Embedding actual audio synthesis (e.g., via miniaudio + the 5-layer spec §8.3 formulas) adds ~3 days and a dependency.

**Recommendation:** NO at v1 — UI frequency display for S12 is enough. Real audio is a v2 enhancement; could become a sibling "audio testbed" project.

### 10.3 Spec revision candidates this testbed will surface

Per §15.4: the testbed is itself a closed-loop measurement instrument. Findings from running it justify v0.130 spec revisions. Predicted findings:

| Predicted finding | Spec section affected |
|---|---|
| Cherenkov implementation produces visible cone; formula confirmed | §6 step 10 + Appendix B locked numerics |
| Warp wake trail is visually compelling and physically motivated | §3.6 + §6 (new sub-section) |
| Some scenario needs `t_source_start` per-body schema concretized | §3.11 (audit's R4) |
| α_lens lensing coefficient empirically tuned to ~3-5 | Appendix B |
| n(W) refractive index function empirically tuned | §6 step 10 + Appendix B |
| Chaos PDE α_base + k_coupling empirically tuned for stable behavior | §7.1 + Appendix B |
| Reflex stub PID gains empirically tuned | §2.3.1 (informational; real Reflex is trained, not PID) |
| Eye-ear decoupling at warp egress visually compelling (or jarring) | §6.3 + §8.3 endogenous/exogenous principle |

Each finding lands as an entry in `KNOWN_ISSUES.md`; per §15.4 the operator decides which justify spec revisions.

---

## 11. Acceptance criteria for the coding agent's delivery

The testbed is "v1 complete" when:

1. ✓ Builds cleanly on Windows 11 + MSVC 2022 + CUDA Toolkit 12.x + CMake 3.24+
2. ✓ Builds cleanly on Linux + GCC 12+ + CUDA Toolkit 12.x + CMake 3.24+ (secondary target)
3. ✓ All 12 scenarios load and run without crashing
4. ✓ Each scenario produces visuals matching the criteria in §5 of this document
5. ✓ State display shows live math values that match `proto/astra_nexus.cpp` standalone output (regression-tested)
6. ✓ Per-pass GPU timing visible in profiler panel
7. ✓ F12 screenshot saves PNG + JSON state dump
8. ✓ Reaches 60 FPS at 1080p on RTX 4070 (target hardware)
9. ✓ Golden-screenshot regression test passes (per-pixel RMSE within tolerance)
10. ✓ Documentation complete: README + BUILD + SCENARIOS + EXPECTED_VISUALS + KNOWN_ISSUES
11. ✓ Catch2 unit tests pass for: warp_field eval, chaos_pde step, cherenkov_math, observation_calc, reflex_stub, rbf_network
12. ✓ No Python in the codebase; no Apple-specific code paths; no UE5 dependency

---

## 12. Out-of-scope explicitly named

To prevent scope creep during implementation:

- ❌ **LLM integration** of any kind. ASTRA's persona is not in this testbed.
- ❌ **Network features**. No multiplayer, no telemetry, no cloud.
- ❌ **Save/load persistence**. Scenarios start fresh each time.
- ❌ **Audio playback**. UI frequency display only for S12.
- ❌ **Ship interior**. The hull is just an exterior mesh.
- ❌ **Camera-free zones**. The testbed has no privacy contract surface to enforce.
- ❌ **REEL retrieval, memory, journal**. LLM-coupled; out of scope.
- ❌ **Sculptor research loop**. LLM-coupled.
- ❌ **TTS / ASR**. Out of scope.
- ❌ **Mod ABI**. Testbed is for engineering validation; not user-facing distribution.
- ❌ **Achievements / progression**. Not a game.
- ❌ **Hull damage interaction**. Optional v1.1 if needed for visual testing.
- ❌ **Niagara-style particle effects beyond chaos field**. Chaos particles only.
- ❌ **Substrate (Strata) material layering**. Simple hull material at v1; UE5 plugin handles Substrate.
- ❌ **Heterogeneous Volumes**. That's UE5; we use a custom CUDA-driven volume render.
- ❌ **NNE / TensorRT**. PID stub Reflex is enough for testbed.
- ❌ **DLSS / FSR / XeSS**. Not needed for diagnostic tool.
- ❌ **VR / stereo rendering**. Mono only.

---

## 13. Total estimated effort

Per-phase breakdown:

| Phase | Days | Cumulative |
|---|---|---|
| 1. Skeleton | 1-2 | 2 |
| 2. Scene framework | 2-3 | 5 |
| 3. Physics math bridge | 2-3 | 8 |
| 4. CUDA-OpenGL interop | 2-3 | 11 |
| 5. CFD-RBF warp field | 3-4 | 15 |
| 6. Geometric lensing | 2-3 | 18 |
| 7. Cherenkov cone | 2-3 | 21 |
| 8. Retarded-time observation | 3-4 | 25 |
| 9. Warp wake trail | 2-3 | 28 |
| 10. Reflex stub + chaos | 2-3 | 31 |
| 11. Starfield Doppler | 2 | 33 |
| 12. UI polish + scenarios + screenshot | 1-2 | 35 |
| 13. Polish + regression | 1-2 | 37 |
| 14. Documentation | 1 | 38 |

**Total: 35-38 days** for a competent single coding agent. Realistic calendar: 2-3 months including review cycles, profiling, scenario iteration.

**Critical-path items (do these FIRST in their phases):**
- Phase 5 (CFD-RBF) — gates Phases 6, 7, 9
- Phase 7 (Cherenkov) — the 5D-F4 gap; closes a known spec deficit
- Phase 8 (Retarded-time) — the canonical visual demonstration of §3.11

**Items that could be deferred to v1.1 if calendar tight:**
- S11 split-screen (needs comparison-mode infrastructure)
- S12 eye-ear (needs UI audio frequency display)
- Linux build (Windows-first is fine)
- Hot-shader-reload (F5; nice-to-have)

---

## 14. Closing rationale

This testbed is the **first visual closed-loop** for ASTRA-7's physics. The C++ assertion suite proves the math is internally consistent; the bench proves the LLM substrate produces correct behavior; THIS testbed proves the math produces the right *visual phenomena*.

Per spec §15.4: "the next findings worth a spec revision come from the closed loop." The testbed is a closed-loop measurement that the spec hasn't yet had. Running it will surface findings the math-only assertion suite cannot.

Per spec §15.7 dual-implementation discipline: the testbed is implementation #1 of the visual side (UE5 plugin is implementation #2). Both consume the same `astra_nexus.cpp` math, the same `proto/constants.toml`, and produce visuals that should agree. **The testbed's visual output IS the canonical reference for what UE5 should produce.** When UE5 Phase E lands, its outputs get compared against the testbed's golden screenshots; mismatches are UE5 implementation drift, caught early.

Per spec §15.10 (NEW v0.129) audit cadence: this testbed becomes a 6th rig (alongside physics binary + textverse bench + UE5 engine + book canon + spec audit). Cadence: each major math change triggers a testbed run; visual regression triggers spec or code revision.

The testbed is small (~38 days), bounded (12 scenarios), and high-leverage (each scenario tests one or more spec sections; failures localize cleanly). The operator gets a Windows .exe that demonstrates the warp field, the Cherenkov cone, the retarded-time reversal, the geometric lensing, the chaos instability, the Reflex stabilization — all rendered, all interactive, all live-tunable. That's the conversion of months of paper-physics into eye-visible truth.

Build it.

---

*End of proposal.*

*One executable. Twelve scenarios. The math made visible. The next coding agent's marching orders are clear; the deliverable surfaces the next class of findings that the spec wants but doesn't yet know it needs.*
