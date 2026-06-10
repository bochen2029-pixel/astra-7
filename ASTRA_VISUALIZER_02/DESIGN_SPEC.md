# ASTRA-7 Visualizer 02 — Design Specification

**Project:** Standalone CUDA + OpenGL visual physics testbed for the ASTRA-7 14-equation framework.
**Target hardware:** Windows 11 + RTX 40-series (baseline RTX 4070; recommended 4090; upper-tier 5090).
**Repository target:** `C:\ASTRA-7\ASTRA_VISUALIZER_02\` (subdirectory of parent ASTRA-7 project).
**Pairs with:** `CLAUDE.md` (operating contract) in this same folder.
**Date authored:** 2026-05-16
**Canon basis:** `docs/spec-v0.129-tentative-2026-05-16.md` (parent project; read-only).

---

## Foreword

`proto/astra_nexus.cpp` (in the parent project) is a 1009-line C++ binary with 66
assertions proving the 14-equation framework math at the mathematical level. **It does
not prove the math maps to the intended visual phenomena.**

This artifact renders those phenomena. A standalone Windows executable that lets a human
SEE the warp field, the Cherenkov cone, the retarded-time orbit reversal, the
photon-source-history disappearance, the Hubble-horizon freeze, the geometric lensing,
the chaos field instability, the Reflex stabilization, the regime contrast, and the
eye-ear decoupling — all rendered, all interactive, all live-tunable. Plus mechanical
pixel-level assertions that compare rendered output against canonical math from
`libastra_nexus` (the local mirror of the canon).

**Defining property:** every numeric value the visualizer compares against traces to a
function call in `libastra_nexus`, which mirrors `proto/astra_nexus.cpp` exactly. The math
is locked in canon; this testbed validates that the math, when rendered, produces the
visuals the spec describes.

The companion to this discipline is **operator sign-off on Scene S05**: the project is
incomplete until the operator personally watches a Kepler orbit visibly run BACKWARDS at
v_apparent = 2c. That is the "you have to see it to believe it" payoff.

---

## Part 1: Goals and Non-Goals

### 1.1 Goals (v1, this document)

1. **Real-time interactive visualization** at 1080p+ on RTX 4070+, ≥60 FPS, of 12 distinct physics scenes.
2. **Headless mode** for CI: render all 12 scenes to PNG with JSON test report; exit 0 if all assertions pass.
3. **Three-layer mechanical validation:** pixel-level assertions + golden image heatmap diff + real-time side-by-side numeric overlay.
4. **`libastra_nexus` local mirror** of the canonical math; bumped from 66 → 69+ assertions via Cherenkov closure.
5. **CUDA-OpenGL interop** via `cudaGraphicsGLRegisterImage`; no engine dependencies.
6. **Engine-agnostic:** no Unreal, no Unity, no Godot. Pure C/C++/CUDA + OpenGL + GLFW + ImGui.
7. **Static linkage** so the .exe runs with only NVIDIA driver + Windows OS DLLs.
8. **Cross-platform CMake** (Windows 11 primary; Linux x86_64 acceptable second target — not blocking).
9. **Operator sign-off on Scene S05** — the project's central visual claim.

### 1.2 Non-Goals (v1)

- Cross-platform macOS / iOS / Android — Platform Discipline prohibits Apple.
- Web / WebAssembly / WebGPU.
- Production rendering quality (TSR, Lumen, Nanite, DLSS, frame generation).
- LLM persona / Narrator / ASTRA conversational features.
- Audio synthesis (sibling testbed; UI audio-frequency display only for S12).
- NNE / TensorRT real Reflex inference (PID stub validates contract, not weights).
- Save/load persistence, network features, multiplayer, VR.
- Production-grade hull mesh (low-poly placeholder for v1).
- Real CFD-OpenFOAM RBF baking (synthetic RBF for v1; real bake deferred to v1.1).

### 1.3 Hard constraints (from parent CLAUDE.md)

- **Language Discipline:** C / C++17+ / CUDA / GLSL only. No Python anywhere in this folder.
- **Platform Discipline:** Windows 11 primary; Linux x86_64 acceptable. No Apple / Mac / Metal / iOS.
- **Scope:** ALL work happens inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`. Files outside are read-only.

---

## Part 2: Architecture

### 2.1 Stack

```
Window + input:    GLFW 3.4
GL loader:         GLAD v2.0.6
Display:           OpenGL 4.6 core profile
GPU compute:       CUDA 12.x or 13.x; compute_89 (Ada) + compute_120 (Blackwell)
Host language:     C++20 (MSVC 14.40+)
Build:             CMake 3.27+ + Ninja
UI:                Dear ImGui 1.91+ (docking branch)
Math (host):       GLM 1.0+
Image I/O:         stb_image + stb_image_write
JSON:              nlohmann/json
Tests:             doctest
Static link:       CUDA::cudart_static + MSVC MultiThreaded runtime
```

CUDA-OpenGL interop: physics state (chaos field, warp metric volume, body positions) lives
in CUDA-allocated buffers also bound as OpenGL textures via `cudaGraphicsGLRegisterImage`.
Compute kernels write the buffers; display fragment shaders sample the textures.
Zero-copy round-trip.

### 2.2 Per-frame pipeline

