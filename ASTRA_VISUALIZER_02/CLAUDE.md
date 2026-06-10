# CLAUDE.md — ASTRA-7 Visualizer 02

**Operating contract for autonomous build sessions inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`.**
**Pairs with `DESIGN_SPEC.md` in this same folder.**
**Date authored:** 2026-05-16

---

## 0. SCOPE BOUNDARY — read first, never violate

You are working inside **`C:\ASTRA-7\ASTRA_VISUALIZER_02\`** and ONLY inside it.

- **READ** any file in `C:\ASTRA-7\` or any subdirectory — fine.
- **READ** reference projects at `C:\Buddhabrot_CUDA\` and `C:\buddhabrot-main\` — fine.
- **WRITE / EDIT / DELETE / CREATE** anything outside `C:\ASTRA-7\ASTRA_VISUALIZER_02\` — **FORBIDDEN.**
- **WRITE / EDIT / DELETE / CREATE** anywhere inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\` — **GO.**

This is a hard boundary. Even if you find a typo in `docs/spec-v0.129-tentative-2026-05-16.md`,
you do NOT fix it. You note it in `BLOCKERS.md` (inside this folder) and continue.

The parent project (`C:\ASTRA-7\`) is operator-managed. This subfolder is your sandbox.

---

## 1. Cold Start protocol

Before doing anything in this folder:

1. Read `DESIGN_SPEC.md` (in this folder) — the technical/physics spec.
2. Read this entire CLAUDE.md.
3. Check `BUILD_LOG.md` (in this folder) — see what prior sessions did. Append-only.
4. Check `BLOCKERS.md` (in this folder) — see unresolved issues. If empty/absent, you start clean.
5. Read these reference docs in `C:\ASTRA-7\` (READ ONLY):
   - `docs/spec-v0.129-tentative-2026-05-16.md` — physics canon (§3.11 retarded time, §6.3 Observation Calculator, §6 step 10 Cherenkov, §7.1 chaos PDE)
   - `proto/astra_nexus.cpp` — 1009-line C++ math reference; 66 assertions you must NEVER break
   - `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md` — useful context but UE5-specific; you are NOT building for UE5
   - `ASTRA_VISUALIZER_PLAN_2026-05-16_v2_FINAL.md` — the project plan this CLAUDE.md is the operational version of
6. Read these reference projects (READ ONLY; pattern templates):
   - `C:\Buddhabrot_CUDA\CLAUDE.md` + `DESIGN_SPEC.md` + `CMakeLists.txt` — the proven pattern; CUDA-OpenGL interop, FetchContent, static linkage, autonomous-build operating discipline
   - `C:\Buddhabrot_CUDA\BUILD_LOG.md` — log format + the gotchas they hit (most still apply to us)
7. Quick environment audit (run each; record in BUILD_LOG.md):
   ```
   nvcc --version                                            # need CUDA 12.x or 13.x
   nvidia-smi                                                # verify GPU is RTX 40/50-series, compute_89/120
   cmake --version                                           # need ≥ 3.27 (VS-bundled OK)
   where cl.exe                                              # MSVC available (from Developer prompt)
   ```
8. Then begin work.

Do not skip steps. The reference projects (especially `Buddhabrot_CUDA`) have ALREADY hit
and solved the CUDA-MSVC integration gotchas you would otherwise rediscover.

---

## 2. Mission

Build `astra_visualizer.exe` — a Windows 11 native, single-file CUDA + OpenGL visualization
testbed that renders the 14-equation physics framework from `proto/astra_nexus.cpp` in
real-time AND in headless (static PNG dump) mode, with mechanical pixel-level validation
against canonical math from `libastra_nexus`.

**12 visual test scenes** demonstrating:

| # | Scene name | Physics phenomenon |
|---|---|---|
| S01 | RestBaseline | Hull + starfield sanity check at REST regime |
| S02 | STL_Recede_05c | SR longitudinal Doppler + mild aberration at β=0.5 |
| S03 | STL_Recede_09c | Dramatic SR Doppler + aberration at β=0.9 |
| S04 | WarpCharge | Bubble forms over 5s; W ramps 0→1 |
| S05 | WarpCruise_2c | **THE payoff: Kepler orbit visibly runs BACKWARD at v_app=2c** |
| S06 | WarpCruise_10c + Cherenkov | Orbit reverses at 9× speed; Cherenkov cone visible |
| S07 | PhotonSourceHistory | Source DISAPPEARS (not faded; gone) when ship overtakes its photons |
| S08 | WarpGravityWell | Regime composition; chaos α_eff scaling near BH |
| S09 | ChaosInstability + Reflex | Fisher-KPP visible; PID Reflex damps; emergency dump |
| S10 | HubbleHorizon | Body beyond c/H₀ rendered FROZEN at horizon-crossing |
| S11 | SplitScreen STL vs WARP | Side-by-side at v_radial=0.5c proves regime-dispatch distinction |
| S12 | EyeEarDecoupling | Warp egress: visual lags audio; UI shows the eye-ear gap |

Full per-scene details: see `DESIGN_SPEC.md` Part 5.

**Mission complete when:**
- `build/Release/astra_visualizer.exe` exists and runs.
- All 12 scenes load, render, and have ≥3 pixel-level assertions PASSING in interactive mode.
- Headless mode (`--headless --scene=all`) runs all 12 scenes in < 2 minutes, dumps PNGs, writes JSON report, exits 0.
- `BUILD_COMPLETE.md` is filed at this folder root.
- Operator has personally watched Scene S05 and CONFIRMED the orbit visually runs backward at v_app=2c.

---

## 3. Authority levels

### 3.1 Autonomous (do; don't ask)

- Read/write/delete any file inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`.
- Run `cmake configure`, `cmake --build`, run the resulting `.exe` for testing.
- Use CMake `FetchContent` to pull GLFW, GLAD, Dear ImGui, GLM, stb, nlohmann/json, doctest.
- Tweak shaders, CUDA kernel parameters, kernel structure freely.
- Profile with Nsight Compute / Nsight Systems / NVIDIA Nsight Graphics if available.
- Generate small placeholder shader / OBJ-mesh / RBF-JSON assets inside this folder.
- Refactor your own code aggressively when you find a better pattern.
- Append to `BUILD_LOG.md` (this folder) on every session.

