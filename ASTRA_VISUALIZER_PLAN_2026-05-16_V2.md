# ASTRA-7 Visual Physics Testbed — Implementation Plan (V2)

**Date:** 2026-05-16
**Status:** Proposal v2 for coding-agent implementation. NOT yet implemented.
**Author:** Claude Opus 4.7 (1M context, polish-pass synthesis)
**Predecessors (sibling proposals):**
- `PROPOSAL_2026-05-16_VISUAL_PHYSICS_TESTBED.md` (Opus pass 1; this author; 1,176 lines)
- `ASTRA_VISUALIZER_PLAN_2026-05-16.md` (Opus pass 2; different session; 1,316 lines)
**Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md`; `proto/astra_nexus.cpp` (1009 lines, 66 assertions after Tier 1A+1B)
**Target reader:** the coding agent who will pick this up cold and implement it.

---

## 0. What this v2 is

This document integrates the best of the two sibling proposals. Where they agreed, both reinforced. Where they disagreed, this v2 picks the sharper choice. Where neither went deep enough, v2 fills in.

**Synthesis: what changed from v1 to v2**

| Element | V1 of my proposal | V2 (this document) | Change reason |
|---|---|---|---|
| Math linkage | "Link with proto/astra_nexus.cpp" | **Extract `libastra_nexus` static library + thin `main()` wrapper** | Sibling plan's architectural insight: single source of truth for math; visualizer + nexus exe both link the same lib |
| Validation | Screenshot regression + state display | **Three-layer validation: pixel-level assertions + heatmap diff + side-by-side numeric overlay with PASS/FAIL** | Sibling plan's mechanical validation methodology; makes "math matches pixels" a CI-gateable property, not eye-balled |
| CI integration | F12 screenshot for golden regression | **Full headless mode from V0 with JSON report; CI exit-code gate** | CI-gateable from day 1, not retrofitted |
| Cherenkov | Implementation phase 7 | **Explicit project deliverable: closes 5D-F4 gap by adding `compute_cherenkov_angle()` to libastra_nexus; 3+ new assertions** | Sibling plan's clear deliverable framing; the gap is named and closed |
| Goldens policy | "regression test" | **Explicit `--regenerate-goldens` flag; operator sign-off discipline; mirrors textverse `scope.yaml` required_invariants pattern** | Project-wide discipline consistency |
| Project positioning | Diagnostic tool | **Rig 3 per spec §15.8 + 3B-U3 (engine-side rendering verification); de-risks UE5; publishable artifact** | Spec-methodology positioning |
| Calendar estimate | 35-38 days aggressive | **14-16 weeks realistic (includes validation infra + CI hardening + Linux build + documentation)** | Realistic budget per sibling plan's experience |
| Scenarios | 12 (S01-S12) | **12 (kept mine including eye-ear S12; merged sibling's gauge/regime-contrast/full-voyage equivalents)** | Coverage breadth preserved |
| Warp wake trail (P3) | Flagged as potential spec-revision finding | **Same — kept; sibling plan treats wake as in-spec via §6 step 7 instead** | The "wake as new finding" framing is mine; preserved as spec-revision candidate |
| UI layout + hotkeys | ASCII diagram + hotkey list | **Same — kept** | Concrete enough for implementing agent |
| Tech rationale | Explicit NOT-chosen alternatives | **Same — kept and tightened** | Helps coding agent understand decision boundaries |
| Coding-agent handoff | Implicit | **Explicit Section 11 with onboarding brief + "where to look when stuck" troubleshooting table** | Sibling plan's strong onboarding pattern |

**What this means in practice:** if you read just one document to implement the visualizer, read this v2. The sibling plans remain as cross-references and historical record of the two parallel discovery passes that produced this synthesis.

---

## 1. Why this exists (the gap to close)

`proto/astra_nexus.exe` proves the math works at the mathematical level. 66 C++ assertions verify the 14-equation framework: AstraCoord renormalization at 974 Mly reach with sub-mm precision, 3-vector rapidity ζ⃗ with γ-clamp at 10⁷, composition rule across regimes, regime-dispatched apparent-rate (SR longitudinal Doppler vs. classical retarded-time), Kepler-at-t_emit orbit reversal under v_apparent > c, photon-source-history bound + Hubble horizon flags, the cross-substrate stdio JSON-RPC bridge.

**It does not prove that the math actually produces the VISUAL phenomena the spec describes.**

The spec talks about phenomena with visible signatures:

- A warp bubble whose metric W(x,t) is volumetrically renderable (violet glow with sharp gradient at boundary)
- A wake trail behind the moving bubble (NOT IN SPEC explicitly; the testbed may surface this as a spec-revision finding)
- A Cherenkov cone with half-angle `cos θ_c = 1/(n·β)` narrowing as β increases (per spec §6 step 10 — locked at 4 sites, **zero code implementation today** per AUDIT 5D-F4)
- Starfield aberration warping star directions forward at high γ
- An orbit appearing to **run backward** when observed at retarded time during warp egress at v_app > c (per spec §3.11 — empirically verified mathematically at [astra_nexus.cpp:639-677](proto/astra_nexus.cpp:639) but never RENDERED)
- A source that becomes **gone** (not faded; gone) when ship has overtaken every photon it ever emitted (`beyond_photon_history` per spec §3.11)
- A Hubble-horizon body rendered **frozen** at horizon-crossing instant, dimming on a separate timescale (`beyond_hubble_horizon` per spec §3.12)
- Geometric lensing — light rays bent by ∇W near the bubble boundary, producing Einstein-ring-style distortion of background stars
- Chaos field χ(x,t) modulating the bubble shell with reaction-diffusion dynamics (Fisher-KPP per spec §7.1)
- Hull SDF + damage map rendering as the ship's surface (per spec §1.3 dual-binding pattern)
- Doppler-colored starfield with multiplicative redshift composition `(1+z_total) = (1+z_cosmo)·(1+z_kin)·(1+z_metric)`
- Time-dilation indicator showing dτ_ship/dt_cosmic from the composition rule

These are **visual claims with mathematical bodies.** The math is locked (`proto/astra_nexus.cpp`); the visual fidelity is not yet confirmed.

**The gap:** until human eyes can see a frame and confirm "yes, that's what v_app = 2c looks like — orbit running backward, color shifted to red, Cherenkov cone open at the calculated half-angle," we cannot say the implementation is *visually correct*, only *mathematically correct*. UE5 will eventually render these effects (Phase E0-E5 per `DISCOVERY_2026-05-16_TECHDIVE_UE5.md`), but UE5 is heavy, opaque, engine-bound, and months away.

**We need a thin layer**: raw C++/CUDA + OpenGL + ImGui, no engine, that renders the math directly and lets a human (and pixel-level mechanical assertions) confirm "the math produces this image, and this image is correct."

This testbed reuses `proto/astra_nexus.cpp` (extracted as a `libastra_nexus` static library — see §3 below) as its math source of truth. **If the testbed shows the wrong visuals, that's a finding** (either the math is missing something the spec wants, or the math is right and the spec needs a different formula). Per spec §15.4 "revise on findings": this testbed produces findings the math-only assertion suite cannot.

---

## 2. Scope, non-goals, and what success looks like

### 2.1 In scope

- A **standalone Windows 11 executable** (`astra_visualizer.exe`) that runs 12 visual test scenes.
- **Pure C++17/CUDA 12.x/OpenGL 4.6/GLFW/Dear ImGui/GLM** — all engine-agnostic, header-mostly, well-documented.
- **Visual rendering** of every physics effect named in spec §§1, 3, 6, 7 that has a visible signature.
- **Three-layer validation** (pixel-level assertions + heatmap diff + side-by-side numeric overlay) for mechanical "math agrees with pixels" verification.
- **Dual-mode operation**: interactive (GLFW + ImGui + camera controls) and headless (CI batch render with PNG dumps + JSON report).
- **Linkage with `libastra_nexus`** as a static library; the math is the single source of truth.
- **Cross-platform**: Windows 11 primary; Linux x86_64 secondary (both tested from V0).
- **Closes the Cherenkov gap (5D-F4)** by implementing `compute_cherenkov_angle()` in libastra_nexus with ≥3 C++ assertions (bumps from 66 to 69+).

### 2.2 Explicitly out of scope

- ❌ **No Unreal Engine integration.** This is the engine-agnostic ground-truth layer.
- ❌ **No production rendering quality.** No TSR, no Lumen, no Nanite, no DLSS. Straight forward-rendering with custom shaders.
- ❌ **No LLM / persona.** Pure physics → pixels.
- ❌ **No audio synthesis.** §8.3 audio is verified separately (MetaSound path).
- ❌ **No NNE/TensorRT Reflex inference.** PID stub only; real Reflex training is a separate effort.
- ❌ **No Apple / Mac / Metal / iOS.** Per CLAUDE.md Platform Discipline (2026-05-15). Don't `#ifdef __APPLE__` even defensively.
- ❌ **No Python in new code.** Per CLAUDE.md Language Discipline (2026-05-15). All new code is C/C++/CUDA/HLSL/GLSL. CMake permitted as build-data.
- ❌ **No save/load persistence.** Scenarios start fresh each launch.
- ❌ **No network features.** Local-only execution per spec §4.8 Privacy/Network.
- ❌ **No VR/stereo rendering.** Mono only.
- ❌ **No production-grade hull mesh.** Simple low-poly placeholder; full hull is UE5 Phase E0 work.