```
1. POLL INPUT (GLFW)
   - Mouse: orbit camera (drag) + zoom (wheel)
   - Keys: scene-switch (1-9, Shift+1-3), pause (Space), reset (R),
            screenshot (F12), help (F1), debug overlays (F4), quit (Esc)
   - Scenario UI: select via top-bar ImGui dropdown
   - Parameter sliders: W, β, v_app, BH mass, BH distance, α_lens,
                        chaos α_base, etc. — feeds into libastra_nexus call layer

2. PHYSICS UPDATE (libastra_nexus call layer, CPU)
   - Update time state: t_cosmic advances per scene clock
   - Compute Rapidity, γ, dτ/dt via libastra_nexus::compute_*
   - Compute ObservableState for each visible body via libastra_nexus::observe()
   - These values feed both UI display AND assertion comparisons

3. COMPUTE PASSES (CUDA)
   a. chaos_pde_step: Fisher-KPP RK2 step; double-buffered surfaces
   b. warp_field_eval: CFD-RBF sample to 3D texture (W and ∇W via dual numbers)
   c. observation_calc (optional GPU path): per-body retarded-time Newton iteration
   d. wake_field_update: trail position write + decay (P3 wake)
   e. reflex_stub_step: PID controller; chaos amplitude → control vector

4. RENDER PASSES (OpenGL 4.6)
   a. Volume ray-march: fullscreen quad fragment shader samples warp 3D texture +
      chaos 3D texture; produces violet-blue volumetric bubble with sharp boundary
   b. Lensing post-pass: per-pixel ray-march through ∇W field; deflects to background
   c. Starfield: point sprites with per-star Doppler color + aberration warp
   d. Cherenkov cone: forward-facing geometric mesh; half-angle from cherenkov_angle
   e. Wake trail: billboard strip; decay over τ_ship
   f. Hull mesh: simple Phong + SDF damage overlay
   g. Retarded bodies: each body rendered at observation_state.t_emit
   h. ImGui overlay: parameter panel + state display + numeric assertion overlay

5. VALIDATION LAYER
   - PixelSampler::Sample(scene, framebuffer) walks scene.assertions()
   - For each assertion: glReadPixels at coord; compare to libastra_nexus value
   - Updates ImGui PASS/FAIL overlay
   - In headless mode: writes to report.json

6. SWAP / PRESENT
   - glFinish() before glReadPixels (avoid race)
   - glfwSwapBuffers()
```

### 2.3 Key data structures

**`WarpFieldSample`** — the shared type used across kernels, shaders, and assertions:

```cpp
struct WarpFieldSample {
    float metric;             // W(x,t)
    float metric_gradient[3]; // ∇W
    float metric_shift;       // gravitational + warp redshift (NOT kinematic Doppler)
    float chaos_intensity;
    float vorticity;
    float ray_deflection[3];  // α_lens · ∇W · Δs contribution per march step
    float cherenkov_angle;    // local Cherenkov cone angle (radians)
};
```

Lives in `src/libastra_nexus/include/astra_nexus/types.h` — shared between this project
and any future UE5 plugin.

**`ObservableState`** — per-body retarded-time observation result:

```cpp
struct ObservableState {
    double d_proper;
    double v_radial;
    double z_cosmo;
    double z_kin;
    double z_metric;
    double z_total;
    double t_emit;
    double apparent_rate;
    bool   time_reversed;
    bool   beyond_photon_history;
    bool   beyond_hubble_horizon;
};
```

Per spec §6.3 v0.129. Produced by `libastra_nexus::observe(...)`.

**`AstraCoord`** — 128-bit composite position (per spec §1.1):

```cpp
struct AstraCoord {
    int64_t sx, sy, sz;       // 1000 km sector indices
    double  lx, ly, lz;       // sub-mm local offset, |·| ≤ 500 km
};
```

**`ChaosField`** — 128³ Fisher-KPP scalar field, double-buffered:

```cpp
struct ChaosField {
    cudaArray_t front;        // read in current frame
    cudaArray_t back;         // write target this frame
    cudaTextureObject_t tex_front;
    cudaSurfaceObject_t surf_back;
    int resolution;           // 128
};
```

Swap front/back after each kernel step.

**`RBFNetwork`** — analytical Alcubierre approximation:

```cpp
struct RBFNode {
    float center[3];          // ship-local position
    float sigma_inv_sq;       // 1 / (2σ²) precomputed
    float weight;
};

struct RBFNetwork {
    std::vector<RBFNode> nodes;
    // Spatial hash for O(N=20) candidates per sample:
    std::vector<uint32_t> voxel_offsets;
    std::vector<uint16_t> node_indices;
    int hash_grid_size;       // 32³ default
    float hash_voxel_size;    // hash_grid extent / 32
};
```

For v1: synthesize ~50-200 Gaussian RBF nodes analytically (Alcubierre `f(r_s)` shape
function with hull-axis modulation). Real CFD-baked RBF deferred to v1.1.

### 2.4 Project layout

