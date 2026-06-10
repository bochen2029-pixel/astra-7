# ASTRA-7 Visualizer — Implementation Plan for Visual Ground-Truth Physics Testbed

**Date:** 2026-05-16
**Status:** Design proposal for coding-agent implementation. NOT yet implemented.
**Author:** Claude Opus 4.7 (operator brief: design a standalone CUDA + C/C++ visual physics testbed that goes beyond the math-only console assertions in `proto/astra_nexus.cpp`)
**Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md` (tentative draft); `proto/astra_nexus.cpp` (1009 lines, 66 assertions after Tier 1A+1B closure)
**Target reader:** Another coding agent who picks this up cold and implements it.

---

## 0. Why this exists

`proto/astra_nexus.exe` proves the math works. 66 C++ assertions verify:
- AstraCoord renormalization (sub-mm precision at 974 Mly reach)
- 3-vector rapidity ζ⃗ math (γ = cosh(ω), OMEGA_MAX clamp at γ = 10⁷)
- Composition rule across regimes (REST, STL_REL, WARP_CRUISE, GRAVITY_WELL)
- Regime-dispatched apparent rate (SR longitudinal Doppler vs classical retarded-time)
- Kepler-at-t_emit orbit reversal under v_apparent > c
- Photon-source-history bound + Hubble horizon flags
- Cross-substrate stdio JSON-RPC bridge

**What it does not prove:** that the math actually produces the *visual phenomena* the spec describes. The spec talks about:

- A warp bubble's metric W(x,t) being volumetrically renderable
- A wake trail behind the bubble
- A Cherenkov cone narrowing as β increases
- Starfield aberration warping star directions forward
- An orbit that "runs backward" when observed at retarded time during warp egress
- A source that disappears (not fades) when ship overtakes its photon history
- Geometric lensing — light rays bent by ∇W near the bubble boundary
- A chaos field χ(x,t) modulating the bubble shell with reaction-diffusion dynamics
- Hull SDF + damage map rendering as the ship's surface
- Doppler-colored starfield with multiplicative composition (1+z_total)

These are **visual claims with mathematical bodies.** The math is locked
(`proto/astra_nexus.cpp`); the visual fidelity is not yet confirmed.

**The gap:** until human eyes can see a frame and confirm "yes, that's what
v_app = 2c looks like — orbit running backward, color shifted to red,
Cherenkov cone open at the calculated half-angle," we cannot say the
implementation is *visually correct*, only *mathematically correct*. UE5
will eventually render these effects (Phase E0-E5 per the deep-dive plan),
but UE5 is heavy, opaque, and engine-bound. **We need a thin layer:** raw
C++/CUDA + OpenGL + ImGui, no engine, that renders the math directly and
lets a human (and pixel-level assertions) confirm "the math produces this
image, and this image is correct."

This plan specifies that thin layer.

---

## 1. Scope + non-goals

### In scope

- **A standalone Windows 11 executable** (`astra_visualizer.exe`) that runs all 11 visual test scenes.
- **C/C++17, CUDA 12.x, OpenGL 4.6, GLFW, Dear ImGui, GLM** — all engine-agnostic, well-documented, header-mostly stacks.
- **Visual rendering** of every physics effect named in spec §§3, 6, 7, 8 that has a visible signature.
- **Pixel-level assertion** layer that samples specific pixels and verifies values against canonical math from `proto/astra_nexus.cpp`.
- **Headless mode** for CI: same scenes render to PNG dumps; assertion layer runs without a window; exit code reports pass/fail.
- **Side-by-side comparison**: each scene displays its analytic prediction (from `astra_nexus` library) next to the rendered image.
- **Linkage to `astra_nexus.cpp`** as a static library; the math is the single source of truth; this app is the visual harness on top.

### Explicitly out of scope

- **No Unreal Engine integration.** This is the engine-agnostic ground-truth layer; UE comes later (per `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`).
- **No production rendering quality.** TSR, Lumen, Nanite, MegaLights — all UE-side. This app uses straight forward-rendering with custom shaders.
- **No game logic.** No persona LLM, no scenarios, no scoring; pure physics → pixels.
- **No audio.** §8.3 audio synthesis is verified separately (MetaSound path; not this app's scope).
- **No Reflex stabilizer.** NNE inference is verified separately.
- **No Apple/Mac/Metal/iOS.** Per CLAUDE.md Platform Discipline (2026-05-15). Windows 11 primary, Linux x86_64 secondary.
- **No new Python.** Per CLAUDE.md Language Discipline (2026-05-15). All new code is C/C++/CUDA/HLSL/GLSL.

### What success looks like

`astra_visualizer.exe` runs on a Windows 11 machine with an NVIDIA GPU.
The user picks a scene from a menu. The scene renders at 60+ FPS. UI
controls let them sweep parameters (e.g., β from 0 to 0.999 for the
Cherenkov scene). For every scene, an on-screen assertion overlay says
"PASS / FAIL" comparing rendered pixels to canonical math. Headless mode
runs all 11 scenes, dumps PNGs to disk, and writes a JSON report; CI
gates on the report.

---

## 2. Technology stack (locked recommendations)

| Layer | Technology | Why this and not alternatives |
|---|---|---|
| Build system | **CMake 3.27+** | Per CLAUDE.md "the only acceptable build system that has Python adjacency, treated as data, not as a Python runtime dependency." Cross-platform; targets MSVC + clang + gcc. |
| C/C++ standard | **C++20** (C++17 minimum) | C++20 for concepts + designated initializers; CUDA 12.x supports it. |
| Compiler (Windows) | **MSVC 19.38+** (Visual Studio 2022 17.8+) | NVCC 12.x integrates well. |
| Compiler (Linux) | **gcc 13+ or clang 16+** | Both support C++20 + CUDA. |
| GPU compute | **CUDA 12.4+** | NVIDIA-only per Platform Discipline; CUDA 12.x for the latest stdio_server compatibility. |
| Graphics API | **OpenGL 4.6 Core Profile** | Mature CUDA interop (`cudaGraphicsGLRegisterBuffer/Image`); compute shaders (GL 4.3+) for fragment-rate compute; simpler than Vulkan for ground-truth visualization. **Not Vulkan** (more boilerplate; production target later). **Not DX12** (engine-specific; we want engine-agnostic). |
| Window + input | **GLFW 3.4+** | De facto standard for OpenGL/Vulkan windowing; works on Windows/Linux; no Apple paths. |
| GL function loader | **GLAD 2** | Single header generated for the GL 4.6 core profile we use. |
| Math library | **GLM 1.0+** | Header-only; matches GLSL/HLSL conventions; well-tested. |
| UI | **Dear ImGui 1.91+** | Single-source-tree drop-in; OpenGL3 + GLFW backends; debug overlays, control panels, plots. |
| Image I/O | **stb_image + stb_image_write** | Single-header; PNG read/write for assertion dumps. |
| JSON | **nlohmann/json** (single-header) | Already in the project's accepted library set per spec §15.6 "Replacements" table. |
| Logging | **spdlog** (header-only) OR plain `fprintf` | spdlog is nicer; plain works. Either acceptable. |
| Test framework | **doctest** (single-header) OR **Catch2** | Per spec §15.6 "Replacements" table both are approved. doctest is lighter. |
| Linkage | **Static-link `astra_nexus` as `libastra_nexus.a` / `astra_nexus.lib`** | The math library; this app links against it directly so every numeric trace to the same source as the math test. |

### What we explicitly are NOT using

- **Vulkan** — too heavy for a ground-truth visualization tool; production-stack-y. Use if and only if OpenGL proves insufficient (unlikely).
- **DirectX 12** — engine-specific; closer to UE production target but locks us into Windows-only and adds boilerplate.
- **OptiX or RTX ray-tracing extensions** — proprietary; we want straight compute-shader ray-marching that any GPU can run.
- **Qt or wxWidgets** — too heavy for a debug viewer. ImGui is right.
- **OpenGL ES** — mobile-targeted; not our path.
- **WebGPU / Dawn** — emerging but not yet production-stable on Windows native; reconsider if the project later wants a web-based visualization.

---

## 3. Architecture overview

```
┌──────────────────────────────────────────────────────────────────┐
│  astra_visualizer.exe                                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ App: GLFW window + GL context + ImGui setup + main loop    │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ SceneRouter: list of registered Scenes; UI for switching;  │  │
│  │ shared parameter UI (β, regime, W, body positions, ...)    │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ Scene Impls (one IScene per visual phenomenon)             │  │
│  │  ┌──────────────────┐  ┌──────────────────┐                │  │
│  │  │ WarpBubbleAtRest │  │ CherenkovCone    │  ...11 scenes  │  │
│  │  └──────────────────┘  └──────────────────┘                │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ Renderer (OpenGL 4.6 wrappers)                             │  │
│  │  - Compute shaders for ray-march, chaos PDE, Doppler       │  │
│  │  - Graphics pipelines for visualization composites         │  │
│  │  - GL/CUDA shared buffer registration                      │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ CUDA kernels (the math compute layer)                      │  │
│  │  - chaos_pde.cu  (Fisher-KPP solver, double-buffered)     │  │
│  │  - warp_field.cu (CFD-RBF eval + ∇W)                       │  │
│  │  - obs_calc.cu   (per-body retarded time)                  │  │
│  │  - sdf_sphere_trace.cu (hull SDF traversal)                │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ libastra_nexus.lib (linked from proto/astra_nexus.cpp)     │  │
│  │  - canonical math (compose, observe, compute_apparent_rate)│  │
│  │  - 66 assertions still callable as test_run_all()          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ValidationLayer: pixel-sampling + assertion comparison     │  │
│  │  - PixelSampler reads specific framebuffer pixels          │  │
│  │  - Comparator checks vs canonical math from libastra_nexus │  │
│  │  - On-screen PASS/FAIL overlay + JSON output for CI        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Output: PNG dumps, MP4 (optional), JSON test reports       │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 Dual-mode operation

