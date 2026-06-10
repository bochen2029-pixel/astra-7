# ASTRA-7 Visual Physics Testbed — Design Specification

**Project:** Engine-agnostic, real-time visual ground-truth testbed for ASTRA-7 spec v0.129 physics
**Target hardware:** RTX 4070 / 4070 Ti SUPER baseline; RTX 4090 / 5090 for upper-tier; RTX 3060 minimum
**Sandbox:** `C:\ASTRA-7\ASTRA_VISUALIZER\` (you may NOT write outside this; see `CLAUDE.md` §Sandbox)
**Spec basis:** `C:\ASTRA-7\docs\spec-v0.129-tentative-2026-05-16.md` (read-only; fallback `spec-v0.128.md`)
**Math basis:** `C:\ASTRA-7\proto\astra_nexus.cpp` (1009 lines, read-only; you EXTRACT into `libastra_nexus/` in this sandbox)
**Pair document:** `CLAUDE.md` in this folder (operating contract)
**Predecessor design pass:** `C:\ASTRA-7\ASTRA_VISUALIZER_PLAN_2026-05-16_V2.md` (this DESIGN_SPEC is its in-sandbox expansion)

---

## Foreword

ASTRA-7's `proto/astra_nexus.cpp` is a 1009-line C++ binary with 66 assertions proving the 14-equation framework at the *mathematical* level — console output, PASS/FAIL counters, voyage-demo tables. **It does not prove the math actually produces the *visual* phenomena the spec describes.**

The spec talks about: a violet warp bubble whose shape comes from the CFD-RBF field; geometric lensing of starlight through the warp gradient (∇W ray deflection); a Cherenkov cone at v_app > c with `cos θ_c = 1/(n·β)`; a visible warp wake — metric_shift residual trailing behind the ship as it moves; retarded-time orbit reversal — a planet behind the ship appearing to run backward at v_app > c; Doppler-shifted starfield colors at relativistic STL velocities; chaos PDE instability at the bubble boundary visible as particle artifacts; Reflex stabilizer's effect on chaos amplitude; photon-source-history bound (a source becoming **gone**, not faded); Hubble-horizon decoupling (frozen + dimming).

These are **visual claims with mathematical bodies.** The math is locked. The visual fidelity is not yet confirmed.

This testbed is the engine-agnostic ground-truth layer between the math and the eventual UE5 rendering. It validates the visual claims of spec v0.129 without depending on UE5's complexity. It also **closes the Cherenkov formula gap** (AUDIT 5D-F4: locked at 4 spec sites, zero code implementation) by adding `compute_cherenkov_angle()` to `libastra_nexus` with assertions.

When this testbed ships, the operator can hold up a frame and say: "Yes. That's what 2c retreat from Earth looks like. The orbit runs backward. The math agrees with the pixels."

That is the artifact's defining property. Everything else flows from it.

---

## Part 1: Goals and Non-Goals

### 1.1 Goals (v1.0)

1. **A standalone Windows 11 executable** (`astra_visualizer.exe`) that renders 12 visual physics scenes (S01-S12) per §6 of this spec.
2. **Pure C++17/CUDA 12.4+/OpenGL 4.6/GLFW 3.4/GLAD 2/Dear ImGui 1.91+/GLM 1.0+**. No engine. No Python. No Apple targets.
3. **Three-layer mechanical validation**: pixel-level scalar assertions + heatmap diff vs goldens + side-by-side numeric overlay with live PASS/FAIL color. Per §7 of this spec.
4. **Dual-mode operation**: interactive (window + ImGui + camera controls) and headless (CI batch render with PNG dumps + JSON report).
5. **Link `libastra_nexus`** — a static library EXTRACTED INTO this sandbox from a read-only reference to `C:\ASTRA-7\proto\astra_nexus.cpp`. Single source of truth for math. Per §3.1 of this spec.
6. **Closes the Cherenkov gap** (AUDIT 5D-F4): adds `compute_cherenkov_angle(W, beta, n_refractive)` to libastra_nexus with ≥3 C++ assertions. Bumps assertion count 66 → 69+.
7. **60+ FPS at 1080p** on RTX 4070 reference; 30 FPS minimum on RTX 3060 fallback; 120 FPS at 1080p on RTX 5090.
8. **Cross-platform**: Windows 11 primary (MSVC 2022 17.8+); Linux x86_64 secondary (GCC 13+). Both tested from V0.
9. **Operator-visible orbit reversal** in Scene S05 at v_apparent = 2c — the canonical demonstration of spec §3.11. Operator sign-off required for v1.0.

### 1.2 Non-Goals (v1.0)

- ❌ No Unreal Engine integration. UE5 is the eventual production rendering (Phase E2-E5 per `DISCOVERY_2026-05-16_TECHDIVE_UE5.md`); this testbed is the engine-agnostic ground truth that runs before UE5 lands.
- ❌ No production rendering quality. No TSR, no Lumen, no Nanite, no DLSS, no Frame Generation, no path tracing. Forward-rendering with custom shaders only.
- ❌ No LLM / persona / Sculptor / textverse. Track A territory; orthogonal.
- ❌ No real audio playback. Scene S12 simulates audio frequency in UI display only. (Real audio synthesis lives in MetaSound per spec §8.3 — UE5 substrate.)
- ❌ No NNE / TensorRT for Reflex. PID stub controller only. Real Reflex training is a separate effort (Phase E1 per techdive doc).
- ❌ No Apple / Mac / Metal / iOS / Swift / Objective-C. Per CLAUDE.md Platform Discipline (2026-05-15).
- ❌ No new Python in this sandbox. Per CLAUDE.md Language Discipline (2026-05-15).
- ❌ No save/load persistence between sessions. Scenarios start fresh each launch.
- ❌ No network features. Local-only execution per spec §4.8.
- ❌ No VR / stereo rendering. Mono only.
- ❌ No production-grade hull mesh. Simple low-poly placeholder; full hull is UE5 Phase E0 work.
- ❌ No deep-zoom Mandelbrot-style precision tricks. f32 math everywhere in shaders; f64 where math demands (libastra_nexus uses double per spec).
- ❌ No game logic, achievements, progression, persistence. Pure physics → pixels.

### 1.3 What success looks like

`astra_visualizer.exe` runs on a Windows 11 machine with an NVIDIA RTX 40-series+ GPU. The user picks a scene from a menu. Scene renders at 60+ FPS at 1080p. UI controls let them sweep parameters (e.g., β from 0 to 0.999 for Cherenkov). For every scene, an on-screen assertion overlay says **PASS / FAIL** comparing rendered pixels to canonical math from `libastra_nexus`.

Headless mode (`--headless --scene=all --output=ci_results/`) runs all 12 scenes, dumps 12 PNGs to disk, writes a JSON test report. CI gates on `summary.scenes_failed == 0`.

Operator watches S05 and SEES the orbit running backward at v_app=2c — the "you have to see it to believe it" payoff that requires final human sign-off.

---

## Part 2: Architecture

### 2.1 Stack (locked recommendations)

| Layer | Technology | Rationale |
|---|---|---|
| Build system | **CMake 3.27+** | Per CLAUDE.md Language Discipline. FetchContent eliminates manual third-party setup. Cross-platform (MSVC + GCC + Clang). |
| C++ standard | **C++20** (C++17 minimum) | Concepts + designated initializers; CUDA 12.x supports it. Use C++17 if your toolchain ever balks. |
| Compiler (Windows) | **MSVC 19.38+** (Visual Studio 2022 17.8+) | NVCC 12.4+ integrates cleanly. Operator's machine has 14.16, 14.29, 14.43; use 14.43. |
| Compiler (Linux) | **gcc 13+ or clang 16+** | Both support C++20 + CUDA. |
| GPU compute | **CUDA 12.4+** (13.x preferred) | NVIDIA-only per Platform Discipline. Modern CUDA Graphs supported. |
| Graphics API | **OpenGL 4.6 Core Profile** | Mature CUDA interop (`cudaGraphicsGLRegisterBuffer/Image`); compute shaders (GL 4.3+); engine-agnostic; cross-vendor. |
| Window + input | **GLFW 3.4+** | Lightweight; works Windows + Linux; permissive (zlib). |
| GL function loader | **GLAD 2.0.6+** | Single header generated for GL 4.6 core profile. |
| Math library | **GLM 1.0+** | Header-only; matches GLSL conventions. |
| UI | **Dear ImGui 1.91+** (docking branch) | Industry standard for graphics tooling. OpenGL3 + GLFW backends. |
| Image I/O | **stb_image + stb_image_write** | Single-header; PNG read/write for assertions + goldens. |
| JSON | **nlohmann/json** (single-header) | Per spec §15.6 "Replacements" table. For scenarios + test reports. |
| Logging | **spdlog** (header-only mode) | Optional; plain `fprintf` acceptable. |
| Test framework | **doctest** (single-header) | Per spec §15.6; lightweight. |
| Linkage | **`libastra_nexus.lib`** statically linked | Single source of truth for math. Extracted INTO sandbox. |
| CUDA runtime | **`CUDA::cudart_static`** | Static linkage; .exe has no `cudart64_*.dll` dependency. |
| MSVC runtime | **MultiThreaded$<$<CONFIG:Debug>:Debug>** | Static CRT; .exe has no MSVC redistributable dependency. Cascades to FetchContent'd subprojects. |
| Target CUDA archs | **sm_89, sm_90, sm_120** | RTX 40-series (Ada), Hopper datacenter, RTX 50-series (Blackwell consumer). |

### 2.2 What we're NOT using (rejected explicitly)

| Rejected | Why |
|---|---|
| Vulkan | Too much boilerplate for ground-truth visualization. Use only if OpenGL proves insufficient (unlikely). |
| DirectX 12 | Engine-specific (UE5 will use it separately). Locks Windows-only. |
| OptiX / RTX ray-tracing | Proprietary; we want straight compute-shader ray-marching. |
| Qt / wxWidgets | Heavy. ImGui is the right tool. |
| OpenGL ES | Mobile-targeted. |
| WebGPU / Dawn | Emerging but not production-stable on Windows native as of May 2026. |
| Unreal / Unity / Godot / Bevy | The whole point is engine-agnostic. |
| Boost | Heavy; not needed. |
| Any Python | Per CLAUDE.md Language Discipline. Including no Python build scripts. |
| Any Apple-specific code paths | Per Platform Discipline. Don't `#ifdef __APPLE__` even defensively. |