```
C:\ASTRA-7\ASTRA_VISUALIZER_02\
├── CLAUDE.md                          # operating contract (already authored)
├── DESIGN_SPEC.md                     # this file
├── README.md                          # user-facing controls + run instructions
├── BUILD.md                           # detailed build instructions
├── SCENES.md                          # per-scene walkthrough (operator-facing)
├── VALIDATION.md                      # the three-layer methodology
├── KNOWN_ISSUES.md                    # findings → v0.130 spec candidates
├── BUILD_LOG.md                       # append-only session log
├── BLOCKERS.md                        # unresolved issues (created if needed)
├── BUILD_COMPLETE.md                  # filed at v1 completion (created if needed)
├── CMakeLists.txt                     # build configuration
├── tools/
│   ├── build.bat                      # Windows convenience (vcvarsall + cmake)
│   └── build.sh                       # Linux convenience
├── third_party/                       # FetchContent-populated
│   └── (glfw, glad, imgui, glm, stb, nlohmann_json, doctest, tinyobjloader)
├── src/
│   ├── main.cpp                       # entry: GLFW + GL + ImGui + main loop + CLI
│   ├── libastra_nexus/                # local mirror of canon math (V0 task)
│   │   ├── include/astra_nexus/       # public headers
│   │   ├── src/                       # implementations
│   │   └── CMakeLists.txt
│   ├── app/
│   │   ├── application.{cpp,h}        # app lifecycle
│   │   ├── scene_router.{cpp,h}       # scene registration + switching
│   │   ├── cli.{cpp,h}                # command-line parser
│   │   ├── headless_mode.{cpp,h}      # CI batch render path
│   │   ├── camera.{cpp,h}             # free-fly + scenario-locked + split-screen
│   │   ├── input.{cpp,h}              # keyboard + mouse
│   │   └── time_step.{cpp,h}          # sim time vs wall time decoupling
│   ├── renderer/
│   │   ├── gl_context.{cpp,h}         # GL setup + debug callback
│   │   ├── compute_program.{cpp,h}    # compute shader loader
│   │   ├── graphics_program.{cpp,h}   # vert + frag shader loader
│   │   ├── texture.{cpp,h}            # GL texture wrapper
│   │   ├── buffer.{cpp,h}             # SSBO / UBO wrappers
│   │   ├── cuda_gl_interop.{cpp,h}    # cudaGraphicsGLRegister* manager
│   │   ├── volume_renderer.{cpp,h}    # warp + chaos volume ray-march
│   │   ├── starfield.{cpp,h}          # point sprites with Doppler
│   │   ├── cherenkov.{cpp,h}          # cone mesh / billboard
│   │   ├── lensing.{cpp,h}            # geometric lensing post-pass
│   │   ├── hull.{cpp,h}               # hull mesh + SDF
│   │   ├── trail.{cpp,h}              # warp wake (P3)
│   │   ├── retarded_body.{cpp,h}      # per-instance Kepler-at-t_emit render
│   │   └── overlays.{cpp,h}           # debug: ∇W arrows, RBF nodes
│   ├── physics/
│   │   ├── physics_core.{cpp,h}       # facade over libastra_nexus
│   │   ├── rbf_network.{cpp,h}        # CFD-RBF + spatial hash
│   │   ├── chaos_field.{cpp,h}        # 128³ chaos state mgmt
│   │   ├── hull_sdf.{cpp,h}           # SDF loader / synthesizer
│   │   ├── reflex_stub.{cpp,h}        # PID Reflex glue
│   │   ├── wake_field.{cpp,h}         # warp wake state
│   │   ├── cfd_synthesizer.{cpp,h}    # analytic Alcubierre RBF synth
│   │   └── state_bus.{cpp,h}          # simplified state container (mirrors §4.2)
│   ├── scenes/
│   │   ├── i_scene.h                  # interface
│   │   ├── scene_base.{cpp,h}         # shared helpers
│   │   ├── s01_rest_baseline.{cpp,h}
│   │   ├── s02_stl_recede_05c.{cpp,h}
│   │   ├── s03_stl_recede_09c.{cpp,h}
│   │   ├── s04_warp_charge.{cpp,h}
│   │   ├── s05_warp_cruise_2c.{cpp,h}              # THE PAYOFF
│   │   ├── s06_warp_cruise_10c_cherenkov.{cpp,h}   # closes 5D-F4
│   │   ├── s07_photon_source_history.{cpp,h}
│   │   ├── s08_warp_gravity_well.{cpp,h}
│   │   ├── s09_chaos_instability_reflex.{cpp,h}
│   │   ├── s10_hubble_horizon.{cpp,h}
│   │   ├── s11_split_screen_stl_vs_warp.{cpp,h}
│   │   └── s12_eye_ear_decoupling.{cpp,h}
│   ├── validation/
│   │   ├── pixel_sampler.{cpp,h}
│   │   ├── assertion.{cpp,h}
│   │   ├── scalar_pixel_assertion.{cpp,h}
│   │   ├── heatmap_diff_assertion.{cpp,h}
│   │   ├── numeric_overlay.{cpp,h}
│   │   ├── test_report.{cpp,h}
│   │   └── validation_panel.{cpp,h}
│   ├── ui/
│   │   ├── imgui_setup.{cpp,h}
│   │   ├── parameter_panel.{cpp,h}
│   │   ├── state_display.{cpp,h}
│   │   ├── scenario_selector.{cpp,h}
│   │   ├── profiler.{cpp,h}
│   │   └── help_overlay.{cpp,h}
│   ├── kernels/                       # CUDA .cu files
│   │   ├── chaos_pde.cu               # Fisher-KPP RK2 solver
│   │   ├── warp_field_eval.cu         # CFD-RBF eval + ∇W
│   │   ├── observation_calc.cu        # per-body retarded time (Newton)
│   │   ├── wake_field.cu              # trail evolution
│   │   ├── reflex_stub.cu             # PID Reflex
│   │   ├── sdf_sphere_trace.cu        # hull SDF traversal
│   │   └── kernels.h                  # C++ declarations
│   ├── shaders/                       # GLSL
│   │   ├── common/
│   │   │   ├── constants.glsl         # physical constants
│   │   │   ├── astra_coord.glsl       # AstraCoord helpers
│   │   │   ├── redshift.glsl          # color shift functions
│   │   │   └── camera.glsl            # view/projection helpers
│   │   ├── volume/
│   │   │   ├── raymarch.vert          # fullscreen quad vertex
│   │   │   └── raymarch.frag          # warp + chaos volume
│   │   ├── starfield/
│   │   │   ├── starfield.vert         # point sprites with Doppler
│   │   │   └── starfield.frag
│   │   ├── cherenkov/
│   │   │   └── cone.frag              # Cherenkov cone overlay
│   │   ├── lensing/
│   │   │   └── post.frag              # geometric lensing
│   │   ├── hull/
│   │   │   ├── hull.vert
│   │   │   └── hull.frag              # simple Phong + SDF damage
│   │   ├── trail/
│   │   │   ├── trail.vert
│   │   │   └── trail.frag             # wake billboards
│   │   └── retarded_body/
│   │       ├── body.vert              # per-instance Kepler-at-t_emit
│   │       └── body.frag              # redshift-colored body
│   └── util/
│       ├── log.{cpp,h}                # structured stdout
│       ├── timer.{cpp,h}              # CPU + GPU (cuEvent) timers
│       ├── screenshot.{cpp,h}         # PNG via stb_image_write
│       └── color.{cpp,h}              # blackbody + Doppler color
├── assets/
│   ├── hull/
│   │   └── astra7_lowpoly.obj         # ~10K tris placeholder
│   ├── starfield/
│   │   └── starfield_10k.bin          # 10K stars binary
│   ├── cfd/
│   │   └── warp_cfd_rbf_synthetic_v1.json   # ~50-200 node test RBF
│   ├── scenarios/                     # 12 JSON files; one per scene
│   │   └── s01..s12.json
│   └── reference_renders/             # golden PNGs (canon-locked)
│       └── s01..s12_canonical.png
├── tests/                             # doctest unit tests
│   ├── test_pixel_sampler.cpp
│   ├── test_rbf_eval.cpp
│   ├── test_chaos_pde_step.cpp
│   ├── test_observation_calc.cpp
│   ├── test_cherenkov_math.cpp
│   └── test_assertion_layer.cpp
└── build/                             # CMake output (gitignored)
```

**Estimated total:** ~10,000-12,000 LOC across ~40 C++ + ~6 CUDA kernels + ~20 shader files + 12 scenario JSONs.

---

## Part 3: The 12 visual test scenes

Each scene has the same structural pattern:

1. **Goal** — physics effect being verified visually
2. **Spec basis** — exact spec § + line number from parent project
3. **Math primitives** — which `libastra_nexus` functions get called
4. **Rendering technique** — how pixels get produced
5. **UI controls** — parameters the operator can sweep
6. **Assertions** — pixel-level checks against canonical math (≥3 per scene)
7. **Pass criteria** — mechanical pass condition + operator-eye check