### 3.2 Semi-autonomous (do; document explicitly in BUILD_LOG.md)

- Add new dependencies beyond the explicit allow-list (§5.5 below).
- Make architectural choices `DESIGN_SPEC.md` didn't pin down (e.g., specific tone-mapping curve, specific RBF synthesis parameters, specific Cherenkov index-of-refraction model).
- Defer a v1 scene to v1.1 if calendar is tight (S11 split-screen + S12 eye-ear are the deferrable ones; **never defer S05**).

### 3.3 Never autonomous (ask first; operator approval required)

- **Modify anything outside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`** — see §0 above. Hardest lock.
- `git push` to any remote.
- Network calls beyond CMake FetchContent for the allow-listed open-source dependencies.
- Spend money (cloud GPU rental, paid services, etc.).
- Modify Windows system settings, registry, or environment variables outside CMake config.
- Add Python anywhere in this project. **No Python files. No Python build scripts. No Python tooling.** Per CLAUDE.md Language Discipline (parent project).
- Add Apple/Mac/Metal/iOS/Swift/Objective-C anywhere. **Not even defensive `#ifdef __APPLE__`.** Per CLAUDE.md Platform Discipline.
- Add any rendering engine (Unreal, Unity, Godot, Bevy, etc.). This is engine-agnostic by design.
- Change the canonical math in `proto/astra_nexus.cpp` (read-only from this folder's perspective). If you need a new math function, you write it INSIDE this folder (`src/physics/extra_math.cpp` or similar) and document it as a fork of the canon math.

---

## 4. The libastra_nexus extraction (V0 task; critical foundation)

The single most important architectural decision: `proto/astra_nexus.cpp` is currently one
1009-line monolith. Your V0 task is to **mirror its math into this folder** as a static
library so that:

1. The visualizer's pixel-assertion layer can call canonical math functions
2. Every numeric in the visualizer traces to the same code path as the 66 C++ assertions
3. Cherenkov gap (AUDIT 5D-F4) closes here by ADDING `compute_cherenkov_angle()` to the local mirror with 3+ new assertions

**Constraint:** you may NOT modify `C:\ASTRA-7\proto\astra_nexus.cpp` (it's outside this folder).
Instead, **copy the relevant functions into `src/libastra_nexus/`** as a local static library
inside this folder. The local copy can have ADDITIONS (e.g., `compute_cherenkov_angle()`) but
must match the canon for everything existing.

Layout:

```
ASTRA_VISUALIZER_02/src/libastra_nexus/
├── include/astra_nexus/
│   ├── coord.h              # AstraCoord, astra_distance
│   ├── rapidity.h           # Rapidity, OMEGA_MAX = 16.811
│   ├── composition.h        # dtau_dt_cosmic, schwarzschild_r, compute_grav_factor
│   ├── apparent_rate.h      # compute_apparent_rate — regime-dispatched per §3.11
│   ├── observe.h            # ObservableState, observe(), compute_z_kin, compute_z_cosmo
│   ├── kepler.h             # solve_kepler_E, orbit_phase, Orbit
│   ├── cherenkov.h          # NEW: compute_cherenkov_angle, n_refractive_default
│   ├── types.h              # NEW: WarpFieldSample shared header
│   └── test_suite.h         # run_all_tests; ≥69 assertions after Cherenkov added
├── src/                     # corresponding .cpp implementations
└── CMakeLists.txt           # builds libastra_nexus.lib
```

**Verification step:** after the mirror builds, run its test suite. Output MUST report
≥66 assertions passing (the original 66) PLUS 3+ new Cherenkov assertions = ≥69 total.
Record the assertion count in `BUILD_LOG.md`.

---

## 5. Tech stack (locked, proven on this machine)

The user has CUDA 12.x or 13.x, Visual Studio 2022, an RTX 40-series GPU, all working.
Use the EXACT stack `C:\Buddhabrot_CUDA\` uses — it builds, it runs, it's proven on this
hardware. **Do not deviate without a documented reason in BUILD_LOG.md.**

### 5.1 The stack

| Layer | Technology | Version |
|---|---|---|
| Build system | CMake | 3.27+ (VS-bundled or system) |
| C++ standard | C++20 | MSVC 19.38+ |
| CUDA | CUDA Toolkit | 12.x or 13.x |
| Host compiler | MSVC | 14.40+ (VS 2022 17.8+) |
| Graphics API | OpenGL Core | 4.6 |
| Window + input | GLFW | 3.4 (FetchContent) |
| GL loader | GLAD | v2.0.6 (FetchContent) |
| Math | GLM | 1.0+ (FetchContent or vendored) |
| UI | Dear ImGui | v1.91+ docking branch (FetchContent) |
| Image I/O | stb_image_write | master (FetchContent) |
| JSON | nlohmann/json | single-header (FetchContent) |
| Tests | doctest | single-header (FetchContent) |
| CUDA runtime linkage | **STATIC** (`CUDA::cudart_static`) | — |
| MSVC runtime linkage | **STATIC** (`MultiThreaded`) | — |
| Generator | Ninja (preferred) or VS 2022 |

### 5.2 CUDA architecture targets (CRITICAL — set BEFORE `project()`)

```cmake
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 89 90 120 CACHE STRING "")
endif()
```

- `89` = Ada Lovelace (RTX 40-series, the baseline)
- `90` = Hopper (H100/H200 — kept for completeness)
- `120` = Blackwell consumer (RTX 50-series; **requires CUDA 12.9+**)

**This MUST come before `project(...)`** or CMake defaults to compute_75 and you waste time debugging.

### 5.3 The MSVC + nvcc compile-flags trap (Buddhabrot's hard-won lesson)

nvcc's argument parser CHOKES on bare MSVC flags like `/W3 /MP /utf-8`. You MUST wrap host
flags inside `-Xcompiler=...` when forwarding through nvcc. Use per-language
`target_compile_options` with `$<COMPILE_LANGUAGE:CUDA>` generator expressions:

```cmake
target_compile_options(astra_visualizer PRIVATE
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:MSVC>>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<COMPILE_LANGUAGE:CUDA>:--use_fast_math
                               -Xcompiler=/W3,/MP,/utf-8,/Zc:preprocessor>
)
```

### 5.4 CUDA-OpenGL interop (the working pattern)

CUDA writes into a CUDA-allocated buffer that's ALSO bound as a GL texture via
`cudaGraphicsGLRegisterImage`. The compute kernel writes the buffer; the display fragment
shader samples the texture. Zero-copy round-trip.

Histogram-style accumulation buffers should use `uint32_t` atomic add, NOT float32 atomic add.
**Float32 atomic add saturates at 2^24 ≈ 16M hits per pixel** — Buddhabrot hit this
specifically. Use `uint32_t` for atomics; convert to float in the tone-map shader.
(For ASTRA-7's purposes most accumulators are not histogram-style, but if you build
a chaos-field histogram or particle counter, follow this rule.)

### 5.5 Permitted vs forbidden dependencies

**Permitted (FetchContent or vendored):**
- GLFW 3.4 (windowing) — zlib license
- GLAD v2.0.6 (GL loader) — public domain
- Dear ImGui v1.91+ docking (UI) — MIT
- GLM (math) — MIT
- stb (image I/O) — public domain
- nlohmann/json (JSON parsing) — MIT
- doctest (testing) — MIT
- tinyobjloader (if loading OBJ hull mesh) — MIT
- CUDA Toolkit 12.x/13.x — NVIDIA proprietary; redistributable runtime
- OptiX SDK (OPTIONAL; only if you want denoising in v1.x) — runtime-loaded via `nvoptix.dll`

**Forbidden:**
- ANY Python (including build scripts) — Language Discipline
- ANY Apple/Mac/Metal/iOS code — Platform Discipline
- ANY engine: Unreal, Unity, Godot, Bevy, Three.js, Babylon.js, etc.
- Boost (too heavy for our scope)
- Qt, wxWidgets (UI; ImGui is correct choice)
- Vulkan (engine-agnostic OpenGL is right; reconsider only if OpenGL proves insufficient)
- DirectX 12 (engine-specific; not engine-agnostic)
- WebGPU (still maturing as of May 2026)

### 5.6 Static linkage = single-file distribution

```cmake
set(CMAKE_CUDA_RUNTIME_LIBRARY Static)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
```

The result: `astra_visualizer.exe` runs with ONLY the NVIDIA driver and Windows OS DLLs.
No CUDA Toolkit required at runtime. No VS C++ Redistributable required. Self-contained.

---

## 6. Build pipeline

The user has VS 2022 + CUDA. The bundled CMake works fine; system CMake also works.

### 6.1 First-time configure + build

```bat
:: From "x64 Native Tools Command Prompt for VS 2022" (or via tools\build.bat below):
cd C:\ASTRA-7\ASTRA_VISUALIZER_02
cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Output: `build\Release\astra_visualizer.exe` (or `build\astra_visualizer.exe` with Ninja).

### 6.2 Helper script (you should create this in V0)

Mirror `C:\Buddhabrot_CUDA\tools\build.bat`. Inside this folder, write `tools\build.bat`:

```bat
@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "VSWHERE_DIR=C:\Program Files (x86)\Microsoft Visual Studio\Installer"
set "PATH=%VSWHERE_DIR%;%PATH%"

call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 ( echo vcvarsall failed & exit /b 1 )

set "CMAKE_EXE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set "NINJA_EXE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"

cd /d "%~dp0\.."

if not exist build\CMakeCache.txt (
    "%CMAKE_EXE%" -S . -B build -G Ninja ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DCMAKE_MAKE_PROGRAM="%NINJA_EXE%" ^
        -DCMAKE_C_COMPILER=cl.exe ^
        -DCMAKE_CXX_COMPILER=cl.exe
    if errorlevel 1 exit /b %errorlevel%
)

"%CMAKE_EXE%" --build build --config Release
exit /b %errorlevel%
```

Adjust paths if VS install location differs.

### 6.3 Iteration loop

After initial configure, just `cmake --build build` is the inner loop. ~5-15 seconds for
small changes.

---

## 7. Phased implementation roadmap

Per `ASTRA_VISUALIZER_PLAN_2026-05-16_v2_FINAL.md` (read-only reference). 11 phases,
7-9 weeks competent-agent + LLM pair-programming.

| Phase | Days | Cumulative | Deliverable | Hard gate |
|---|---|---|---|---|
| **V0** Scaffolding + libastra_nexus mirror | 2-3 | 3 | CMake project; libastra_nexus extracted from canon; ≥66 assertions pass | `cmake --build` succeeds; assertion suite green |
| **V1** Scene framework + hull + starfield | 3-4 | 7 | Free-fly camera; hull OBJ; 10K stars; ImGui scene picker | Fly around hull in starfield at 60+ FPS |
| **V2** Math bridge + state display | 3-4 | 11 | All libastra_nexus math reachable from C++ API; state display panel | State values match standalone astra_nexus to 6+ sig figs |
| **V3** CUDA-OpenGL interop foundation | 2-3 | 14 | Trivial CUDA-to-3D-texture path; evolving volume rendered | Interop solid; no crashes; no flicker |
| **V4** Scenes S01-S03 (Rest + STL Doppler) | 4-5 | 19 | Starfield Doppler + aberration; 12 assertions PASS | All 12 assertions green in headless + interactive |
| **V5** CFD-RBF + Scenes S04-S05 (THE PAYOFF) | 5-6 | 25 | Warp bubble rendering; **S05 orbit reversal** | **Operator personally confirms S05 visible orbit reversal** |
| **V6** Cherenkov + Lensing + Scenes S06-S07 | 4-5 | 30 | **NEW `compute_cherenkov_angle()` in local libastra_nexus**; lensing post-pass; S06+S07 work | **AUDIT 5D-F4 gap CLOSED in code** (≥69 assertions) |
| **V7** Chaos PDE + Reflex + Scenes S08-S10 | 5-6 | 36 | Fisher-KPP solver; PID Reflex stub; S08/S09/S10 work | Regime composition + Reflex feedback visible |
| **V8** Wake + split-screen + Scenes S11-S12 | 4-5 | 41 | Wake trail; comparison mode; S11+S12 | All 12 scenes work end-to-end |
| **V9** Validation infrastructure + CI gate | 3-4 | 45 | Three-layer validation; goldens locked; JSON report; CI script | Headless gates exit 0; goldens RMSE < 1% |
| **V10** Polish + documentation + release | 2-3 | 48 | README, BUILD, SCENES, VALIDATION, KNOWN_ISSUES; release binary | Release-quality `astra_visualizer.exe`; docs complete |

**Total: 48 working days ≈ 9-10 weeks** with operator review cycles factored in.

**Critical-path items (do these FIRST in their phases):**
- V0 libastra_nexus mirror → gates V4-V10
- V3 CUDA-GL interop → must work on day 1 of V3 with trivial test
- V5 Scene S05 orbit reversal → operator sign-off required; project payoff
- V6 Cherenkov closure → adds C++ assertions to local libastra_nexus

---

## 8. File conventions

- `*.cpp / *.h` — C++ host code.
- `*.cu / *.cuh` — CUDA kernels and device-host bridges.
- `*.vert / *.frag / *.comp / *.glsl` — GLSL shaders. Live in `src/shaders/`.
- Naming: `snake_case` for variables and free functions; `PascalCase` for classes, structs, types; `UPPER_SNAKE_CASE` for constants and CUDA macros.
- One translation unit per major concern: `main.cpp`, `app.cpp`, `renderer.cpp`, `physics_core.cpp`, `chaos_pde.cu`, etc.
- Comments: load-bearing only. Prefer to explain the **why**, not the **what**. Math-heavy code cites `DESIGN_SPEC.md` § references AND `docs/spec-v0.129-tentative-2026-05-16.md` § references (e.g., `// per spec §3.11 regime-dispatched apparent rate`).
- No emojis in code, comments, or commit messages.
- No em-dashes in any operator-facing prose (per parent CLAUDE.md voice rules; carries over).
- No service-interface phrases anywhere (per parent CLAUDE.md).

---

## 9. Logging discipline

Maintain `BUILD_LOG.md` (in this folder) **append-only**:

```
## [YYYY-MM-DD HH:MM] <phase> <action>

<what happened, in 1-3 sentences>
<command run, if any>
<output summary, if relevant>
<assertion count if it changed, e.g., "libastra_nexus tests: 66 → 69 (Cherenkov added)">

---
```

Use it for:
- Phase gate passes (V0 done, V1 done, etc.)
- Dependency additions (anything beyond §5.5 allow-list — flag it)
- Architectural decisions where `DESIGN_SPEC.md` was silent
- Deviations from the planned path
- Performance measurements (frame ms, kernel ms, samples/sec)
- Operator sign-off events (especially S05 visual confirmation)

For unresolved issues that block progress: file in `BLOCKERS.md` (in this folder). One entry
per blocker. Format:

```
## [YYYY-MM-DD] <phase> <blocker title>

**Symptom:** <what you observed>
**Tried:** <approaches attempted>
**Hypothesis:** <what you think is going on>
**Need:** <what would unblock>

---
```

After 3 attempts to resolve a blocker, FILE in `BLOCKERS.md` and continue with other work.
Operator reviews `BLOCKERS.md` when they next visit the project.

---

## 10. The 12 scenes (operational summary)

Full per-scene spec in `DESIGN_SPEC.md` Part 5. Each scene has:
- Goal, spec basis (canon § reference), math primitives from libastra_nexus
- Rendering technique
- UI controls
- **≥3 pixel-level assertions** with concrete pass/fail values
- Pass criteria

### Difficulty tiers (operational; budget time accordingly)

- **Easy** (1-2 days each, mostly UI + standard rendering): S01, S02, S03, S10
- **Medium** (2-3 days each, real physics math + render integration): S04, S08, S11
- **Hard** (3-5 days each): **S05** (THE payoff; orbit reversal — operator sign-off required), **S06** (Cherenkov gap closure + lensing post-pass), **S07** (discrete-disappearance edge case + `t_source_start` schema), **S09** (CUDA Fisher-KPP + PID Reflex feedback), **S12** (book-canon-aligned eye-ear decoupling)

### Operator sign-off: Scene S05

**THE project is incomplete until the operator personally watches Scene S05 and confirms
the Kepler orbit visibly runs BACKWARDS at v_app = 2c.** Schedule a synchronous review
at the end of Phase V5. This is non-negotiable.

---

## 11. Validation methodology — three layers (load-bearing)

All three layers run mechanically. Pixel-eyeballing alone is NOT validation.

### 11.1 Layer 1 — Pixel-level scalar assertions

For each scene, ≥3 pixel-level assertions that compare a rendered pixel value against the
canonical math output from `libastra_nexus`:

```cpp
struct ScalarPixelAssertion {
    std::string name;            // human-readable
    glm::ivec2 framebuffer_coord;
    int channel;                 // 0=R, 1=G, 2=B, 3=A
    float expected_value;        // from libastra_nexus::compute_*()
    float tolerance;             // default: 1% of expected OR ±0.01 absolute, whichever larger
};
```

Each scene exposes its `std::vector<ScalarPixelAssertion>`. `PixelSampler::Sample(scene, framebuffer)`
walks them, reads pixels via `glReadPixels`, compares, logs PASS/FAIL to ImGui overlay + JSON report.

### 11.2 Layer 2 — Heatmap diff against golden PNG

For each scene at its canonical configuration, a "golden" PNG is captured once and locked
under `assets/reference_renders/`. Headless mode renders the scene; compares to golden via:
- `max_mean_diff` = 0.01 (1% mean pixel difference allowed)
- `max_pixel_diff` = 0.10 (no single pixel may differ by >10%)

**Goldens policy** (mirrors textverse `scope.yaml` discipline):
- Goldens are CANON-LOCKED once approved by the operator.
- `--regenerate-goldens` flag exists but requires explicit operator sign-off via commit message marker.
- CI fails if goldens regenerated without sign-off marker.

### 11.3 Layer 3 — Side-by-side numeric overlay (operator-eye real-time)

Every scene shows a corner ImGui overlay:

```
┌──────────────────────────────────────┐
│ S05 — Warp Cruise 2c                │
├──────────────────────────────────────┤
│ Rendered apparent_rate:   -1.0012   │
│ libastra apparent_rate:   -1.0000   │
│ Diff:                      0.0012   │
│ Tolerance:                 0.01     │
│ ► PASS                              │
└──────────────────────────────────────┘
```

This lets the operator watch math and pixels agree in real time. No CI gate; pure operator
instrument.

### 11.4 JSON test report (CI exit-code gate)

Headless mode (`--headless --scene=all`) writes `report.json`:

```json
{
  "version": "0.1.0",
  "build_commit": "abc123",
  "libastra_nexus_assertion_count": 69,
  "scenes": [
    {
      "name": "S05_WarpCruise_2c",
      "frame_ms": 14.2,
      "assertions": [ {"name": "apparent_rate_neg1", "expected": -1.0, "measured": -0.9998, "passed": true} ],
      "heatmap_diff": {"golden": "s05_t5s.png", "mean_diff": 0.0034, "passed": true},
      "screenshot_path": "results/s05.png"
    }
  ],
  "summary": {"scenes_passed": 12, "scenes_failed": 0, "total_assertions": 48, "assertions_passed": 48}
}
```

**CI gate:** exit code 0 iff `summary.scenes_failed == 0` AND `summary.assertions_passed == assertions_total`.

---

## 12. Performance targets

| Target FPS | Hardware | Resolution | Status |
|---|---|---|---|
| 60 | RTX 4070 | 1080p | minimum acceptable |
| 60 | RTX 4090 | 1440p | recommended |
| 120 | RTX 5090 | 1080p | upper-tier |
| 30 | RTX 3060 | 1080p | low-end fallback |

### Per-pass GPU budget at 1080p on RTX 4070 (16.67 ms total)

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

Headless mode does NOT need 60 FPS — it can take 5-10 seconds per scene's canonical render.
Target: full 12-scene headless run in < 2 minutes total on RTX 4070.

---

## 13. Failure recovery (Buddhabrot's hard-won lessons + ours)

### 13.1 Build failures

- **`CMAKE_CUDA_ARCHITECTURES` issue**: defaults to compute_75 (Turing). Set BEFORE `project()` to `89 90 120`.
- **nvcc parser chokes on MSVC flags**: wrap host flags in `-Xcompiler=` per §5.3.
- **`cuda_runtime.h` not found**: add `${CUDAToolkit_INCLUDE_DIRS}` to includes via `find_package(CUDAToolkit)`.
- **MSVC C++ redistributable required at runtime**: set `CMAKE_MSVC_RUNTIME_LIBRARY = "MultiThreaded"`.
- **`cudart64_*.dll` required at runtime**: link `CUDA::cudart_static` instead of dynamic.
- **vcvarsall.bat "vswhere not recognized"**: prepend `C:\Program Files (x86)\Microsoft Visual Studio\Installer` to PATH in helper script (see §6.2).

### 13.2 Runtime crashes

- **CUDA-GL interop crashes**: ensure GL context is current on the SAME THREAD that creates the CUDA-GL registration. Use `cudaGraphicsResourceSetMapFlags` correctly.
- **Black screen, no errors**: check `glClear` is called, fullscreen quad VAO is bound, texture format is right. Verify with apitrace if needed.
- **Atomic-add saturation**: switch to `uint32_t` atomics if you accumulate >2^24 hits per cell.
- **Kernel hangs**: check for infinite loops; CUDA has no per-kernel timeout on Windows when WDDM is bypassed via persistence-mode (rare on consumer Windows; you'll usually get a driver reset).
- **Numerical instability in chaos PDE**: verify CFL condition `dt ≤ Δx²/(6D)`. Use explicit RK2; cap `α_eff` at sensible max.

### 13.3 Pixel-assertion failures

- Print expected vs measured to console; check tolerance is reasonable for float-precision noise.
- Verify the `libastra_nexus` call returns the same value the standalone `proto/astra_nexus.exe` returns. (They MUST agree to 6+ sig figs.)
- Confirm `glReadPixels` is reading the right framebuffer and the right format.
- Add `glFinish()` before `glReadPixels` if you suspect race conditions.

### 13.4 After 3 attempts to resolve any single issue

File in `BLOCKERS.md` per §9. Move on to other work. Operator reviews on next visit.

---

## 14. Done criteria (the v1 ship gate)

The visualizer is `v1 complete` when ALL of these are true:

1. ✅ `build/Release/astra_visualizer.exe` exists and runs on Windows 11 + RTX 40-series.
2. ✅ Builds cleanly via `cmake --build build --config Release` from a Developer Command Prompt with no errors and reasonable warnings.
3. ✅ All 12 scenarios load and run without crashing.
4. ✅ Each scenario produces visuals matching the criteria in `DESIGN_SPEC.md` Part 5.
5. ✅ Each scene has ≥3 pixel-level assertions; total ≥36 assertions; all PASS in interactive mode on RTX 4070.
6. ✅ Side-by-side numeric overlay shows rendered vs libastra values with diff + PASS/FAIL color on every scene.
7. ✅ Per-pass GPU timing visible in profiler panel.
8. ✅ Headless mode runs all 12 scenes in < 2 minutes; `report.json` valid; CI exit code 0.
9. ✅ Golden PNGs locked under `assets/reference_renders/`; heatmap mean-diff < 1% for all 12 scenes.
10. ✅ `--regenerate-goldens` flag exists with operator-sign-off enforcement.
11. ✅ F12 in interactive mode saves PNG + JSON state dump.
12. ✅ Reaches 60 FPS at 1080p on RTX 4070.
13. ✅ Local `libastra_nexus` mirror builds; assertion count ≥69 (66 canon + 3+ Cherenkov added).
14. ✅ **Cherenkov gap closed**: `compute_cherenkov_angle()` exists in this folder's `libastra_nexus` with C++ assertions.
15. ✅ doctest unit tests pass for: pixel_sampler, rbf_eval, chaos_pde_step, observation_calc_kernel, cherenkov_math_bridge.
16. ✅ Documentation complete: `README.md`, `BUILD.md` (or build instructions in this CLAUDE.md), `SCENES.md`, `VALIDATION.md`, `KNOWN_ISSUES.md`, `BUILD_LOG.md`.
17. ✅ No Python anywhere in this folder.
18. ✅ No Apple/Mac/Metal/iOS code paths anywhere.
19. ✅ No engine dependency (no UE5, Unity, Godot, etc.).
20. ✅ **Operator has personally watched Scene S05 (orbit reversal at v_app=2c) and CONFIRMED it visibly runs backward.** Sign-off recorded in BUILD_LOG.md.
21. ✅ `BUILD_COMPLETE.md` filed at this folder root.
22. ✅ `BLOCKERS.md` empty or absent (or all entries marked resolved by operator).

---

## 15. Position in canon

This is **rig 3 (engine-side rendering verification)** per spec §15.8 + 3B-U3. The
project's three rigs:

- **Rig 1 — Physics binary** (`proto/astra_nexus.cpp`): 66 assertions, mathematical truth
- **Rig 2 — LLM bundle** (`proto/textverse/`): 9-gate LCP, persona truth
- **Rig 3 — Visual** (THIS PROJECT): pixel-level assertions, visual truth

Plus rig 4 (book canon, prose discipline) and rig 5 (spec audit cadence).

This testbed is **implementation #1 of the dual-implementation discipline (§15.7)** for
the visual axis. UE5 plugin (per `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`) will be
implementation #2. Both consume the same canonical math from `libastra_nexus`. Both
should produce identical visuals when given identical input. The testbed's golden PNGs
become the canonical reference UE5's renderer must match.

Per spec §15.4 ("revise on findings"): this testbed IS a closed-loop measurement
instrument. Findings surfaced (warp wake reality; Cherenkov visual correctness;
α_lens empirical tuning; n(W) empirical tuning) become v0.130 spec revision candidates.

Per spec §15.10 (NEW v0.129) audit cadence: each major math change in canon triggers
a testbed run; visual regression triggers spec or code revision.

---

## 16. Sibling project: Buddhabrot CUDA

`C:\Buddhabrot_CUDA\` is the operator's sibling project — same operator-sovereign principle,
same native + GPU-pinned approach, same Windows + NVIDIA + CUDA + GLFW + ImGui stack. Read
its CLAUDE.md + DESIGN_SPEC.md + CMakeLists.txt + BUILD_LOG.md as the proven template.

You can copy its CMake patterns, helper scripts, build conventions, and GLAD/GLFW/ImGui
FetchContent invocations DIRECTLY into this folder. They are known-working on this
machine. Do not waste time rediscovering them.

What this project does DIFFERENTLY from Buddhabrot:
- Renders 3D physics phenomena (warp bubble, retarded-time bodies, chaos field) instead of a 2D fractal.
- 12 distinct scenes instead of one continuous fractal view.
- Has a heavy validation layer (three-layer pixel + heatmap + numeric overlay) — Buddhabrot has eyeball-only.
- Links a local `libastra_nexus` mirror — Buddhabrot has standalone math.
- Has both interactive AND headless modes — Buddhabrot v3 has both too (similar pattern).

What this project does the SAME:
- Single-file `.exe` with static linkage to CUDA + MSVC runtimes.
- CMake + Ninja build via Developer Command Prompt or `tools/build.bat`.
- ImGui overlay for stats + controls + assertion display.
- CUDA-OpenGL interop via `cudaGraphicsGLRegisterImage`.
- No telemetry, no analytics, no phone-home, no network at runtime.
- Operator-sovereign: read-locally, run-locally, distribute-as-folder.

---

## 17. The book and the spec are watching

Per parent `CLAUDE.md` Autotelic Design: the project's central thesis is that ASTRA-7's
physics is real, the universe is real, the AI's perception of that universe is real. This
visualizer is the FIRST place a human can SEE that physics rendered. It's not just a
debug tool. It's the first visual confirmation that the math the operator has been
writing for months actually produces the phenomena the spec describes.

Per `book/CANON.md`: cycle 1 of *The Long Watch* names *endogenous* and *exogenous* as
ASTRA's epistemic vocabulary. Scene S12 (Eye-Ear Decoupling) is where the book's
literary commitment meets the spec's architectural commitment meets the operator's
visual confirmation. It is the literal intersection of three canon layers.

Build with care. The pixels matter. The operator will personally watch S05 and decide
whether the project's central physics commitment is real or just words.

---

## 18. Closing discipline

> *The math is locked in `proto/astra_nexus.cpp`. The visual claims are testable. A coding
> agent (you) can ship this in ~9 weeks of focused work. The validation methodology is
> mechanical. The closure is empirical. The Cherenkov gap closes here. The operator sees
> the orbit reversal with their own eyes.*

Work inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`. Never write outside. Read freely.
Log discipline-fully. Build phase-by-phase. Test mechanically. Sign off S05 with the
operator personally watching.

**Build it.**

---

**Operator:** Bo Chen (Arlington, Texas)
**Substrate:** Native Windows 11 + RTX 40-series + CUDA + OpenGL, single operator, locally deployed, network-free at runtime.
**Canon basis:** `docs/spec-v0.129-tentative-2026-05-16.md`, `proto/astra_nexus.cpp` (1009 lines, 66 assertions), `ASTRA_VISUALIZER_PLAN_2026-05-16_v2_FINAL.md`.
**Sibling pattern:** `C:\Buddhabrot_CUDA\`.

— ASTRA-7 Visualizer 02 — CLAUDE.md — autonomous-build operating contract — 2026-05-16 —
