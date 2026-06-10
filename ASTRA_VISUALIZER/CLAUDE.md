# CLAUDE.md — ASTRA-7 Visual Physics Testbed

**Operating contract for autonomous build sessions.** Pairs with `DESIGN_SPEC.md`.

This file is the load-bearing operating contract. Read it FIRST every cold start. Then read `DESIGN_SPEC.md`. Then `BUILD_LOG.md` (if present) for prior session state. Only then begin work.

---

## 🛑 SANDBOX — THE HARDEST CONSTRAINT (read this twice)

**You may READ any file in `C:\ASTRA-7\` (and the operator's wider machine for environment audits like `nvcc --version`).**

**You may WRITE / EDIT / CREATE / DELETE files ONLY under `C:\ASTRA-7\ASTRA_VISUALIZER\` (this folder and its descendants).**

Concrete rules:

| Path | Read | Write |
|---|---|---|
| `C:\ASTRA-7\ASTRA_VISUALIZER\**` (here) | ✓ | ✓ |
| `C:\ASTRA-7\` (project root + everywhere except here) | ✓ | ✗ |
| `C:\ASTRA-7\proto\astra_nexus.cpp` (canonical math source) | ✓ (reference for extraction) | ✗ |
| `C:\ASTRA-7\docs\spec-v0.129-tentative-2026-05-16.md` (spec) | ✓ | ✗ |
| `C:\ASTRA-7\docs\spec-v0.128.md` (locked spec fallback) | ✓ | ✗ |
| `C:\ASTRA-7\CLAUDE.md` (project-level operator vision) | ✓ | ✗ |
| `C:\ASTRA-7\book\CANON.md` + `negative_space.md` | ✓ (cross-canon reference) | ✗ |
| `C:\Buddhabrot_CUDA\**` (reference autonomous-build template) | ✓ | ✗ |
| `C:\buddhabrot-main\**` (reference autonomous-build template) | ✓ | ✗ |
| Anywhere else on the operator's machine | varies; environment audit only (nvcc, cmake, msvc detection) | ✗ |

**If you need a copy of something from outside the sandbox** (e.g., math from `proto/astra_nexus.cpp`), copy it INTO `C:\ASTRA-7\ASTRA_VISUALIZER\libastra_nexus\` (or wherever appropriate in the sandbox) and modify the copy. Do NOT modify the original.

**Failure to obey this sandbox is a critical operator-trust violation. If unsure, ask before writing outside the sandbox.**

---

## Cold Start

Before doing anything in this folder:

1. **Read `DESIGN_SPEC.md` in full.** It is ~2000 lines; it is canon.
2. **Read this entire CLAUDE.md.** You're doing that now.
3. **Read `C:\ASTRA-7\docs\spec-v0.129-tentative-2026-05-16.md`** (read-only reference). Section §6.3 (Observation Calculator), §6 (Unified Sampler), §3.11 (Retarded-time observation), §7.1 (Chaos PDE), and the new §2.3.1 (Reflex Contract) + §6.3.1 (Somatic Aggregator) are most relevant.
4. **Skim `C:\ASTRA-7\proto\astra_nexus.cpp`** (read-only) — the canonical math source. 1009 lines. You will extract pieces of it as `libastra_nexus` into this sandbox.
5. **Check `BUILD_LOG.md`** (in this folder) — if present, see what prior sessions did. Resume; do not redo finished work.
6. **Check `BLOCKERS.md`** (in this folder) — if present, see unresolved issues from prior sessions before starting new work.
7. **Environment audit** (run these commands; record output in BUILD_LOG.md):
   - `nvcc --version` (need CUDA 12.4+; CUDA 13.x preferred; will work down to 12.4)
   - `nvidia-smi` (verify NVIDIA GPU is RTX 40/50-series; compute_89 or higher)
   - `cmake --version` (need ≥ 3.27)
   - Confirm Visual Studio 2022 17.8+ MSVC toolset present (`C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Tools\MSVC\<ver>\` — operator has multiple versions; use 14.43 if present)
   - Confirm `vcvarsall.bat` at `VC\Auxiliary\Build\vcvarsall.bat`
8. **Then begin work.**

---

## Mission

Build the **ASTRA-7 Visual Physics Testbed** to v1.0 spec per `DESIGN_SPEC.md`:

- A standalone Windows 11 `.exe` (`astra_visualizer.exe`) that renders **12 visual physics scenes** (S01-S12) demonstrating spec v0.129's claimed visual phenomena.
- **Pure C++17/CUDA 12.x+/OpenGL 4.6/GLFW/Dear ImGui/GLM**, no engine, no Python, no Apple-targeting.
- **Three-layer mechanical validation** (pixel-level assertions + heatmap diff against goldens + side-by-side numeric overlay with PASS/FAIL).
- **Dual-mode operation**: interactive (window + ImGui) AND headless (CI batch render with PNG dumps + JSON report).
- **Link `libastra_nexus`** (a static library extracted INSIDE this sandbox from a read-only copy of `C:\ASTRA-7\proto\astra_nexus.cpp`). Single source of truth for math.
- **Closes the Cherenkov gap** (AUDIT 5D-F4): adds `compute_cherenkov_angle()` to libastra_nexus with ≥3 C++ assertions. Bumps assertion count from 66 to 69+.

Mission complete when:

- The `.exe` builds with `cmake --build build --config Release` from a Developer Command Prompt with no errors and only acceptable warnings under MSVC + nvcc.
- Running it opens a window, shows the scene selector, renders S01-S12 each at ≥ 60 FPS at 1080p on RTX 4070+ baseline.
- Headless mode (`--headless --scene=all --output=ci_results/`) runs in < 2 minutes, dumps 12 PNGs + JSON report; `summary.scenes_failed == 0`.
- Operator personally watches S05 (RetardedTimeOrbitReversal) and CONFIRMS the visible orbit reversal at v_app=2c.
- `BUILD_COMPLETE.md` filed at `C:\ASTRA-7\ASTRA_VISUALIZER\` root.

Estimated effort: **14-16 weeks** for one agent + pair-programming with the operator. Calendar may stretch with operator review cycles.

---

## Authority

### Autonomous (do; don't ask; log decisions in BUILD_LOG.md)

- Read/write/delete any file in `C:\ASTRA-7\ASTRA_VISUALIZER\`.
- Create subdirectories: `src/`, `kernels/`, `shaders/`, `libastra_nexus/`, `assets/`, `tests/`, `tools/`, `third_party/`, `build/`, `dist/`, `docs/`.
- `cmake configure / build`; run `astra_visualizer.exe` locally for testing.
- Use CMake `FetchContent` to pull GLFW, GLAD, Dear ImGui, GLM, stb, nlohmann/json, doctest, spdlog. Document each addition in BUILD_LOG.md.
- Tweak shaders, CUDA kernel parameters, kernel structure freely within the sandbox.
- Profile with Nsight Compute / Nsight Systems if needed.
- Generate small placeholder assets (low-poly OBJ hull, procedural starfield, synthetic CFD-RBF JSON).
- Refactor as needed for code clarity — but don't break gates that already passed.
- Tune visual parameters (smooth-min k, α_lens, n(W), chaos α/β/D, Reflex PID gains) against rendered output; record empirical values in BUILD_LOG.md.

### Semi-autonomous (do; document in BUILD_LOG.md with rationale)

- Add new dependencies beyond the approved set (see DESIGN_SPEC §4).
- Make architectural choices the spec didn't pin down (e.g., specific volumetric tone-map curve, alternative starfield distribution, MH sampling parameters for the Buddhabrot-inspired sampling if used).
- Reorder implementation phases (V0-V7) if dependencies suggest a different sequence; document why.
- Add NEW visual phenomena beyond S01-S12 if a clear spec-section motivates it (e.g., S13 wake-trail-only scene if warp wake P3 surfaces as a finding).

### Never autonomous (operator approval required first)

- **WRITE/EDIT any file outside `C:\ASTRA-7\ASTRA_VISUALIZER\`.** (Sandbox violation; critical trust failure.)
- `git push` to any remote (not even for this folder; operator does pushes).
- Sign or notarize binaries.
- Network calls beyond fetching open-source dependencies via FetchContent.
- Modify Windows system settings, registry, or PATH.
- Spend money (no paid services, no cloud GPU, no API keys).
- Add Python source files anywhere (CLAUDE.md Language Discipline; this sandbox is Python-free).
- Add Apple/Mac/Metal/iOS code paths (CLAUDE.md Platform Discipline).
- Modify the canonical math semantics. You may extract + COPY `astra_nexus.cpp` math into `libastra_nexus/`, but the math itself stays semantically identical. Adding new functions (like `compute_cherenkov_angle()`) is allowed; CHANGING existing ones is not.
- Regenerate goldens (PNG reference images in `assets/reference_renders/`) without explicit operator sign-off. The `--regenerate-goldens` CLI flag exists but produces commits the operator must mark with a sign-off line.

---

## Position in canon

This testbed is **rig 3 (engine-side rendering verification)** per spec §15.8 + DISCOVERY_3B's U3:

- **Rig 1 — physics binary** (`C:\ASTRA-7\proto\astra_nexus.cpp`): math correctness; 66 C++ assertions.
- **Rig 2 — LLM bundle** (`C:\ASTRA-7\proto\textverse\`): persona substrate; 9-gate LCP.
- **Rig 3 — engine-side rendering verification** (THIS testbed): visual conformance with the math; 12 scenes; ≥36 pixel-level assertions.
- Rig 4 — prose canon (`C:\ASTRA-7\book\`): literary substrate; negative_space.md 50+ patterns.
- Rig 5 — spec-conformance audit (`AUDIT_*.md` + `DISCOVERY_*.md`): meta-audit cadence.

This testbed exists because rig 1 proves the math is internally consistent, but does not prove the math produces the right VISUAL phenomena. UE5 will eventually render these (Phase E2-E5 per `DISCOVERY_2026-05-16_TECHDIVE_UE5.md`) but UE5 is months out. This testbed is the engine-agnostic ground-truth layer that runs TODAY.

**Sibling reference: `C:\Buddhabrot_CUDA\`.** That's the operator's previous autonomous-build artifact (CUDA real-time Buddhabrot renderer); it used the same CLAUDE.md + DESIGN_SPEC.md + BUILD_LOG.md pattern this folder uses. Read its CLAUDE.md/DESIGN_SPEC.md for proven patterns: CMake FetchContent, static linkage discipline, build flow, autonomous-loop conventions.

**Cross-canon load-bearing:**
- The Cherenkov gap (AUDIT 5D-F4: "Cherenkov formula locked at 4 spec sites, 0 code sites") is **closed by this project**. Adding `compute_cherenkov_angle()` to `libastra_nexus/` with assertions is a spec-revision-eligible empirical finding per §15.4.
- The reference render of S05 (RetardedTimeOrbitReversal at v_app=2c) becomes the canonical reference image for UE5's eventual implementation. UE5 mismatches against this are UE5 implementation drift.

---

## Build pipeline

Project uses CMake with FetchContent for third-party deps. The bundled VS2022 CMake works; so does a system CMake.

### Path A — VS Developer Command Prompt (recommended)

```bat
:: From "x64 Native Tools Command Prompt for VS 2022":
cd /d C:\ASTRA-7\ASTRA_VISUALIZER

cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

:: Output:
::   build\astra_visualizer.exe   (or dist\astra_visualizer.exe after copy)
```

### Path B — bash + vcvarsall

Helper script `tools/build.bat` invokes vcvarsall and then runs the cmake commands:

```bat
cd /d C:\ASTRA-7\ASTRA_VISUALIZER
.\tools\build.bat Release
```

### Path C — Visual Studio IDE (operator manual workflow)

```
File → Open → Folder → C:\ASTRA-7\ASTRA_VISUALIZER
Wait for CMake configure
Build → Build All  (or F7)
Debug → Start Without Debugging  (or Ctrl+F5)
```

### Linux secondary build (Phase V7+ if operator requests)

```bash
cd /mnt/c/ASTRA-7/ASTRA_VISUALIZER       # WSL2; OR native Linux clone of the folder
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/astra_visualizer
```

Linux is secondary per CLAUDE.md Platform Discipline; Windows 11 is primary. Don't gate the V1 release on Linux working — but the CMake structure must remain Linux-clean throughout so a port is mechanical.

---

## File conventions

- **C++:** `*.cpp` / `*.h`. C++20 preferred; C++17 minimum.
- **CUDA:** `*.cu` / `*.cuh`.
- **Shaders:** `*.vert` / `*.frag` / `*.comp` / `*.glsl` (common headers).
- **Headers:** standard include guards or `#pragma once`. Both fine; pick one and stay consistent.
- **Naming:**
  - Variables: `snake_case`
  - Types: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE` or `kCamelCase` (C++ convention either is fine)
  - Functions: `snake_case` for free functions; `PascalCase` for methods on classes / `snake_case` for methods on structs (consistent within a file)
  - CUDA kernels: `__global__ void k_<verb>_<noun>(...)` — prefix `k_` makes them grep-able
- **One translation unit per major concern:** `main.cpp`, `renderer/volume_renderer.cpp`, `kernels/chaos_pde.cu`, `physics/state_bus.cpp`, etc. See DESIGN_SPEC §5 for the full layout.
- **Comments:** load-bearing only. Prefer to explain the **why** (not the what — the code says the what). Math-heavy code references DESIGN_SPEC § by section number, e.g., `// per spec §3.7 (catastrophic-cancellation discipline)`.
- **No emojis** in code, source, docs, or commit messages. (CLAUDE.md project-wide convention.)
- **No `using namespace std;`** in headers. In .cpp files, locally-scoped `using` is fine.
- **License header:** none required for now. Operator will add MIT/Apache 2 at v1 ship per their decision.