### Scene S01 — RestBaseline

- **Goal:** Sanity render. Hull + starfield + sun + Earth visible at REST regime; no warp, no chaos, no Cherenkov.
- **Spec basis:** §1.1 (AstraCoord), §1.2 (two-clock), §3.3 (REST regime).
- **Math primitives:** `Rapidity::gamma()` returns 1.0; `dtau_dt_cosmic(W=0, grav=1, γ=1, warp=false)` returns 1.0.
- **Rendering:** hull OBJ + 10K star field + sun point + Earth point. ImGui state panel shows γ=1.0, dτ/dt=1.0, regime=REST.
- **UI:** camera orbit, zoom.
- **Assertions (3):**
  1. Pixel at viewport center renders hull color (`alpha > 0`).
  2. Sun pixel shows yellow-ish color (`R > 0.8, G > 0.6, B < 0.3`).
  3. UI state display: γ matches `libastra_nexus::Rapidity::gamma()` to 6 decimals.
- **Pass:** all 3 assertions pass; golden PNG match RMSE < 1%.

### Scene S02 — STL_Recede_05c

- **Goal:** SR longitudinal Doppler visible at β=0.5.
- **Spec basis:** §3.4 (four optical effects), §3.7 (rapidity), §3.11 (apparent_rate).
- **Math primitives:** `compute_apparent_rate(0.5c, R_STL_REL)` = √(1/3) ≈ 0.5774; `compute_z_kin(0.5c)` = √3 − 1 ≈ 0.732.
- **Rendering:** ship cockpit rear-view; planet behind redshifted; rear stars redshifted; mild forward-aberration on starfield.
- **UI:** β slider (0 to 0.999), camera direction toggle.
- **Assertions (4):**
  1. apparent_rate rendered value matches `libastra::compute_apparent_rate(0.5c, R_STL_REL)` to 0.001.
  2. Planet pixel: R > G > B (visible redshift).
  3. Star at 90° from motion direction: rendered angular position shifted toward forward by SR aberration formula within 1°.
  4. No warp visual (all W=0).
- **Pass:** all 4 pass.

### Scene S03 — STL_Recede_09c

- **Goal:** Dramatic SR effects at β=0.9.
- **Spec basis:** §3.11 + §3.4.
- **Math primitives:** `Rapidity` with `ζ⃗.z = atanh(0.9)`; γ=2.294; β=0.9; `compute_z_kin(0.9c)` = √19 − 1 ≈ 3.359.
- **Rendering:** rear-view; planet dramatically redshifted (deep red); strong forward aberration compression; rear stars mostly invisible (IR).
- **UI:** same as S02.
- **Assertions (4):**
  1. apparent_rate at β=0.9 matches `√((1-0.9)/(1+0.9))` ≈ 0.2294 within 0.001.
  2. Planet R-channel >> G+B (extreme redshift).
  3. Forward hemisphere star density 2-4× rear (aberration).
  4. γ matches `cosh(atanh(0.9))` from libastra.

### Scene S04 — WarpCharge sequence

- **Goal:** Bubble forms over 5 seconds; regime transitions WARP_CHARGE → WARP_CRUISE.
- **Spec basis:** §3.3 (regime transitions), §6 step 4 (smooth-min blend), §6.1 (CFD validity).
- **Math primitives:** RBF eval; W ramps 0→1 over scenario time; `dtau_dt_cosmic(W, grav, γ, true)`.
- **Rendering:** orbiting third-person camera; bubble fades in as violet/blue volumetric glow with sharp boundary at high |∇W|; chaos field activates with faint particles.
- **UI:** play/pause, regime override, W slider.
- **Assertions (4):**
  1. At t=0, pixel at canonical bubble-center position has no bubble color.
  2. At t=2.5s (W=0.5), bubble pixel intensity > 0 and < t=5 intensity.
  3. At t=5s, pixel at canonical bubble-boundary matches `libastra_nexus::eval_rbf_at(...)` expected W value.
  4. Symmetry: pixels at (+x, 0, 0) and (-x, 0, 0) of ship show same W to within 0.01.

### Scene S05 — WarpCruise_2c (THE PAYOFF)

- **Goal:** Kepler-orbiting planet 1 ly behind ship visibly runs BACKWARDS at apparent_rate = −1. The canonical visual test of §3.11.
- **Spec basis:** §3.11 (retarded-time observation); §6.3 (ObservableState); §10 ("Retarded-time orbit reversal" validation row); existing C++ test at `proto/astra_nexus.cpp:639-677`.
- **Math primitives:**
  - `compute_apparent_rate(2c, R_WARP_CRUISE) = -1.000`
  - `observe(ship_pos, ship_vel, t_cosmic, body_pos, 0, R_WARP_CRUISE)` → ObservableState with `t_emit < t_cosmic`
  - `orbit_phase(orbit, observable.t_emit)` for each frame
- **Rendering:** rear-view; planet rendered at `body_state(t_emit)` position (Kepler solved at retarded time). Trail mode shows decaying trail of where planet WAS rendered (visualizes reverse motion). ImGui plot shows orbital_phase over t_cosmic.
- **UI:** v_app slider [−10c, 10c]; orbit period; trail toggle; pause; reset to t_cosmic=0.
- **Assertions (4):**
  1. At v_app = 0 (slider set to 0): `dphase/dt > 0` (forward time).
  2. At v_app = 2c: `dphase/dt < 0` monotonically (orbit running backward). **The locked v0.127 effect.**
  3. At v_app = c exactly: `dphase/dt ≈ 0` (frozen).
  4. Retarded-time math from `observe()` exactly matches rendered orbital_phase to 0.01 radians.
- **Pass criteria:** all 4 assertions pass AND **operator personally confirms visible orbit reversal**.

**Sign-off requirement:** schedule synchronous operator review at end of V5 phase. Operator
must watch the scene, see the planet's orbit visibly run backwards, and record sign-off
in `BUILD_LOG.md` with timestamp. Until this happens, project is incomplete.

### Scene S06 — WarpCruise_10c + Cherenkov (closes 5D-F4)