- **Interactive mode:** GLFW window + ImGui UI. Operator picks scenes, sweeps parameters, sees PASS/FAIL overlay. 60+ FPS target.
- **Headless mode:** `--headless --scene=all --output=test_results/`. No window; runs each scene's "canonical configuration" (e.g., Cherenkov at β=0.5, 0.9, 0.99); dumps PNG per scene + JSON report. Exit code 0 if all assertions pass, else 1. Suitable for CI.

CLI:
```
astra_visualizer.exe                            # interactive, scene chooser
astra_visualizer.exe --scene=CherenkovCone      # interactive, jump to scene
astra_visualizer.exe --headless --scene=all     # run all scenes headless, dump artifacts
astra_visualizer.exe --headless --scene=all --output=ci_results/
astra_visualizer.exe --record=mp4 --scene=FullVoyageDemo --duration=30  # video capture
```

### 3.2 Linkage with `astra_nexus.cpp`

Two-step refactor of the existing math binary:

**Step 1:** Split `astra_nexus.cpp` into a static library + thin `main()`:

```
proto/
├── astra_nexus.cpp          (existing; keep working as main exe)
├── libastra_nexus/          (NEW; just the math + test_run_all)
│   ├── include/astra_nexus/
│   │   ├── coord.h          (AstraCoord, astra_distance)
│   │   ├── rapidity.h       (Rapidity, integrate)
│   │   ├── composition.h    (dtau_dt_cosmic, schwarzschild_r, compute_grav_factor)
│   │   ├── apparent_rate.h  (compute_apparent_rate)
│   │   ├── observe.h        (Observable, observe, compute_z_kin, compute_z_cosmo)
│   │   ├── kepler.h         (solve_kepler_E, orbit_phase)
│   │   ├── stdio_server.h   (run_stdio_server)
│   │   └── test_suite.h     (run_all_tests, returns pass/fail counters)
│   ├── src/
│   │   └── *.cpp            (same code, split per header)
│   └── CMakeLists.txt
└── build.bat                (updated to build the lib first, then exe)
```

**Step 2:** The visualizer's CMakeLists.txt links against `libastra_nexus`:

```cmake
add_subdirectory(${CMAKE_SOURCE_DIR}/../proto/libastra_nexus libastra_nexus_build)
target_link_libraries(astra_visualizer PRIVATE astra_nexus)
```

This way, every numeric value the visualizer compares against is the **same
implementation** that runs the 66 assertions. Single source of truth.

---

## 4. Project structure

```
proto/visualizer/                                # NEW: lives alongside proto/textverse and proto/libastra_nexus
├── CMakeLists.txt
├── README.md
├── build.bat                                    # Windows convenience
├── build.sh                                     # Linux convenience
├── third_party/
│   ├── glfw/                                    # vendored submodule
│   ├── glad/                                    # generated for GL 4.6 core
│   ├── glm/                                     # header-only submodule
│   ├── imgui/                                   # vendored
│   ├── stb/                                     # stb_image.h, stb_image_write.h
│   ├── doctest/                                 # single-header
│   └── nlohmann_json/                           # single-header
├── shaders/
│   ├── ray_march_warp.comp                      # GLSL compute shader
│   ├── starfield_doppler.frag                   # GLSL fragment
│   ├── starfield.vert
│   ├── hull_sdf.comp                            # GLSL compute, sphere trace
│   ├── chaos_field_render.comp                  # 3D field → 2D slice visualization
│   ├── lensing_quad.frag                        # background with ∇W deflection
│   ├── ui_overlay.frag                          # ImGui-rendered overlays
│   └── common.glsl                              # shared utility functions
├── kernels/
│   ├── chaos_pde.cu                             # CUDA Fisher-KPP solver
│   ├── warp_field_eval.cu                       # CFD-RBF eval at sample points
│   ├── observation_calc.cu                      # per-body retarded time
│   ├── ism_impact.cu                            # §7.2 ISM dispatch visualization
│   └── kernels.h                                # C++ declarations
├── src/
│   ├── main.cpp                                 # entry: GLFW + GL + ImGui + main loop
│   ├── app/
│   │   ├── App.cpp / App.h                      # main app class
│   │   ├── SceneRouter.cpp / .h                 # scene registration + switching
│   │   ├── CLI.cpp / .h                         # command-line parser
│   │   └── HeadlessMode.cpp / .h                # CI / batch rendering path
│   ├── renderer/
│   │   ├── GLContext.cpp / .h                   # GL setup + debug callback
│   │   ├── ComputeProgram.cpp / .h              # compute shader loader
│   │   ├── GraphicsProgram.cpp / .h             # vert+frag shader loader
│   │   ├── Texture.cpp / .h                     # GL texture wrapper
│   │   ├── Buffer.cpp / .h                      # SSBO + UBO wrappers
│   │   ├── CudaGLInterop.cpp / .h               # cudaGraphicsGLRegister*
│   │   └── RenderPass.cpp / .h
│   ├── physics/
│   │   ├── PhysicsCore.cpp / .h                 # facade over libastra_nexus
│   │   ├── RBFNetwork.cpp / .h                  # CFD-RBF + spatial hash
│   │   ├── ChaosField.cpp / .h                  # 128³ chaos field state mgmt
│   │   ├── HullSDF.cpp / .h                     # SDF loader / generator
│   │   └── StateBus.cpp / .h                    # simplified state container (mirrors §4.2 schema)
│   ├── scenes/
│   │   ├── IScene.h                             # interface
│   │   ├── SceneBase.cpp / .h                   # shared helpers
│   │   ├── WarpBubbleAtRest.cpp / .h            # Scene 1
│   │   ├── WarpBubbleCruise.cpp / .h            # Scene 2
│   │   ├── CherenkovCone.cpp / .h               # Scene 3
│   │   ├── GeometricLensing.cpp / .h            # Scene 4
│   │   ├── RetardedTimeOrbitReversal.cpp / .h   # Scene 5
│   │   ├── PhotonSourceHistory.cpp / .h         # Scene 6
│   │   ├── ChaosPDEVisualization.cpp / .h       # Scene 7
│   │   ├── HullSDFRayMarch.cpp / .h             # Scene 8
│   │   ├── CompositionRuleGauge.cpp / .h        # Scene 9
│   │   ├── RegimeContrast.cpp / .h              # Scene 10
│   │   └── FullVoyageDemo.cpp / .h              # Scene 11
│   ├── validation/
│   │   ├── PixelSampler.cpp / .h
│   │   ├── Assertion.cpp / .h
│   │   ├── ScalarPixelAssertion.cpp / .h
│   │   ├── HeatmapDiffAssertion.cpp / .h
│   │   ├── TestReport.cpp / .h
│   │   └── ValidationOverlay.cpp / .h
│   ├── ui/
│   │   ├── ImGuiSetup.cpp / .h
│   │   ├── ScenePicker.cpp / .h
│   │   ├── ParameterPanel.cpp / .h
│   │   ├── PerformancePanel.cpp / .h
│   │   └── ValidationPanel.cpp / .h
│   └── util/
│       ├── Logger.cpp / .h
│       ├── PngWriter.cpp / .h
│       ├── VideoRecorder.cpp / .h (optional; can skip in v1)
│       └── Color.cpp / .h           # blackbody, Doppler color shift helpers
├── tests/                                       # doctest-driven internal tests
│   ├── test_rbf_eval.cpp
│   ├── test_chaos_pde_step.cpp
│   ├── test_observation_calc.cpp
│   └── test_validation_pixel_sample.cpp
└── assets/                                      # baked SDFs, RBF networks, test refs
    ├── hull_sdf_test_v1.bin                     # 256³ float16 baked from a simple test hull
    ├── warp_cfd_rbf_test_v1.json                # ~50-node test RBF network (synthetic, not from real CFD)
    └── reference_renders/                        # PNG goldens per scene
        ├── warp_bubble_rest_canonical.png
        ├── cherenkov_beta_0_5.png
        └── ... etc
```