### 2.3 What success looks like

`astra_visualizer.exe` runs on a Windows 11 machine with an NVIDIA RTX 40-series+ GPU. The user picks a scene from a menu. The scene renders at 60+ FPS at 1080p. UI controls let them sweep parameters (e.g., β from 0 to 0.999 for the Cherenkov scene). For every scene, an on-screen assertion overlay says **PASS / FAIL** comparing rendered pixels to canonical math from `libastra_nexus`.

Headless mode (`--headless --scene=all --output=ci_results/`) runs all 12 scenes, dumps PNGs to disk, writes a JSON test report; CI gates on the report's `summary.scenes_failed == 0`.

The operator can watch Scene 5 (Retarded-Time Orbit Reversal) and SEE the orbit running backward at v_app = 2c — the "you have to see it to believe it" payoff scene that requires operator sign-off as final acceptance.

---

## 3. Architecture overview

```
┌──────────────────────────────────────────────────────────────────┐
│  astra_visualizer.exe                                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ App: GLFW window + GL context + ImGui + main loop          │  │
│  │      + CLI parser (interactive / headless mode select)     │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ SceneRouter: 12 IScene implementations; UI selector;       │  │
│  │ shared parameter UI; per-scene parameter widgets           │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ Renderer (OpenGL 4.6 + custom shaders)                     │  │
│  │  - Compute shaders for ray-march, chaos PDE, Doppler       │  │
│  │  - Graphics pipelines for visualization composites         │  │
│  │  - CUDA-GL interop via cudaGraphicsGLRegisterBuffer/Image  │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ CUDA kernels (the math compute layer)                      │  │
│  │  - chaos_pde.cu     (Fisher-KPP solver, double-buffered)  │  │
│  │  - warp_field.cu    (CFD-RBF eval + ∇W via dual-numbers)   │  │
│  │  - observation_calc.cu (per-body retarded time)            │  │
│  │  - sdf_sphere_trace.cu (hull SDF traversal)                │  │
│  │  - wake_field.cu    (trail evolution)                      │  │
│  └────────────────────┬───────────────────────────────────────┘  │
│                       │                                          │
│  ┌────────────────────▼───────────────────────────────────────┐  │
│  │ libastra_nexus.lib (linked from proto/libastra_nexus/)     │  │
│  │  - canonical math: composition rule, observe(),            │  │
│  │    compute_apparent_rate, AstraCoord, Rapidity,            │  │
│  │    Kepler solver, NEW compute_cherenkov_angle()            │  │
│  │  - 69+ assertions still callable as run_all_tests()        │  │
│  │  - stdio_server (preserved; not used by visualizer but     │  │
│  │    available)                                              │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ValidationLayer (THREE-LAYER mechanical verification)      │  │
│  │  1. PixelSampler: framebuffer pixel reads via glReadPixels │  │
│  │     → ScalarPixelAssertion comparison against libastra     │  │
│  │     → on-screen PASS/FAIL overlay (green/red)              │  │
│  │  2. HeatmapDiffAssertion: full-PNG comparison vs golden    │  │
│  │     → mean-pixel-diff + max-pixel-diff tolerances          │  │
│  │  3. NumericOverlay: per-scene, side-by-side display of     │  │
│  │     rendered value vs canonical math value vs diff         │  │
│  │  → JSON test report for CI exit-code gate                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Output: PNG dumps, JSON test reports, optional PNG-sequence│  │
│  │ recording for post-processing into MP4 (operator-side)     │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.1 The `libastra_nexus` extraction (critical foundation)

**The sibling plan's sharpest architectural insight.** Today `proto/astra_nexus.cpp` is one 1009-line monolith with `main()` at the bottom plus all the math + test suite + stdio_server above. Split it:

```
proto/
├── astra_nexus.cpp              (existing thin wrapper; keep building as exe)
│                                 - just main() + calls into libastra_nexus
├── libastra_nexus/              (NEW; the canonical math library)
│   ├── include/astra_nexus/
│   │   ├── coord.h              (AstraCoord, astra_distance, renormalize)
│   │   ├── rapidity.h           (Rapidity, integrate_rapidity_step, OMEGA_MAX)
│   │   ├── composition.h        (dtau_dt_cosmic, schwarzschild_r, compute_grav_factor)
│   │   ├── apparent_rate.h      (compute_apparent_rate — regime-dispatched)
│   │   ├── observe.h            (Observable, ObservableState, observe, compute_z_kin,
│   │   │                         compute_z_cosmo, compute_lookback)
│   │   ├── kepler.h             (solve_kepler_E, orbit_phase, Orbit)
│   │   ├── cherenkov.h          (NEW: compute_cherenkov_angle, n_refractive_default)
│   │   ├── stdio_server.h       (run_stdio_server — preserved)
│   │   └── test_suite.h         (run_all_tests, returns pass/fail counters)
│   ├── src/
│   │   ├── coord.cpp
│   │   ├── rapidity.cpp
│   │   ├── composition.cpp
│   │   ├── apparent_rate.cpp
│   │   ├── observe.cpp
│   │   ├── kepler.cpp
│   │   ├── cherenkov.cpp        (NEW)
│   │   ├── stdio_server.cpp
│   │   └── tests/
│   │       ├── test_coord.cpp
│   │       ├── test_rapidity.cpp
│   │       ├── test_composition.cpp
│   │       ├── test_apparent_rate.cpp
│   │       ├── test_observe.cpp
│   │       ├── test_kepler.cpp
│   │       └── test_cherenkov.cpp  (NEW; +3 assertions minimum)
│   └── CMakeLists.txt           (builds libastra_nexus.lib / libastra_nexus.a)
└── visualizer/                  (NEW; this proposal)
    └── (see §4 layout)
```

**Why:** every numeric value the visualizer compares against is the **same implementation** that runs the 66 (now 69+) assertions. Single source of truth. The visualizer's pixel-assertion layer calls `libastra_nexus::compute_apparent_rate(0.5*C_LIGHT, R_STL_REL)` and compares its output against the rendered pixel. **If the math changes, both the assertion suite and the visualizer pick it up in the next build.**

This refactor is the V0 deliverable; everything else depends on it.

### 3.2 Dual-mode operation (interactive + headless)

**Interactive mode** (default): GLFW window + ImGui UI. Operator picks scenes, sweeps parameters, sees the PASS/FAIL overlay update in real-time. 60+ FPS target on RTX 4070+.

**Headless mode** (`--headless`): no window. Runs each scene's "canonical configuration" (e.g., Cherenkov at β=0.5, 0.9, 0.99); dumps PNG per scene + JSON report. Exit code 0 if all assertions pass, else 1. Suitable for CI.

CLI surface:
```
astra_visualizer.exe                                  # interactive, scene chooser
astra_visualizer.exe --scene=CherenkovCone            # interactive, jump to scene
astra_visualizer.exe --headless --scene=all           # all scenes headless, dump artifacts
astra_visualizer.exe --headless --scene=all --output=ci_results/
astra_visualizer.exe --headless --scene=Scene05 --output=smoke/
astra_visualizer.exe --regenerate-goldens --scene=all # operator-sign-off action only
astra_visualizer.exe --record-png-sequence --scene=Scene11 --duration=30  # 30s PNG seq for MP4 post
astra_visualizer.exe --version                        # prints "astra_visualizer v0.1.0;
                                                       #         linked libastra_nexus v0.129"