- **Goal:** Orbit reverses at 9× speed; Cherenkov cone with `cos θ_c = 1/(n·β)`.
- **Spec basis:** §6 step 10 (Cherenkov formula); §7 truth table; Appendix B (formula locked); AUDIT 5D-F4 (gap to close).
- **Math primitives:**
  - `compute_apparent_rate(10c, R_WARP_CRUISE) = -9.000`
  - **NEW in local libastra_nexus:** `compute_cherenkov_angle(W, beta, n_refractive_default)` returns `acos(1/(n·β))` in radians.
  - Provisional `n_refractive_default(W) = 1 + W` per v2 plan; tunable via UI slider.
- **Rendering:** bubble + cone mesh (forward-facing geometric cone with half-angle from cherenkov_angle). Cone tinted blue-cyan per spec.
- **UI:** v_app, W, n-coefficient slider; cone visibility toggle.
- **Assertions (4):**
  1. apparent_rate at v_app=10c matches canonical −9.000 within 0.001.
  2. Cherenkov cone half-angle within 1° of `acos(1/(n·β))` from libastra.
  3. At β → 0, cone collapses; UI shows "Cherenkov inactive: n·β ≤ 1".
  4. Cone widens as W increases (sweep W 0.5 → 1.0; angle increases monotonically). Per cos(theta_c) = 1/(n*beta): higher W => higher n => larger angle.
- **Pass:** all 4 pass. **C++ assertion count: 66 → 69+** with new Cherenkov assertions in local libastra_nexus test suite.

### Scene S07 — PhotonSourceHistory (8000c)

- **Goal:** Source DISAPPEARS (not faded; **gone**) when ship overtakes its photon emission history.
- **Spec basis:** §3.11 photon-source-history bound; `ObservableState.beyond_photon_history` flag.
- **Math primitives:** `observe(...)` → check `beyond_photon_history`; `t_source_start` per body (provisional schema per AUDIT R4).
- **Rendering:** star with explicit `t_source_start = -10⁹ s` (turned on 1 Gy before scenario start). Ship pulls away at v_app=8000c. Each frame: call `observe`; if flag true, omit star from frame.
- **UI:** v_app slider; t_source_start slider; "step time forward by 1 cosmic hour" button.
- **Assertions (4):**
  1. Before crossover, pixel at source position has bright color.
  2. After crossover, pixel at source position has background color (source absent).
  3. Transition is DISCRETE: frame N has source visible; frame N+1 has source absent; NO intermediate fading.
  4. Crossover timing matches cosmic-time at which `beyond_photon_history` first turned true within 1 frame.

### Scene S08 — WarpGravityWell

- **Goal:** Regime composition (`WARP_CRUISE | GRAVITY_WELL = 0x28`); chaos `α_eff` coupling visible; gravitational lensing distinct from warp lensing.
- **Spec basis:** §3.3 regime composition; §7.1 chaos coupling `α_eff = α_base · (1 + k·M·L²/r³)`; §7.4 Warp Exclusion Zone (r > 100·r_s).
- **Math primitives:**
  - `compute_grav_factor(bh_list, ship_pos)` returns `√(1 − r_s/r)` for dominant BH
  - `dtau_dt_cosmic(W, grav, γ, true)` composes
  - α_eff formula per §7.1
- **Rendering:** ship + bubble + BH as black disc with subtle gravitational lensing (separate from warp ∇W lensing); chaos field intensifies as r decreases.
- **UI:** BH mass slider [1, 10⁸ M_sun]; ship-to-BH distance slider [50, 1000 r_s]; v_app, W.
- **Assertions (4):**
  1. UI shows regime as bitmask `WARP_CRUISE | GRAVITY_WELL` (0x28).
  2. Schwarzschild factor `√(1 − r_s/r)` rendered/displayed value matches `libastra::compute_grav_factor()` to 6 decimals.
  3. α_eff displayed = α_base · (1 + k·M·L²/r³) matches §7.1 formula.
  4. dτ/dt_cosmic gauge needle matches `dtau_dt_cosmic()` output.

### Scene S09 — ChaosInstability + Reflex stabilizer

- **Goal:** Fisher-KPP chaos visible; PID Reflex damps; emergency dump triggers visually on excess.
- **Spec basis:** §7.1 chaos PDE; §2.3.1 Reflex Contract (v0.129 NEW); §1.5 double-buffered field.
- **Math primitives:** CUDA chaos PDE (RK2 explicit step) + PID Reflex stub (`reflex_stub.cu`) reads chaos amplitude, emits 3-float control vector.
- **Rendering:** 2D slice heatmap (viridis colormap) + 3D volumetric render of χ field. Time-series plot of `max(χ)`, `mean(χ)`.
- **Script:**
  - t=0..5s: Reflex DISABLED; chaos grows
  - t=5s: Reflex ENABLED; rapid damp
  - t=10..15s: user manually injects chaos via slider; Reflex re-damps; visible feedback loop
- **UI:** Reflex toggle; chaos α_base, D sliders; manual chaos injection slider; emergency dump button.
- **Assertions (4):**
  1. Field stays in [0,1] throughout (no NaN, no overflow per voxel).
  2. CFL stability: at `dt < Δx²/(6D)`, simulation does not blow up; `max(χ)` bounded.
  3. When Reflex enabled at t=5s, `max(χ)` decreases monotonically over ~1s damping period.
  4. Emergency dump fires when chaos exceeds threshold; regime visibly snaps to STL.

### Scene S10 — HubbleHorizon

- **Goal:** Body beyond Hubble horizon rendered FROZEN at horizon-crossing; dimming on separate timescale.
- **Spec basis:** §3.12 cosmological expansion; `ObservableState.beyond_hubble_horizon`.
- **Math primitives:** `observe(...)` returns `beyond_hubble_horizon = true` when `d > c/H₀`.
- **Rendering:** distant body at `d = 1.2 · c/H₀` (beyond Hubble for H₀=70 km/s/Mpc). Body rendered at frozen frame from horizon-crossing instant; color extremely redshifted (near-IR); brightness fading over scenario time.
- **UI:** distance slider; H₀ slider.
- **Assertions (4):**
  1. UI shows `beyond_hubble_horizon = true`.
  2. d_proper displayed in Mpc matches `astra_distance(ship, body)` from libastra.
  3. z_cosmo displayed matches `compute_z_cosmo(d) = H₀·d/c` to 6 decimals.
  4. Body pixel color: R >> G ≈ B (extreme redshift).

**Why separate from S07:** S07 tests kinematic bound (ship overtakes photons); S10 tests
cosmological bound (expansion outruns photons). Different physics; separate scenes.

### Scene S11 — SplitScreen STL_REL vs WARP_CRUISE at v=0.5c