### 2.3 Top-level pipeline

```
Per frame (interactive mode):
  POLL INPUT
    - Mouse wheel, drag, keyboard
    - On scene change: tear down old, setup new
    - On parameter change: update CUDA constants / RBF modulation
  SIM TICK
    - libastra_nexus calls: update TimeState, regime, composition rule
    - CUDA chaos PDE step (RK2)
    - CUDA warp field SVT populate (RBF eval + ∇W via dual numbers)
    - CUDA observation_calc step (per-body retarded time)
    - CUDA reflex_stub eval (if active)
  RENDER
    - GL fullscreen quad → volume_renderer fragment shader → samples CUDA-shared 3D textures
    - GL retarded_body instanced draw → per-body shader with Doppler color
    - GL starfield point sprites with redshift
    - GL cherenkov_cone billboard (if v_app > c)
    - GL lensing post-pass (geometric ray deflection)
    - GL hull mesh
    - GL trail (warp wake)
    - GL overlay (∇W arrows, RBF centers if debug toggled)
  VALIDATION
    - PixelSampler reads canonical framebuffer pixels via glReadPixels
    - libastra computes the expected values
    - Compare; emit PASS/FAIL events
    - Numeric overlay updates with live diffs
  UI
    - ImGui: scenario selector, parameter panel, state display, validation panel, profiler
  PRESENT
    - glfwSwapBuffers
```

```
Per frame (headless mode):
  - No GLFW window visible (invisible 16x16 context for GL)
  - All passes same as interactive
  - At canonical timestamp per scene:
    - glReadPixels full framebuffer to CPU
    - Write PNG via stb_image_write
    - Run all assertions; record results
  - After all scenes:
    - Write JSON test report
    - Exit 0 if all PASS; exit 1 otherwise
```

### 2.4 CUDA-OpenGL interop pattern

This is the same pattern Buddhabrot_CUDA uses successfully. Operator's hardware works with this; replicate.

**Setup (once at startup, after GL context created):**

```cpp
// CUDA registers GL 3D texture for write access
cudaGraphicsResource* cuda_chaos_resource;
cudaGraphicsGLRegisterImage(
    &cuda_chaos_resource,
    gl_chaos_texture_id,
    GL_TEXTURE_3D,
    cudaGraphicsRegisterFlagsSurfaceLoadStore  // we want to write via surface
);
```

**Per frame:**

```cpp
// Map for CUDA write
cudaArray_t cuda_array;
cudaGraphicsMapResources(1, &cuda_chaos_resource);
cudaGraphicsSubResourceGetMappedArray(&cuda_array, cuda_chaos_resource, 0, 0);

// Bind as surface
cudaResourceDesc res_desc = {};
res_desc.resType = cudaResourceTypeArray;
res_desc.res.array.array = cuda_array;
cudaSurfaceObject_t surface;
cudaCreateSurfaceObject(&surface, &res_desc);

// Run CUDA kernel that writes via surf3Dwrite()
k_chaos_pde_step<<<grid, block>>>(surface, ...);

// Cleanup + unmap
cudaDestroySurfaceObject(surface);
cudaGraphicsUnmapResources(1, &cuda_chaos_resource);

// GL can now sample the texture
glBindTexture(GL_TEXTURE_3D, gl_chaos_texture_id);
// ... draw call ...
```

**Why this pattern:** the chaos field (and warp SVT) live in a single 3D texture that CUDA writes (via surface) and GL reads (via texture). Zero-copy round-trip. Same memory; two views. Per spec §1.3 / §8.1 dual-binding pattern (adapted for OpenGL — the Engine-track UE5 implementation will use the DX12 variant).

### 2.5 Memory budget (approximate, on RTX 4070+)

| Item | Size |
|---|---|
| Chaos field (128³ × float32 × 2 buffers) | 16 MB |
| Warp field volume (256³ × float32, sparse-est-aware) | up to 64 MB; expect ~8 MB occupied |
| Hull SDF placeholder (256³ × float16) | 32 MB |
| Damage map (sparse, max 64 MB pre-allocated) | 64 MB pre-allocated; ~0 used at start |
| CFD-RBF + spatial hash | ~250 KB |
| Per-body observation state (10K bodies × 64 B) | 640 KB |
| Starfield (10K stars × 32 B) | 320 KB |
| GL render targets (color + depth × 2 buffers @ 1920×1080) | ~50 MB |
| ImGui internal | ~10 MB |
| Reflex stub state | <1 KB |
| **Total physics + render** | **~250 MB** |

Well under the 8GB target hardware floor. Won't even pressure a 3060.

---

## Part 3: Module breakdown — the libastra_nexus extraction

This is the **V0 critical-path deliverable**. Everything depends on it.

### 3.1 What gets extracted (read from proto/astra_nexus.cpp)

Reference: `C:\ASTRA-7\proto\astra_nexus.cpp` is 1009 lines containing:

| Line range | Concern | Extract target |
|---|---|---|
| 52-67 | Physical constants (C_LIGHT, G_GRAV, M_SUN, PARSEC, LIGHT_YEAR, MPC, H0_KMS_MPC, H0_SI, OMEGA_M, OMEGA_LAM, OMEGA_MAX) | `libastra_nexus/include/astra_nexus/constants.h` |
| 72-84 | `struct Vec3` | `constants.h` (used everywhere) |
| 86-113 | `struct AstraCoord` + `astra_distance()` | `coord.h` + `coord.cpp` |
| 118-140 | Regime enum + bitmask values + `regime_label()` | `regime.h` (small inline file) |
| 145-166 | `struct Rapidity` + `integrate_rapidity_step()` | `rapidity.h` + `rapidity.cpp` |
| 171-217 | `struct BHEntry` + `schwarzschild_r()` + `compute_grav_factor()` | `composition.h` + `composition.cpp` |
| 219-232 | `f_warp_canon()` + `dtau_dt_cosmic()` | `composition.h` + `composition.cpp` |
| 245-282 | `struct Observable` + `compute_apparent_rate()` | `observe.h` + `observe.cpp` (rename Observable → ObservableState per spec §6.3 v0.129) |
| 283-307 | `compute_z_kin()` + `compute_z_cosmo()` + `compute_lookback()` | `observe.h` + `observe.cpp` |
| 309-342 | `observe()` full function | `observe.h` + `observe.cpp` |
| 346-374 | `struct Orbit` + `solve_kepler_E()` + `orbit_phase()` | `kepler.h` + `kepler.cpp` |
| 379-702 | `namespace test` with `run_all()` | `tests/test_*.cpp` (split per concern; use doctest framework) |
| 706-763 | `demo_voyage()` | optional: extract to `demo.cpp` or leave out (visualizer is its own demo) |
| 782-984 | `namespace stdio_server` | `stdio_server.h` + `stdio_server.cpp` (preserve; not used by visualizer but available) |
| 989-1009 | `main()` | NOT extracted; visualizer has its own main. The original astra_nexus.exe's main stays in proto/astra_nexus.cpp (unchanged). |

### 3.2 What gets ADDED to libastra_nexus

```cpp
// libastra_nexus/include/astra_nexus/cherenkov.h
// NEW: closes the AUDIT 5D-F4 gap.

#pragma once
#include "constants.h"

namespace astra {

// Default refractive index model for warp field.
// Provisional: n(W) = 1 + n_coefficient * W
// where n_coefficient is a tuning parameter (default 1.0).
inline double n_refractive_default(double W, double n_coefficient = 1.0) {
    return 1.0 + n_coefficient * W;
}

// Compute Cherenkov half-angle per spec §6 step 10.
// Returns angle in radians if n*beta > 1 (cone exists);
// returns -1.0 if n*beta <= 1 (cone inactive / undefined).
//
// cos(theta_c) = 1.0 / (n * beta)
//
// Inputs:
//   W: warp field magnitude at evaluation point [0, 1]
//   beta: effective velocity / c (use v_apparent/c for warp; raw beta for STL)
//   n_coefficient: tuning parameter for n(W) = 1 + n_coefficient * W (default 1.0)
//
// Output:
//   theta_c in radians, or -1.0 if cone inactive
double compute_cherenkov_angle(double W, double beta, double n_coefficient = 1.0);

}  // namespace astra
```

```cpp
// libastra_nexus/src/cherenkov.cpp
#include "astra_nexus/cherenkov.h"
#include <cmath>

namespace astra {

double compute_cherenkov_angle(double W, double beta, double n_coefficient) {
    double n = n_refractive_default(W, n_coefficient);
    double n_beta = n * beta;
    if (n_beta <= 1.0) return -1.0;  // cone inactive
    return std::acos(1.0 / n_beta);
}

}  // namespace astra
```