```

**Headless mode is not optional.** It must work from V0 — CI gates on it. If interactive mode renders a scene at 60 FPS and headless mode crashes, that's a bug to fix before declaring the scene done.

---

## 4. Tech stack — locked recommendations with rationale

| Layer | Technology | Rationale |
|---|---|---|
| Build system | **CMake 3.27+** | Per CLAUDE.md: "the only acceptable build system that has Python adjacency, treated as data, not as a Python runtime dependency." Cross-platform; targets MSVC + clang + gcc. FetchContent eliminates manual third-party setup. |
| C++ standard | **C++20** (C++17 minimum) | C++20 for concepts + designated initializers; CUDA 12.x supports it. C++17 fallback for one specific compiler edge case. |
| Compiler (Windows) | **MSVC 19.38+** (Visual Studio 2022 17.8+) | NVCC 12.x integrates cleanly. |
| Compiler (Linux) | **gcc 13+ or clang 16+** | Both support C++20 + CUDA. |
| GPU compute | **CUDA 12.4+** | NVIDIA-only per Platform Discipline. CUDA 12.x for the latest stdio_server compatibility and modern CUDA Graphs. |
| Graphics API | **OpenGL 4.6 Core Profile** | Mature CUDA interop (`cudaGraphicsGLRegisterBuffer/Image`); compute shaders (GL 4.3+) for fragment-rate compute; simpler than Vulkan for ground-truth visualization. Engine-agnostic (UE5 will use DX12 separately). |
| Window + input | **GLFW 3.4+** | De facto standard for OpenGL windowing; works on Windows/Linux; permissive (zlib). |
| GL function loader | **GLAD 2** | Single header generated for the GL 4.6 core profile we use. |
| Math library | **GLM 1.0+** | Header-only; matches GLSL conventions; well-tested. |
| UI | **Dear ImGui 1.91+ (docking branch)** | Single-source-tree drop-in; OpenGL3 + GLFW backends; debug overlays, control panels, plots. Industry standard for graphics tooling. |
| Image I/O | **stb_image + stb_image_write** | Single-header; PNG read/write for assertion dumps + golden comparisons. |
| JSON | **nlohmann/json** (single-header) | Per spec §15.6 "Replacements" table. For scenario configs + test reports. |
| Logging | **spdlog** (header-only) OR plain `fprintf` | spdlog is nicer; either acceptable. |
| Test framework | **doctest** (single-header) | Per spec §15.6; lightweight; preferred over Catch2 for simplicity. |
| Linkage | **Static-link `libastra_nexus`** | Single source of truth for math (per §3.1 above). |

### 4.1 What we explicitly are NOT using

| Rejected | Why |
|---|---|
| **Vulkan** | Too much boilerplate for a ground-truth visualization tool. Use if and only if OpenGL proves insufficient (unlikely). |
| **DirectX 12** | Engine-specific; locks us into Windows-only and adds boilerplate; UE5 will use DX12 separately. |
| **OptiX / RTX ray-tracing extensions** | Proprietary; we want straight compute-shader ray-marching that any GPU can run. |
| **Qt / wxWidgets** | Too heavy for a debug viewer. ImGui is the right tool. |
| **OpenGL ES** | Mobile-targeted; not our path. |
| **WebGPU / Dawn** | Emerging but not yet production-stable on Windows native as of May 2026; reconsider for a future web-based visualization. |
| **Python anywhere** | Per CLAUDE.md Language Discipline; including no Python build scripts. CMake-only. |
| **Unreal / Unity / Godot / Bevy** | The whole point is engine-agnostic. |
| **Boost** | Heavy; not needed for this scope. |

---

## 5. Project structure

```
proto/visualizer/                                # NEW; sibling to proto/libastra_nexus + proto/textverse
├── CMakeLists.txt
├── README.md
├── BUILD.md
├── SCENES.md
├── VALIDATION.md
├── build.bat                                    # Windows convenience
├── build.sh                                     # Linux convenience
├── third_party/                                 # vendored or FetchContent-pulled
│   ├── glfw/
│   ├── glad/                                    # generated for GL 4.6 core
│   ├── glm/                                     # header-only submodule
│   ├── imgui/                                   # docking branch
│   ├── stb/                                     # stb_image.h, stb_image_write.h
│   ├── doctest/                                 # single-header
│   ├── nlohmann_json/                           # single-header
│   └── spdlog/                                  # optional; header-only mode
├── shaders/
│   ├── common/
│   │   ├── constants.glsl                       # physical constants header
│   │   ├── astra_coord.glsl                     # AstraCoord helpers
│   │   ├── redshift.glsl                        # color shift functions
│   │   └── camera.glsl                          # view/proj helpers
│   ├── volume/
│   │   ├── raymarch.vert                        # fullscreen quad vertex
│   │   └── raymarch.frag                        # warp + chaos volume ray-march
│   ├── starfield/
│   │   ├── starfield.vert                       # point sprites with Doppler color
│   │   └── starfield.frag                       # apparent-rate + brightness
│   ├── cherenkov/
│   │   └── cone.frag                            # Cherenkov cone overlay
│   ├── lensing/
│   │   └── post.frag                            # geometric lensing background-sample pass
│   ├── hull/
│   │   ├── hull.vert
│   │   └── hull.frag                            # simple Phong + SDF damage overlay
│   ├── trail/
│   │   ├── trail.vert
│   │   └── trail.frag                           # warp wake billboards
│   ├── retarded_body/
│   │   ├── body.vert                            # per-instance Kepler-at-t_emit
│   │   └── body.frag                            # redshift-colored body
│   ├── chaos/
│   │   └── slice_2d.frag                        # 2D slice heatmap of χ(x,t)
│   └── overlay/
│       ├── arrows.vert/.frag                    # debug ∇W arrows
│       └── rbf_nodes.vert/.frag                 # debug RBF center points
├── kernels/
│   ├── chaos_pde.cu                             # CUDA Fisher-KPP solver (RK2)
│   ├── warp_field.cu                            # CFD-RBF eval + ∇W via dual-numbers
│   ├── observation_calc.cu                      # per-body retarded time (Newton)
│   ├── ism_impact.cu                            # §7.2 ISM dispatch visualization
│   ├── wake_field.cu                            # warp wake trail evolution
│   ├── reflex_stub.cu                           # simple PID Reflex (chaos field damping)
│   └── kernels.h                                # C++ declarations
├── src/
│   ├── main.cpp                                 # entry: GLFW + GL + ImGui + main loop
│   ├── app/
│   │   ├── application.cpp / .h                 # app lifecycle
│   │   ├── scene_router.cpp / .h                # scene registration + switching
│   │   ├── cli.cpp / .h                         # command-line parser
│   │   ├── headless_mode.cpp / .h               # CI / batch render path
│   │   ├── camera.cpp / .h                      # free-fly + scenario-locked
│   │   ├── input.cpp / .h                       # keyboard + mouse handling
│   │   └── time_step.cpp / .h                   # sim time vs wall time
│   ├── renderer/
│   │   ├── gl_context.cpp / .h                  # GL setup + debug callback
│   │   ├── compute_program.cpp / .h             # compute shader loader
│   │   ├── graphics_program.cpp / .h            # vert+frag shader loader
│   │   ├── texture.cpp / .h                     # GL texture wrapper
│   │   ├── buffer.cpp / .h                      # SSBO + UBO wrappers
│   │   ├── cuda_gl_interop.cpp / .h             # cudaGraphicsGLRegister* manager
│   │   ├── volume_renderer.cpp / .h
│   │   ├── starfield.cpp / .h
│   │   ├── cherenkov.cpp / .h
│   │   ├── lensing.cpp / .h
│   │   ├── hull.cpp / .h
│   │   ├── trail.cpp / .h
│   │   ├── retarded_body.cpp / .h
│   │   └── overlays.cpp / .h
│   ├── physics/
│   │   ├── physics_core.cpp / .h                # facade over libastra_nexus
│   │   ├── rbf_network.cpp / .h                 # CFD-RBF + spatial hash
│   │   ├── chaos_field.cpp / .h                 # 128³ chaos field state mgmt
│   │   ├── hull_sdf.cpp / .h                    # SDF loader / synthesizer
│   │   ├── reflex_stub.cpp / .h                 # PID Reflex (C++ glue)
│   │   ├── cherenkov_math.cpp / .h              # cos θ_c bridge (calls libastra_nexus)
│   │   └── state_bus.cpp / .h                   # simplified state container (mirrors §4.2 schema)
│   ├── scenes/
│   │   ├── i_scene.h                            # interface
│   │   ├── scene_base.cpp / .h                  # shared helpers
│   │   ├── s01_rest_baseline.cpp / .h
│   │   ├── s02_stl_recede_05c.cpp / .h
│   │   ├── s03_stl_recede_09c.cpp / .h
│   │   ├── s04_warp_charge.cpp / .h
│   │   ├── s05_warp_cruise_2c.cpp / .h
│   │   ├── s06_warp_cruise_10c_cherenkov.cpp / .h
│   │   ├── s07_warp_8000c_history_bound.cpp / .h
│   │   ├── s08_warp_gravity_well.cpp / .h
│   │   ├── s09_chaos_instability_reflex.cpp / .h
│   │   ├── s10_hubble_horizon.cpp / .h
│   │   ├── s11_split_screen_stl_vs_warp.cpp / .h
│   │   └── s12_eye_ear_decoupling.cpp / .h
│   ├── validation/
│   │   ├── pixel_sampler.cpp / .h
│   │   ├── assertion.cpp / .h
│   │   ├── scalar_pixel_assertion.cpp / .h
│   │   ├── heatmap_diff_assertion.cpp / .h
│   │   ├── numeric_overlay.cpp / .h
│   │   ├── test_report.cpp / .h
│   │   └── validation_panel.cpp / .h
│   ├── ui/
│   │   ├── imgui_setup.cpp / .h
│   │   ├── parameter_panel.cpp / .h
│   │   ├── state_display.cpp / .h
│   │   ├── scenario_selector.cpp / .h
│   │   ├── profiler.cpp / .h
│   │   └── help_overlay.cpp / .h
│   ├── data/
│   │   ├── cfd_synthesizer.cpp / .h             # synthesize analytic Alcubierre RBF
│   │   ├── hull_loader.cpp / .h                 # load OBJ or generate procedural
│   │   ├── starfield_loader.cpp / .h            # generate or load star catalog
│   │   └── scenario_loader.cpp / .h             # parse scenario JSON files
│   └── util/
│       ├── log.cpp / .h
│       ├── timer.cpp / .h                       # CPU + GPU timers
│       ├── screenshot.cpp / .h                  # PNG capture via stb_image_write
│       └── color.cpp / .h                       # blackbody, Doppler color shift
├── tests/
│   ├── test_pixel_sampler.cpp                   # doctest unit tests
│   ├── test_rbf_eval.cpp
│   ├── test_chaos_pde_step.cpp
│   ├── test_observation_calc_kernel.cpp
│   ├── test_cherenkov_math_bridge.cpp
│   └── test_assertion_layer.cpp
├── assets/
│   ├── hull/
│   │   └── astra7_lowpoly.obj                   # ~10K tris placeholder
│   ├── starfield/
│   │   └── starfield_10k.bin                    # 10K star catalog
│   ├── cfd/
│   │   └── warp_cfd_rbf_synthetic_v1.json       # ~50-200 node test RBF (synthetic)
│   ├── scenarios/
│   │   ├── s01_rest_baseline.json
│   │   ├── s02_stl_recede_05c.json
│   │   ├── ... (one per scene)
│   │   └── s12_eye_ear_decoupling.json
│   └── reference_renders/                       # golden PNGs (canon-locked)
│       ├── s01_t0_canonical.png
│       ├── s05_t5s_warp_2c.png
│       └── ... (one per scene per canonical timestamp)
└── docs/
    ├── DESIGN.md                                # this v2 plan, copied as design ref
    ├── SCENES.md                                # per-scene walkthrough
    ├── VALIDATION.md                            # the three-layer methodology
    ├── BUILD.md                                 # Windows + Linux build
    ├── KNOWN_ISSUES.md                          # findings surfaced; spec-revision candidates
    └── CHANGELOG.md                             # per-phase landings