- **Goal:** Side-by-side comparison proves regime-dispatched apparent_rate is real, not artifact.
- **Spec basis:** §3.11; §10 validation row "STL_REL formula was NOT 1/γ"; voyage-demo canonical anchor at `proto/astra_nexus.cpp:537-588`.
- **Math primitives:**
  - `compute_apparent_rate(0.5c, R_STL_REL)` = √(1/3) ≈ 0.5774
  - `compute_apparent_rate(0.5c, R_WARP_CRUISE)` = 0.5
- **Rendering:** split screen — left half STL_REL ship rear view; right half WARP_CRUISE ship rear view; same planet rendered in both; same v_radial. ImGui shows both rates side-by-side.
- **UI:** v_radial slider; toggle "synchronize cosmic time."
- **Assertions (4):**
  1. STL_REL apparent_rate at β=0.5 = 0.5774 ± 0.001 (locked v0.127 value).
  2. WARP_CRUISE apparent_rate at v_app=0.5c = 0.5000 ± 0.001.
  3. Visual orbital-phase ratio matches: STL planet at 0.5774× speed, WARP planet at 0.5× speed.
  4. At v_radial > c: WARP panel shows reverse; STL panel shows "regime invalid" indicator.

### Scene S12 — EyeEarDecoupling at warp egress

- **Goal:** Visualize §6.3 + §8.3 endogenous/exogenous principle. Visual orbit reverses while audio frequency stays current. The literal intersection of book canon + spec architecture + user-facing perception.
- **Spec basis:** §6.3 + §8.3 endogenous/exogenous; book `CANON.md` endogenous/exogenous vocabulary; cycle 1 of *The Long Watch*.
- **Math primitives:** all of S05 (retarded-time) + UI audio-frequency display (NOT real audio playback; display only).
- **Rendering:** rear view shows planet running backward; UI shows two displays:
  - "AUDIO (t_cosmic = NOW): warp drone 247Hz" — updates immediately at warp disengage
  - "VISUAL (t_emit = 1.0 years ago): orbit phase −1.31 rad" — lags by light-travel-time
- **Script:**
  - t=0..10s: WARP_CRUISE at 2c; visual reversed; audio = warp drone (frequency display)
  - t=10s: `warp.disengage(emergency)`; audio = warp shutdown (immediate UI change); visual continues reversed for ~1y scenario time then re-syncs as t_emit catches up
- **UI:** play/pause; "trigger warp disengage" button; scrubber.
- **Assertions (4):**
  1. During warp, UI shows audio_t = cosmic_time, visual_t = retarded_time, with `t_emit < t_cosmic` by `ship_distance/c`.
  2. At t=10s (warp shutdown), audio_t jumps to new value (drone → shutdown label); visual_t continues reverse-walking.
  3. Over warp-shutdown period (t=10 to ~13s simulation time), the audio_t − visual_t gap shrinks asymptotically.
  4. Numerical gap matches `t_cosmic − t_emit` from libastra `observe()` to 6 decimals.

**Why this scene matters:** book canon cycle 1 names endogenous/exogenous as ASTRA's
epistemic vocabulary; spec §6.3 names it as architectural routing rule; this scene
makes it **visually concrete**. The audio-DSP-engineer outsider voice in discovery 5D
specifically called for a "dedicated playtest scenario for warp egress audio-visual
decoupling before Phase E4 ships" — this is that scenario, except for the testbed,
not Phase E4.

---

## Part 4: Algorithm details

### 4.1 Composition rule (§3.2)

```cpp
// libastra_nexus/src/composition.cpp — mirrors proto/astra_nexus.cpp:227
double dtau_dt_cosmic(double W, double grav_factor, double gamma_kin, bool warp_active) {
    double f_w = warp_active ? f_warp_canon(W) : 1.0;
    return f_w * grav_factor / gamma_kin;
}

double f_warp_canon(double W) {
    return std::max(0.5, 1.0 - 0.5 * W * W);
}
```

### 4.2 Rapidity ζ⃗ (§3.7)

```cpp
struct Rapidity {
    Vec3 zeta;
    double omega() const { return zeta.mag(); }
    double gamma() const { return std::cosh(omega()); }  // NEVER 1/sqrt(1-β²)
    double beta()  const { return std::tanh(omega()); }
    Vec3 velocity() const {
        double w = omega();
        if (w < 1e-30) return {0,0,0};
        return zeta * (C_LIGHT * std::tanh(w) / w);
    }
};

constexpr double OMEGA_MAX = 16.811;  // gives γ_max ≈ 10⁷

Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);
    return Rapidity{new_zeta};
}
```

### 4.3 Regime-dispatched apparent rate (§3.11)

```cpp
// libastra_nexus/src/apparent_rate.cpp — mirrors proto/astra_nexus.cpp:258
double compute_apparent_rate(double v_radial, uint32_t regime) {
    double beta = v_radial / C_LIGHT;

    if (regime & R_WARP_CRUISE) {
        // Classical retarded-time. Can go arbitrarily negative.
        return 1.0 - beta;
    }
    if (regime & R_STL_REL) {
        // SR longitudinal Doppler; always positive.
        double bc = beta;
        if (bc >=  0.9999) bc =  0.9999;
        if (bc <= -0.9999) bc = -0.9999;
        return std::sqrt((1.0 - bc) / (1.0 + bc));
    }
    return 1.0 - beta;  // REST/STL_NONREL linear
}
```

### 4.4 Observe() — the 12-step retarded-time workflow (§6.3)

```cpp
// libastra_nexus/src/observe.cpp — mirrors proto/astra_nexus.cpp:309
ObservableState observe(Vec3 ship_pos, Vec3 ship_velocity, double t_cosmic,
                         Vec3 body_pos, double body_metric_shift, uint32_t regime) {
    ObservableState obs = {};
    Vec3 to_body = body_pos - ship_pos;
    obs.d_proper = std::max(to_body.mag(), 1.0);
    Vec3 r_hat = to_body / obs.d_proper;

    obs.v_radial = -ship_velocity.dot(r_hat);
    obs.z_cosmo  = compute_z_cosmo(obs.d_proper);
    obs.z_kin    = compute_z_kin(obs.v_radial);
    obs.z_metric = body_metric_shift;
    obs.z_total  = (1+obs.z_cosmo) * (1+obs.z_kin) * (1+obs.z_metric) - 1;

    double lookback = compute_lookback(obs.d_proper, obs.z_cosmo);
    obs.t_emit = t_cosmic - lookback;

    obs.apparent_rate = compute_apparent_rate(obs.v_radial, regime) / (1 + obs.z_cosmo);
    obs.time_reversed = obs.apparent_rate < 0;

    // Photon-source-history bound (per body's t_source_start)
    obs.beyond_photon_history = (obs.t_emit < body_t_source_start);

    // Hubble horizon
    obs.beyond_hubble_horizon = (obs.d_proper > C_LIGHT / H0_SI);

    return obs;
}
```