```cpp
// libastra_nexus/tests/test_cherenkov.cpp
// Adds ≥3 assertions to the test suite; closes 5D-F4 at the code level.

#define DOCTEST_CONFIG_IMPLEMENT
#include <doctest/doctest.h>
#include "astra_nexus/cherenkov.h"
#include <cmath>

using namespace astra;

TEST_CASE("Cherenkov inactive when n*beta <= 1") {
    // At beta = 0.1, W = 0: n=1.0, n*beta=0.1 → cone inactive
    CHECK(compute_cherenkov_angle(0.0, 0.1) == -1.0);
    // At beta = 0.5, W = 0: n=1.0, n*beta=0.5 → cone inactive
    CHECK(compute_cherenkov_angle(0.0, 0.5) == -1.0);
}

TEST_CASE("Cherenkov angle at canonical beta + W=1") {
    // At W=1.0, n=2.0; beta=0.6: n*beta=1.2; cos(theta)=1/1.2=0.833;
    // theta=acos(0.833)≈0.5857 rad ≈ 33.56°
    double angle = compute_cherenkov_angle(1.0, 0.6);
    CHECK(angle > 0.0);
    CHECK(std::abs(angle - std::acos(1.0/1.2)) < 1e-9);
    CHECK(std::abs(angle - 0.585685543) < 1e-6);
}

TEST_CASE("Cherenkov angle narrows as beta increases") {
    // Fixed W=1.0 (n=2.0); test angle decreases as beta grows
    double a1 = compute_cherenkov_angle(1.0, 0.55);  // n*beta = 1.10
    double a2 = compute_cherenkov_angle(1.0, 0.75);  // n*beta = 1.50
    double a3 = compute_cherenkov_angle(1.0, 0.95);  // n*beta = 1.90
    CHECK(a1 > 0.0);
    CHECK(a2 > 0.0);
    CHECK(a3 > 0.0);
    CHECK(a1 > a2);  // narrower as beta grows
    CHECK(a2 > a3);
}

TEST_CASE("Cherenkov angle independent test against spec § 6 step 10 formula") {
    // At a known operating point: W=0.5 (n=1.5), beta=0.8 (n*beta=1.20)
    // cos(theta_c) = 1/1.2 = 0.8333
    double angle = compute_cherenkov_angle(0.5, 0.8);
    CHECK(std::abs(std::cos(angle) - (1.0/1.2)) < 1e-9);
}
```

**Total new assertions:** 4 test cases × multiple CHECKs ≈ 10+ individual checks. Libastra assertion count goes from 66 → 76+ when all these pass.

### 3.3 The CMake split

```cmake
# libastra_nexus/CMakeLists.txt
add_library(astra_nexus STATIC
    src/coord.cpp
    src/rapidity.cpp
    src/composition.cpp
    src/observe.cpp
    src/kepler.cpp
    src/cherenkov.cpp        # NEW: 5D-F4 gap closure
    src/stdio_server.cpp     # preserved
)
target_include_directories(astra_nexus PUBLIC include)
target_compile_features(astra_nexus PUBLIC cxx_std_20)

# Standalone test binary
add_executable(libastra_nexus_test
    tests/test_coord.cpp
    tests/test_rapidity.cpp
    tests/test_composition.cpp
    tests/test_apparent_rate.cpp
    tests/test_observe.cpp
    tests/test_kepler.cpp
    tests/test_cherenkov.cpp  # NEW
)
target_link_libraries(libastra_nexus_test PRIVATE astra_nexus doctest)
```

```cmake
# Top-level CMakeLists.txt
add_subdirectory(libastra_nexus)

target_link_libraries(astra_visualizer PRIVATE astra_nexus)
```

### 3.4 V0 acceptance gate

Before proceeding to V1:

1. `libastra_nexus/` directory exists with the layout above.
2. `cmake -B build && cmake --build build --target libastra_nexus_test` succeeds clean.
3. `./build/libastra_nexus_test` runs and reports `[PASS] N of N tests` where N ≥ 69 (66 original ports + ≥3 new Cherenkov).
4. The original `C:\ASTRA-7\proto\astra_nexus.cpp` is UNTOUCHED (you can verify by `git status` showing no changes outside the sandbox).

---

## Part 4: Numerical algorithms (detailed)

### 4.1 Composition rule (per spec §3.2; from libastra_nexus)

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic
```

Implemented as `astra::dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin, bool warp_active)`. Visualizer calls this; never reimplements.

### 4.2 Rapidity ζ⃗ (per spec §3.7)

- ω = |ζ⃗|; clamped at OMEGA_MAX = 16.811 → γ_max ≈ 10⁷
- γ = cosh(ω) (NEVER compute via 1/√(1-β²); catastrophic cancellation)
- β = tanh(ω)
- v⃗ = c · tanh(ω) · ζ⃗/ω

Implemented as `astra::Rapidity` struct + `integrate_rapidity_step()`. Visualizer queries gamma, beta, velocity via accessors.

### 4.3 Retarded-time Newton solver (per spec §3.11)

For each visible body each frame:

```
Initial: t_emit_0 = t_cosmic - distance(ship, body) / c
For i in 0..5:
    body_pos = Kepler(orbit, t_emit_i)
    body_vel = KeplerVelocity(orbit, t_emit_i)
    f = t_emit_i + |body_pos - ship_pos| / c - t_cosmic
    f' = 1 - (r_hat · body_vel) / c
    t_emit_{i+1} = t_emit_i - f / f'
    if |t_emit_{i+1} - t_emit_i| < 1e-6: break
```

Implemented in `kernels/observation_calc.cu` (CUDA kernel; one thread per body). Visualizer calls into libastra's `observe()` for CPU-side calibration assertions; CUDA kernel mirrors the math for GPU execution.

### 4.4 Chaos PDE — Fisher-KPP with BH coupling (per spec §7.1)

```
∂χ/∂t = D∇²χ + α_eff(x,t) · χ · (1 − χ) + η(x,t)
α_eff = α_base · (1 + k · M_BH · L_bubble² / r³)
```

**Discretization:**
- Spatial: 128³ uniform grid; central finite differences for Laplacian
- Temporal: explicit RK2 (midpoint method); CFL bound D·Δt/Δx² < 1/6
- Boundary: periodic (v0); can switch to Dirichlet if needed
- Memory: 128³ × float × 2 buffers = 16 MB

**Kernel:** `kernels/chaos_pde.cu`; thread block 8×8×8 = 512; shared-memory tile 10×10×10 = 4 KB; tree-reduce max-rate-of-change for convergence detection.

**Convergence detection:** per spec §4.6 — `|χ̇_max| < ε_convergence` OR N=60 frames, whichever first.

### 4.5 Warp field sampling — 12-step pipeline (per spec §6)

```cuda
__device__ WarpFieldSample sample_warp_field_unified(
    float3 world_pos, float3 view_dir,
    const UnifiedWarpState& state, PerceptionFlags flags)
{
    // 1. Transform to ship-local
    float3 local = world_to_local(world_pos, state.ship_pose);
    // 2. Sample hull SDF (read via cudaTextureObject_t)
    float hull_d = tex3D<float>(state.hull_sdf_tex, ...);
    float hull_damage = surf3Dread<float>(state.damage_surface, ...);
    float hull_d_eff = hull_d - hull_damage;
    // 3. Evaluate RBF via spatial hash (dual-numbers for value+grad)
    DualScalar W_dual = evaluate_rbf_via_spatial_hash(local, state, flags);
    // 4. Smooth-min blend hull + bubble SDFs
    float bubble_d = compute_bubble_sdf(local, W_dual.value);
    float blended = smooth_min(hull_d_eff, bubble_d, SMOOTH_K);
    // 5. Sample chaos surface
    float chaos = surf3Dread<float>(state.chaos_surface_read, ...);
    // 6. Modulate W by chaos
    float W_mod = W_dual.value * (1.0f + state.chaos_eps * chaos);
    // 7. Wake metric + vortex contribution (NEW per spec §6 step 7)
    float wake = compute_wake_contribution(local, state.ship_velocity, state.t_cosmic);
    W_mod += wake;
    // 8. Gradient ∇W (from dual-number pass; "step 8" is conceptual — math done in step 3)
    float3 grad_W = W_dual.dx;
    // 9. Ray-deflection contribution
    float3 ray_deflection = state.alpha_lens * grad_W * MARCH_STEP_SIZE;
    // 10. Cherenkov angle (call libastra_nexus::compute_cherenkov_angle)
    float n_refr = 1.0f + W_mod;  // n(W) default per cherenkov.h
    float beta_eff = compute_effective_beta(state);
    float cherenkov_angle = (n_refr * beta_eff > 1.0f)
                            ? acosf(1.0f / (n_refr * beta_eff))
                            : -1.0f;
    // 11. metric_shift from W + local Phi
    float phi_local = compute_local_grav_potential(world_pos, state.bh_list, state.bh_count);
    float metric_shift = (W_mod * state.metric_shift_warp_coeff)
                       + sqrtf(1.0f + 2.0f * phi_local / (C_LIGHT*C_LIGHT)) - 1.0f;
    // 12. Return WarpFieldSample
    return {W_mod, grad_W, metric_shift, chaos, vorticity, ray_deflection, cherenkov_angle, ...};
}
```

This kernel is the hot path. Per spec budget: ≤ 4 ms at half-res 4K. Implementation must use shared-memory tile for RBF spatial-hash list cache to make this feasible (RBF eval is the dominant cost; ~20 exp() calls per sample).

### 4.6 Cherenkov math (NEW — closes 5D-F4 gap)

```
cos θ_c = 1 / (n · β)
```

Where:
- `n = 1 + W` (default; tunable via `n_coefficient` parameter)
- `β = v_app/c` for WARP regime; raw `tanh(ω)` for STL regime
- Cone visible when `n · β > 1`; undefined/inactive otherwise

Implementation lives in `libastra_nexus/src/cherenkov.cpp` (per §3.2 above). CUDA kernel (above, step 10) calls libastra at CPU-side calibration; CUDA does the per-pixel computation itself (mirroring the same formula in `__device__` code for speed).

### 4.7 Reflex stub (per spec §2.3.1 v0.129)

Simple PID controller; no NN training. Read chaos field amplitude; emit control vector:

```cpp
struct ControlVector {
    float nacelle_damping;   // [0, 1]
    float conformality;      // [0, 1]
    float emergency_dump;    // {0, 1}
};