```

**Module count:** ~40 C++ files + ~20 CUDA files + ~25 shader files + 12 scenario JSONs. Estimated total: ~10,000-12,000 LOC.

---

## 6. The 12 visual test scenes

Each scene has the same structural pattern:
1. **Goal** — the physical effect being verified visually
2. **Spec basis** — exact spec section + line number
3. **Math primitives** — which `libastra_nexus` calls
4. **Rendering technique** — how pixels get produced
5. **UI controls** — what parameters the operator can sweep
6. **Assertions** — pixel-level checks against canonical math (≥3 per scene)
7. **Pass criteria** — what makes the scene pass mechanically

I retain my 12-scene structure from V1 (including the eye-ear decoupling scene the sibling plan didn't have). Below are the abbreviated definitions; full per-scene specs go in `docs/SCENES.md` when the implementing agent writes them.

### S01 — REST baseline (sanity check)

**Goal:** Confirm baseline render works; sun + Earth visible; starfield static; UI shows γ=1, dτ/dt=1, regime=REST.

**Spec basis:** §1.1 AstraCoord; §1.2 two-clock split; §3.3 regime state machine.

**Math primitives:** `Rapidity::gamma()` (returns 1.0 at REST); `dtau_dt_cosmic(W=0, grav=1, γ=1, warp=false) = 1.0`.

**Rendering:** hull mesh + starfield + sun point + Earth as point at 1 AU.

**Assertions:**
1. Pixel at ship center renders hull color
2. Pixel sample near Earth position shows the Earth's expected color
3. UI numeric overlay shows γ=1.000, dτ/dt=1.000 matching `libastra_nexus` to 6 decimals

### S02 — STL_REL recede at β=0.5

**Goal:** SR longitudinal Doppler visible on rear-facing starfield; aberration mild.

**Spec basis:** §3.4 four optical effects; §3.7 rapidity.

**Math primitives:** `Rapidity::gamma()` = cosh(atanh(0.5)) ≈ 1.155; `compute_z_kin(0.5*C_LIGHT)` ≈ 0.732.

**Rendering:** ship cockpit rear-view; planet behind redshifted per multiplicative composition.

**Assertions:**
1. Pixel at planet position shows R-channel shifted higher than B-channel (red-shifted)
2. Numeric overlay shows γ matching `libastra_nexus::Rapidity::gamma()` to 6 decimals
3. Aberration: stars in forward hemisphere visibly compressed toward center

### S03 — STL_REL recede at β=0.9

**Goal:** Dramatic redshift + aberration; γ=2.294; z_kin = √19 − 1 ≈ 3.359.

**Same structure as S02 with stronger parameters.**

### S04 — Warp charge sequence

**Goal:** Bubble forms over 5 seconds; CFD-RBF evaluated correctly; smooth-min blend visible at boundary.

**Spec basis:** §6 step 4 (smooth-min); §3.3 WARP_CHARGE → WARP_CRUISE transition.

**Math primitives:** RBF eval; W ramps 0→1 over scenario time.

**Rendering:** orbiting camera shows ship; bubble fades in as violet/blue volumetric glow with sharp boundary at high |∇W|.

**Assertions:**
1. At t=0, pixel near ship shows no bubble color
2. At t=5s, pixel at canonical bubble-boundary position shows expected W value (matches `eval_rbf_at()` from libastra)
3. Symmetry: pixels at (+x, 0, 0) and (-x, 0, 0) of ship show same W to within 0.01

### S05 — Warp cruise at v_app = 2c (THE PAYOFF SCENE — orbit reversal)

**Goal:** Planet 1 ly behind ship's orbit visibly runs BACKWARD at 1× speed when sampled at t_emit. THE canonical test of §3.11 retarded-time math.

**Spec basis:** §3.11 retarded-time observation; §10 "Retarded-time orbit reversal" validation row; existing C++ test [astra_nexus.cpp:639-677](proto/astra_nexus.cpp:639).

**Math primitives:** `observe(ship_pos, ship_vel, t_cosmic, body_pos, 0, R_WARP_CRUISE)` → ObservableState; `orbit_phase(orbit, observable.t_emit)`.

**Rendering:** rear-view; planet rendered at `body_state(t_emit)` position; trail mode shows decaying trail of where planet WAS rendered (visualizes reverse motion).

**Assertions:**
1. At v_app = 2c, observable's `apparent_rate` matches `compute_apparent_rate(2c, R_WARP_CRUISE) = -1.000` to 6 decimals
2. Orbital phase plotted in ImGui as time-series: dphase/dt < 0 (orbit running backward)
3. Over 30 simulation-seconds, total phase traversal matches Kepler integration: `phase(t+30) - phase(t) ≈ -30 * 2π / period` (1× reverse)
4. Trail mode shows clockwise → counter-clockwise transition visible to operator

**Pass criteria:** all 4 assertions pass AND **operator confirms the orbit visually appears to run backward** (final human sign-off).

### S06 — Warp cruise at v_app = 10c with Cherenkov cone (closes 5D-F4 gap)

**Goal:** Orbit reverses at 9× speed; Cherenkov cone visible with half-angle from `cos θ_c = 1/(n·β)`.

**Spec basis:** §6 step 10 + Appendix B (Cherenkov formula locked); §3.11.

**Math primitives:**
- `compute_apparent_rate(10c, R_WARP_CRUISE) = -9.000`
- **NEW:** `compute_cherenkov_angle(W, beta, n_refractive_default)` (closes 5D-F4 by adding to libastra_nexus)
- Provisional `n(W) = 1 + W` per the deep-dive `pre-Phase-E1` value (tunable)

**Rendering:** bubble + cone (forward-facing geometric mesh with half-angle from cherenkov_angle). Cone tinted blue-cyan per spec.

**Assertions:**
1. At W=1, β=10 (effective), cone half-angle within 1° of `acos(1/(n·β))` from libastra
2. apparent_rate matches libastra's compute_apparent_rate to 6 decimals
3. At β→0, cone collapses (UI shows "Cherenkov inactive: n·β ≤ 1")
4. Cone narrows as W increases (verified by sweeping W slider; angle decreases monotonically)

**Pass criteria:** all 4 assertions pass; the Cherenkov gap is CLOSED at code level (libastra_nexus assertion count: 66 → 69+).

### S07 — Warp cruise at v_app = 8000c (photon-source-history bound)

**Goal:** Source appears initially; after enough cosmic time, `t_emit < t_source_start` → `beyond_photon_history = true` → source DISAPPEARS (not faded; gone).

**Spec basis:** §3.11 photon-source-history bound; ObservableState.beyond_photon_history flag.

**Math primitives:** `observe(...)` → check `beyond_photon_history` flag; `t_source_start` per body (provisional schema per AUDIT R4).

**Rendering:** star with explicit `t_source_start = -10⁹ s` (turned on 1 Gy before scenario start). Ship pulls away at 8000c. Each frame, call `observe`; if flag true, omit star from frame.

**Assertions:**
1. Before crossover, source renders normally; pixel at source position has bright color
2. After crossover, pixel at source position has background color (source absent)
3. The transition is discrete: at frame N source visible, at frame N+1 source absent — NO intermediate fading
4. Crossover timing matches: cosmic-time at which `beyond_photon_history` first turned true matches simulation time within 1 frame

**Why this matters:** spec §3.11 says "the source is gone — not faded, not redshifted to extinction, *gone*." Most fictional warp treatments show fade. This scene proves the spec's distinct claim visually.

### S08 — Warp + Gravity Well composition

**Goal:** Bubble near 10·M_sun BH at r=200·r_s. Composition rule visible; tidal stress α_eff scaling visible; gravitational lensing (separate from warp lensing).

**Spec basis:** §3.2 composition rule; §7.1 chaos coupling `α_eff = α_base·(1 + k·M·L²/r³)`; §7.4 warp exclusion zone.

**Math primitives:** `compute_grav_factor(bh_list, ship_pos)`; `dtau_dt_cosmic(W, grav, γ, true)` composes; α_eff scaling per §7.1.

**Rendering:** ship with bubble; BH as black disc with subtle background lensing; chaos field intensity ramping up as r decreases.

**Assertions:**
1. UI shows regime as bitmask `WARP_CRUISE | GRAVITY_WELL` (0x28)
2. Schwarzschild factor `√(1 - r_s/r)` displayed value matches `libastra_nexus::compute_grav_factor` to 6 decimals
3. α_eff displayed = α_base · (1 + k·M·L²/r³) matches the §7.1 formula
4. dτ/dt_cosmic gauge needle matches `dtau_dt_cosmic()` output

### S09 — Chaos instability + Reflex stabilizer

**Goal:** Chaos PDE grows unstable when Reflex disabled; rapidly damps when Reflex enabled. Visible feedback loop.

**Spec basis:** §7.1 Fisher-KPP; §2.3.1 Reflex Contract (v0.129 NEW).

**Math primitives:** CUDA chaos PDE kernel (RK2 explicit step); PID Reflex stub (`reflex_stub.cu`) reads chaos amplitude, emits control vector.

**Rendering:** 2D slice heatmap of chaos field (viridis colormap) + 3D volume render. Time-series plot of max(χ), mean(χ).

**Script:**
- t=0..5s: Reflex DISABLED; chaos grows
- t=5s: Reflex ENABLED; chaos rapidly damps
- t=10..15s: operator slider injects chaos; Reflex re-damps; feedback visible

**Assertions:**
1. Field stays in [0,1] throughout (no NaN, no overflow)
2. CFL stability bound: at dt = 1/60s with provisional D, field bounded
3. When Reflex enabled, max(χ) decreases monotonically over ~1s damping period
4. Emergency dump triggers visually when chaos exceeds threshold (regime snap to STL)

### S10 — Hubble horizon body

**Goal:** Body at d > c/H₀ rendered frozen at horizon-crossing, dimming on separate timescale.

**Spec basis:** §3.12 cosmological expansion; `beyond_hubble_horizon` flag.

**Math primitives:** `observe(...)` → `beyond_hubble_horizon` flag.

**Rendering:** distant body rendered at frozen frame from horizon-crossing instant; color extremely redshifted; brightness fading over scenario time.

**Assertions:**
1. UI shows `beyond_hubble_horizon = true`
2. d_proper displayed in Mpc matches `astra_distance(ship, body)` from libastra
3. z_cosmo displayed matches `compute_z_cosmo(d) = H₀·d/c` to 6 decimals
4. Body pixel color is in the "extremely red" sector of RGB (R >> G ≈ B)

### S11 — Split-screen STL_REL vs WARP_CRUISE at same v_radial

**Goal:** Side-by-side comparison at v_radial = 0.5c shows different apparent_rate values per regime. Proves regime-dispatch is real, not artifact.

**Spec basis:** §3.11; §10 validation row "STL_REL formula was NOT 1/γ".

**Math primitives:**
- `compute_apparent_rate(0.5c, R_STL_REL)` = √(1/3) ≈ 0.5774
- `compute_apparent_rate(0.5c, R_WARP_CRUISE)` = 0.5

**Rendering:** split screen; left = STL_REL ship rear view; right = WARP_CRUISE ship rear view; same planet rendered in both with the same v_radial.

**Assertions:**
1. STL_REL planet's orbital phase advances at 0.5774× speed (libastra value)
2. WARP planet's orbital phase advances at 0.500× speed (libastra value)
3. Numerical readout shows both rates matching libastra to 4 decimals
4. The ratio (STL_rate / WARP_rate) at v=0.5c = √(1/3)/0.5 ≈ 1.155 — the regime-distinction is real

### S12 — Eye-ear decoupling at warp egress

**Goal:** Visual orbit reverses while audio frequency stays current. Proves §6.3 endogenous/exogenous principle is the designed experience.

**Spec basis:** §6.3 + §8.3 endogenous/exogenous; eye-ear decoupling as "feature not bug."

**Math primitives:** all of S05 (retarded-time) + simulated audio frequency display (UI only — no actual audio playback at v1).

**Rendering:** rear view shows planet running backward; UI shows "AUDIO (t_cosmic = NOW): warp drone 247Hz" and "VISUAL (t_emit = 1.0 years ago): orbit phase −1.31 rad". Time-gap shrinks after warp disengage at t=10s.

**Script:**
- t=0..10s: WARP_CRUISE at 2c; visual reversed; audio = warp drone (UI display)
- t=10s: warp.disengage(emergency); audio = warp shutdown (immediate UI change); visual continues reversed for ~1 year scenario time then re-syncs

**Assertions:**
1. During warp, UI shows audio_t = cosmic_time, visual_t = retarded_time, with t_emit < t_cosmic by ship-distance/c
2. At t=10s, audio_t jumps to new value (drone → shutdown sound label); visual_t continues reverse-walking
3. Over warp-shutdown period, the audio_t - visual_t gap shrinks to zero asymptotically
4. The numerical gap matches `t_cosmic - t_emit` from libastra `observe()` to 6 decimals

---

## 7. Visual ground-truth validation methodology (the load-bearing piece)

The bench's claim "math is correct AND it produces the right pixels" needs a methodology to mechanically verify. **Three layers of validation, each with a specific role:**

### 7.1 Layer 1 — Pixel-level scalar assertions (per-scene; runtime)

Each scene exposes a list of expected-pixel assertions:

```cpp
struct ScalarPixelAssertion {
    std::string name;                    // "bubble_center_W", human-readable
    glm::ivec2 framebuffer_coord;        // (x, y) in framebuffer
    int channel;                         // 0=R, 1=G, 2=B, 3=A, or special tag
    float expected_value;                // canonical math output via libastra_nexus
    float tolerance;                     // pass if |measured - expected| < tolerance
};