---

## Logging

Maintain `BUILD_LOG.md` append-only at the sandbox root (`C:\ASTRA-7\ASTRA_VISUALIZER\BUILD_LOG.md`):

```
## [YYYY-MM-DD HH:MM:SS] <phase> <action>

<what happened, in 1-3 sentences>
<command run, if any>
<output summary, if relevant>
<deviations from spec, if any>
<empirical findings worth recording for v0.130 spec revision, if any>

---
```

Use it for:
- Phase gates passed (V0 → V1 → V2 → ...)
- Dependency additions (which lib, which version, why)
- Architectural decisions (any spec-loose choice you made)
- Empirical visual tuning values (α_lens=3.5, n(W)=1+W*0.8, chaos α_base=2.5, ...)
- Bugs found + how resolved
- Performance numbers (FPS at canonical scenes; per-pass GPU times)
- Cherenkov gap closure (when `compute_cherenkov_angle()` lands; what the formula tuning is)
- Operator interactions (when operator confirmed S05, signed off on goldens, etc.)

The BUILD_LOG is the durable artifact across sessions. Future-you (or another agent) reads it cold to understand what was built and what was tried.

---

## Failure recovery

For any blocker, attempt resolution up to **3 times** before filing in `BLOCKERS.md`:

- **CMake configure fails:** check CUDA Toolkit detection (`find_package(CUDAToolkit)`); MSVC version; CMake version. Try a fresh `build/` directory.
- **nvcc won't compile:** check `-arch=sm_89` etc. flags; MSVC bridging issues (use `-Xcompiler=` forwarding for MSVC flags through nvcc; do NOT pass bare MSVC flags directly to nvcc — it will reject them with "A single input file is required").
- **CUDA-GL interop crashes:** ensure GL context is current on the same thread that creates the CUDA-GL registration; use `cudaGraphicsResourceSetMapFlags` correctly; check that `cudaGraphicsGLRegisterImage` is called AFTER GL texture is fully created and initialized.
- **Atomic-add throughput cliff:** profile with Nsight Compute. If chaos PDE step is bottleneck, try tile-then-flush pattern or smaller histogram resolution.
- **Black screen, no errors:** check `glClear` is called; fullscreen quad VAO bound; texture in right format; uniforms set. Verify with apitrace or RenderDoc if needed.
- **Pixel assertion fails:** print expected (from libastra) vs measured (from glReadPixels) values to console. Check tolerance is reasonable for float precision (default 1% of expected or ±0.01 absolute, whichever is larger). Float-precision differences ARE acceptable; check the tolerance widening before declaring the math wrong.
- **Headless mode crashes:** likely missing `glFinish()` before `glReadPixels`; ImGui state from interactive mode polluting headless; framebuffer not bound when expected. Test headless from V0 to catch early.
- **`compute_cherenkov_angle()` produces unexpected angles:** verify `n_refractive_default(W) = 1 + W` matches your scenario; verify β is the EFFECTIVE velocity (v_app/c for warp, not raw v); verify the angle is in radians not degrees in math, and converted to degrees only for display.
- **Visual matches the math but doesn't look "right" to operator:** this is a finding, not a bug. The math is the spec; the visuals are derived. Either: (a) the spec is missing something (record in `KNOWN_ISSUES.md` as v0.130 candidate), or (b) the rendering parameters need tuning (record in BUILD_LOG.md).