ControlVector compute_reflex_stub(float chaos_mean, float chaos_max, float dt) {
    ControlVector c;
    float kp = 1.5f, ki = 0.3f, kd = 0.1f;  // tunable in BUILD_LOG.md
    float target = 0.3f;  // desired chaos amplitude
    float error = chaos_mean - target;
    static float integral = 0.0f;
    static float prev_error = 0.0f;
    integral += error * dt;
    float deriv = (error - prev_error) / dt;
    float u = kp * error + ki * integral + kd * deriv;
    prev_error = error;
    c.nacelle_damping = clamp(u, 0.0f, 1.0f);
    c.conformality = 1.0f - c.nacelle_damping;
    c.emergency_dump = (chaos_max > 0.95f) ? 1.0f : 0.0f;
    return c;
}
```

This is V0 stub. Real Reflex (TensorRT-inferred CNN+LSTM per spec §2.3.1) is Phase E1 UE5 work; out of scope for this testbed. Per spec §15.4 boundary: spec defines the contract, implementation chooses the substrate. Stub satisfies contract.

### 4.8 Auto-diff for ∇W via dual numbers (optimization)

Per TECHDIVE §3.8: computing W and ∇W in one pass via dual numbers saves ~5 ms/frame at 4K full-res. Implementation:

```cuda
struct DualScalar { float value; float3 dx; };

__device__ DualScalar exp_d(DualScalar x) {
    float e = __expf(x.value);
    return {e, {e * x.dx.x, e * x.dx.y, e * x.dx.z}};
}