### 4.1 CMake structure (one source of truth for build)

```cmake
# proto/visualizer/CMakeLists.txt
cmake_minimum_required(VERSION 3.27)
project(astra_visualizer LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_ARCHITECTURES 86 89 90)  # RTX 30, 40, 50 series

# Link astra_nexus math library
add_subdirectory(${CMAKE_SOURCE_DIR}/../libastra_nexus libastra_nexus_build)

# Third-party (vendored)
add_subdirectory(third_party/glfw)
add_subdirectory(third_party/glad)
add_subdirectory(third_party/imgui)

# GLM, stb, json, doctest are header-only
add_library(headeronly INTERFACE)
target_include_directories(headeronly INTERFACE
    third_party/glm
    third_party/stb
    third_party/nlohmann_json
    third_party/doctest
)

# Main executable
add_executable(astra_visualizer
    src/main.cpp
    src/app/App.cpp
    src/app/SceneRouter.cpp
    src/app/CLI.cpp
    src/app/HeadlessMode.cpp
    # ... renderer, physics, scenes, validation, ui, util sources ...
)

target_link_libraries(astra_visualizer PRIVATE
    astra_nexus       # math
    glfw glad imgui
    headeronly
    CUDA::cudart
)

# CUDA kernels compiled separately and linked
add_library(visualizer_kernels STATIC
    kernels/chaos_pde.cu
    kernels/warp_field_eval.cu
    kernels/observation_calc.cu
    kernels/ism_impact.cu
)
set_target_properties(visualizer_kernels PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
)
target_link_libraries(astra_visualizer PRIVATE visualizer_kernels)

# Shaders are embedded as resources (one-time at config time)
# Or loaded from disk relative to executable

# Tests
enable_testing()
add_subdirectory(tests)
```

---

## 5. The 11 visual test scenes (detailed)

Each scene has the same structural pattern:
1. **Goal** — what physical effect is being verified visually.
2. **Spec basis** — exact spec section + line number.
3. **Math primitives used** — which `libastra_nexus` calls.
4. **Rendering technique** — how the pixels get produced.
5. **UI controls** — what parameters the user can sweep.
6. **Assertions** — pixel-level checks against canonical math.
7. **Pass criteria** — what makes the scene pass.

### Scene 1: WarpBubbleAtRest

**Goal:** Visualize the metric field W(x,t) of a stationary warp bubble.
Confirm the bubble is a closed, smooth, axially-symmetric shape; visualize
∇W as gradient arrows; sample W at the center vs. boundary vs. far field.

**Spec basis:** §6 Unified Sampler step 4 (conformal bubble SDF, smooth-min blend);
§6.1 CFD validity bounds; §6.2 RBF spatial acceleration.

**Math primitives:**
- `astra::libastra_nexus::eval_rbf_at(local_pos, hash)` — CFD-RBF sample
- `astra::smooth_min(a, b, k)` — smooth-min blend
- Internal: `compute_metric_gradient(p, state)` — for ∇W arrows

**Rendering technique:**
- Volumetric ray-march via OpenGL compute shader (`shaders/ray_march_warp.comp`)
- Per-pixel: shoot a ray; sample W at 256 steps; accumulate color by `vec4(W, chaos, 0, density)` blending
- Result: bubble appears as a translucent volumetric blob; user can rotate camera
- Wireframe overlay: ∇W arrows at a sparse 8³ grid for direction visualization

**UI controls:**
- Camera rotation (mouse drag) + zoom (scroll)
- Slider: smooth-min `k` parameter (visual tuning per spec §6 step 4)
- Slider: RBF network selector (provided test RBF or load custom)
- Toggle: show ∇W arrows
- Toggle: show RBF node centers as small spheres (debug)