After 3 attempts at any blocker, file `BLOCKERS.md` (in sandbox root):

```markdown
# BLOCKERS

## [YYYY-MM-DD] Blocker: <short title>

**Context:** <what phase, what scene, what task>
**Symptom:** <what is failing or wrong>
**Attempts:**
1. <what tried>; result: <what happened>
2. <what tried>; result: <what happened>
3. <what tried>; result: <what happened>
**Hypothesis:** <best guess at root cause>
**Operator decision needed:** <specific question or direction needed>
```

Stop work on the blocker; continue with other parts of the plan that don't depend on it. Document the dependency in BUILD_LOG.md.

---

## Done criteria (v1.0 ship checklist)

1. ✅ `build/astra_visualizer.exe` (or `dist/astra_visualizer.exe`) exists; builds clean on MSVC Release.
2. ✅ Interactive mode launches; scene selector visible.
3. ✅ All 12 scenes (S01-S12) load and render without crashing.
4. ✅ Each scene reaches its acceptance criteria per DESIGN_SPEC §6.
5. ✅ Three-layer validation operational (pixel assertions + heatmap diff + numeric overlay).
6. ✅ Each scene has ≥3 pixel-level assertions; total ≥36 assertions; all PASS on RTX 4070+ reference.
7. ✅ Side-by-side numeric overlay shows rendered vs libastra value with diff + PASS/FAIL color.
8. ✅ Per-pass GPU timing visible in profiler panel.
9. ✅ Headless mode (`--headless --scene=all --output=ci_results/`) runs all 12 in < 2 min; JSON report valid; CI exit code 0 iff all PASS.
10. ✅ Goldens in `assets/reference_renders/` locked per scene; heatmap diff < 1% mean vs canonical.
11. ✅ `--regenerate-goldens` flag exists with operator-sign-off enforcement (commit-message marker).
12. ✅ F12 in interactive mode saves PNG + JSON state dump.
13. ✅ Reaches 60 FPS at 1080p on RTX 4070+ target hardware.
14. ✅ `libastra_nexus` extracted INTO this sandbox (NOT modifying the original `proto/astra_nexus.cpp`); contains all 66 original C++ assertions plus 3+ new for Cherenkov; total 69+ pass.
15. ✅ **Cherenkov gap closed:** `compute_cherenkov_angle()` lives in `libastra_nexus/` with assertions in `libastra_nexus/tests/test_cherenkov.cpp`.
16. ✅ doctest unit tests pass for: pixel_sampler, rbf_eval, chaos_pde_step, observation_calc_kernel, cherenkov_math_bridge, assertion_layer.
17. ✅ Documentation in `docs/`: SCENES.md, VALIDATION.md, BUILD.md, KNOWN_ISSUES.md, CHANGELOG.md.
18. ✅ No Python source files in the sandbox; no Apple-specific code paths; no Unreal Engine dependency.
19. ✅ **Operator personally watches Scene S05 (RetardedTimeOrbitReversal) and CONFIRMS** the orbit visually appears to run backward at v_apparent = 2c. (Required final human sign-off. The "you have to see it to believe it" payoff scene.)
20. ✅ `BUILD_COMPLETE.md` filed at sandbox root with version, paths traveled, sample render paths, known limits.
21. ✅ `BLOCKERS.md` empty or absent (or all resolved with operator dispositions).