class PixelSampler {
public:
    // After scene.Render(), reads back framebuffer via glReadPixels
    // Walks scene.assertions(); samples pixel; logs PASS/FAIL
    std::vector<AssertionResult> Sample(const IScene& scene, GLuint framebuffer);
};
```

**Default tolerance:** 1% of expected value OR ±0.01 absolute, whichever is larger.

**Why this matters:** the canonical math value comes from `libastra_nexus::compute_*()` — the SAME implementation that runs the 69+ C++ assertions. The visualizer compares a pixel against the same math the test suite uses. Mechanical, not eye-balled.

### 7.2 Layer 2 — Heatmap diff assertions (golden image comparison)

For each scene, a canonical configuration produces a golden PNG (`assets/reference_renders/scene_N.png`). CI compares headless renders to goldens:

```cpp
struct HeatmapDiffAssertion {
    std::string golden_path;             // "assets/reference_renders/s01_t0.png"
    float max_mean_diff;                 // 0.01 = 1% mean diff tolerance
    float max_pixel_diff;                // 0.10 = no individual pixel may differ by >10%
};
```

**Goldens regeneration policy** (mirrors textverse's `scope.yaml` required_invariants discipline):
- Goldens are CANON-LOCKED once approved.
- `--regenerate-goldens` flag exists but requires explicit operator sign-off in commit message.
- CI fails if goldens regenerated without sign-off marker.
- Documented in `docs/VALIDATION.md` as project discipline.

### 7.3 Layer 3 — Side-by-side numeric overlay (real-time operator validation)

Every scene shows in a corner overlay:
- Current rendered value (sampled from focal pixel)
- Canonical math value (from `libastra_nexus`)
- Difference (absolute + relative)
- PASS/FAIL color (green/red)

```
┌─────────────────────────────────────┐
│ S06 — Warp Cruise 10c + Cherenkov   │
├─────────────────────────────────────┤
│ Rendered apparent_rate:   -9.0012   │
│ libastra apparent_rate:   -9.0000   │
│ Diff:                      0.0012   │
│ Tolerance:                 0.01     │
│ ► PASS                              │
├─────────────────────────────────────┤
│ Rendered cherenkov_angle: 84.27°    │
│ libastra cherenkov_angle: 84.26°    │
│ Diff:                      0.01°    │
│ Tolerance:                 1.0°     │
│ ► PASS                              │
└─────────────────────────────────────┘
```

This lets a human watch math and pixels agree in real time during interactive use.

### 7.4 The validation report (JSON output for CI)

After headless run, write structured JSON:

```json
{
  "version": "0.1.0",
  "build_commit": "abc123def456",
  "ran_at": "2026-05-20T10:00:00Z",
  "platform": "Windows 11 / RTX 5090 / CUDA 12.4 / GL 4.6",
  "libastra_nexus_version": "v0.129.day3",
  "libastra_nexus_assertion_count": 69,
  "scenes": [
    {
      "name": "S01_RestBaseline",
      "frame_ms": 14.2,
      "assertions": [
        {
          "name": "ship_center_pixel_hull",
          "expected": 0.45,
          "measured": 0.452,
          "diff": 0.002,
          "tolerance": 0.01,
          "passed": true
        }
      ],
      "heatmap_diff": {
        "golden": "s01_t0_canonical.png",
        "mean_diff": 0.0034,
        "max_diff": 0.012,
        "tolerance_mean": 0.01,
        "tolerance_max": 0.10,
        "passed": true
      },
      "screenshot_path": "ci_results/s01.png"
    }
  ],
  "summary": {
    "scenes_total": 12,
    "scenes_passed": 12,
    "scenes_failed": 0,
    "assertions_total": 48,
    "assertions_passed": 48,
    "total_runtime_seconds": 87.3
  }
}
```

**CI gate:** exit code 0 iff `summary.scenes_failed == 0` and `summary.assertions_passed == assertions_total`.

---

## 8. UI design

### 8.1 Layout (Dear ImGui docking branch)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Scenario: S05 Warp Cruise 2c ▼] [Reset] [Pause] 60 FPS / 16.2 ms  │  ← Top bar
├──────────┬───────────────────────────────────┬──────────────────────┤
│          │                                   │                      │
│  PARAM   │                                   │   STATE              │
│  PANEL   │           VIEWPORT                │   + VALIDATION       │
│          │                                   │                      │
│  [slider │     (the 3D render goes here)     │  Regime: WARP_CRUISE │
│   W=1.0] │                                   │  γ: 1.000            │
│          │                                   │  W: 1.00             │
│  [slider │                                   │  dτ/dt: 0.5          │
│   v_app  │                                   │  Apparent rate:      │
│   =2c]   │                                   │   rendered:  -1.0012 │
│          │                                   │   libastra:  -1.0000 │
│  [Reflex │                                   │   diff:       0.0012 │
│   ON/OFF]│                                   │   ► PASS             │
│          │                                   │                      │
│  ...     │                                   │  Per-pass timing:    │
│          │                                   │  Chaos PDE:   0.8 ms │
│  [F12    │                                   │  Warp eval:   1.5 ms │
│   ScrCap]│                                   │  Lensing:     0.6 ms │
│          │                                   │  ... (live)          │
├──────────┴───────────────────────────────────┴──────────────────────┤
│ Console: [scenario loaded: s05] [Reflex enabled] [t=15.3s sim time] │  ← Status bar
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Hotkeys

- **WASD**: camera movement (free mode)
- **Q/E**: camera up/down
- **Mouse drag**: camera look (free mode)
- **1-9**: select scenarios 1-9
- **Shift+1, Shift+2, Shift+3**: scenarios 10, 11, 12
- **Space**: pause/resume
- **R**: reset current scenario
- **F1**: toggle help overlay
- **F2**: toggle parameter panel
- **F3**: toggle state display
- **F4**: toggle debug overlays (∇W arrows, RBF nodes)
- **F5**: hot-reload shaders (development)
- **F11**: toggle fullscreen
- **F12**: screenshot (PNG + JSON state dump)
- **Esc**: quit

### 8.3 Parameter panel + state display per scene

Each scene contributes its own parameter widgets to the left panel (e.g., S03 adds β slider; S08 adds BH mass + distance sliders). The validation overlay (right panel section) auto-populates from `scene.assertions()`.

---

## 9. Performance budgets

Per-pass budget at 1080p on RTX 4070 (target ≥60 FPS = 16.67 ms budget):

| Pass | Budget (ms) |
|---|---|
| CPU: physics driver tick | 0.5 |
| CPU + GPU: chaos PDE step (RK2) | 1.5 |
| GPU: warp field SVT-equivalent populate | 1.5 |
| GPU: volume ray-march | 3-4 |
| GPU: geometric lensing post | 1.5 |
| GPU: starfield render | 1.0 |
| GPU: cherenkov + trail | 0.5 |
| GPU: hull + UI + post-process | 3.0 |
| Reserve | ~3 |

**Hardware tier targets:**

| Target | Hardware | Resolution | Notes |
|---|---|---|---|
| 60 FPS | RTX 4070 | 1080p | minimum acceptable |
| 60 FPS | RTX 4090 | 1440p | recommended |
| 120 FPS | RTX 5090 | 1080p | upper-tier |
| 30 FPS | RTX 3060 | 1080p | low-end fallback |

VRAM at 5090 reference tier:
- Hull SDF (placeholder + damage map): ~20 MB
- CFD-RBF + spatial hash: ~250 KB
- Chaos field (2× 128³): 16 MB
- Warp field volume: ~8 MB
- Reflex stub state: <1 KB
- Total physics: ~45 MB
- Plus UE5-style render targets: ~2 GB
- Total: ~2 GB free; trivially fits.

---

## 10. Phased implementation roadmap (14-16 weeks realistic)

### V0 — Scaffolding (weeks 1-2)

**Deliverables:**
- CMake project skeleton with FetchContent for GLFW, glad, ImGui, glm, stb, nlohmann_json, doctest
- `libastra_nexus` static library extracted from `proto/astra_nexus.cpp` (PER §3.1 — the critical foundation)
- `proto/astra_nexus.exe` continues to build, passes all 66 assertions, links against the new library
- GLFW window opens at 1280×720; OpenGL 4.6 context valid; ImGui renders "Hello, ASTRA-7 Visualizer"
- CUDA toolkit detected; trivial CUDA kernel runs; cudaGraphicsGLRegisterBuffer sanity test passes
- CLI parser handles `--help`, `--scene=`, `--headless`, `--output=`, `--version`
- Headless mode framework exists (no scenes yet); exits 0 with empty JSON report
- Builds on Windows 11 (MSVC) AND Linux x86_64 (gcc-13) from same CMake

**Gate:** `astra_visualizer.exe --help` prints usage. Empty window opens in interactive mode. Headless mode exits 0 with empty scene list. `proto/astra_nexus.exe` still passes 66 assertions.

### V1 — Renderer foundations + Scenes 1-2 (weeks 3-4)

**Deliverables:**
- `renderer/cuda_gl_interop` glue (shared 3D textures)
- `renderer/compute_program` + `graphics_program` GL wrappers
- `physics/rbf_network` loads synthetic 50-200 node test RBF from JSON
- Compute shader `warp_field.cu` + GLSL `raymarch.frag` evaluates RBF + renders volumetric bubble
- `physics/physics_core` facade over libastra_nexus
- Scene S01 (REST baseline) with hull + starfield + planet
- Scene S04 (Warp Charge) extends S01 with bubble formation
- PixelSampler implementation; 6-8 assertions across both scenes
- Validation overlay rendering (Layer 3 side-by-side numeric display)

**Gate:** S01 + S04 render at 60+ FPS on RTX 4070; all assertions PASS in interactive mode; headless mode dumps PNGs; JSON report valid; goldens captured.

### V2 — Doppler + Starfield Scenes (weeks 5-6)

**Deliverables:**
- Scene S02 (STL_REL β=0.5) + Scene S03 (STL_REL β=0.9)
- Starfield Doppler shift in `starfield.frag` shader
- Aberration math in vertex shader
- Color shift via blackbody approximation (Tanner Helland fit) keyed on z_total

**Gate:** S02 + S03 render correctly; visible color shifts; pixel assertions match libastra-computed z_kin values; all assertions PASS.

### V3 — Cherenkov + Lensing (weeks 7-8)

**Deliverables:**
- **NEW C++ in libastra_nexus:** `compute_cherenkov_angle(W, beta, n_refractive_default)` with ≥3 assertions in libastra's test suite (libastra count: 66 → 69+). **CLOSES 5D-F4 GAP.**
- `physics/cherenkov_math.cpp` bridges to libastra
- Scene S06 (Warp Cruise 10c + Cherenkov): cone mesh + θ_c computation
- Geometric lensing post-pass; `lensing.frag` deflects ray direction by ∇W; samples background skybox
- Scene supports lensing sweep via `α_lens` slider

**Gate:** S06 renders; Cherenkov cone visible with correct angle; lensing visible around bubble; all assertions PASS; libastra Cherenkov assertions pass standalone.

### V4 — THE PAYOFF: Scenes 5 + 7 (weeks 9-11)

This is the most visually distinctive phase. Budget extra time.

**Deliverables:**
- `kernels/observation_calc.cu`: per-body Newton iteration for t_emit (mirrors libastra `observe()`)
- `renderer/retarded_body`: per-instance Kepler-at-t_emit rendering
- Scene S05 (Warp Cruise 2c — orbit reversal): trail mode; orbital phase plot
- Scene S07 (Photon-source-history bound): clean source disappearance
- Numeric overlay shows live t_emit, apparent_rate, beyond_photon_history flag

**Gate:** S05 + S07 render correctly. **Operator personally watches S05 and CONFIRMS** the orbit visually appears to run backward at v_apparent = 2c. This is the "you have to see it to believe it" payoff scene; operator sign-off required.

### V5 — Chaos PDE + Reflex (weeks 12-13)

**Deliverables:**
- `kernels/chaos_pde.cu`: RK2 Fisher-KPP solver; double-buffered surface objects
- 2D slice + 3D volumetric chaos visualization
- `physics/reflex_stub` + `kernels/reflex_stub.cu`: PID controller (chaos amplitude → control vector)
- Scene S09 (Chaos Instability + Reflex): toggle Reflex; observe damping
- Scene S08 (Warp + Gravity Well): composition rule visualization

**Gate:** S08 + S09 work; chaos PDE stable; Reflex feedback visible; emergency dump triggers correctly; all assertions PASS.

### V6 — Hubble + Split-screen + Eye-Ear (weeks 14-15)

**Deliverables:**
- Scene S10 (Hubble horizon): frozen + dim body rendering
- Scene S11 (Split-screen STL vs WARP at v=0.5c): dual-viewport render setup
- Scene S12 (Eye-ear decoupling): warp egress with UI audio-frequency display
- All 12 scenes complete

**Gate:** All 12 scenes render correctly; all ~48 assertions PASS; goldens captured for each; headless mode runs all 12 in <2 minutes.

### V7 — CI integration + polish + documentation (week 16)

**Deliverables:**
- Golden PNG references generated for each scene at canonical configurations
- Headless mode hardened; JSON test report finalized
- CI script (GitHub Actions or local batch) runs `--headless --scene=all` and gates on report
- Performance overlay (per-pass GPU timing visible)
- Documentation: `README.md`, `BUILD.md`, `SCENES.md`, `VALIDATION.md`, `KNOWN_ISSUES.md`
- Release build: `astra_visualizer.exe` for Windows 11 + Linux x86_64 binary

**Gate:** CI runs visualizer; reports PASS for all 12 scenes; gates green. Documentation complete. Release-quality binary.

**Total: 16 weeks (~4 months) for one developer pair-programming with Claude Code or similar; 6 months solo with operator review cycles.**

---

## 11. Coding-agent handoff brief

### 11.1 What you (the next coding agent) need to know

1. **Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md` (then v0.128 as fallback). The physics is locked there; when in doubt, the spec wins.