**Assertions (3 pixel samples + 1 invariant):**
1. **Pixel at bubble center** in the W-coded color channel: `W_center > 0.9` (the bubble's metric is maximum at center).
2. **Pixel at bubble boundary** (samples the surface at known radius): `0.4 < W_boundary < 0.6` (smooth transition).
3. **Pixel at far-field** (10 × bubble radius): `W_far < 0.01` (RBF has finite support).
4. **Symmetry invariant:** sample a pixel at `(+x, 0, 0)` and `(-x, 0, 0)`; both should have the same W to within 0.01 (axial symmetry around the ship).

**Pass criteria:** all 4 assertions pass. ImGui overlay shows PASS in green.

**Reference render:** golden PNG at canonical camera angle stored in
`assets/reference_renders/warp_bubble_rest_canonical.png`. CI compares the
headless render to the golden with mean-pixel-diff < 1% tolerance.

---

### Scene 2: WarpBubbleCruise (Wake)

**Goal:** Visualize the wake trail behind the bubble when moving. Confirm
that v_apparent > 0 produces a trailing metric extension.

**Spec basis:** §6 step 7 (wake metric + vortex contributions); §3.6
(spatial update under relativistic motion); §7 truth table WARP_CRUISE row.

**Math primitives:**
- `astra::libastra_nexus::compute_wake_metric(local_pos, view_dir, v_apparent, state)` — wake contribution to W
- Composition: `W_total = smooth_min(bubble, wake_contribution)`

**Rendering technique:**
- Same compute-shader ray-march as Scene 1
- Bubble moves through volume at chosen v_apparent
- Camera follows from a "trailing observer" position
- Wake renders as elongated trail with diminishing W along ship's motion vector

**UI controls:**
- Slider: `v_apparent` in [0, 100c] (range below + above light speed)
- Slider: bubble motion direction (Euler angles)
- Slider: wake decay constant (visual tuning)
- Toggle: show motion vector arrow
- Toggle: snapshot mode (freeze bubble; static viewing)

**Assertions:**
1. **Wake exists when v_apparent > 0:** sample pixel one bubble-radius behind the ship; expect `W_wake > 0.1`.
2. **Wake is absent when v_apparent = 0:** same pixel; expect `W_wake < 0.01`.
3. **Wake scales with v_apparent:** at v_app = 10c, sample is brighter than at v_app = 1c.
4. **Front of bubble symmetric to rest case:** sample pixel one radius ahead of ship; matches Scene 1's boundary intensity.

**Pass criteria:** all 4 assertions pass.

---

### Scene 3: CherenkovCone

**Goal:** Visualize the Cherenkov-analog cone emerging from the bubble at
increasing β. Verify the half-angle matches `cos θ_c = 1 / (n · β)` from
spec §6 step 10.

**Spec basis:** §6 step 10 (Cherenkov angle formula); §7 truth table
Cherenkov row; Appendix B (formula locked).

**Math primitives:**
- `astra::libastra_nexus::cherenkov_angle(W, beta, n_model)` — returns θ_c in radians
- Provisional `n(W) = 1 + W` per the deep-dive `pre-Phase-E1` value

**Rendering technique:**
- Bubble rendered same as Scene 2
- Cone overlay: instanced cone-shape mesh anchored at the bubble center, oriented along ship velocity, half-angle = θ_c
- Mesh tinted by chaos intensity for aesthetic
- The cone is GEOMETRIC, not volumetric (the cone visualizes the angle; the actual rendering of relativistic-emission radiation is Phase E5+ UE5 work)

**UI controls:**
- Slider: β in [0, 0.999]
- Slider: index of refraction model parameter (the `1` in `n = 1 + W`)
- Toggle: show analytical θ_c value as ImGui text overlay
- Toggle: cone wireframe vs solid

**Assertions:**
1. **At β = 0.5:** cone half-angle within 1 degree of math's `acos(1/(n·0.5))`.
2. **At β = 0.9:** cone half-angle within 1 degree.
3. **At β = 0.999:** cone half-angle within 0.5 degree (tightest cone, hardest test).
4. **At β → 0:** cone collapses to undefined / no cone rendered (per spec §7 truth table "undef" cells).

**Pass criteria:** assertions 1-3 pass; assertion 4 confirms the
edge-case handling.

---

### Scene 4: GeometricLensing

**Goal:** Visualize starfield distortion caused by ∇W ray deflection near
the bubble boundary. Verify that the deflection magnitude matches
`α_lens · ∇W · Δs` from spec §6 step 9.

**Spec basis:** §3.4 (geometric lensing as third effect); §6 step 9
(ray-deflection contribution); Appendix B (α_lens provisional).

**Math primitives:**
- `astra::libastra_nexus::eval_metric_gradient(pos, state)` — returns ∇W
- Ray bending integrated along ray-march steps

**Rendering technique:**
- Background: synthetic starfield (procedurally placed white dots on black)
- Foreground: ray-march the warp bubble
- For each ray: at each march step, accumulate deflection per `α_lens · ∇W · Δs`
- The deflected ray determines which background star (if any) it samples
- Result: stars APPEAR DISPLACED near the bubble's silhouette; classic gravitational-lens / Einstein-ring-like appearance

**UI controls:**
- Slider: `α_lens` from 0 (no deflection) to 10 (extreme)
- Slider: bubble radius (visual scale)
- Toggle: show ray paths (debug; shows curved rays as a 2D top-down view)
- Slider: starfield density

**Assertions:**
1. **No deflection at α_lens = 0:** stars appear at their natural positions.
2. **Visible deflection at α_lens > 0.5:** stars within 2 bubble radii are visibly displaced by at least 1 pixel.
3. **Far-field unaffected:** stars at >10 bubble radii are not deflected.
4. **Symmetric deflection:** stars on opposite sides of the bubble are deflected symmetrically.

**Pass criteria:** all 4 assertions pass; visual matches classic
gravitational-lens illustration shape.

---

### Scene 5: RetardedTimeOrbitReversal

**Goal:** Visualize a body in orbit appearing to run BACKWARDS as the ship
warps away from it at v_apparent > c. This is the most counterintuitive
visual claim in the spec; it must be seen to be confirmed.

**Spec basis:** §3.11 (retarded-time observation; regime-dispatched
apparent-rate formula); §10 "Retarded-time orbit reversal" validation row;
the existing 3-assertion C++ test in `astra_nexus.cpp:639-677`.

**Math primitives:**
- `astra::libastra_nexus::observe(ship_pos, ship_vel, t_cosmic, body_pos, body_metric_shift, regime)` → ObservableState
- `astra::libastra_nexus::orbit_phase(orbit, t_emit)` → orbital phase at retarded time
- Per-frame: solve `t_emit`; sample Kepler at `t_emit`; render body at that orbital phase

**Rendering technique:**
- Scene: a central star + a planet orbiting it (canonical "Earth-like at 1 ly")
- Ship starts at rest 1 ly from the star; warps away at chosen v_apparent
- Camera tracks from the ship's POV (rear-view)
- The planet renders at its retarded-time orbital phase
- An ImGui plot shows: x-axis = `t_cosmic`; y-axes = (orbital_phase_predicted, orbital_phase_rendered, t_emit_difference)
- When v_apparent > c, the rendered orbital_phase DECREASES over time (orbit running backward) — VISUALLY VERIFIABLE

**UI controls:**
- Slider: `v_apparent` in [-50c, 50c] (negative = approach)
- Slider: orbit period (1 day to 1 year)
- Slider: orbit inclination (so the planet visibly traces a circle on screen)
- Toggle: show retarded-time numerical readout
- Button: "Reset to t_cosmic=0"
- Button: "Trail mode" — leaves a fading trail of where the planet was rendered, visualizing the reverse motion

**Assertions:**
1. **At v_apparent = 0:** orbital phase advances monotonically (forward in time). Sample dphase/dt > 0.
2. **At v_apparent = 2c:** orbital phase DECREASES monotonically (dphase/dt < 0). This is the locked v0.127 effect.
3. **At v_apparent = c (exactly):** orbital phase frozen (dphase/dt ≈ 0).
4. **The retarded-time math from `observe()` exactly matches the rendered orbital_phase to 0.01 radians.**

**Pass criteria:** all 4 assertions pass; the operator can SEE the orbit
running backward in the rendered view; the side-by-side numerical plot
confirms the math.

**Note:** This is THE scene that proves the spec's most distinctive
physics claim. Headless mode captures a 30-second trail of orbital
positions and dumps as PNG; the assertion is that the rendered trail
traverses the orbit in the opposite direction from the math's `t_cosmic`
advance.

---

### Scene 6: PhotonSourceHistory

**Goal:** Visualize a source DISAPPEARING (not fading) when the ship has
overtaken every photon it ever emitted (the `beyond_photon_history`
property from spec §3.11).

**Spec basis:** §3.11 photon-source-history bound; ObservableState.beyond_photon_history flag.

**Math primitives:**
- `observe(...)` → check `beyond_photon_history` flag
- `t_source_start` per body (per AUDIT R4 / future body-generation schema)

**Rendering technique:**
- Scene: a star with explicit `t_source_start = -10⁹ s` (the star "turned on" 10⁹ seconds before scenario start)
- Ship starts at rest near the star; warps away at v_apparent > c
- Each frame: call `observe(...)`; if `beyond_photon_history == true`, omit star from frame
- Otherwise render star at retarded-time-resolved color
- Visual: at some moment, the star JUST DISAPPEARS — no fade, no transition

**UI controls:**
- Slider: `v_apparent` (must exceed c for the effect)
- Slider: source's `t_source_start` (how long the source has existed)
- Slider: initial ship-to-source distance
- Toggle: show numerical t_emit + t_source_start readout
- Button: "Step time forward by 1 cosmic hour"

**Assertions:**
1. **Before crossover:** source renders normally.
2. **After crossover:** source does NOT render. (Pixel-sample at source position; expect background color, not source color.)
3. **The transition is discrete:** previous frame had source visible; current frame has it absent; no intermediate "fading" state.
4. **The transition timing matches:** the cosmic-time at which the crossover happened matches `t_now` where `observe()`'s `beyond_photon_history` first turned true to within one frame.

**Pass criteria:** all 4 assertions pass; the operator can see the source
abruptly vanish; the timing matches math.

**Why this matters:** spec §3.11 says explicitly: *"the source is gone — not faded, not redshifted to extinction, gone, because no photon remains to be received."* Most fictional warp treatments show fade. This scene proves the spec's distinct claim.

---

### Scene 7: ChaosPDEVisualization

**Goal:** Visualize the chaos field χ(x,t) evolving under the Fisher-KPP
PDE on the bubble shell. Confirm that the field reacts diffuses correctly,
that double-buffering produces no race artifacts, and that BH coupling
modulates α_eff as specified.

**Spec basis:** §1.5 (double-buffered state); §7.1 (chaos PDE BH coupling
α_eff = α_base · (1 + k·M·L²/r³)); §4.6 (chaos field convergent-forward-integration re-init).

**Math primitives:**
- CUDA kernel `chaos_pde.cu` — Fisher-KPP solver
- `α_eff` formula from §7.1 evaluated per BH-distance configuration

**Rendering technique:**
- The chaos field is 128³; visualized as a 2D slice (XY plane through bubble center) using a heatmap (e.g., viridis colormap on χ ∈ [0,1])
- Animation plays in real-time; ImGui slider scrubs through history
- Optional 3D volumetric render (similar to Scene 1's compute shader) for full-field visualization

**UI controls:**
- Slider: `α_base` in [1.0, 5.0]
- Slider: `β` (PDE damping coefficient) in [1.0, 20.0]
- Slider: `D` (diffusion) in [0.1, 2.0]
- Slider: BH mass + distance (drives α_eff scaling per §7.1)
- Slider: time step `dt` (CFL-bounded indicator displayed)
- Button: reset field to baseline noise (the §4.6 re-init pattern)
- Button: pause / resume / step-once
- Toggle: 2D slice vs 3D volumetric
- Plot: max(χ), mean(χ), energy(∫χ²) over last N frames

**Assertions:**
1. **Field stays in [0,1]:** every voxel; throughout simulation.
2. **CFL stability:** at dt < Δx²/(6D), simulation does not blow up; max(χ) bounded.
3. **CFL violation:** at dt > 2× CFL limit, simulation visibly explodes (this is a NEGATIVE test — proves the stability bound is real; useful for ground truth on what NOT to ship).
4. **BH coupling activates α_eff scaling:** at M = solar mass, r = 50·r_s, the α_eff displayed value matches `α_base · (1 + k·M·L²/r³)` per the §7.1 formula.
5. **Re-init produces convergent steady state:** restarting with baseline noise, after N=60 frames the field converges (max(|χ̇|) below threshold).

**Pass criteria:** assertions 1, 2, 4, 5 pass; assertion 3 demonstrates
the failure mode visibly (for documentation; not a failure of the scene).

---

### Scene 8: HullSDFRayMarch

**Goal:** Visualize the ship's hull rendered via SDF sphere-tracing. Test
the §1.3 dual-binding (cudaTextureObject_t for read; cudaSurfaceObject_t
for damage write). Visualize hull damage events updating the surface in
real time.

**Spec basis:** §1.3 (Hull SDF + additive damage map); §8.1 (DX12-CUDA
shared resource ownership — adapted here for OpenGL-CUDA interop).

**Math primitives:**
- CUDA kernel `sdf_sphere_trace.cu` — sphere-traces the hull SDF
- Damage write via `cudaSurfaceObject_t.surf3Dwrite()`

**Rendering technique:**
- Base SDF: 256³ float16 volume texture
- For a test hull, use a procedurally generated simple shape (sphere + cylinder + box composite — represents ship hull at minimum fidelity)
- For each pixel, ray-march into the SDF
- On hit, render with simple Phong-like shading
- ImGui button "Inflict damage at cursor" reads cursor screen-space; ray-casts to find world-space hit; CUDA surf3Dwrite a Gaussian bump there

**UI controls:**
- Camera orbit / zoom
- Button: "Inflict damage at cursor" + slider: damage magnitude + slider: damage radius
- Button: "Reset hull" (clear damage map to zero)
- Toggle: show SDF as wireframe / show damage map as colored overlay
- Slider: hull resolution at runtime (256³ → 128³ → 64³ — verifies §1.3 tolerance)

**Assertions:**
1. **Pristine hull SDF renders correctly:** silhouette matches expected hull shape.
2. **Damage causes visible surface deformation:** after one damage event, a dent appears at the impact location.
3. **Damage persists across frames:** dent is still there next frame (verifies persistent surface writes).
4. **Damage composes additively:** two damage events at same location produce larger dent than one (verifies §1.3 additive-damage rule).

**Pass criteria:** all 4 assertions pass; the dual-binding pattern is
empirically validated in OpenGL-CUDA interop (functionally identical to
DX12-CUDA case the spec locks).

---

### Scene 9: CompositionRuleGauge

**Goal:** Visualize the composition rule `dτ_ship/dt_cosmic` as a gauge
that updates live with the ship's regime. Verify each regime's value
matches `dtau_dt_cosmic()` from `libastra_nexus`.

**Spec basis:** §3.2 (composition rule); §3.7 (rapidity discipline);
§7 truth table (`τ_ship rate` row for each regime).

**Math primitives:**
- `astra::libastra_nexus::dtau_dt_cosmic(W_warp, grav_factor, gamma_kin, warp_active)`
- `astra::libastra_nexus::compute_grav_factor(bh_list, ship_pos)`
- `astra::libastra_nexus::Rapidity::gamma()`

**Rendering technique:**
- Two visual elements:
  1. **Gauge** (ImGui-rendered radial/circular dial): shows current dτ/dt as a needle on a [0, 1] dial.
  2. **Time-comparison animation:** two clocks — one ticking at `t_cosmic` rate (universe), one at `τ_ship` rate (ship). Visible separation grows over time at dilated regimes.
- A regime-dispatched mathematical readout panel shows each factor: f_warp(W), Schwarzschild, weak-field-other, γ_kin — and their product.

**UI controls:**
- Slider: ship velocity β (drives γ_kin)
- Slider: ship-to-BH distance (drives Schwarzschild factor)
- Slider: warp factor W (drives f_warp)
- Regime selector: REST / STL_REL / WARP_CRUISE / GRAVITY_WELL / WARP+GRAVITY combo
- Toggle: dual-clock animation play/pause
- Button: "Reset clocks"

**Assertions:**
1. **REST (β=0, W=0, no BH):** dτ/dt = 1.000 exactly.
2. **STL_REL γ=2:** dτ/dt = 0.500 exactly.
3. **WARP_CRUISE W=1, no BH:** dτ/dt = 0.5 (per `f_warp_canon(1) = 0.5`).
4. **Full composition W=0.8, grav=0.9, γ=2:** dτ/dt = f_warp(0.8) · 0.9 / 2 ≈ 0.306.
5. **Gauge needle position matches the readout numeric value to within 0.01.**

**Pass criteria:** all 5 assertions pass; visual gauge accurately reflects math.

---

### Scene 10: RegimeContrast

**Goal:** Visualize side-by-side the SAME observed body under STL_REL vs.
WARP_CRUISE at the same v_radial value. Confirms the regime-dispatched
apparent-rate formulas produce visibly different results — the v0.127
regime-distinction lock.

**Spec basis:** §3.11 regime-dispatched apparent rate; §7 truth table
t_obs rate row (STL_REL = √((1-β)/(1+β)); WARP_CRUISE = 1 - v_app/c).

**Math primitives:**
- `astra::libastra_nexus::compute_apparent_rate(v_radial, regime)`

**Rendering technique:**
- Split screen: left half is STL_REL regime; right half is WARP_CRUISE
- Same body (star + orbiting planet) rendered in both halves
- Same v_radial value (a slider)
- The planet's apparent orbital phase advances at different rates in the two halves
- Numerical readout shows both rates side by side

**UI controls:**
- Slider: `v_radial` in [0, 1.5c] (lets WARP go above c; STL clamps below c)
- Toggle: synchronize cosmic time across both regimes
- Slider: orbital period

**Assertions:**
1. **At v_radial = 0.5c (STL_REL):** apparent_rate = √(0.5/1.5) ≈ 0.5774. Matches the locked v0.127 value to 4 decimals.
2. **At v_radial = 0.5c (WARP_CRUISE):** apparent_rate = 0.5. Matches the locked v0.127 value to 4 decimals.
3. **The visual phase-progression of the two planets has the predicted ratio:** WARP planet at 0.5c moves at 0.5× speed; STL planet at 0.5c moves at 0.5774× speed; ratio matches math.
4. **At v_radial > c (only WARP allowed):** WARP planet reverses; STL panel shows "regime invalid" indicator (STL_REL requires β < 1).

**Pass criteria:** all 4 assertions pass. The user can SEE the regime
distinction is real, not a math artifact.

---

### Scene 11: FullVoyageDemo

**Goal:** Cinematic playback that sweeps through every regime in sequence
(REST → STL_NONREL → STL_REL → WARP_CHARGE → WARP_CRUISE → WARP_SHUTDOWN →
back to STL → CRYOSLEEP), demonstrating the integrated visual effect of
the whole physics stack. Equivalent to the existing `demo_voyage()` in
astra_nexus.cpp, but visual.

**Spec basis:** All of §3, §6, §7; the voyage-demo table in §10 locked as canonical.

**Math primitives:**
- All of the above scenes' primitives, composed

**Rendering technique:**
- Camera follows the ship through a scripted timeline
- Background starfield + a "destination" star system (for reference visual)
- All effects active simultaneously: warp bubble, wake, Cherenkov cone (when applicable), lensing, retarded-time-aware starfield
- ImGui timeline scrubber lets the user pause/rewind through the voyage
- The 11-phase voyage from `astra_nexus.cpp:742-754` mapped to keyframes

**UI controls:**
- Play / pause / rewind / forward
- Speed multiplier (0.1× to 10×)
- Timeline scrubber
- Toggle: show / hide each individual effect (decouple visualization)
- Toggle: cinematic camera vs free-look

**Assertions:**
At each of the 11 voyage phases (canonical voyage demo points), the
rendered state matches the math values from `astra_nexus.cpp:demo_voyage()`:
1. Phase REST: apparent_rate ≈ 1.0 (planet behind ship moves at real time).
2. Phase STL_REL 0.5c: rate ≈ 0.5774 (SR Doppler).
3. Phase WARP_CRUISE 2c: rate = -1.0 (full orbit reversal at 1× speed).
4. Phase WARP_CRUISE 10c: rate = -9.0 (rewind at 9× speed).
5. Phase WARP_CRUISE 100c: rate = -99.0 (very fast rewind).
6. Phase WARP approach (-2c): rate = +3.0 (fast-forward).
…all 11 phases sampled.

**Pass criteria:** All 11 phases pass their canonical assertions. The
voyage looks coherent end-to-end. Operator can SEE all the effects
working together.

---

## 6. Visual ground-truth validation methodology

The bench's "math is correct AND it produces the right pixels" claim
needs a methodology to mechanically verify. Three layers of validation:

### 6.1 Pixel-level assertion (per-scene; runtime)

```cpp
// Each Scene exposes a list of expected pixels:
struct ScalarPixelAssertion {
    std::string name;                    // human-readable
    glm::ivec2 framebuffer_coord;        // (x, y) in framebuffer
    int channel;                         // 0=R, 1=G, 2=B, 3=A, or special "depth"
    float expected_value;                // canonical math output
    float tolerance;                     // pass if |measured - expected| < tolerance
};

class PixelSampler {
    // After scene.Render(), reads back the framebuffer
    // Walks scene.assertions(); for each, samples pixel; logs PASS/FAIL
    std::vector<AssertionResult> Sample(const Scene& s, GLuint framebuffer);
};
```

**Tolerance:** default 1% of expected value or ±0.01 absolute, whichever
is larger.

### 6.2 Heatmap-difference assertion (golden image comparison)

For each scene, a canonical configuration produces a "golden" PNG. The CI
compares headless renders to goldens via mean-pixel-difference:

```cpp
struct HeatmapDiffAssertion {
    std::string golden_path;             // assets/reference_renders/scene1.png
    float max_mean_diff;                 // 0.01 = 1% mean diff tolerance
    float max_pixel_diff;                // 0.10 = no individual pixel may differ by >10%
};
```

A `--regenerate-goldens` CLI flag lets the operator update goldens after
confirmed-correct visual changes. (Without this flag, goldens are
canon-locked.)

### 6.3 Side-by-side numeric overlay (operator-eye validation)

Every scene shows in a corner overlay:
- Current rendered value (sampled from a focal pixel)
- Canonical math value (from `libastra_nexus`)
- Difference
- PASS/FAIL with green/red color

This lets a human watch the math and the pixels agree in real time
during interactive use.

### 6.4 The validation report (JSON output for CI)

After headless run:

```json
{
  "version": "0.1.0",
  "build_commit": "abc123",
  "ran_at": "2026-05-20T10:00:00Z",
  "platform": "Windows 11 / RTX 5090 / CUDA 12.4",
  "scenes": [
    {
      "name": "Scene1_WarpBubbleAtRest",
      "assertions": [
        { "name": "bubble_center_W", "expected": 0.95, "measured": 0.9512, "passed": true },
        { "name": "bubble_boundary_W", "expected": 0.5, "measured": 0.498, "passed": true },
        ...
      ],
      "heatmap_diff": { "golden": "warp_bubble_rest_canonical.png", "mean_diff": 0.0034, "max_diff": 0.012, "passed": true },
      "frame_ms": 14.2,
      "screenshot_path": "ci_results/scene1.png"
    },
    ...
  ],
  "summary": { "scenes_passed": 11, "scenes_failed": 0, "total_assertions": 44, "assertions_passed": 44 }
}
```

CI gate: exit code 0 iff `scenes_failed == 0`.

---

## 7. Phased implementation roadmap

### Phase V0: Scaffolding (weeks 1-2)

**Deliverables:**
- CMake project skeleton; GLFW window opens; OpenGL 4.6 context valid; ImGui renders "Hello, ASTRA-7 Visualizer" in window.
- `libastra_nexus` static library extracted from `proto/astra_nexus.cpp`; linked; calls compile and return canonical values.
- CUDA toolkit detected; one trivial CUDA kernel (vector add) runs and outputs to console (verifies CUDA pipeline).
- CUDA-GL interop sanity test: `cudaGraphicsGLRegisterBuffer` succeeds on a test SSBO.
- CLI parser handles `--help`, `--scene=X`, `--headless`.

**Gate:** `astra_visualizer.exe --help` prints usage. Empty window opens.
Headless mode exits 0 with no scenes.

### Phase V1: Scene 1 + 2 + Renderer foundations (weeks 3-4)

**Deliverables:**
- `Renderer/ComputeProgram` + `GraphicsProgram` GL wrappers.
- `Renderer/CudaGLInterop` glue for sharing 3D textures.
- `physics/RBFNetwork` loads a synthetic test RBF (50 nodes) from JSON.
- Compute shader `ray_march_warp.comp` evaluates RBF + renders volumetric bubble.
- Scene1 WarpBubbleAtRest implemented with camera controls.
- Scene2 WarpBubbleCruise extends Scene1 with wake.
- PixelSampler reads back framebuffer; runs 8 assertions across both scenes.

**Gate:** Scenes 1 and 2 render at 60+ FPS; all 8 assertions PASS in
interactive mode; headless mode dumps PNGs.

### Phase V2: Scenes 3 + 4 (weeks 5-6)

**Deliverables:**
- Scene3 CherenkovCone: cone mesh + θ_c computation.
- Scene4 GeometricLensing: starfield + ∇W ray deflection.
- Refactoring: scene parameter UI lives in `ui/ParameterPanel`; each scene contributes its parameter widgets.

**Gate:** Scenes 3-4 render correctly; all 8 assertions PASS.

### Phase V3: Scene 5 + 6 (THE PAYOFF) (weeks 7-9)

**Deliverables:**
- Scene5 RetardedTimeOrbitReversal: this is the most visually striking scene; budget extra time.
- Scene6 PhotonSourceHistory: simpler in render but tests the discrete-transition edge case.
- Kepler solver integration; orbit visualization.
- The orbital phase plot in ImGui.

**Gate:** Scenes 5-6 render correctly; the operator can SEE the orbit
running backward (this is the visual payoff of the whole project); all
assertions PASS.

### Phase V4: Scenes 7 + 8 (CUDA-heavy) (weeks 10-12)

**Deliverables:**
- Scene7 ChaosPDEVisualization: CUDA Fisher-KPP solver; double-buffered surface; 2D slice + 3D volumetric render modes.
- Scene8 HullSDFRayMarch: SDF loading; sphere-trace shader; damage event handling via surf3Dwrite.
- Refactor `physics/StateBus` to mirror spec §4.2 schema (subset; this app doesn't need full LLM state).

**Gate:** Scenes 7-8 work; chaos PDE remains stable; damage events
persist; all assertions PASS.

### Phase V5: Scenes 9 + 10 + 11 (composition + cinematic) (weeks 13-15)

**Deliverables:**
- Scene9 CompositionRuleGauge: simple ImGui-heavy scene; verifies composition rule.
- Scene10 RegimeContrast: split-screen rendering setup.
- Scene11 FullVoyageDemo: cinematic camera + 11-phase timeline; integrates all prior scenes.

**Gate:** All 11 scenes pass; FullVoyageDemo plays end-to-end at 60+ FPS.

### Phase V6: Validation infrastructure + CI integration (weeks 16-17)

**Deliverables:**
- Golden PNG references generated for each scene at canonical configuration.
- Headless mode hardened; produces JSON test report.
- CI script (GitHub Actions or local batch) runs `--headless` and gates on report.
- Documentation: README.md, BUILD.md, SCENES.md, VALIDATION.md.

**Gate:** CI runs the visualizer; reports PASS for all 11 scenes; gates
green.

### Phase V7: Polish + release (week 18)

**Deliverables:**
- Recordable mode (MP4 capture via stb_image_write frame-by-frame + ffmpeg post — or skip MP4 and rely on PNG sequences).
- Performance overlay (frame time, GPU memory, kernel times).
- Release build of `astra_visualizer.exe` for Windows 11 (and `.deb` for Linux x86_64).

**Gate:** Release-quality binary; documentation complete; reports
generated automatically.

**Total: 18 weeks (~4.5 months) for one full-time developer + LLM-pair-programming.**
Realistically 6-8 months for solo dev with operator review cycles.

---

## 8. Build instructions (for the coding agent)

### 8.1 Windows 11

```batch
:: prerequisites
:: - Visual Studio 2022 17.8+
:: - CUDA Toolkit 12.4+
:: - CMake 3.27+
:: - Git (for submodules)

cd proto\visualizer
git submodule update --init --recursive

cmake -B build -G "Visual Studio 17 2022" -A x64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      -DCMAKE_CUDA_ARCHITECTURES="86;89;90"
cmake --build build --config Release

build\Release\astra_visualizer.exe
```

### 8.2 Linux x86_64

```bash
# prerequisites: gcc-13, CUDA 12.4, CMake 3.27

cd proto/visualizer
git submodule update --init --recursive

cmake -B build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CUDA_ARCHITECTURES="86;89;90"
cmake --build build

./build/astra_visualizer
```

### 8.3 Quick smoke test

```bash
# Verify the math library links
./astra_visualizer --version
# Expected: "astra_visualizer v0.1.0; linked against libastra_nexus v0.129.day2"

# Verify headless mode
./astra_visualizer --headless --scene=Scene1_WarpBubbleAtRest --output=smoke_results/
# Expected: PNG dumped to smoke_results/scene1.png; report.json shows PASS
```

---

## 9. Coding agent handoff brief

### What you (the next coding agent) need to know

1. **Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md`. Read it; the
   physics is locked there. When in doubt, the spec wins.

2. **Math basis:** `proto/astra_nexus.cpp` (1009 lines, 66 assertions).
   This is the canonical math; every numeric in the visualizer must trace
   back here. Extract as `libastra_nexus` (Phase V0 task).

3. **Vision basis:** This document. It tells you what to build but NOT
   how to write the C++. Use idiomatic modern C++ (C++20 if your toolchain
   supports; C++17 minimum).

4. **The 11 scenes are NOT all equal effort:**
   - Scenes 1, 2, 9, 10 are straightforward.
   - Scenes 3, 4, 8 are medium effort.
   - **Scenes 5, 6, 7 are the hardest** — Scene 5 (orbit reversal) is the
     most visually distinctive AND the most likely to have subtle math/render
     misalignment. Budget extra time.
   - Scene 11 (full voyage) is a polish-and-integration phase; its
     difficulty comes from coordinating all prior scenes' rendering.

5. **CUDA-GL interop is the most likely source of bugs.** Test the
   interop with trivial cases (vector-add → SSBO → fragment shader) BEFORE
   building it into Scene 1. Get a CUDA kernel writing to a GL buffer and
   a fragment shader reading the buffer working end-to-end on day 1 of
   Phase V1.

6. **The validation methodology (Section 6) is load-bearing.** Don't skip
   pixel-level assertions. They are how we PROVE the math matches the
   visuals. Without them, the project is "the math test does math; this
   tool does pixels; we hope they agree." With them: "the math test does
   math; this tool does pixels; we MECHANICALLY VERIFY they agree."

7. **Headless mode is not optional.** CI needs it. Build it from Phase V0;
   maintain it through every scene addition. If interactive mode renders a
   scene at 60 FPS and headless mode crashes on it, that's a bug to fix
   before declaring the scene done.

8. **Goldens (reference PNGs) are canon.** Once a scene is operator-approved
   visually, its golden PNG is locked. Future changes that alter the
   golden require operator review (same discipline as scope.yaml's
   required_invariants in textverse).

9. **Don't reinvent the math.** Every numeric quantity the visualizer
   compares against MUST come from a `libastra_nexus` function call. Do
   NOT reimplement `compute_apparent_rate` in HLSL or GLSL or Python.
   The math lives in C++ in one place. The visualizer's shaders may
   approximate for speed (e.g., float32 instead of float64) but the
   pixel-assertion comparison ALWAYS runs the canonical float64 math
   from the library.

10. **Cross-platform discipline:** Per CLAUDE.md Platform Discipline,
    Windows 11 is primary; Linux x86_64 acceptable second. Test BOTH
    every phase. **No Apple/Mac/Metal/iOS anywhere.** Don't `#ifdef
    __APPLE__` even defensively; the codebase is Apple-free by lock.

11. **C/C++ only for new code:** Per CLAUDE.md Language Discipline. No
    Python in the visualizer (including no Python build scripts; CMake
    is the build system). The existing `proto/textverse/` Python is
    grandfathered; the visualizer does NOT depend on textverse.

12. **The Cherenkov gap (per discovery 5D F4) is closed by this project.**
    Spec §6 step 10's `cos θ_c = 1/(n·β)` formula has zero code
    implementation today; Scene 3 will be its first implementation. Land
    `compute_cherenkov_angle()` in libastra_nexus as part of Phase V2;
    add ≥3 assertions (β=0.5, β=0.9, β=0.999) to bring the C++ test count
    from 66 to 69+.

### Where to look when stuck

| Problem | First-look reference |
|---|---|
| Math behaving unexpectedly | `proto/astra_nexus.cpp` source + assertion outputs |
| Physics interpretation unclear | `docs/spec-v0.129-tentative-2026-05-16.md` (then fallback to v0.128) |
| Visual effect not matching expectation | This document, the scene's "Rendering technique" section |
| CUDA-GL interop hanging | NVIDIA CUDA sample `simpleGL` is the canonical reference |
| Performance below 60 FPS | Performance overlay; profile with NVIDIA Nsight |
| Pixel assertion failing | Print expected vs measured to console; check tolerance is reasonable for float-precision noise |
| ImGui controls not responding | Verify `ImGui_ImplGlfw_NewFrame()` + `ImGui_ImplOpenGL3_NewFrame()` called in loop |
| Build failing on Linux but works on Windows | CUDA architecture selection; nvcc version; pthread linking |

### Acceptance criteria (when is this done?)

The visualizer is **done** when:

1. ✅ `astra_visualizer.exe` runs interactively on Windows 11 + RTX 4090/5090/3090.
2. ✅ All 11 scenes implemented and visually plausible.
3. ✅ Every scene has ≥3 pixel-level assertions; total ≥44 assertions across all scenes.
4. ✅ Every assertion passes in interactive mode on the reference 5090 setup.
5. ✅ Headless mode runs all 11 scenes in <2 minutes; JSON report shows all PASS.
6. ✅ Golden PNG references in `assets/reference_renders/`; headless-vs-golden mean-diff < 1% for all scenes.
7. ✅ The visualizer builds on Linux x86_64 (Ubuntu 24.04 LTS).
8. ✅ `libastra_nexus` extracted and the original `proto/astra_nexus.exe` still passes all 66 (now 69+) assertions.
9. ✅ The Cherenkov gap is closed: `compute_cherenkov_angle()` in libastra_nexus; 3+ assertions added.
10. ✅ Documentation complete: `README.md`, `BUILD.md`, `SCENES.md`, `VALIDATION.md`.
11. ✅ Operator has personally watched Scene 5 RetardedTimeOrbitReversal and CONFIRMED the orbit visually appears to run backward at v_apparent = 2c. (This is the "you have to see it to believe it" payoff scene; it requires operator sign-off.)

---

## 10. Open questions for operator (before coding-agent starts)

### OQ1 — Linux build priority: weeks 1-18 or post-Windows-completion?

Building cross-platform from Phase V0 adds ~10-15% time but ensures
Linux x86_64 works (per CLAUDE.md Platform Discipline). Building Windows
first and porting after is faster initially but historically produces
more porting bugs.

**Recommendation:** cross-platform from V0. The CMake structure makes
it cheap if done upfront; expensive if retrofitted.

### OQ2 — MP4 video recording: V7 polish item or skip entirely?

V7 includes optional MP4 capture (PNG sequence + ffmpeg). It's nice for
sharing visualizations but not load-bearing. Could skip and rely on PNG
sequences + screenshots.

**Recommendation:** PNG sequences are sufficient; MP4 is operator-side
post-processing. Skip in V1; add later if needed.

### OQ3 — Scene 11 (FullVoyageDemo) cinematic camera: scripted timeline or operator-controlled?

The voyage-demo in `astra_nexus.cpp` has 11 discrete phases. The visualizer's
Scene 11 could play them as a fixed cinematic OR let the operator step
through interactively.

**Recommendation:** both. Default is interactive scrubbing; a "play
cinematic" button runs the scripted 30-second voyage. Headless mode
runs the cinematic.

### OQ4 — Reference RBF network: synthetic test or real CFD output?

Phase V1 needs a CFD-RBF network for the warp field. Options:
- **(a) Synthetic test RBF** (~50 hand-placed Gaussians forming a bubble shape) — fast to make, no CFD dependency, sufficient for visual ground-truth.
- **(b) Real CFD output** processed offline with OpenFOAM + RBF fit — proper but multi-week additional work.

**Recommendation:** synthetic for V1-V6; real CFD output deferred to a
later "v0.2 visualizer" that closes Phase E0 deeper requirements. The
synthetic RBF is sufficient for testing whether the rendering pipeline
correctly evaluates an RBF; whether the RBF correctly represents real
CFD physics is a separate question (covered by `proto/astra_nexus`
math validation, not by the visualizer).

### OQ5 — Cherenkov closure: in libastra_nexus or in visualizer only?

The Cherenkov gap (per discovery 5D F4) is the project's only locked
formula with zero implementation. Scene 3 needs the implementation.
Where does it live?

**Recommendation:** in `libastra_nexus::cherenkov_angle()` with assertions
in the C++ test suite. This way the gap is closed at the math layer
(where every other formula lives) and the visualizer just calls it.

### OQ6 — Goldens regeneration policy: when goldens drift?

After scene refinement, the golden PNG may need updating. Strict policy:
goldens require explicit operator sign-off. Lenient policy: any commit
can regenerate goldens.

**Recommendation:** strict. Goldens are canonical reference images; they
require the same care as `proto/astra_nexus.cpp` assertions. Operator
review for any regeneration.

### OQ7 — Should V1 (Phase V1) implement Scene 1 OR Scenes 1+2 together?

Scene 2 is mostly a parameter extension of Scene 1 (add wake; same
ray-march). Doing them together is ~1.3× the effort of Scene 1 alone;
doing them separately is 2 phases of similar work.

**Recommendation:** together. The marginal cost is low; the shared
rendering pipeline benefits.

---

## 11. The deeper structural value of this project

Beyond the immediate "verify the math produces the right pixels," this
project serves three structural roles:

### 11.1 It is rig 3 (engine-side rendering verification) per spec §15.8 + 3B-U3

Spec §15.8 names three rigs: physics binary (Rig 1), LLM bundle (Rig 2),
engine (Rig 3 — deferred per spec). Discovery 3B's U3 added rig 4 (prose
canon) and rig 5 (spec audit). **`astra_visualizer.exe` IS rig 3.** It's
the engine-side verification instrument that the spec called for but
didn't have a concrete implementation path. The project does not need to
wait for UE5 integration to run rig 3; this visualizer runs it on bare
OpenGL.

### 11.2 It de-risks UE5 integration

When UE5 Phase E2-E5 lands (per `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`),
every visual effect that ships there will have been previously validated
in the visualizer. UE5 surprises become: "the math + bare OpenGL produces
correct visuals; UE5 wraps that same math + a fancier renderer; if UE5
disagrees with bare OpenGL, the bug is in UE5's wrapper, not in the
math." This bounds where UE5 bugs can hide.

### 11.3 It is a publishable artifact

A standalone Windows .exe that visually demonstrates retarded-time orbit
reversal at v_apparent > c is a compelling proof-of-concept for the
project. It can ship with the GitHub repo as a "see the physics" demo.
It can be referenced in academic discussions of analog-gravity
warp-field simulations. It can be the project's first publicly-shareable
artifact while the main game is still in pre-Phase-E0 development.

---

## 12. Summary table — what gets built

| Phase | Weeks | Deliverable | Gate |
|---|---|---|---|
| V0 | 1-2 | Scaffolding + GLFW + libastra_nexus split | Window opens; CUDA detected; CLI parses |
| V1 | 3-4 | Renderer foundations + Scenes 1+2 (Warp Bubble at Rest + Cruise) | 60 FPS; 8 assertions PASS |
| V2 | 5-6 | Scenes 3+4 (Cherenkov + Lensing) | 8 more assertions PASS |
| V3 | 7-9 | Scenes 5+6 (Orbit Reversal + Photon Source) | THE payoff scenes; operator confirms visual |
| V4 | 10-12 | Scenes 7+8 (Chaos PDE + Hull SDF) | CUDA-GL interop hardened |
| V5 | 13-15 | Scenes 9+10+11 (Gauge + Regime Contrast + FullVoyage) | Complete coverage |
| V6 | 16-17 | Validation infra + CI gating | Golden PNGs locked; JSON report; CI green |
| V7 | 18 | Polish + release | Production-quality binary |

**Total: 18 weeks (4.5 months) for one developer pair-programming with
Claude Code (or similar LLM); 6-8 months solo with operator review
cycles.**

---

## 13. Closing

This visualizer is the **engine-agnostic ground truth** between the math
(`proto/astra_nexus.cpp`) and the eventual UE5 rendering. It validates
the visual physics claims of v0.129 without depending on UE5's complexity.
It closes the Cherenkov gap. It produces canonical reference images that
UE5's rendering must match.

The math is locked. The visual claims are testable. A coding agent can
pick this up and ship in 18 weeks. The validation methodology is
mechanical. The closure is empirical.

Build it.

— Plan, 2026-05-16 —