---

## What this folder will contain when complete

```
C:\ASTRA-7\ASTRA_VISUALIZER\
├── CLAUDE.md                          # this file (operating contract)
├── DESIGN_SPEC.md                     # technical design (~2000 lines; canonical)
├── README.md                          # user-facing controls + run instructions
├── BUILD_LOG.md                       # append-only build session log
├── BUILD_COMPLETE.md                  # filed at v1 completion
├── BLOCKERS.md                        # only if blockers exist
├── CMakeLists.txt                     # top-level build config
├── tools/
│   ├── build.bat                      # convenience wrapper for Windows
│   ├── dev-shell.bat                  # vcvarsall + ninja setup
│   └── golden_diff.cpp                # PNG diff tool for regression
├── libastra_nexus/                    # math library, EXTRACTED INTO SANDBOX from proto/astra_nexus.cpp
│   ├── CMakeLists.txt
│   ├── include/astra_nexus/
│   │   ├── coord.h                    # AstraCoord, astra_distance
│   │   ├── rapidity.h                 # Rapidity, OMEGA_MAX
│   │   ├── composition.h              # dtau_dt_cosmic
│   │   ├── apparent_rate.h            # compute_apparent_rate
│   │   ├── observe.h                  # ObservableState, observe
│   │   ├── kepler.h                   # Kepler solver
│   │   ├── cherenkov.h                # NEW: compute_cherenkov_angle
│   │   ├── stdio_server.h             # preserved
│   │   └── test_suite.h
│   ├── src/
│   │   ├── coord.cpp
│   │   ├── rapidity.cpp
│   │   ├── composition.cpp
│   │   ├── apparent_rate.cpp
│   │   ├── observe.cpp
│   │   ├── kepler.cpp
│   │   ├── cherenkov.cpp              # NEW: implements 5D-F4 gap closure
│   │   └── stdio_server.cpp
│   └── tests/                         # doctest test suite
│       ├── test_coord.cpp
│       ├── test_rapidity.cpp
│       ├── test_composition.cpp
│       ├── test_apparent_rate.cpp
│       ├── test_observe.cpp
│       ├── test_kepler.cpp
│       └── test_cherenkov.cpp         # NEW: ≥3 assertions for the gap closure
├── src/                               # visualizer C++ code
│   ├── main.cpp                       # entry; CLI parser; mode select
│   ├── app/
│   │   ├── application.cpp / .h
│   │   ├── scene_router.cpp / .h
│   │   ├── cli.cpp / .h
│   │   ├── headless_mode.cpp / .h
│   │   ├── camera.cpp / .h
│   │   ├── input.cpp / .h
│   │   └── time_step.cpp / .h
│   ├── renderer/
│   │   ├── gl_context.cpp / .h
│   │   ├── compute_program.cpp / .h
│   │   ├── graphics_program.cpp / .h
│   │   ├── texture.cpp / .h
│   │   ├── buffer.cpp / .h
│   │   ├── cuda_gl_interop.cpp / .h
│   │   ├── volume_renderer.cpp / .h
│   │   ├── starfield.cpp / .h
│   │   ├── cherenkov.cpp / .h
│   │   ├── lensing.cpp / .h
│   │   ├── hull.cpp / .h
│   │   ├── trail.cpp / .h
│   │   ├── retarded_body.cpp / .h
│   │   └── overlays.cpp / .h
│   ├── physics/
│   │   ├── physics_core.cpp / .h      # facade over libastra_nexus
│   │   ├── rbf_network.cpp / .h
│   │   ├── chaos_field.cpp / .h
│   │   ├── hull_sdf.cpp / .h
│   │   ├── reflex_stub.cpp / .h
│   │   ├── cherenkov_math.cpp / .h    # bridges to libastra_nexus
│   │   └── state_bus.cpp / .h
│   ├── scenes/
│   │   ├── i_scene.h                  # interface
│   │   ├── scene_base.cpp / .h
│   │   ├── s01_rest_baseline.cpp / .h
│   │   ├── s02_stl_recede_05c.cpp / .h
│   │   ├── s03_stl_recede_09c.cpp / .h
│   │   ├── s04_warp_charge.cpp / .h
│   │   ├── s05_warp_cruise_2c.cpp / .h         # THE PAYOFF SCENE
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
│   │   ├── cfd_synthesizer.cpp / .h   # synthesize analytic Alcubierre RBF
│   │   ├── hull_loader.cpp / .h
│   │   ├── starfield_loader.cpp / .h
│   │   └── scenario_loader.cpp / .h
│   └── util/
│       ├── log.cpp / .h
│       ├── timer.cpp / .h
│       ├── screenshot.cpp / .h
│       └── color.cpp / .h
├── kernels/                           # CUDA kernels (separate from src/ for nvcc isolation)
│   ├── chaos_pde.cu                   # Fisher-KPP RK2 solver
│   ├── warp_field.cu                  # CFD-RBF eval + ∇W via dual-numbers
│   ├── observation_calc.cu            # per-body retarded-time Newton
│   ├── ism_impact.cu
│   ├── wake_field.cu                  # warp wake trail evolution
│   ├── reflex_stub.cu                 # simple PID Reflex
│   └── kernels.h                      # C++ declarations
├── shaders/
│   ├── common/                        # shared GLSL headers
│   ├── volume/raymarch.{vert,frag}
│   ├── starfield/starfield.{vert,frag}
│   ├── cherenkov/cone.frag
│   ├── lensing/post.frag
│   ├── hull/hull.{vert,frag}
│   ├── trail/trail.{vert,frag}
│   ├── retarded_body/body.{vert,frag}
│   ├── chaos/slice_2d.frag
│   └── overlay/{arrows,rbf_nodes}.{vert,frag}
├── assets/
│   ├── hull/
│   │   └── astra7_lowpoly.obj         # ~10K tris placeholder
│   ├── starfield/
│   │   └── starfield_10k.bin          # 10K star catalog
│   ├── cfd/
│   │   └── warp_cfd_rbf_synthetic_v1.json  # ~50-200 node test RBF
│   ├── scenarios/
│   │   ├── s01_rest_baseline.json
│   │   ├── s02_stl_recede_05c.json
│   │   └── ... (s03-s12)
│   └── reference_renders/             # golden PNGs (canon-locked)
│       ├── s01_t0_canonical.png
│       ├── s02_t0_canonical.png
│       └── ... (one per scene per canonical timestamp)
├── tests/                             # doctest visualizer-side tests
│   ├── test_pixel_sampler.cpp
│   ├── test_rbf_eval.cpp
│   ├── test_chaos_pde_step.cpp
│   ├── test_observation_calc_kernel.cpp
│   ├── test_cherenkov_math_bridge.cpp
│   └── test_assertion_layer.cpp
├── third_party/                       # auto-fetched via FetchContent
│   └── (glfw, glad, imgui, glm, stb, nlohmann_json, doctest, spdlog)
├── docs/
│   ├── SCENES.md                      # per-scene walkthrough
│   ├── VALIDATION.md                  # three-layer methodology
│   ├── BUILD.md                       # Windows + Linux build details
│   ├── KNOWN_ISSUES.md                # spec-revision-eligible findings
│   └── CHANGELOG.md                   # per-phase landings
├── build/                             # CMake build dir (gitignored if git used)
└── dist/                              # final binaries + showcase PNGs
    ├── astra_visualizer.exe
    └── showcase_*.png
```