// Use in RBF eval loop:
// gauss = exp_d({-r²/(2σ²), -(x-c)/σ²})  // closed-form ∇ of Gaussian RBF
// contrib = node.weight * gauss          // value + gradient propagate via overloaded ops
// W_dual.value += contrib.value; W_dual.dx += contrib.dx;
```

Save ~50% on exp() calls vs separate value + gradient passes. Implementation in `kernels/warp_field.cu`.

---

## Part 5: Project layout (full sandbox structure)

See `CLAUDE.md` §"What this folder will contain when complete" for the canonical structure. Summary:

```
C:\ASTRA-7\ASTRA_VISUALIZER\
├── CLAUDE.md, DESIGN_SPEC.md, README.md, BUILD_LOG.md, [BUILD_COMPLETE.md, BLOCKERS.md]
├── CMakeLists.txt
├── tools/             # build.bat, dev-shell.bat, golden_diff.cpp
├── libastra_nexus/    # math library (V0 hard requirement)
│   ├── include/astra_nexus/  # public headers
│   ├── src/                  # implementations
│   └── tests/                # doctest test suite
├── src/               # visualizer C++ (app/, renderer/, physics/, scenes/, validation/, ui/, data/, util/)
├── kernels/           # CUDA .cu/.cuh
├── shaders/           # GLSL .vert/.frag/.comp/.glsl
├── assets/            # hull, starfield, CFD, scenarios, reference_renders
├── tests/             # doctest visualizer-side tests
├── third_party/       # FetchContent-managed
├── docs/              # SCENES.md, VALIDATION.md, BUILD.md, KNOWN_ISSUES.md, CHANGELOG.md
├── build/             # CMake build dir
└── dist/              # final binaries + showcase PNGs
```

Module count target: ~40 C++ files + ~20 CUDA files + ~25 shader files + 12 scenario JSONs + libastra_nexus's ~15 files. Total estimated: **~10,000-12,000 LOC** for full visualizer; **~1,500 LOC** for libastra_nexus extraction.

---

## Part 6: The 12 visual test scenes

Each scene is a `cpp/h` pair in `src/scenes/` plus a JSON config in `assets/scenarios/`. Each scene exposes:

```cpp
class IScene {
public:
    virtual ~IScene() = default;
    virtual const char* name() const = 0;
    virtual void setup(GLContext&, PhysicsCore&) = 0;
    virtual void tick(float sim_dt_seconds) = 0;
    virtual void render(RenderContext&) = 0;
    virtual void render_ui(UIContext&) = 0;  // ImGui parameter widgets
    virtual void teardown() = 0;
    virtual std::vector<ScalarPixelAssertion> assertions() const = 0;
    virtual const char* golden_image_path() const = 0;
    virtual float canonical_timestamp_seconds() const = 0;  // when to capture for golden
};
```

The 12 scenes:

### S01 — REST baseline (sanity check)

**Spec basis:** §1.1 AstraCoord; §1.2 two-clock split; §3.3 regime state machine

**Initial state:** regime=REST, W=0, ship at origin, Sun at (0, +1AU, 0), Earth-like planet at (0, 0, +1 AU).

**Script:** none; static.

**Camera:** orbiting third-person around ship, ~50m away.

**Render:** hull mesh (procedural box if no OBJ yet) + Sun (yellow point + halo) + Earth (blue dot) + starfield (10K random).

**UI controls:** camera rotation, zoom.

**Assertions (≥3):**
1. Pixel at ship center renders hull color (≠ background)
2. Pixel near Earth shows expected color (within 20% tolerance)
3. UI overlay shows γ=1.000, dτ/dt=1.000 matching `libastra_nexus::Rapidity{{0,0,0}}.gamma()` and `dtau_dt_cosmic(0, 1.0, 1.0, false)` to 6 decimals

**Pass criteria:** all 3 PASS; visual baseline acceptable.

**Golden:** `assets/reference_renders/s01_t0_canonical.png` (1920×1080).

---

### S02 — STL_REL recede at β=0.5

**Spec basis:** §3.4 SR longitudinal Doppler; §3.7 rapidity

**Initial state:** regime=STL_REL, ζ⃗=(0,0,atanh(0.5))≈(0,0,0.5493), planet 1 AU behind in -z.

**Camera:** ship cockpit, rear view (-z).

**Render:** planet behind redshifted per `compute_z_kin(0.5*C_LIGHT)≈0.732`; stars aberration mild.

**UI controls:** β slider (override scenario default).

**Assertions (≥3):**
1. Pixel at planet shows R-channel > B-channel (redshifted; tolerance 0.05)
2. UI overlay γ=1.155 matches `Rapidity{{0,0,0.5493}}.gamma()` (within 0.001)
3. UI overlay z_kin ≈ 0.732 matches `compute_z_kin(0.5*C_LIGHT)` (within 0.005)

**Pass criteria:** all 3 PASS; visible color shift on planet.

**Golden:** `s02_t0_canonical.png`.

---

### S03 — STL_REL recede at β=0.9

**Spec basis:** same as S02 with stronger parameters

**Initial state:** ζ⃗=(0,0,atanh(0.9))≈(0,0,1.472), γ=2.294.

**Render:** dramatic redshift; forward starfield compression visible.

**Assertions (≥3):**
1. Planet pixel R-channel dominates (R>>G≈B; redshifted to near-IR; aesthetic test)
2. γ=2.294 matches libastra
3. z_kin matches `compute_z_kin(0.9*C_LIGHT)=√19-1≈3.359` within 0.01

**Golden:** `s03_t0_canonical.png`.

---

### S04 — Warp charge sequence

**Spec basis:** §6 step 4 smooth-min blend; §3.3 WARP_CHARGE → WARP_CRUISE transition

**Initial state:** regime=REST, W=0.

**Script:**
- t=0: regime → WARP_CHARGE (warp.phase = "charging")
- t=0..5s: W ramps linearly 0 → 1
- t=5s: regime → WARP_CRUISE; v_app=2c

**Camera:** orbiting; sees bubble form.

**Render:** bubble fades in as W ramps; CFD-RBF evaluated correctly; smooth-min blend visible at boundary.

**UI controls:** W slider (override script).

**Assertions (≥4):**
1. At t=0, pixel near ship is background color (no bubble)
2. At t=5s, pixel at canonical bubble-boundary radius shows expected W value (matches `eval_rbf_at()` from libastra to within 0.05)
3. Axial symmetry: pixels at (+x,0,0) and (-x,0,0) of ship show same W within 0.01
4. UI shows regime transition WARP_CHARGE → WARP_CRUISE at correct time

**Golden:** capture at t=5s.

---

### S05 — Warp cruise at v_app=2c (THE PAYOFF SCENE — orbit reversal)

**Spec basis:** §3.11 retarded-time observation; §10 "Retarded-time orbit reversal" validation row; original C++ test [astra_nexus.cpp:639-677](C:/ASTRA-7/proto/astra_nexus.cpp:639)

**Initial state:** regime=WARP_CRUISE, W=1, v_app=2c in +z, planet 1 ly behind in -z with Earth-like Kepler orbit (1-year period, ~Mercury inclination for visibility).

**Script:** none; coast at 2c forever.

**Camera:** ship cockpit, rear view (-z); planet visible.

**Render:**
- Bubble stable around ship
- Planet rendered at `Kepler(orbit, t_emit)` position
- t_emit decreases at rate `apparent_rate = -1.0` per sim-time second
- Trail mode (toggleable) shows decaying trail of where planet WAS rendered
- ImGui plot: x-axis = t_cosmic; y-axis = orbital phase (rendered vs predicted from libastra)

**UI controls:**
- v_app slider [-50c, +50c] (override default)
- Orbit period slider (1 day to 1 year)
- Trail mode toggle
- Numeric readout: t_emit, apparent_rate, dphase/dt

**Assertions (≥4):**
1. `compute_apparent_rate(2*C_LIGHT, R_WARP_CRUISE)` from libastra returns -1.0 ± 1e-9
2. Over 30 simulation seconds, rendered planet's orbital phase delta matches `-30 * 2π / period` (within 1% — i.e., orbit traversed in REVERSE)
3. The rendered orbital phase matches `orbit_phase(orbit, observable.t_emit)` from libastra to within 0.01 rad
4. At v_app=c exactly (sweep test): orbital phase is FROZEN (dphase/dt ≈ 0)

**Pass criteria:**
- All 4 assertions PASS mechanically
- **Operator personally watches the scene and CONFIRMS the orbit visually appears to run backward.** (Final human sign-off; required for v1.0 release.)

**Note:** This is THE scene that proves the spec's most distinctive physics claim. Budget extra time. The trail mode is critical — without it, instantaneous reverse motion is hard for the human eye to perceive. Trail makes it obvious.

**Golden:** capture at t=15s with trail enabled.

---

### S06 — Warp cruise at v_app=10c with Cherenkov cone (closes 5D-F4)

**Spec basis:** §6 step 10 + Appendix B (Cherenkov formula locked); §3.11

**Initial state:** regime=WARP_CRUISE, W=1, v_app=10c in +z, planet 1 ly behind.

**Render:**
- Orbit reverses at 9× speed (`apparent_rate = -9.000`)
- Cherenkov cone visible (forward-facing) with half-angle from `compute_cherenkov_angle(W=1.0, beta=10/c_norm, n_coef=1.0)`
- Cone tinted blue-cyan per spec
- Bubble dimmer than at 2c (everything redshifted)

**UI controls:**
- W slider (override; tests Cherenkov angle changes with W)
- Cone visibility toggle
- n_coefficient slider (live tuning)
- Numeric overlay: angle in degrees + rad + cos value

**Assertions (≥4):**
1. `compute_apparent_rate(10*C_LIGHT, R_WARP_CRUISE)` returns -9.000 ± 1e-9
2. **`compute_cherenkov_angle(W=1.0, beta=10/c_norm_visualizer, n_coef=1.0)` returns the angle that matches the rendered cone's drawn angle within 1°** (THE 5D-F4 GAP CLOSURE TEST)
3. At β→0 (sweep slider), cone disappears (cherenkov_angle returns -1.0; UI shows "Cherenkov inactive")
4. Cone narrows monotonically as W increases from 0.5 to 1.0 (sweep slider; assertion checks angle(W=0.5) > angle(W=1.0))

**Pass criteria:** all 4 PASS; **AND** the visible Cherenkov cone is "the right shape" per operator's eye. This is the 5D-F4 gap empirically closed.

**Golden:** `s06_t0_canonical.png`.

---

### S07 — Warp cruise at v_app=8000c (photon-source-history bound)

**Spec basis:** §3.11 photon-source-history bound; `ObservableState.beyond_photon_history` flag

**Initial state:** regime=WARP_CRUISE, W=1, v_app=8000c in +z, planet at -1 ly with `t_source_start = -1e9 seconds` (turned on 1 Gy before scenario start).

**Script:** ship pulls away at 8000c; planet observed.

**Render:** planet visible initially; as t_emit retreats, eventually `t_emit < t_source_start` → `beyond_photon_history = true` → planet DISAPPEARS (clean cut; no fade).

**Assertions (≥4):**
1. Before crossover, pixel at planet position has expected planet color
2. After crossover, pixel at planet position has background color (planet absent)
3. Transition is discrete: at frame N planet visible, frame N+1 absent — no intermediate fading
4. Crossover timing matches: `observe(...)` returns `beyond_photon_history=true` at the exact frame the visual disappears (within 1 frame)

**Pass criteria:** all 4 PASS; operator sees the abrupt disappearance.

**Why this matters:** Spec §3.11 explicitly says "the source is gone — not faded, not redshifted to extinction, gone, because no photon remains to be received." Most fictional warp shows fade. This scene proves the spec's distinct claim.

**Golden:** capture two frames — one before, one after.

---

### S08 — Warp + Gravity Well composition

**Spec basis:** §3.2 composition rule; §7.1 chaos coupling `α_eff = α_base·(1 + k·M·L²/r³)`; §7.4 Warp Exclusion Zone

**Initial state:** regime=WARP_CRUISE|GRAVITY_WELL (bitmask 0x28), W=0.8, ship at r=200·r_s of a 10·M_sun BH.

**Script:** ship gradually approaches BH (r ramps 200·r_s → 150·r_s over 30s).

**Render:** ship + bubble + BH (black disc); bubble distorts toward BH; chaos PDE α_eff scaling visible.

**UI controls:**
- BH mass slider [1, 1e8] M_sun
- BH distance slider [0, 1000] AU
- W slider

**Assertions (≥4):**
1. UI shows regime label "WARP_CRUISE | GRAVITY_WELL" with bitmask 0x28
2. Schwarzschild factor `√(1-r_s/r)` displayed matches `compute_grav_factor(bh_list, ship_pos)` from libastra to 6 decimals
3. α_eff displayed = α_base · (1 + k·M·L²/r³) — matches §7.1 formula
4. dτ/dt_cosmic gauge matches `dtau_dt_cosmic(W=0.8, grav=..., gamma=1.0, warp_active=true)` output

**Pass criteria:** all 4 PASS; bubble distortion visible.

**Golden:** capture at t=15s (mid-approach).

---

### S09 — Chaos instability + Reflex stabilizer

**Spec basis:** §7.1 Fisher-KPP; §2.3.1 Reflex Contract (NEW v0.129); §4.6 chaos field convergent re-init

**Initial state:** regime=WARP_CRUISE, W=0.95 (near max), no BH; Reflex stub initially OFF.

**Script:**
- t=0..5s: Reflex DISABLED; chaos grows; particles bloom
- t=5s: Reflex ENABLED; rapid damping over ~1s
- t=10..15s: operator slider injects chaos manually; Reflex re-damps

**Render:**
- 2D slice heatmap of chaos field (viridis colormap on χ ∈ [0, 1])
- Optional 3D volumetric chaos render
- Time-series plot of `max(χ)`, `mean(χ)`, `energy(∫χ²)` over last N frames
- Reflex control vector display (nacelle_damping, conformality, emergency_dump)

**UI controls:**
- α_base slider [1.0, 5.0]
- β (PDE damping coefficient) slider [1.0, 20.0]
- D (diffusion) slider [0.1, 2.0]
- Reflex ON/OFF toggle
- "Inject chaos at center" button (manual stimulus)
- Time step `dt` slider (CFL-bounded indicator displayed)
- Reset chaos field button

**Assertions (≥5):**
1. Field stays in [0, 1] throughout (no NaN, no overflow)
2. CFL stability: at dt = 1/60s with provisional D=0.8, field bounded
3. CFL violation (NEGATIVE test): at dt=2*CFL_limit, simulation visibly explodes (proves bound real)
4. BH coupling activates α_eff scaling: at M=10·M_sun, r=50·r_s, displayed α_eff matches `α_base · (1 + k·M·L²/r³)` per §7.1 formula
5. Re-init convergence: from baseline noise, after N=60 frames the field converges (max(|χ̇|) below threshold)
6. When Reflex enabled, max(χ) decreases monotonically over ~1s damping period (regression: check 5-frame moving average)
7. Emergency dump triggers visually when chaos exceeds 0.95 threshold (regime snap to STL; bubble collapses in 1 frame)

**Pass criteria:** assertions 1, 2, 4, 5, 6, 7 PASS; assertion 3 demonstrates failure mode visibly (ok if it crashes; that's the point of the negative test).

**Golden:** capture at t=8s (post-Reflex damping).

---

### S10 — Hubble horizon body

**Spec basis:** §3.12 cosmological expansion; `ObservableState.beyond_hubble_horizon` flag

**Initial state:** regime=REST, ship at origin, body at d = 1.2 · c/H₀ (beyond Hubble horizon).

**Script:** none; static.

**Render:** body rendered FROZEN (paused frame from horizon-crossing); color extremely redshifted; dimming over scenario time.

**Assertions (≥3):**
1. UI shows `beyond_hubble_horizon = true`
2. d_proper in Mpc matches `astra_distance(ship, body)` from libastra
3. z_cosmo matches `compute_z_cosmo(d) = H₀·d/c` from libastra to 6 decimals
4. Body pixel color is in the "extremely red" sector (R >> G ≈ B; tolerance check)

**Golden:** capture at t=0 (frozen) + t=30s (dimmed); two-frame comparison.

---

### S11 — Split-screen STL_REL vs WARP_CRUISE at same v_radial

**Spec basis:** §3.11 regime-dispatched apparent rate; §10 validation row "STL_REL formula was NOT 1/γ"

**Initial state:** TWO simulated ships; one in STL_REL at v=0.5c receding; one in WARP_CRUISE at v_app=0.5c receding; both observing the same planet.

**Render:** split-screen; left = STL ship rear view; right = WARP ship rear view. Same planet rendered with each ship's apparent_rate applied to its orbital phase.

**UI controls:** v_radial slider [-1.5c, +1.5c] (lets WARP go above c; STL clamps below c).

**Assertions (≥4):**
1. `compute_apparent_rate(0.5*C_LIGHT, R_STL_REL)` from libastra returns √(1/3) ≈ 0.5774 ± 1e-9
2. `compute_apparent_rate(0.5*C_LIGHT, R_WARP_CRUISE)` returns 0.5 ± 1e-9
3. LEFT (STL) planet's orbital phase advances at 0.5774× speed (sample over 10s; check ratio)
4. RIGHT (WARP) planet's orbital phase advances at 0.500× speed
5. The ratio (STL_rate / WARP_rate) at v=0.5c = 0.5774/0.5 ≈ 1.155 — regime-distinction is real
6. At v > c (sweep), WARP planet reverses; STL panel shows "regime invalid: β ≥ 1"

**Pass criteria:** all PASS; operator sees the regime distinction is real, not a math artifact.

**Golden:** capture at canonical v=0.5c.

---

### S12 — Eye-ear decoupling at warp egress

**Spec basis:** §6.3 + §8.3 endogenous/exogenous principle; the "eye-ear decoupling" as designed feature

**Initial state:** regime=WARP_CRUISE at v_app=2c, planet 1 ly behind orbiting in reverse (S05's state).

**Script:**
- t=0..10s: WARP_CRUISE; visual reversed (S05 behavior); UI shows "AUDIO: warp drone 247 Hz" (display only — no real audio)
- t=10s: warp.disengage(emergency); regime → STL_REL → REST over ~3s; bubble collapses
- t=10..15s: visual continues reversed for some seconds (eye sees photons from earlier reverse-time samples); UI audio frequency display jumps immediately to "warp shutdown sound" then "silence" (frequency display follows current state, not retarded)
- t=15..30s: visual gradually catches up with audio as `t_emit` re-syncs with `t_cosmic`

**Render:** rear view of planet (S05-style) + UI dual time display.

**UI controls:**
- Disengage warp button
- Audio frequency display (numerical only; mock)
- t_cosmic display vs t_emit display (the gap shrinks over time)

**Assertions (≥3):**
1. During warp, UI shows audio_t = t_cosmic, visual_t = t_emit, with t_emit < t_cosmic by `ship-distance/c`
2. At t=10s, audio_t jumps to new value (drone → shutdown immediate); visual_t continues reverse-walking
3. Over warp-shutdown period, the audio_t - visual_t gap shrinks to zero asymptotically
4. The numerical gap matches `t_cosmic - t_emit` from libastra `observe()` to 6 decimals throughout

**Pass criteria:** all PASS; operator sees the eye-ear mismatch is the spec's intended feature.

**Golden:** capture at t=10.5s (mid-decoupling — visual reversed, audio current).

---

## Part 7: Three-layer validation methodology

### 7.1 Layer 1 — Scalar pixel assertions

```cpp
// validation/scalar_pixel_assertion.h