### 4.5 Cherenkov angle (NEW; closes 5D-F4)

```cpp
// libastra_nexus/src/cherenkov.cpp — NEW per this project; brings test count 66→69+
double n_refractive_default(double W) {
    return 1.0 + W;  // provisional; tunable via UI in S06
}

double compute_cherenkov_angle(double W, double beta, double (*n_model)(double) = nullptr) {
    double n = n_model ? n_model(W) : n_refractive_default(W);
    if (n * beta <= 1.0) return -1.0;  // inactive (no real angle)
    return std::acos(1.0 / (n * beta));
}
```

Test cases to add (the 3+ new assertions):

```cpp
TEST_CASE("cherenkov_angle inactive when n*beta <= 1") {
    REQUIRE(compute_cherenkov_angle(0.5, 0.3) == doctest::Approx(-1.0));  // n=1.5, β=0.3, nβ=0.45
}
TEST_CASE("cherenkov_angle at beta=0.5, W=1") {
    // n=2, β=0.5 → nβ=1 → angle=0 (degenerate)
    double a = compute_cherenkov_angle(1.0, 0.5);
    REQUIRE(a == doctest::Approx(0.0).epsilon(0.01));
}
TEST_CASE("cherenkov_angle at beta=0.9, W=1") {
    // n=2, β=0.9 → nβ=1.8 → angle=acos(1/1.8)=acos(0.5556)≈0.9818 rad ≈ 56.25°
    double a = compute_cherenkov_angle(1.0, 0.9);
    REQUIRE(a == doctest::Approx(0.9818).epsilon(0.001));
}
TEST_CASE("cherenkov_angle widens as W increases at fixed beta") {
    double a05 = compute_cherenkov_angle(0.5, 0.99);
    double a10 = compute_cherenkov_angle(1.0, 0.99);
    REQUIRE(a10 > a05);  // higher W => higher n => higher n*beta => smaller
                         // cos(theta) => LARGER theta. Cone opens wider, not narrower.
                         // The V0 build caught the original "narrows" wording as a
                         // physics error; the formula cos(theta) = 1/(n*beta) implies
                         // the cone WIDENS toward pi/2 as n*beta grows.
}
```

### 4.6 Chaos PDE — Fisher-KPP RK2 step (§7.1)

```cuda
// kernels/chaos_pde.cu — explicit RK2 update; CFL-bounded
__global__ void chaos_pde_step(
    cudaTextureObject_t chi_in,
    cudaSurfaceObject_t chi_out,
    float alpha_eff, float beta, float D, float dt,
    int N  // 128
) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= N || y >= N || z >= N) return;

    auto sample = [&](float xs, float ys, float zs) {
        return tex3D<float>(chi_in, xs+0.5f, ys+0.5f, zs+0.5f);
    };
    float chi    = sample(x, y, z);
    float chi_px = sample(x+1, y, z), chi_nx = sample(x-1, y, z);
    float chi_py = sample(x, y+1, z), chi_ny = sample(x, y-1, z);
    float chi_pz = sample(x, y, z+1), chi_nz = sample(x, y, z-1);

    float lap = chi_px + chi_nx + chi_py + chi_ny + chi_pz + chi_nz - 6.f*chi;
    float reaction = alpha_eff * chi * (1.f - chi) - beta * chi * chi * chi;
    float chi_new = chi + dt * (D * lap + reaction);
    chi_new = fmaxf(0.f, fminf(1.f, chi_new));

    surf3Dwrite(chi_new, chi_out, x*sizeof(float), y, z);
}
```

**CFL bound:** `dt ≤ Δx² / (6D)`. At Δx ≈ 1m (128³ over ~128m bubble), D = 0.8:
`dt_diff = 1/(6·0.8) = 0.21 s`. Frame dt at 60 FPS = 16.67 ms → 12× under CFL bound.
**Explicit forward-Euler / RK2 is safe; no implicit solver needed.**

### 4.7 RBF spatial-hash eval (§6.2)

```cuda
// kernels/warp_field_eval.cu — O(N=20) per sample after hash lookup
__device__ float eval_warp_field(float3 local_pos, RBFNetworkGPU hash) {
    int3 voxel = make_int3(local_pos / hash.voxel_size);
    voxel.x = clamp(voxel.x, 0, hash.grid_size-1);
    voxel.y = clamp(voxel.y, 0, hash.grid_size-1);
    voxel.z = clamp(voxel.z, 0, hash.grid_size-1);
    uint32_t idx = (voxel.z * hash.grid_size + voxel.y) * hash.grid_size + voxel.x;
    uint32_t offset = hash.voxel_offsets[idx];
    uint32_t count  = hash.voxel_offsets[idx+1] - offset;

    float W = 0.0f;
    for (uint32_t i = 0; i < count; i++) {
        const RBFNode& n = hash.nodes[hash.node_indices[offset + i]];
        float3 d = local_pos - make_float3(n.center[0], n.center[1], n.center[2]);
        W += n.weight * __expf(-dot(d, d) * n.sigma_inv_sq);
    }
    return W;
}
```

---

## Part 5: Performance

### 5.1 Per-pass GPU budget at 1080p, RTX 4070 (16.67 ms total)

| Pass | Budget (ms) |
|---|---|
| Chaos PDE step (RK2) | 1.5 |
| Warp field RBF populate | 1.5 |
| Volume ray-march (warp + chaos) | 3-4 |
| Lensing post-pass | 1.5 |
| Starfield + Doppler + aberration | 1.0 |
| Cherenkov + wake | 0.5 |
| Hull + UI + post-process | 3.0 |
| Reserve | ~4 |

### 5.2 Hardware tier targets

| Target | Hardware | Resolution |
|---|---|---|
| 60 FPS | RTX 4070 | 1080p (minimum) |
| 60 FPS | RTX 4090 | 1440p (recommended) |
| 120 FPS | RTX 5090 | 1080p (upper-tier) |
| 30 FPS | RTX 3060 | 1080p (low-end) |