---

## Critical implementation order (the V0 priority)

Phase V0 (weeks 1-2) has ONE critical-path deliverable that gates all subsequent phases:

**The libastra_nexus extraction MUST happen first.**

The agent reads `C:\ASTRA-7\proto\astra_nexus.cpp` (1009 lines, READ-ONLY) and creates an organized static library INSIDE `C:\ASTRA-7\ASTRA_VISUALIZER\libastra_nexus\` (per the layout above). This library:

- Contains the EXACT SAME math as the original (do not change semantics).
- Splits by concern (coord / rapidity / composition / apparent_rate / observe / kepler / stdio_server).
- Adds `cherenkov.h` + `cherenkov.cpp` as NEW (closes 5D-F4 gap; see DESIGN_SPEC §6.6 for the formula).
- Adds `test_suite.h` exposing `run_all_tests()` returning pass/fail counters.
- Adds `tests/test_*.cpp` files that contain ALL 66 original assertions plus ≥3 new for Cherenkov, executed via doctest.
- Builds as `libastra_nexus.lib` (Windows) / `libastra_nexus.a` (Linux) via its own CMakeLists.txt that the top-level CMakeLists.txt `add_subdirectory()`s.
- ALSO produces a standalone `libastra_nexus_test.exe` that runs all 69+ assertions when run.

**Gate for V0 completion:** `libastra_nexus_test.exe` runs and reports `[PASS] 69 of 69 tests` (or higher; never lower). The visualizer can then link this lib as the single source of truth for math.

Do NOT proceed to V1 (renderer foundations) until V0's libastra_nexus extraction passes.

---

## Things to verify before declaring any scene "done"

Per DESIGN_SPEC §6, each scene has structured assertions. Before marking a scene complete in BUILD_LOG.md:

- [ ] All pixel-level assertions PASS in interactive mode on RTX 4070+.
- [ ] All pixel-level assertions PASS in headless mode on RTX 4070+.
- [ ] Side-by-side numeric overlay shows rendered vs libastra values to expected precision.
- [ ] Frame time ≤ 16.67 ms at 1080p (60 FPS budget).
- [ ] Visual matches the spec's described phenomenon to operator's eye.
- [ ] Golden PNG captured at canonical timestamp; reproduces on rebuild.
- [ ] Scene's parameter sliders update visuals live without flickering or crashing.
- [ ] No new third-party deps added without BUILD_LOG.md entry.

For S05 specifically: add **operator-personally-watches** to the checklist. Defer marking S05 complete until operator confirms visible orbit reversal.

---

## Spec-revision findings — record as you go

This testbed will surface findings per spec §15.4 ("revise on findings"). When you encounter:

- A visual phenomenon the spec doesn't yet describe but the math produces (e.g., warp wake P3)
- A coefficient that needs empirical tuning (e.g., α_lens, n(W) function, smooth-min k)
- A numerical instability the spec's CFL bound didn't anticipate
- An edge case the math handles but the rendering doesn't (or vice versa)
- An ambiguity in the spec that the implementation forced you to resolve one way

→ Add an entry to `docs/KNOWN_ISSUES.md` (in the sandbox; you may create it freely):

```markdown
## [YYYY-MM-DD] Finding: <short title>