2. **Math basis:** `proto/astra_nexus.cpp` (1009 lines, 66 assertions at commit 69ee692 + later). This is the canonical math; every numeric in the visualizer must trace back here. **Your V0 task: extract it as `libastra_nexus` static library per §3.1.**

3. **Vision basis:** this document (v2). It tells you WHAT to build but not HOW to write the C++. Use idiomatic modern C++ (C++20 if your toolchain supports; C++17 minimum).

4. **The 12 scenes are NOT all equal effort:**
   - Scenes S01, S02, S03, S10, S11 are straightforward
   - Scenes S04, S08 are medium
   - **Scenes S05, S06, S07, S09, S12 are the hardest** — Scene 5 (orbit reversal) is the most visually distinctive AND the most likely to have subtle math/render misalignment; Scene 6 (Cherenkov) closes the 5D-F4 gap (lands new math); Scene 12 (eye-ear) is the subtlest decoupling visualization. Budget extra time on these.

5. **CUDA-OpenGL interop is the most likely source of bugs.** Test interop with trivial cases (vector-add → SSBO → fragment shader) BEFORE building it into Scene 4. Get a CUDA kernel writing to a GL buffer + a fragment shader reading the buffer working end-to-end on day 1 of Phase V1. NVIDIA's `simpleGL` CUDA sample is the canonical reference.