#pragma once
#include <string>
#include <glm/vec2.hpp>

struct ScalarPixelAssertion {
    std::string name;             // human-readable
    glm::ivec2 framebuffer_coord; // (x, y) in framebuffer
    int channel;                  // 0=R, 1=G, 2=B, 3=A; or -1 for any
    float expected_value;         // canonical math output (from libastra)
    float tolerance;              // pass if |measured - expected| < tolerance
                                  // default: max(1% of expected, 0.01)
    std::string spec_section;     // for traceability, e.g., "§3.11 retarded-time"
    std::string libastra_call;    // e.g., "compute_apparent_rate(2*C_LIGHT, R_WARP_CRUISE)"
};

struct AssertionResult {
    ScalarPixelAssertion assertion;
    float measured_value;
    float diff_abs;
    float diff_rel;
    bool passed;
};
```

```cpp
// validation/pixel_sampler.h

class PixelSampler {
public:
    explicit PixelSampler(GLuint framebuffer);
    std::vector<AssertionResult> sample_and_compare(
        const IScene& scene,
        const std::vector<ScalarPixelAssertion>& assertions);
private:
    GLuint framebuffer_;
    std::vector<float> readback_buffer_;
};
```

**Default tolerance:** `max(0.01 * |expected_value|, 0.01)`. Tighter for spec-locked formulas (e.g., 1e-6 for apparent_rate); looser for tone-mapped colors (5-10%).

### 7.2 Layer 2 — Heatmap diff assertions (vs golden PNGs)

```cpp
// validation/heatmap_diff_assertion.h

struct HeatmapDiffAssertion {
    std::string golden_path;     // "assets/reference_renders/s01_t0.png"
    float max_mean_diff;         // default 0.01 (1% mean per-pixel diff)
    float max_pixel_diff;        // default 0.10 (no pixel may differ by >10%)
};