### 5.3 Headless mode budget

Headless mode does NOT need 60 FPS — it can take 5-10 seconds per scene's canonical render.
**Target: full 12-scene headless run in < 2 minutes total on RTX 4070.**

---

## Part 6: Validation methodology

See `VALIDATION.md` (to be authored during V9). The three layers in summary:

1. **Pixel-level scalar assertions:** each scene exposes a list of expected-pixel checks. PixelSampler reads via `glReadPixels`; compares to canonical math from `libastra_nexus::compute_*()`. Default tolerance: 1% of expected or ±0.01 absolute, whichever larger.

2. **Heatmap-diff against golden PNG:** golden images locked under `assets/reference_renders/`. CI compares headless render to golden; pass if `mean_diff < 0.01` and `max_pixel_diff < 0.10`.

3. **Side-by-side numeric overlay:** every scene shows real-time `rendered vs libastra vs diff` with PASS/FAIL color in ImGui corner overlay.

JSON test report for CI:

```json
{
  "version": "0.1.0",
  "build_commit": "abc123",
  "libastra_nexus_assertion_count": 69,
  "scenes": [...],
  "summary": {"scenes_passed": 12, "scenes_failed": 0, "total_assertions": 48, "assertions_passed": 48}
}
```

**CI gate:** exit 0 iff `summary.scenes_failed == 0`.

---

## Part 7: Build & ship

### 7.1 Configure + build (Windows 11)

```bat
:: From "x64 Native Tools Command Prompt for VS 2022"
cd C:\ASTRA-7\ASTRA_VISUALIZER_02
cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

:: Run interactive:
.\build\astra_visualizer.exe

:: Run headless:
.\build\astra_visualizer.exe --headless --scene=all --output=ci_results\
```

Or via the helper script you'll create at V0: `tools\build.bat`.

### 7.2 CLI surface

```
astra_visualizer.exe                                # interactive, scene picker
astra_visualizer.exe --scene=S05                    # interactive, jump to scene
astra_visualizer.exe --headless --scene=all         # all scenes, CI batch
astra_visualizer.exe --headless --scene=S05 --output=results\
astra_visualizer.exe --regenerate-goldens --scene=all  # operator-sign-off only
astra_visualizer.exe --record=png-seq --scene=S11 --duration=30
astra_visualizer.exe --version
```

### 7.3 Distribution

Output: `build\astra_visualizer.exe` — single-file launchable. Static-linked CUDA runtime
(no `cudart64_*.dll` needed). Static-linked MSVC runtime (no VS Redist needed). Required at
runtime: NVIDIA driver + Windows OS DLLs. That's it.

Distribution shape:
```
ASTRA_VISUALIZER_02_v1\
├── astra_visualizer.exe       (~5-10 MB)
├── assets\
│   ├── hull\astra7_lowpoly.obj
│   ├── starfield\starfield_10k.bin
│   ├── cfd\warp_cfd_rbf_synthetic_v1.json
│   ├── scenarios\s01..s12.json
│   └── reference_renders\s01..s12_canonical.png
└── README.md
```

Optional: ship a sample output gallery (canonical PNGs) so users can compare what their
machine renders against operator-confirmed references.

---

## Part 8: Phase 2+ extensions (out of v1 scope)

- **Real CFD-baked RBF network** from OpenFOAM output (replaces synthetic Alcubierre approximation).
- **Hash-grid SDF for hull** (Instant-NGP style) for 10-16× memory savings.
- **NNE / TensorRT real Reflex inference** (replaces PID stub).
- **OptiX HDR denoising** (sibling Buddhabrot pattern; optional in Phase 2).
- **Real audio playback for S12** via miniaudio (currently UI frequency display only).
- **MP4 video recording** (PNG sequence + ffmpeg post-processing is enough for v1).
- **Substrate-style multi-layer materials** for hull rendering (UE5 pattern).
- **Multi-GPU** if operator runs dual GPUs.
- **Custom RBF authoring tool** (interactive CFD-RBF placement).

---

## Part 9: Position in canon

This is **rig 3 (engine-side rendering verification)** per parent spec §15.8 + discovery 3B-U3:

- Rig 1 — Physics binary (`proto/astra_nexus.cpp`): 66 assertions; mathematical truth
- Rig 2 — LLM bundle (`proto/textverse/`): 9-gate LCP; persona truth
- **Rig 3 — Visual (THIS PROJECT):** pixel-level assertions; visual truth
- Rig 4 — Book canon (`book/CANON.md`); prose discipline
- Rig 5 — Spec audit cadence (§15.10); structural truth

This testbed is **implementation #1 of the dual-implementation discipline (§15.7)** for
the visual axis. UE5 plugin (per `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`) will be
implementation #2. Both consume the same canonical math from `libastra_nexus` + shared
`WarpFieldSample` header. Both produce visuals that should agree. **Testbed's golden PNGs
become canonical reference UE5's renderer must match.**

Per parent spec §15.4 ("revise on findings"): this testbed IS a closed-loop measurement
instrument. Findings surfaced become v0.130 spec revision candidates. Per parent spec
§15.10 (NEW v0.129) audit cadence: each major math change in canon triggers a testbed
run; visual regression triggers spec or code revision.

---

## Closing

The math is locked in `proto/astra_nexus.cpp`. The visual claims are testable. A coding
agent ships this in ~9 weeks of focused work. The validation methodology is mechanical.
The closure is empirical. The Cherenkov gap closes inside this folder's local libastra_nexus.
The operator personally watches S05 and decides whether the project's central physics
commitment is real or just words.

Build it. Run it. Confirm the orbit reversal. File `BUILD_COMPLETE.md`.

---

**Operator:** Bo Chen, Arlington, Texas
**Substrate:** Native Windows 11 + RTX 40-series + CUDA 12.x/13.x + OpenGL 4.6
**Project basis:** `docs/spec-v0.129-tentative-2026-05-16.md`, `proto/astra_nexus.cpp`, `ASTRA_VISUALIZER_PLAN_2026-05-16_v2_FINAL.md`
**Sibling pattern:** `C:\Buddhabrot_CUDA\` (CUDA + OpenGL + GLFW + ImGui + CMake template)

— ASTRA-7 Visualizer 02 — DESIGN_SPEC.md — 2026-05-16 —