6. **The three-layer validation methodology (§7) is load-bearing.** Don't skip pixel-level assertions. They are how we PROVE math matches visuals. Without them: "the math test does math; this tool does pixels; we HOPE they agree." With them: "the math test does math; this tool does pixels; we MECHANICALLY VERIFY they agree."

7. **Headless mode is not optional.** CI needs it. Build it from V0; maintain it through every scene addition. If interactive mode renders a scene at 60 FPS and headless mode crashes on it, fix the headless bug before declaring the scene done.

8. **Goldens (reference PNGs) are canon.** Once a scene is operator-approved visually, its golden PNG is locked. Future changes that alter the golden require operator review (same discipline as scope.yaml's `required_invariants` in textverse). The `--regenerate-goldens` flag requires explicit operator sign-off in commit message.

9. **Don't reinvent the math.** Every numeric quantity the visualizer compares against MUST come from a `libastra_nexus` function call. Do NOT reimplement `compute_apparent_rate` in HLSL or GLSL or anywhere else. The math lives in C++ in one place. Shaders may approximate for speed (float32 instead of float64), but the pixel-assertion comparison ALWAYS runs the canonical float64 math from the library.

10. **Cross-platform discipline:** Windows 11 primary; Linux x86_64 acceptable second. Test BOTH every phase. **No Apple/Mac/Metal/iOS anywhere.** Don't `#ifdef __APPLE__` even defensively; the codebase is Apple-free by lock.

11. **C/C++ only for new code:** No Python in the visualizer (no Python build scripts; CMake is the build system). The existing `proto/textverse/` Python is grandfathered; the visualizer does NOT depend on textverse.

12. **The Cherenkov gap (per AUDIT 5D-F4) is explicitly CLOSED by this project.** Spec §6 step 10's `cos θ_c = 1/(n·β)` formula has zero code implementation today. Phase V3 lands `compute_cherenkov_angle()` in libastra_nexus with ≥3 assertions; brings C++ test count from 66 to 69+.

### 11.2 Where to look when stuck

| Problem | First-look reference |
|---|---|
| Math behaving unexpectedly | `proto/libastra_nexus/` source + assertion outputs from `astra_nexus.exe` |
| Physics interpretation unclear | `docs/spec-v0.129-tentative-2026-05-16.md` (fallback to v0.128) |
| Visual effect not matching expectation | This document, the scene's "Rendering technique" section |
| CUDA-GL interop hanging / crashing | NVIDIA CUDA sample `simpleGL` is the canonical reference |
| Performance below 60 FPS | Performance overlay (built in Phase V7); profile with NVIDIA Nsight Graphics |
| Pixel assertion failing | Print expected vs measured to console; check tolerance reasonable for float-precision noise |
| ImGui controls not responding | Verify `ImGui_ImplGlfw_NewFrame()` + `ImGui_ImplOpenGL3_NewFrame()` called every loop iteration |
| Build failing on Linux but works on Windows | CUDA architecture selection; nvcc version; pthread linking; gcc-13 minimum |
| Headless render differs from interactive | Likely: missing `glFinish()` before `glReadPixels`; ImGui state from interactive mode polluting headless; framebuffer not bound when expected |
| Golden diff fails | Operator-review the diff visually first; if visual change intentional, regenerate goldens with operator sign-off |
| `compute_cherenkov_angle()` produces unexpected angles | Verify `n_refractive_default(W) = 1 + W` matches your scenario; verify β is the EFFECTIVE velocity (not raw v) |

### 11.3 Build instructions

**Windows 11:**
```batch
:: prerequisites: Visual Studio 2022 17.8+, CUDA Toolkit 12.4+, CMake 3.27+, Git
cd proto\visualizer
git submodule update --init --recursive

cmake -B build -G "Visual Studio 17 2022" -A x64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      -DCMAKE_CUDA_ARCHITECTURES="86;89;90"
cmake --build build --config Release

build\Release\astra_visualizer.exe
```

**Linux x86_64:**
```bash
# prerequisites: gcc-13+, CUDA 12.4+, CMake 3.27+
cd proto/visualizer
git submodule update --init --recursive

cmake -B build -G Ninja \
      -DCMAKE_BUILD_TYPE=Release \
      -DCMAKE_CUDA_ARCHITECTURES="86;89;90"
cmake --build build

./build/astra_visualizer
```

**Smoke tests:**
```bash
./astra_visualizer --version
# Expected: "astra_visualizer v0.1.0; linked against libastra_nexus v0.129.day3"

./astra_visualizer --headless --scene=S01_RestBaseline --output=smoke_results/
# Expected: smoke_results/s01.png exists; smoke_results/report.json shows PASS
```

---

## 12. The deeper structural value (three roles this testbed serves)

Beyond the immediate "verify math produces right pixels," this testbed serves three structural roles per spec § frameworks:

### 12.1 It IS rig 3 (engine-side rendering verification) per spec §15.8 + 3B-U3

Spec §15.8 names three rigs (physics binary / LLM bundle / engine — deferred). Discovery 3B's U3 added rig 4 (prose canon) and rig 5 (spec audit). **`astra_visualizer.exe` IS rig 3.** The engine-side verification instrument the spec called for but didn't have a concrete implementation path. The project does not need to wait for UE5 integration to run rig 3; this visualizer runs it on bare OpenGL.

When v0.130 spec is drafted, rig 3 can be cited as operational (alongside rigs 1, 2, 4, 5) — not as deferred.

### 12.2 It de-risks UE5 integration

When UE5 Phase E2-E5 lands (per `DISCOVERY_2026-05-16_TECHDIVE_UE5.md`), every visual effect that ships there will have been previously validated in this visualizer. UE5 surprises become localizable: "the math + bare OpenGL produces correct visuals; UE5 wraps that same math + a fancier renderer; if UE5 disagrees with bare OpenGL, the bug is in UE5's wrapper, not in the math." This bounds where UE5 bugs can hide.

**Golden PNGs from this visualizer become the canonical reference for UE5's rendering**. UE5's output gets compared against these goldens; mismatches are UE5 implementation drift, caught early.

### 12.3 It is a publishable artifact

A standalone Windows .exe that visually demonstrates retarded-time orbit reversal at v_apparent > c is a compelling proof-of-concept for the project. It can ship with the GitHub repo as a "see the physics" demo. It can be referenced in academic discussions of analog-gravity warp-field simulations. It can be the project's first publicly-shareable artifact while the main game is still in pre-Phase-E0 development.

It is also a recruiting and motivation artifact: a contributor watching the orbit-reversal scene visibly working at v_app=2c gets a stronger sense of the project's structural commitments than reading the 765-line spec.

---

## 13. Predicted spec revisions this testbed will surface

Per spec §15.4: this testbed is a closed-loop measurement instrument; findings from running it justify v0.130 spec revisions. Predicted findings (likely; not guaranteed):

| Predicted finding | Spec section affected |
|---|---|
| Cherenkov implementation produces visible cone; formula confirmed; default `n(W) = 1 + W` tuned | §6 step 10 + Appendix B locked numerics |
| Warp wake trail is visually compelling and physically motivated | §3.6 or §6 (new sub-section: wake metric residual) |
| `t_source_start` per-body schema concretization needed (S07 forces the issue) | §3.11 (audit's R4) |
| α_lens lensing coefficient empirically tuned to ~3-5 | Appendix B |
| n(W) refractive index function default empirically tuned | §6 step 10 + Appendix B |
| Chaos PDE α_base + k_coupling empirically tuned for stable behavior | §7.1 + Appendix B |
| Reflex stub PID gains empirically tuned (informational; real Reflex is trained) | §2.3.1 (advisory) |
| Eye-ear decoupling at warp egress visually compelling (or jarring; either is finding) | §6.3 + §8.3 endogenous/exogenous principle |
| Smooth-min `k` parameter for SDF blending empirically settled | §6 step 4 + Appendix B |

Each finding lands as an entry in `docs/KNOWN_ISSUES.md`; per §15.4 the operator decides which justify spec revisions.

---

## 14. Acceptance criteria

The visualizer is **v1 complete** when ALL of:

1. ✅ Builds cleanly on Windows 11 + MSVC 2022 + CUDA Toolkit 12.4+ + CMake 3.27+
2. ✅ Builds cleanly on Linux x86_64 + GCC 13+ + CUDA Toolkit 12.4+ + CMake 3.27+
3. ✅ All 12 scenes load and run without crashing
4. ✅ Each scene produces visuals matching the criteria in §6 of this document
5. ✅ Three-layer validation operational: pixel assertions + heatmap diff + numeric overlay
6. ✅ Each scene has ≥3 pixel-level assertions; total ≥36 assertions; all PASS on reference 5090 setup
7. ✅ Side-by-side numeric overlay shows rendered vs libastra values with diff + PASS/FAIL color
8. ✅ Per-pass GPU timing visible in profiler panel
9. ✅ Headless mode runs all 12 scenes in <2 minutes; JSON report valid; CI gate works
10. ✅ Golden PNGs locked under `assets/reference_renders/`; heatmap diff < 1% mean for all
11. ✅ `--regenerate-goldens` flag exists with operator-sign-off enforcement
12. ✅ F12 in interactive mode saves PNG + JSON state dump
13. ✅ Reaches 60 FPS at 1080p on RTX 4070 (target hardware)
14. ✅ `libastra_nexus` extracted; `proto/astra_nexus.exe` still passes 66 original assertions + 3+ new Cherenkov assertions = 69+
15. ✅ **Cherenkov gap closed:** `compute_cherenkov_angle()` in libastra_nexus with 3+ assertions added to test suite
16. ✅ doctest unit tests pass for: pixel_sampler, rbf_eval, chaos_pde_step, observation_calc_kernel, cherenkov_math_bridge, assertion_layer
17. ✅ Documentation complete: README, BUILD, SCENES, VALIDATION, KNOWN_ISSUES, CHANGELOG
18. ✅ No Python in the codebase; no Apple-specific code paths; no UE5 dependency
19. ✅ **Operator has personally watched Scene S05 (RetardedTimeOrbitReversal) and CONFIRMED the orbit visually appears to run backward at v_apparent = 2c.** (Required human sign-off; the "you have to see it to believe it" payoff.)

---

## 15. Open questions for operator

### Q1 — Linux build priority: from V0 or post-Windows-completion?

Building cross-platform from V0 adds ~10-15% time but ensures Linux x86_64 works. Building Windows-first and porting after is faster initially but historically produces more porting bugs.

**Recommendation:** cross-platform from V0. The CMake structure makes it cheap if done upfront; expensive if retrofitted.

---

### Q2 — `libastra_nexus` extraction: hard requirement V0, or can it slip to V1?

The library extraction is the most important architectural change. If it slips to V1, the visualizer briefly depends on direct `astra_nexus.cpp` inclusion which is fragile.

**Recommendation:** hard requirement V0. Don't start V1 until V0 includes the working extraction.

---

### Q3 — Reference RBF network: synthetic test or real CFD output?

V1 needs a CFD-RBF network for the warp field. Two options:
- **(a) Synthetic test RBF** (~50-200 hand-placed Gaussians forming a bubble shape) — fast to make, no CFD dependency, sufficient for visual ground-truth
- **(b) Real CFD output** processed offline with OpenFOAM + RBF fit — proper but multi-week additional work

**Recommendation:** synthetic for V1-V6. Real CFD output deferred to a future v0.2 visualizer that closes Phase E0 deeper. The synthetic RBF tests rendering pipeline correctness; whether RBF correctly represents real CFD physics is a separate question covered by `proto/astra_nexus` math validation.

---

### Q4 — Cherenkov closure: in libastra_nexus or in visualizer only?

The Cherenkov gap (per AUDIT 5D-F4) is the project's only locked formula with zero implementation. Scene S06 needs it. Where does it live?

**Recommendation:** in `libastra_nexus::cherenkov_angle()` with assertions in C++ test suite. The gap closes at the math layer (where every other formula lives); the visualizer just calls it. Bumps libastra assertion count from 66 to 69+.

---

### Q5 — Goldens regeneration policy: when goldens drift?

After scene refinement, the golden PNG may need updating. Strict policy: goldens require explicit operator sign-off via commit-message marker. Lenient policy: any commit can regenerate goldens.

**Recommendation:** strict. Goldens are canonical reference images; require same care as `proto/astra_nexus.cpp` assertions. `--regenerate-goldens` flag requires operator sign-off marker in commit message; CI fails without it.

---

### Q6 — Should V1 (Phase V1) implement S01 OR S01+S04 together?

S04 is mostly a parameter extension of S01 (add bubble formation; same render pipeline). Doing them together is ~1.3× the effort of S01 alone; separately is 2 phases of similar work.

**Recommendation:** together. The marginal cost is low; shared rendering pipeline benefits.

---

### Q7 — MP4 video recording: V7 polish or skip entirely?

PNG sequence capture (`--record-png-sequence`) is straightforward. MP4 requires either ffmpeg dependency or custom encoder. Could rely on PNG sequence + operator-side ffmpeg conversion.

**Recommendation:** PNG sequences in V7; MP4 conversion is operator-side post-processing. No ffmpeg dependency in the visualizer.

---

### Q8 — Should the visualizer eventually move to its own repo?

The visualizer is engine-agnostic; future ASTRA-7 contributors could use it without touching UE5 or the LLM bundle. Could live in its own repo `astra-7-visualizer` under the same org.

**Recommendation:** initially under `proto/visualizer/` in the main ASTRA-7 repo; split to separate repo when it stabilizes (v1.x); makes recruiting easier as a public artifact.

---

### Q9 — Operator-confirmed scene S05 sign-off: at V4 completion only, or earlier dry-runs?

S05 is the THE payoff scene; final acceptance requires operator personally watching it. Should there be intermediate operator-watching at V3 (with partial S05) or only at V4 (with complete S05)?

**Recommendation:** V4 only. Earlier operator-watching of partial scenes wastes operator attention. V4's S05 is the final form for the sign-off.

---

## 16. Summary table — what gets built and when

| Phase | Weeks | Deliverable | Gate |
|---|---|---|---|
| V0 | 1-2 | Scaffolding + libastra_nexus extraction + CLI + headless framework | Window opens; CUDA detected; CLI parses; original astra_nexus.exe still passes 66 assertions |
| V1 | 3-4 | Renderer + S01 (REST) + S04 (Warp Charge) + 3-layer validation | 60 FPS; 6-8 assertions PASS; goldens captured |
| V2 | 5-6 | S02 + S03 (STL Doppler scenes) + starfield Doppler shader | Color shifts visible; assertions PASS |
| V3 | 7-8 | S06 (Cherenkov + 10c) — closes 5D-F4 — + lensing infrastructure | libastra Cherenkov assertions land (66→69+); cone + lensing visible |
| V4 | 9-11 | **THE PAYOFF: S05 (orbit reversal) + S07 (photon history)** | Operator personally watches S05 + confirms reversal visible |
| V5 | 12-13 | S08 (Warp+Gravity) + S09 (Chaos+Reflex) | CUDA-GL interop hardened; Reflex feedback visible |
| V6 | 14-15 | S10 (Hubble) + S11 (split-screen) + S12 (eye-ear decoupling) | All 12 scenes complete |
| V7 | 16 | CI integration + golden lock + documentation + Linux release | CI green; docs complete; release binary |

**Total: 16 weeks (~4 months) for one developer + Claude Code pair-programming; 6 months solo with operator review cycles.**

---

## 17. Closing

This v2 integrates the best of both sibling proposals:

- From the sibling plan: `libastra_nexus` extraction, three-layer validation methodology, headless CI mode, golden regeneration discipline, three structural roles framing, Cherenkov gap closure as explicit deliverable, troubleshooting table, coding-agent handoff brief structure.

- From my v1: 12-scenario coverage (including S12 eye-ear decoupling), warp wake trail as potential spec-revision finding, detailed tech-stack rationale with explicit NOT-chosen alternatives, UI layout diagram with hotkeys, performance budgets per pass, predicted spec revisions list, risk assessment, explicit out-of-scope enumeration.

- New synthesis: the three-layer validation explicitly mapped to scope-discipline (goldens canon-locked); calendar reset to realistic 16 weeks; libastra_nexus extraction promoted to V0 hard requirement; Scene S05 operator sign-off as final acceptance.

The visualizer is the **engine-agnostic ground truth** between the math (`proto/libastra_nexus`) and the eventual UE5 rendering. It validates the visual physics claims of v0.129 without depending on UE5's complexity. It closes the Cherenkov gap at the math layer. It produces canonical reference images that UE5's rendering must match. It IS rig 3.

The math is locked. The visual claims are testable. A coding agent can pick this up and ship in 16 weeks. The validation methodology is mechanical. The closure is empirical.

**Build it.**

— Plan v2, 2026-05-16 —