struct HeatmapDiffResult {
    HeatmapDiffAssertion assertion;
    float measured_mean_diff;
    float measured_max_diff;
    bool passed;
    std::string diff_image_path; // "ci_results/s01_diff.png" if failed
};
```

**Goldens regeneration policy** — mirrors `proto/textverse/tuning/scope.yaml` `required_invariants` discipline:

- Goldens are CANON-LOCKED after operator approval.
- `--regenerate-goldens` flag exists.
- Goldens may be regenerated only with operator sign-off via commit message: `[GOLDENS-SIGNOFF: <reason>]`.
- CI fails if goldens regenerated without sign-off marker.

### 7.3 Layer 3 — Side-by-side numeric overlay (real-time operator validation)

Per scene, ImGui panel in the right-side state display:

```
┌─────────────────────────────────────┐
│ S06 — Warp Cruise 10c + Cherenkov   │
├─────────────────────────────────────┤
│ Rendered apparent_rate:   -9.0012   │
│ libastra apparent_rate:   -9.0000   │
│ Diff:                      0.0012   │
│ Tolerance:                 1e-6     │
│ ► PASS (green)                      │
├─────────────────────────────────────┤
│ Rendered cherenkov_angle: 84.27°    │
│ libastra cherenkov_angle: 84.26°    │
│ Diff:                      0.01°    │
│ Tolerance:                 1.0°     │
│ ► PASS (green)                      │
└─────────────────────────────────────┘
```

When any assertion fails, the overlay turns red and the top-bar shows "❌ S06: 1 assertion failing".

### 7.4 The validation report (JSON output for CI)

After headless run, write structured JSON to `<output_dir>/report.json`:

```json
{
  "version": "0.1.0",
  "build_commit": "<git hash if available; else 'unversioned'>",
  "ran_at": "2026-05-20T10:00:00Z",
  "platform": "Windows 11 / RTX 4070 Ti SUPER / CUDA 13.1 / GL 4.6 / MSVC 14.43",
  "libastra_nexus_assertion_count": 69,
  "libastra_nexus_assertion_pass_count": 69,
  "scenes": [
    {
      "name": "S01_RestBaseline",
      "frame_ms": 14.2,
      "scenario_path": "assets/scenarios/s01_rest_baseline.json",
      "canonical_timestamp_seconds": 0.0,
      "assertions": [
        {
          "name": "ship_center_pixel_hull",
          "spec_section": "§1.3",
          "libastra_call": "n/a (visual baseline)",
          "expected": 0.45,
          "measured": 0.452,
          "diff_abs": 0.002,
          "diff_rel": 0.0044,
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
        "passed": true,
        "diff_image": null
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

CI gate: exit code 0 iff `summary.scenes_failed == 0` AND `summary.assertions_passed == assertions_total`.

---

## Part 8: CLI design

```
astra_visualizer.exe                                  # interactive, scene chooser
astra_visualizer.exe --scene=S05_WarpCruise2c         # interactive, jump to scene
astra_visualizer.exe --headless --scene=all --output=ci_results/
astra_visualizer.exe --headless --scene=S05_WarpCruise2c --output=smoke/
astra_visualizer.exe --regenerate-goldens --scene=all   # operator-sign-off action
astra_visualizer.exe --record-png-sequence --scene=S05 --duration=30 --output=seq/
astra_visualizer.exe --version
astra_visualizer.exe --help

Scene name format: S<NN>_<short_name> (e.g., S01_RestBaseline, S05_WarpCruise2c).
Alias: --scene=5 also works (numeric shorthand).
```

`--version` output:

```
astra_visualizer v0.1.0
linked: libastra_nexus v0.129 (69 assertions)
built:  2026-05-20T10:00:00Z
toolchain: MSVC 19.43 + CUDA 13.1 + OpenGL 4.6
```

---

## Part 9: UI layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ [Scene: S05 Warp Cruise 2c ▼] [Reset] [Pause] 60 FPS / 16.2 ms              │  Top bar
├──────────┬────────────────────────────────────────────────┬─────────────────┤
│          │                                                │                 │
│  PARAM   │                                                │  STATE +        │
│  PANEL   │            VIEWPORT (3D render)                │  VALIDATION     │
│          │                                                │                 │
│ Scene:   │                                                │ Regime:         │
│ S05 ▼    │                                                │  WARP_CRUISE    │
│          │                                                │ γ: 1.000        │
│ W:       │                                                │ W: 1.00         │
│ ▓▓▓▓░ 1.0│                                                │ dτ/dt: 0.500    │
│          │                                                │                 │
│ v_app:   │                                                │ apparent_rate:  │
│ ▓▓░░░ 2c │                                                │  rendered:      │
│          │                                                │   -1.0012       │
│ Reflex:  │                                                │  libastra:      │
│ [ ON ]   │                                                │   -1.0000       │
│          │                                                │  diff: 0.0012   │
│ Camera:  │                                                │  ► PASS (green) │
│ ◉ Free   │                                                │                 │
│ ○ Fixed  │                                                │ Per-pass timing:│
│          │                                                │  Chaos PDE:0.8ms│
│ [F12]    │                                                │  Warp eval:1.5ms│
│ Screen-  │                                                │  Lensing:  0.6ms│
│ shot     │                                                │  ... (live)     │
├──────────┴────────────────────────────────────────────────┴─────────────────┤
│ Console: scenario loaded · Reflex enabled · t=15.3s sim time                │  Status bar
└─────────────────────────────────────────────────────────────────────────────┘
```

### 9.1 Hotkeys

| Key | Action |
|---|---|
| WASD | Camera movement (free mode) |
| Q/E | Camera up/down |
| Mouse drag | Camera look |
| 1-9 | Select scenarios 1-9 |
| Shift+1, Shift+2, Shift+3 | Scenarios 10, 11, 12 |
| Space | Pause / resume |
| R | Reset current scenario |
| F1 | Toggle help overlay |
| F2 | Toggle parameter panel |
| F3 | Toggle state display |
| F4 | Toggle debug overlays (∇W arrows, RBF nodes) |
| F5 | Hot-reload shaders (dev only) |
| F11 | Toggle fullscreen |
| F12 | Screenshot (PNG + JSON state dump) |
| Esc | Quit |

---

## Part 10: Performance targets

### 10.1 Frame budget at 1080p / 60 FPS (16.67 ms)

| Stage | Budget (ms) |
|---|---|
| CPU: physics driver tick (libastra calls) | 0.5 |
| GPU: chaos PDE step (RK2) | 1.5 |
| GPU: warp SVT populate (RBF + ∇W via dual-numbers) | 1.5 |
| GPU: volume ray-march (warp + chaos) | 3-4 |
| GPU: geometric lensing post | 1.5 |
| GPU: starfield render | 1.0 |
| GPU: Cherenkov cone + trail | 0.5 |
| GPU: hull mesh + UI + post-process | 3.0 |
| Reserve (jitter absorption) | ~3 |

### 10.2 Hardware-tier targets

| Hardware | Resolution | FPS target | Notes |
|---|---|---|---|
| RTX 5090 | 1080p | 120 | upper-tier |
| RTX 4090 | 1440p | 60 | recommended |
| RTX 4070 / 4070 Ti SUPER | 1080p | 60 | minimum acceptable; reference target |
| RTX 3060 | 1080p | 30 | low-end fallback; not all scenes guaranteed 60 FPS |

### 10.3 VRAM budget at RTX 4070 target

| Item | Size |
|---|---|
| Hull SDF + damage map | ~50 MB |
| CFD-RBF + spatial hash | ~250 KB |
| Chaos field (2× 128³ × float) | 16 MB |
| Warp field volume | ~8 MB |
| Reflex stub state | <1 KB |
| GL render targets (color + depth) | ~50 MB |
| Total physics + render | ~125 MB |

Comfortable on 12GB minimum hardware.

---

## Part 11: Phased implementation roadmap (14-16 weeks)

### V0 — Scaffolding + libastra_nexus extraction (weeks 1-2) — CRITICAL PATH

- Set up CMake project (`CMakeLists.txt` with FetchContent for GLFW, GLAD, ImGui, GLM, stb, nlohmann_json, doctest)
- GLFW window opens at 1280×720; OpenGL 4.6 context valid via glad
- ImGui renders "Hello, ASTRA-7 Visualizer" in window
- CUDA toolkit detected; trivial CUDA kernel runs; CUDA-GL interop sanity test
- CLI parser handles `--help`, `--scene=`, `--headless`, `--output=`, `--version`, `--regenerate-goldens`
- Headless mode framework (no scenes yet; empty JSON report)
- **EXTRACT `libastra_nexus`** into the sandbox per §3 of this spec
- All 66 original + ≥3 new Cherenkov assertions pass via `libastra_nexus_test.exe`
- Builds on Windows + Linux from same CMakeLists.txt

**Gate:** all of the above; `libastra_nexus_test.exe` reports `[PASS] 69+ of 69+`; `astra_visualizer.exe --help` works.

### V1 — Renderer foundations + S01 + S04 (weeks 3-4)

- `renderer/cuda_gl_interop` shared 3D textures working
- Compute shader + GLSL `raymarch.frag` evaluates RBF + renders volumetric bubble
- `physics/rbf_network` loads synthetic 50-200 node test RBF from JSON (`assets/cfd/warp_cfd_rbf_synthetic_v1.json`)
- `physics/physics_core` facade over libastra_nexus
- Scene S01 (REST baseline) with hull + starfield + planet
- Scene S04 (Warp Charge) extends S01 with bubble formation animation
- PixelSampler implementation; 6-8 assertions across both scenes
- Three-layer validation overlay (Layer 3 numeric display rendering)

**Gate:** S01 + S04 render at 60+ FPS on RTX 4070; all assertions PASS in interactive AND headless mode; goldens captured.

### V2 — Doppler + starfield (weeks 5-6)

- Scene S02 (STL_REL β=0.5) + Scene S03 (STL_REL β=0.9)
- Starfield Doppler shift in fragment shader (per-star color shift via blackbody approximation, Tanner Helland fit)
- Aberration math in vertex shader

**Gate:** S02 + S03 render correctly; visible color shifts; pixel assertions match libastra-computed z_kin values.

### V3 — Cherenkov + lensing (weeks 7-8) — CLOSES 5D-F4 GAP

- Scene S06 (Warp Cruise 10c + Cherenkov)
- Cherenkov cone mesh + θ_c computation via libastra's `compute_cherenkov_angle()`
- Geometric lensing post-pass; `lensing.frag` deflects ray direction by ∇W; samples background skybox
- Scene supports lensing sweep via `α_lens` slider

**Gate:** S06 renders; Cherenkov cone visible with correct angle (validated by Layer 1 + Layer 3); lensing visible around bubble; all assertions PASS; the libastra Cherenkov assertions are tracked as the 5D-F4 closure.

### V4 — THE PAYOFF: S05 + S07 (weeks 9-11)

- `kernels/observation_calc.cu`: per-body Newton iteration for t_emit (mirrors libastra `observe()` math)
- `renderer/retarded_body`: per-instance Kepler-at-t_emit rendering with z_total color shift
- Scene S05 (Warp Cruise 2c — orbit reversal): trail mode; orbital phase plot
- Scene S07 (Photon-source-history bound): clean source disappearance
- Numeric overlay shows live t_emit, apparent_rate, beyond_photon_history flag

**Gate:** S05 + S07 render correctly. **Operator personally watches S05 and CONFIRMS** the orbit visually appears to run backward at v_apparent = 2c. The "you have to see it to believe it" payoff. Operator sign-off required.

### V5 — Chaos + Reflex + composition (weeks 12-13)

- `kernels/chaos_pde.cu`: RK2 Fisher-KPP solver; double-buffered surface objects
- 2D slice + 3D volumetric chaos visualization
- `physics/reflex_stub` + `kernels/reflex_stub.cu`: PID controller (chaos amplitude → control vector)
- Scene S09 (Chaos Instability + Reflex)
- Scene S08 (Warp + Gravity Well) composition

**Gate:** S08 + S09 work; chaos PDE stable; Reflex feedback visible; emergency dump triggers correctly.

### V6 — Hubble + split-screen + eye-ear (weeks 14-15)

- Scene S10 (Hubble horizon): frozen + dim body rendering
- Scene S11 (Split-screen STL vs WARP at v=0.5c): dual-viewport render
- Scene S12 (Eye-ear decoupling): warp egress with UI audio-frequency display
- All 12 scenes complete

**Gate:** All 12 scenes render correctly; all ≥36 assertions PASS; goldens captured; headless mode runs all 12 in < 2 minutes.

### V7 — CI + polish + documentation (week 16)

- Golden PNG references generated for each scene at canonical configurations
- Headless mode hardened; JSON test report finalized
- Performance overlay (per-pass GPU timing via cuEventRecord)
- Documentation: `README.md`, `docs/SCENES.md`, `docs/VALIDATION.md`, `docs/BUILD.md`, `docs/KNOWN_ISSUES.md`, `docs/CHANGELOG.md`
- Release build: `dist/astra_visualizer.exe` for Windows 11 + Linux binary
- `BUILD_COMPLETE.md` filed at sandbox root

**Gate:** CI runs visualizer; reports PASS for all 12 scenes; gates green. Release-quality binary.

**Total: 16 weeks (~4 months)** for one agent + Claude pair-programming; 6 months solo with operator review cycles.

---

## Part 12: Bake + assets

### 12.1 Hull (placeholder)

A simple low-poly hull OBJ (~10K tris). Either:
- (a) Procedurally generated (box + cylinder composite forming a stylized ship)
- (b) Loaded from `assets/hull/astra7_lowpoly.obj` (the agent generates a placeholder; operator can swap later)

V1 ships placeholder. Real hull (per `memory/hull_design_v0.md` — 280m × 78m × 22m blended-wing-body) comes from UE5 Phase E0 work; not this testbed's concern.

### 12.2 CFD-RBF (synthetic)

`assets/cfd/warp_cfd_rbf_synthetic_v1.json`:

```json
{
  "version": 1,
  "comment": "Synthetic Alcubierre-style RBF network; 50-200 nodes; for testbed only.",
  "nodes": [
    {"center": [0.0, 0.0, 0.0], "sigma": 30.0, "weight": 0.8},
    {"center": [40.0, 0.0, 0.0], "sigma": 15.0, "weight": 0.6},
    // ... ~50-200 nodes hand-placed (or procedural) approximating a bubble shape
  ],
  "spatial_hash": {
    "voxel_size": 32.0,
    "offsets": [0, 5, 12, ...],   // per-voxel start index into indices[]
    "counts":  [5, 7, 4, ...],    // per-voxel RBF count
    "indices": [3, 17, 28, ...]   // RBF node indices
  }
}
```

The agent SYNTHESIZES this at first run (analytic Alcubierre approximation; no OpenFOAM dep needed). `data/cfd_synthesizer.cpp` does this.

Real CFD-baked RBF (OpenFOAM → custom fitter) is deferred to TECHDIVE §10.1; out of testbed scope.

### 12.3 Starfield (synthetic)

`assets/starfield/starfield_10k.bin`:
```
struct Star {
    glm::vec3 position;     // AstraCoord local frame (m or ly; pick + document)
    float magnitude;        // visual magnitude
    float temperature;      // K, for blackbody color
};
```

10K random stars in a spherical distribution at distances 4 ly to 100 ly. Generated at first run if file absent.

### 12.4 Goldens

`assets/reference_renders/s##_t##_canonical.png` for each scene at canonical timestamp. Generated by `--regenerate-goldens --scene=all` ONCE after operator approves visuals. Locked thereafter; regeneration requires operator sign-off.

---

## Part 13: Build instructions (full)

### 13.1 Prerequisites (operator's machine has these per CLAUDE.md cold-start)

- Visual Studio 2022 17.8+ with MSVC 14.43 toolset
- CUDA Toolkit 12.4+ (CUDA 13.1 ideal; matches Buddhabrot reference)
- CMake 3.27+ (VS-bundled at `Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe` is fine)
- Git (for FetchContent or submodule init)
- NVIDIA GPU with compute capability ≥ 8.9 (RTX 40-series Ada or newer)

### 13.2 Windows 11 build

```bat
:: From "x64 Native Tools Command Prompt for VS 2022"
cd /d C:\ASTRA-7\ASTRA_VISUALIZER

:: Configure
cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release

:: Build
cmake --build build --config Release

:: Run
.\build\astra_visualizer.exe
```

### 13.3 Linux x86_64 build (secondary)

```bash
cd /mnt/c/ASTRA-7/ASTRA_VISUALIZER       # WSL2; or native Linux clone
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build
./build/astra_visualizer
```

### 13.4 Smoke tests

```bat
:: Verify libastra extracted + working
.\build\libastra_nexus_test.exe
:: Expected: [PASS] 69 of 69 (or higher)

:: Verify visualizer version
.\build\astra_visualizer.exe --version
:: Expected: astra_visualizer v0.1.0; linked: libastra_nexus v0.129 (69 assertions)

:: Verify headless mode
.\build\astra_visualizer.exe --headless --scene=S01_RestBaseline --output=smoke\
:: Expected: smoke\s01.png exists; smoke\report.json shows passed=true

:: Run full validation suite
.\build\astra_visualizer.exe --headless --scene=all --output=ci_results\
:: Expected: 12 PNGs + report.json; exit 0 iff all PASS
```

### 13.5 CMakeLists.txt template (starting point)

```cmake
cmake_minimum_required(VERSION 3.27)

# Target archs: RTX 40 (Ada, sm_89), Hopper (sm_90), RTX 50 (Blackwell, sm_120)
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 89 90 120 CACHE STRING "")
endif()

project(astra_visualizer
    VERSION 0.1.0
    DESCRIPTION "ASTRA-7 Visual Physics Testbed"
    LANGUAGES C CXX CUDA)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Static linkage so .exe needs no DLL alongside (CUDA runtime, MSVC runtime)
set(CMAKE_CUDA_RUNTIME_LIBRARY Static)
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

find_package(CUDAToolkit REQUIRED)

add_compile_definitions(_CRT_SECURE_NO_WARNINGS NOMINMAX)

include(FetchContent)
set(FETCHCONTENT_QUIET FALSE)

# ---------- GLFW ----------
FetchContent_Declare(glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    GIT_TAG 3.4
    GIT_SHALLOW TRUE)
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(glfw)

# ---------- GLAD (GL 4.6 core) ----------
FetchContent_Declare(glad
    GIT_REPOSITORY https://github.com/Dav1dde/glad.git
    GIT_TAG v2.0.6
    GIT_SHALLOW TRUE
    SOURCE_SUBDIR cmake)
FetchContent_MakeAvailable(glad)
glad_add_library(glad_gl_core_46 REPRODUCIBLE API gl:core=4.6)

# ---------- Dear ImGui ----------
FetchContent_Declare(imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG v1.91.5
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(imgui)
add_library(imgui STATIC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_demo.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp)
target_include_directories(imgui PUBLIC
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends)
target_link_libraries(imgui PUBLIC glfw)

# ---------- GLM (header-only) ----------
FetchContent_Declare(glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.1
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(glm)

# ---------- stb_image_write (single-header) ----------
FetchContent_Declare(stb
    GIT_REPOSITORY https://github.com/nothings/stb.git
    GIT_TAG master
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(stb)
add_library(stb_image_write INTERFACE)
target_include_directories(stb_image_write INTERFACE ${stb_SOURCE_DIR})

# ---------- nlohmann/json ----------
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
    GIT_SHALLOW TRUE)
set(JSON_BuildTests OFF CACHE INTERNAL "")
FetchContent_MakeAvailable(json)

# ---------- doctest ----------
FetchContent_Declare(doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG v2.4.11
    GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(doctest)

# ---------- libastra_nexus (the math library) ----------
add_subdirectory(libastra_nexus)

# ---------- visualizer executable ----------
file(GLOB_RECURSE VIS_SOURCES_CPP CONFIGURE_DEPENDS src/*.cpp)
file(GLOB_RECURSE VIS_SOURCES_CU  CONFIGURE_DEPENDS kernels/*.cu)
add_executable(astra_visualizer ${VIS_SOURCES_CPP} ${VIS_SOURCES_CU})

target_include_directories(astra_visualizer PRIVATE
    src
    kernels
    ${CUDAToolkit_INCLUDE_DIRS}
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends)

target_link_libraries(astra_visualizer PRIVATE
    astra_nexus
    glfw
    glad_gl_core_46
    imgui
    glm::glm
    stb_image_write
    nlohmann_json::nlohmann_json
    CUDA::cudart_static)

# Per-language compile flags (per Buddhabrot pattern: nvcc + -Xcompiler= forwarding)
target_compile_options(astra_visualizer PRIVATE
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:MSVC>>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<COMPILE_LANGUAGE:CUDA>:--use_fast_math
                               -Xcompiler=/W3,/MP,/utf-8,/Zc:preprocessor>)

set_target_properties(astra_visualizer PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON)

# Copy shaders next to .exe at build time
add_custom_command(TARGET astra_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/shaders
        $<TARGET_FILE_DIR:astra_visualizer>/shaders)

# Copy assets next to .exe at build time
add_custom_command(TARGET astra_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/assets
        $<TARGET_FILE_DIR:astra_visualizer>/assets)
```

(Pattern lifted directly from the Buddhabrot_CUDA CMakeLists.txt — it works on the operator's machine.)

---

## Part 14: Cross-references and traceability

| Spec section | Where it appears in this testbed | Validation method |
|---|---|---|
| §1.1 AstraCoord | `libastra_nexus/coord.h` + S01 sanity render | Layer 1 pixel + numeric overlay |
| §1.2 two-clock split | UI state display in every scene | Layer 3 overlay |
| §1.3 hull SDF dual-binding | Adapted for OpenGL via `cuda_gl_interop` | S04 (visual) + libastra tests |
| §2.3.1 Reflex Contract (v0.129) | `physics/reflex_stub` + S09 | Behavioral assertion in S09 |
| §3.2 composition rule | `libastra_nexus/composition.h` + UI gauge | Layer 1 + Layer 3 |
| §3.3 regime state machine | All scenes use it | Regime label in state display |
| §3.4 four optical effects | S02, S03, S05, S06, S10 visualizations | Per-scene pixel assertions |
| §3.7 rapidity ζ⃗ | `libastra_nexus/rapidity.h` | libastra tests |
| §3.11 retarded-time observation | S05 (canonical) + S07 (edge case) | THE central validation |
| §3.12 cosmological expansion | S10 (Hubble horizon) | Layer 1 + Layer 3 |
| §4.6.1 EventStream Primitive (v0.129) | Not directly visualized (data structure) | Out of testbed scope |
| §6 Unified Sampler 12 steps | `kernels/warp_field.cu` 12-step pipeline | S04, S05, S06 visuals |
| §6.3 Observation Calculator | `kernels/observation_calc.cu` + libastra `observe()` | S05, S07, S10 assertions |
| §6.3.1 Somatic Aggregator (v0.129) | Not visualized (LLM input bundle) | Out of testbed scope |
| §6 step 10 Cherenkov | `libastra_nexus/cherenkov.h` (NEW) + S06 | **5D-F4 GAP CLOSURE** |
| §7.1 chaos PDE | `kernels/chaos_pde.cu` + S09 | Layer 1 + behavioral |
| §7.4 Warp Exclusion Zone | S08 (visible at low r) | Behavioral |
| §8.1 DX12-CUDA shared resource | Adapted for OpenGL: `cuda_gl_interop` | Same pattern; OpenGL substrate |
| §8.3 audio endogenous principle | S12 (mock audio UI) | Conceptual visualization |
| §15.6 calculator-bound LLM agency | N/A (no LLMs in testbed) | Out of scope |
| §15.7 dual-implementation | Testbed IS implementation #1 of visual side | This whole project |
| §15.8 Triple-rig methodology | Testbed IS rig 3 | Project positioning |
| §15.10 Cross-integration audit cadence (v0.129) | KNOWN_ISSUES.md feeds back | Per-finding logging |

---

## Part 15: Closing — what makes this testbed canonical

This visualizer is the **engine-agnostic ground truth** between the math (`libastra_nexus`) and the eventual UE5 rendering. It validates the visual physics claims of v0.129 without depending on UE5's complexity. It closes the Cherenkov gap at the math layer. It produces canonical reference images that UE5's rendering must match.

Per spec §15.8 + DISCOVERY_3B's U3: this testbed IS **rig 3** (engine-side rendering verification). The spec called for it but didn't have a concrete implementation path. This testbed runs it on bare OpenGL. When v0.130 is drafted, rig 3 can be cited as operational, not deferred.

Per spec §15.4: this testbed produces findings the math-only assertion suite cannot. Every empirical visual finding (α_lens tuning, n(W) tuning, warp wake visibility, etc.) lands in `docs/KNOWN_ISSUES.md` for operator review. These are the v0.130 spec-revision candidates.

Per spec §15.7 Five Shared Surfaces: this testbed implements Surface 2 (Physics envelope) at the visual level. UE5 will implement the same surface differently; both must agree. Goldens from this testbed become UE5's reference.

The math is locked. The visual claims are testable. The sandbox is bounded. The autonomous loop is established (Buddhabrot_CUDA pattern). The Cherenkov gap is closed in the same PR. The operator personally signs off on the orbit reversal scene.

Build it. Render it. Validate it. Watch S05. File BUILD_COMPLETE.md. The visual physics of v0.129 becomes empirically demonstrated.

The black is the inside. The Buddha is the density. The orbit running backward at 2c is the spec made visible.

---

**Operator:** Bo Chen — Arlington, Texas
**Sandbox:** `C:\ASTRA-7\ASTRA_VISUALIZER\`
**Predecessors:** `C:\ASTRA-7\PROPOSAL_2026-05-16_VISUAL_PHYSICS_TESTBED.md`, `C:\ASTRA-7\ASTRA_VISUALIZER_PLAN_2026-05-16.md`, `C:\ASTRA-7\ASTRA_VISUALIZER_PLAN_2026-05-16_V2.md`
**Reference autonomous-build artifact:** `C:\Buddhabrot_CUDA\` (same CLAUDE.md + DESIGN_SPEC.md + BUILD_LOG.md pattern; proven on operator's hardware)

— DESIGN_SPEC.md, 2026-05-16 —