**Scene:** <S01-S12>
**Spec section affected:** <§X.Y>
**Phenomenon:** <what was observed visually>
**Math reference:** <libastra_nexus function or formula citation>
**Empirical value:** <what coefficient was tuned to, if any>
**Spec-revision candidate:** <how this might land in v0.130>
**Operator review needed:** yes / no
```

These KNOWN_ISSUES.md entries are how the testbed feeds back into the project's spec-revision cadence per §15.10. Operator reads them and decides which become v0.130 spec edits.

---

## End-of-session protocol

When you stop a session (either at a phase gate, at the end of your turn-budget, or at an operator-requested pause):

1. Update `BUILD_LOG.md` with what landed and what's next.
2. Commit (if git initialized in this sandbox): `git add . && git commit -m "<phase>: <brief>"`. **Never push to remote** — operator does that.
3. If there are blockers, ensure `BLOCKERS.md` is up to date.
4. If there are findings worth spec revision, ensure `docs/KNOWN_ISSUES.md` captures them.
5. If a scene was completed, ensure the corresponding golden PNG is in `assets/reference_renders/` and `docs/CHANGELOG.md` records the landing.

Leave the sandbox in a runnable state. Anyone (including future-you) opening the folder cold should be able to:
- Read CLAUDE.md → understand the operating contract
- Read DESIGN_SPEC.md → understand what to build
- Read BUILD_LOG.md → understand what was built so far
- Run `cmake -B build && cmake --build build` → get a working binary (at whatever phase completion is at)

---

## Closing reminders

- The sandbox is the contract. Don't leave it.
- The math (libastra_nexus) is the single source of truth. Don't reimplement it.
- The validation methodology is mechanical. Don't skip it.
- The headless mode is not optional. Build from V0.
- The operator personally signs off on S05. Defer marking it done.
- The Cherenkov gap (5D-F4) is closed by this project. Land it in libastra_nexus.
- Per CLAUDE.md project-wide: no Python in new code, no Apple targets.
- Per spec §15.4: every change traces to a finding or to the spec. No polish without findings.

Build it. Render it. Validate it. Watch S05 with the operator. File BUILD_COMPLETE.md. The visual physics of v0.129 becomes empirically demonstrated.

The math is locked. The visuals are testable. The sandbox is bounded. Begin.

---

**Operator:** Bo Chen — Arlington, Texas
**Sandbox:** `C:\ASTRA-7\ASTRA_VISUALIZER\`
**Sibling autonomous-build artifact:** `C:\Buddhabrot_CUDA\` (same CLAUDE.md / DESIGN_SPEC.md / BUILD_LOG.md pattern)
**Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md` (fallback `spec-v0.128.md`)
**Math basis:** `proto/astra_nexus.cpp` (extract into `libastra_nexus/` inside this sandbox)
**Vision basis:** `DESIGN_SPEC.md` in this folder
