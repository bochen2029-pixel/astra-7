# ASTRA-7 Visualizer — Implementation Plan v2 FINAL (Polish Pass)

**Date:** 2026-05-16
**Status:** Polish-pass synthesis. Integrates insights from `PROPOSAL_2026-05-16_VISUAL_PHYSICS_TESTBED.md` into `ASTRA_VISUALIZER_PLAN_2026-05-16.md`.
**Author:** Claude Opus 4.7 (1M context window)
**Filename note:** A `ASTRA_VISUALIZER_PLAN_2026-05-16_v2.md` already exists from a parallel session that did its own integration; this file is the alternative polish pass with a slightly different emphasis. Operator chooses which version to keep.
**Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md` (tentative draft); `proto/astra_nexus.cpp` (1009 lines, 66 assertions after Tier 1A+1B closure)
**Target reader:** Another coding agent who picks this up cold and implements it

---

## 0. What this polish pass adds beyond v1

I read `PROPOSAL_2026-05-16_VISUAL_PHYSICS_TESTBED.md` carefully and identified
**eight insights** worth integrating into my v1, plus **six elements of v1
worth preserving**. This v2 is the integration.

### What I integrated from the sibling proposal

| # | Insight | Where it lands in v2 |
|---|---|---|
| 1 | **Five-finding-class taxonomy** for why the testbed exists epistemically | New §2 (replaces v1's brief "deeper structural value" framing in §0) |
| 2 | **S12 Eye-Ear Decoupling at warp egress** as 12th scene | §6.12 (was: 11 scenes total) |
| 3 | **Hubble-horizon as separate scene** from photon-source-history | §6.10 split from §6.07 (was conflated in v1) |
| 4 | **Risk Assessment** table (technical / scope / validation) | New §11 |
| 5 | **Predicted §15.4 spec revision candidates** the testbed will surface | New §12 |
| 6 | **Per-pass GPU budget at 1080p on RTX 4070** (not just 5090) | §9.2 (more concrete than v1's 5090-only numbers) |
| 7 | **`WarpFieldSample` shared header** for testbed + future UE5 reuse | §4.2 step 3 |
| 8 | **Warp wake (Scene 9 in v1) framed as §15.4 finding candidate** | §6.5 / §13 explicit framing |

### What I kept from my v1

| # | Element | Why preserved |
|---|---|---|
| 1 | **Three-layer validation methodology** (pixel assertion + heatmap diff + side-by-side numeric overlay) | Stronger than sibling's golden-screenshot-only framing |
| 2 | **Dual-mode interactive/headless with explicit CLI flags** | Clean CI integration path |
| 3 | **`libastra_nexus.lib` extraction with full file structure** | Architectural foundation; both versions agree on this |
| 4 | **"Deeper structural value" framing** (rig 3 per §15.8; de-risks UE5; publishable artifact) | Strong methodology positioning |
| 5 | **Coding-agent handoff brief** with 14 specific things to know | Onboarding clarity for the next coding agent |
| 6 | **Per-scene specific pixel assertions with concrete values** | Mechanical validation, not narrative |

### Reconciled differences

| Element | v1 (mine) | Sibling proposal | v2 reconciled |
|---|---|---|---|
| Effort estimate | 18 weeks | 38 days (5.5 weeks) | **7-9 weeks** (sibling too aggressive; v1 too thin) |
| Phase ordering | Interop in V0 alongside scaffolding | Math bridge V3, interop V4 | **Math bridge V2 → interop V3 → scenes V4+** (verify canon math before plumbing pixels) |
| Scene count | 11 | 12 (added eye-ear) | **12** (eye-ear is genuinely novel; book-canon-aligned) |
| Calendar | Solo dev cycles | Single agent + LLM pair | **7-9 weeks agent + 25-50% operator review** |

---

## 1. Why this exists

`proto/astra_nexus.exe` proves the math works at the **mathematical level**.
66 C++ assertions verify AstraCoord renormalization, 3-vector rapidity math
with γ-clamp at 10⁷, composition rule across regimes, regime-dispatched
apparent rate, Kepler-at-t_emit orbit reversal at v_app > c,
photon-source-history + Hubble horizon flags, cross-substrate stdio.

**It does not validate that the math MAPS TO THE INTENDED VISUAL PHENOMENA.**

The spec describes visible phenomena with mathematical bodies:

- A warp bubble whose metric W(x,t) is volumetrically renderable
- A wake trail behind the moving bubble (**NOT yet in spec; §15.4 candidate**)
- A Cherenkov cone with `cos θ_c = 1/(n·β)` (**locked at 4 spec sites; 0 code implementations** per AUDIT 5D-F4)
- Starfield aberration warping star directions forward at high γ
- An orbit appearing to run BACKWARD when observed at retarded time during warp egress at v_app > c
- A source that becomes **gone, not faded** when ship overtakes its photon emission history
- A Hubble-horizon body rendered **frozen** at horizon-crossing instant, dimming on a separate timescale
- Geometric lensing — light rays bent by ∇W producing Einstein-ring-style distortion
- Chaos field χ(x,t) modulating the bubble shell with Fisher-KPP dynamics
- The eye-ear decoupling at warp egress (§6.3 + §8.3 endogenous/exogenous)
- A composition rule gauge showing live `dτ_ship/dt_cosmic`

**Until human eyes see a frame and confirm "yes, that's what v_app = 2c
looks like — orbit running backward, color shifted, Cherenkov cone open
at the calculated half-angle," the implementation is mathematically
correct but visually unverified.**

UE5 will eventually render these effects (Phase E0-E5 per
`WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`), but UE5 is heavy, opaque, and
engine-bound, and months away. **We need a thin layer:** raw C/C++/CUDA +
OpenGL + ImGui, no engine, that renders the math directly and lets a human
(and pixel-level mechanical assertions) confirm the math produces the
right image.

---

## 2. Why this matters — the five finding classes (from sibling proposal §2)

Per spec §15.4 ("revise on findings, not on polish"), the testbed surfaces
findings the math-only assertion suite cannot. **Five distinct finding
classes**, each justifying spec revisions or implementation work:

### Class 1 — Visual phenomena that need additional math

The 66 C++ assertions don't compute Cherenkov; AUDIT 5D-F4 noted
"Cherenkov formula locked at 4 spec sites, 0 code sites." The testbed
will DEMAND the Cherenkov implementation. Running Scene S06 will surface
whether `cos θ_c = 1/(n·β)` produces a visually-correct cone, and what
`n(W)` function works.

**Closure target:** `compute_cherenkov_angle()` in `libastra_nexus` with
≥3 new C++ assertions (β = 0.5, 0.9, 0.999). Bumps test count from 66 to 69+.

### Class 2 — Math right, visuals wrong

If `apparent_rate = 1 − v_app/c` produces correct numerics (−9 at v_app=10c
per the test suite) but the VISUAL planet's orbit reversal looks WRONG to
the human eye, that's a spec-level finding: maybe the orbit reversal needs
an additional damping term, or maybe the rendering needs a different
mapping. **Pixel-level assertions catch math-right + render-path-wrong.**

### Class 3 — Math right, math missing

The visual warp wake (P3 below) is **NOT in the spec.** If it's visually
compelling AND physically motivated (the metric_shift residual from the
ship's prior positions decaying over τ_ship), the spec should add a §6
sub-section. If it's neither, the spec stays silent. **The testbed
determines which.**

### Class 4 — Spec-internal inconsistency surfaced visually

The Eye-Ear Decoupling (§8.3 endogenous-audio vs §6.3 exogenous-visual at
warp egress) has been treated as "feature, not bug." But until the testbed
makes it visually concrete (rear-view shows planet running backward; UI
audio-frequency display shows current warp drone with no delay), the
operator can't *see* whether the decoupling is the intended experience or
whether it's jarring in a way that breaks immersion. **Scene S12 is the
operator's first chance to see this with their own eyes.**

### Class 5 — Closing audit gaps from a different direction

The C++ binary's stdio_server has limited ops; v0.129 added 5 of 6 needed
for Narrator-LLM. The testbed validates the SAME `astra_nexus.cpp` API
surface but from the **graphics-rendering direction**. If both
Narrator-LLM (text side) and Testbed (graphics side) consume the same ops
cleanly, that's **two-direction conformance verification**.

**Per §15.4: the testbed IS a closed-loop measurement instrument.** Not
the textverse LCP gates; a parallel visual conformance instrument.

---

## 3. Scope

### 3.1 In scope (the 15 phenomena to render)

| # | Phenomenon | Spec source | Verified by |
|---|---|---|---|
| P1 | Hull (ship body) | §1.3 | S01 |
| P2 | Warp bubble from CFD-RBF | §6 sample_warp_field_unified | S04, S05, S06 |
| P3 | Warp wake / trail | §3.6 + §6 (extension; §15.4 candidate) | S05, S06 |
| P4 | Geometric ray-deflection (warp lensing) | §3.4 + §6 step 9 | S04, S05 |
| P5 | Cherenkov cone | §6 step 10 (closes 5D-F4) | S06 |
| P6 | Chaos field χ(x,t) | §7.1 Fisher-KPP + §1.5 | S09 |
| P7 | Doppler / aberration on starfield | §3.4 SR Doppler | S02, S03 |
| P8 | Retarded-time orbit reversal | §3.11 + §6.3 | S05 |
| P9 | Photon-source-history bound | §3.11 | S07 |
| P10 | Hubble-horizon decoupling | §3.12 | S10 |
| P11 | Metric redshift composition | §3.4 + §6 step 11 | S02, S03 (visible in body color) |
| P12 | Composition rule gauge | §3.2 + §7 truth table | All scenes (UI overlay) |
| P13 | Regime state machine | §3.3 | All scenes (UI label) |
| P14 | Reflex control vector | §2.3.1 (v0.129) | S09 |
| P15 | Eye-ear decoupling | §6.3 + §8.3 endogenous/exogenous | S12 |

### 3.2 Explicitly out of scope

- ❌ **No Unreal Engine integration.** Engine-agnostic ground truth.
- ❌ **No production rendering.** No TSR, Lumen, Nanite, DLSS.
- ❌ **No LLM / persona.** Pure physics → pixels.
- ❌ **No audio synthesis.** §8.3 audio is sibling testbed.
- ❌ **No NNE/TensorRT Reflex.** PID stub validates the CONTRACT, not trained weights.
- ❌ **No Apple/Mac/Metal/iOS.** Per CLAUDE.md Platform Discipline.
- ❌ **No Python.** Per CLAUDE.md Language Discipline.
- ❌ **No save/load persistence.**
- ❌ **No network features.**
- ❌ **No VR/stereo rendering.**
- ❌ **No production hull mesh.** Simple low-poly placeholder.
- ❌ **No real audio playback for S12.** UI audio-frequency display only.

### 3.3 What success looks like

`astra_visualizer.exe` runs on Windows 11 + NVIDIA RTX 40-series. Operator
picks a scene from a menu; it renders at 60+ FPS at 1080p. UI controls
sweep parameters. For every scene, an on-screen assertion overlay says
**PASS / FAIL** comparing rendered pixels to canonical math from
`libastra_nexus`. Headless mode (`--headless --scene=all`) runs all 12
scenes; CI gates on JSON report.

**The operator personally watches Scene S05 and confirms** the planet at
v_app=2c orbits BACKWARDS. That's the "you have to see it to believe it"
payoff that requires operator sign-off as final acceptance.

---

## 4. Technology stack (locked)

| Layer | Technology | Why |
|---|---|---|
| Build | **CMake 3.24+** with FetchContent | Per CLAUDE.md. Cross-platform. |
| C++ | **C++17** (C++20 acceptable) | CUDA 12.x compatible. |
| Compiler Windows | **MSVC 19.38+** (VS 2022) | NVCC 12.x integrates. |
| Compiler Linux | **gcc 13+ or clang 16+** | C++17/20 + CUDA. |
| GPU compute | **CUDA 12.x** | Per Platform Discipline. |
| Graphics API | **OpenGL 4.6 Core** | Mature CUDA interop; compute shaders; engine-agnostic. |
| Window/input | **GLFW 3.4+** | Lightweight; cross-platform; zlib license. |
| GL loader | **glad 2** | Single header. |
| Math | **GLM 1.0+** | Header-only; GLSL conventions. |
| UI | **Dear ImGui 1.91+ (docking)** | De facto standard for tooling UI. |
| Image I/O | **stb_image + stb_image_write** | Single-header PNG. |
| JSON | **nlohmann/json** | Per spec §15.6. |
| Tests | **doctest** | Per spec §15.6. |
| Math linkage | **Static-link `libastra_nexus`** | Single source of truth. |

**Explicitly NOT using:** Vulkan (boilerplate), DirectX 12 (engine-specific),
Qt (heavy), WebGPU (immature), Python anywhere, any engine.

---

## 5. Architecture (the libastra_nexus extraction is critical)

### 5.1 The two-step refactor of `astra_nexus.cpp`

**Step 1:** Split into static library + thin `main()`:

```
proto/
├── astra_nexus.cpp                    (existing; thin wrapper; keep working as exe)
├── libastra_nexus/                    (NEW; the canonical math library)
│   ├── include/astra_nexus/
│   │   ├── coord.h                    (AstraCoord, astra_distance, renormalize)
│   │   ├── rapidity.h                 (Rapidity, integrate, OMEGA_MAX)
│   │   ├── composition.h              (dtau_dt_cosmic, schwarzschild_r, compute_grav_factor)
│   │   ├── apparent_rate.h            (compute_apparent_rate — regime-dispatched)
│   │   ├── observe.h                  (ObservableState, observe, compute_z_*)
│   │   ├── kepler.h                   (solve_kepler_E, orbit_phase, Orbit)
│   │   ├── cherenkov.h                (NEW: compute_cherenkov_angle, n_refractive_default)
│   │   ├── types.h                    (NEW: WarpFieldSample, shared with future UE5 plugin)
│   │   ├── stdio_server.h             (run_stdio_server — preserved)
│   │   └── test_suite.h               (run_all_tests; pass/fail counters)
│   ├── src/                           (split sources per header)
│   └── CMakeLists.txt
└── visualizer/                        (NEW; this project)
```

**Step 2:** Visualizer's CMakeLists links against `libastra_nexus`:
```cmake
add_subdirectory(${CMAKE_SOURCE_DIR}/../libastra_nexus libastra_nexus_build)
target_link_libraries(astra_visualizer PRIVATE astra_nexus)
```

**Step 3:** `WarpFieldSample` struct (per §6 line 1139) lives in
`libastra_nexus/include/astra_nexus/types.h`. **Both the testbed and the
future UE5 plugin consume the same header.** Single type definition; no
cross-substrate drift.

**Result:** Every numeric the visualizer compares against is the **same
implementation** that runs the 66+ assertions. Single source of truth.

### 5.2 Dual-mode operation

**Interactive mode:** GLFW window + ImGui UI. Operator picks scenes, sweeps
parameters, sees PASS/FAIL overlay. 60+ FPS on 4070+.

**Headless mode:** `--headless --scene=all`. No window; runs each scene's
canonical configuration; dumps PNG + JSON report. Exit code 0 if all
assertions pass. **Required for CI.**

CLI:
```
astra_visualizer.exe                                   # interactive
astra_visualizer.exe --scene=S05_WarpCruise_2c         # interactive, jump
astra_visualizer.exe --headless --scene=all            # all scenes headless
astra_visualizer.exe --headless --output=ci_results/
astra_visualizer.exe --regenerate-goldens --scene=all  # operator-sign-off only
astra_visualizer.exe --version
```

---

## 6. The 12 scenes (one paragraph each + assertion summary)

Each scene has: goal, spec basis, math primitives used, rendering technique,
UI controls, ≥3 pixel-level assertions, pass criteria. Below is the
abbreviated form; full per-scene specs go in `docs/SCENES.md`.

### S01 — RestBaseline
**Goal:** Sanity check. Hull + starfield + sun + Earth visible at REST.
**Spec basis:** §1.1, §1.2, §3.3 REST regime.
**Assertions (3):** Hull pixel renders; sun pixel yellow-ish; UI shows γ=1.0, dτ/dt=1.0.
**Pass:** All 3 pass; visual matches golden.

### S02 — STL_Recede_05c
**Goal:** Validate SR longitudinal Doppler at β=0.5 (z_kin = √3 − 1 ≈ 0.732).
**Spec basis:** §3.4, §3.11, §3.7.
**Math:** `Rapidity::gamma() = cosh(atanh(0.5)) ≈ 1.155`; `compute_z_kin(0.5c) ≈ 0.732`.
**Assertions (4):** apparent_rate matches √(1/3); planet color shifted red; aberration mild; no warp visual.

### S03 — STL_Recede_09c
**Goal:** Dramatic SR effects at β=0.9 (γ=2.294; z_kin=√19−1≈3.359).
**Assertions:** apparent_rate matches √((1-0.9)/(1+0.9))=0.2294; planet R≫G+B; strong aberration; γ matches libastra.

### S04 — WarpCharge sequence
**Goal:** Bubble forms over 5s; W ramps 0→1; regime transitions WARP_CHARGE→WARP_CRUISE.
**Spec basis:** §3.3 transitions; §6 smooth-min blend.
**Assertions:** At t=0 no bubble; at t=5s bubble fully formed; symmetric in xy plane; Cherenkov NOT YET visible.

### S05 — WarpCruise_2c (THE PAYOFF — orbit reversal)
**Goal:** Planet 1 ly behind orbits BACKWARDS at apparent_rate=−1 from ship warping at 2c. **The canonical visual test of §3.11.**
**Spec basis:** §3.11 retarded-time; §6.3 ObservableState; nexus.cpp:639-677 (existing 3 C++ assertions).
**Math:** `compute_apparent_rate(2c, R_WARP_CRUISE) = -1.000`; `observe(...)` returns `t_emit < t_cosmic`.
**Rendering:** Rear-view; planet at Kepler-at-t_emit position; trail mode shows reverse motion.
**Assertions (4):** apparent_rate=−1.000 ± 0.001; dphase/dt < 0; Kepler integration matches; trail visibly reverses.
**Pass:** All 4 pass + **operator personally confirms visible orbit reversal** (required sign-off).

### S06 — WarpCruise_10c + Cherenkov (closes 5D-F4)
**Goal:** Orbit reverses at 9× speed; Cherenkov cone with `cos θ_c = 1/(n·β)`.
**Math NEW:** `compute_cherenkov_angle(W, β, n_default)` lands in libastra_nexus with 3+ assertions. **C++ test count 66→69+.**
**Assertions:** apparent_rate=−9.000; cone half-angle matches `acos(1/(n·β))` ± 1°; cone narrows as W increases; cone collapses at β→0.

### S07 — WarpCruise_8000c (photon-source-history)
**Goal:** Source disappears (not faded; **gone**) when ship overtakes its photon emission history.
**Spec basis:** §3.11 photon-source-history bound; ObservableState.beyond_photon_history.
**Assertions:** Before crossover source visible; after crossover absent (no afterimage); transition discrete (1-frame); timing matches `beyond_photon_history` flag.
**Why this matters:** Spec §3.11 says "*gone, because no photon remains to be received.*" Most fiction shows fade. **This scene proves the spec's distinct claim.**

### S08 — WarpGravityWell
**Goal:** Regime composition (`WARP_CRUISE | GRAVITY_WELL = 0x28`); chaos α_eff coupling; gravitational lensing distinct from warp lensing.
**Spec basis:** §3.3 regime composition; §7.1 chaos coupling; §7.4 Warp Exclusion Zone.
**Assertions:** Schwarzschild factor matches `√(1−r_s/r)`; α_eff scaling matches formula; chaos field intensifies as r decreases; composition rule output correct.

### S09 — ChaosInstability + Reflex
**Goal:** Chaos PDE grows unstable; Reflex damps; emergency dump on excess.
**Spec basis:** §7.1 Fisher-KPP; §2.3.1 Reflex Contract (v0.129 NEW).
**Math:** CUDA chaos PDE (RK2 explicit) + PID Reflex stub.
**Assertions:** Field stays in [0,1]; CFL stability holds at dt=1/60s; Reflex damps chaos when enabled; emergency dump fires on threshold.

### S10 — HubbleHorizon
**Goal:** Body beyond Hubble horizon rendered FROZEN at horizon-crossing; dimming on separate timescale.
**Spec basis:** §3.12 cosmological expansion; ObservableState.beyond_hubble_horizon.
**Assertions:** flag=true; visual stays frozen; color extremely redshifted; brightness fades slowly.
**Why separate from S07:** S07 tests kinematic bound (ship overtakes photons); S10 tests cosmological bound (expansion outruns photons). **Different physics; separate scenes.**

### S11 — SplitScreen STL_REL vs WARP_CRUISE at v=0.5c
**Goal:** Side-by-side comparison proves regime-dispatched apparent_rate is real, not artifact.
**Spec basis:** §3.11; §10 validation row "STL_REL formula was NOT 1/γ".
**Math:** STL_REL apparent_rate = √(1/3) ≈ 0.5774; WARP_CRUISE = 0.5.
**Assertions:** Both rates match libastra; visual orbital-phase ratio matches; at v>c WARP reverses while STL panel shows "invalid."

### S12 — EyeEarDecoupling at warp egress
**Goal:** Visual orbit reverses while audio frequency stays current. Proves §6.3 + §8.3 endogenous/exogenous principle is the designed experience.
**Spec basis:** §6.3 + §8.3 endogenous/exogenous; book CANON.md endogenous/exogenous vocabulary.
**Math:** All of S05 + simulated UI audio frequency display (NOT real audio playback).
**Script:** t=0..10s WARP_CRUISE (visual reversed; audio = warp drone display); t=10s warp.disengage(emergency) (audio jumps to shutdown frequency; visual continues reverse for ~1y scenario time then re-syncs).
**Assertions:** During warp, UI shows audio_t=cosmic, visual_t=retarded with gap; at t=10s audio jumps; gap shrinks; gap matches `t_cosmic - t_emit` from `observe()`.
**Why this scene matters:** Cycle 1 of *The Long Watch* names endogenous/exogenous as ASTRA's epistemic vocabulary; spec §6.3 names it as architectural routing; this scene makes it **visually concrete**. The literal intersection of book canon + spec architecture + user-facing perception.

---

## 7. Validation methodology — three layers

### 7.1 Layer 1 — Pixel-level scalar assertions (per-scene; runtime)

```cpp
struct ScalarPixelAssertion {
    std::string name;
    glm::ivec2 framebuffer_coord;
    int channel;                 // 0=R, 1=G, 2=B, 3=A
    float expected_value;        // canonical math output from libastra_nexus
    float tolerance;
};

class PixelSampler {
    std::vector<AssertionResult> Sample(const IScene& scene, GLuint framebuffer);
};
```

**Default tolerance:** 1% of expected OR ±0.01 absolute, whichever larger.

**Why this matters:** the canonical value comes from `libastra_nexus::compute_*()` — the SAME implementation as the 66+ C++ assertions. **Mechanical, not eye-balled.**

### 7.2 Layer 2 — Heatmap diff (golden image comparison)

```cpp
struct HeatmapDiffAssertion {
    std::string golden_path;
    float max_mean_diff;       // 0.01 = 1% mean diff
    float max_pixel_diff;      // 0.10 = no single pixel >10% off
};
```

**Goldens regeneration policy** (mirrors textverse's `scope.yaml` discipline):
- Goldens are **canon-locked** once approved.
- `--regenerate-goldens` flag requires explicit operator sign-off in commit message.
- CI fails if goldens regenerated without sign-off marker.

### 7.3 Layer 3 — Side-by-side numeric overlay (real-time operator validation)

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

### 7.4 JSON test report (CI gate)

After headless run:
```json
{
  "version": "0.1.0",
  "build_commit": "abc123",
  "libastra_nexus_version": "v0.129",
  "libastra_assertion_count": 69,
  "scenes": [ { "name": "S05_WarpCruise_2c", "assertions": [...], "heatmap_diff": {...}, "frame_ms": 14.2 } ],
  "summary": { "scenes_passed": 12, "scenes_failed": 0, "total_assertions": 48, "assertions_passed": 48 }
}
```

**CI gate:** exit code 0 iff `summary.scenes_failed == 0`.

---

## 8. UI design

### 8.1 Layout (ImGui docking branch)

```
┌─────────────────────────────────────────────────────────────────────┐
│ [Scenario: S05 ▼] [Reset] [Pause]   60 FPS / 16.2 ms               │  ← Top bar
├──────────┬───────────────────────────────────┬──────────────────────┤
│  PARAM   │                                   │   STATE +            │
│  PANEL   │           VIEWPORT                │   VALIDATION         │
│          │     (3D render here)              │                      │
│ [W=1.0]  │                                   │ Regime: WARP_CRUISE  │
│ [v=2c]   │                                   │ γ=1.000 W=1.00       │
│ [Reflex] │                                   │ apparent_rate:       │
│  ...     │                                   │  rendered: -1.0012   │
│          │                                   │  libastra: -1.0000   │
│ [F12]    │                                   │  ► PASS              │
├──────────┴───────────────────────────────────┴──────────────────────┤
│ Console: [scenario loaded: s05] [t=15.3s sim time]                  │  ← Status bar
└─────────────────────────────────────────────────────────────────────┘
```

### 8.2 Hotkeys

- **WASD / Q-E**: camera move; **Mouse drag**: look
- **1-9**: scenarios 1-9; **Shift+1-3**: scenarios 10-12
- **Space**: pause; **R**: reset; **F1-F4**: toggle panels; **F11**: fullscreen; **F12**: screenshot

---

## 9. Performance budgets

### 9.1 Target FPS by hardware

| Target | Hardware | Resolution |
|---|---|---|
| 60 | RTX 4070 | 1080p (minimum) |
| 60 | RTX 4090 | 1440p (recommended) |
| 120 | RTX 5090 | 1080p (upper-tier) |
| 30 | RTX 3060 | 1080p (low-end) |

### 9.2 Per-pass GPU budget at 1080p on RTX 4070 (16.67 ms total)

| Pass | Budget (ms) |
|---|---|
| Chaos PDE step (RK2) | 1.5 |
| Warp field RBF populate | 1.5 |
| Volume ray-march (warp+chaos) | 3-4 |
| Lensing post-pass | 1.5 |
| Starfield + Doppler + aberration | 1.0 |
| Cherenkov + wake | 0.5 |
| Hull + UI + post-process | 3.0 |
| Reserve | ~4 |

### 9.3 NOT goals

No cinematic look; no HDR pipeline; no Lumen/RTX GI; no DLSS/FSR; no
volumetric clouds; no AA beyond MSAA 4×.

---

## 10. Phased roadmap (7-9 weeks)

| Phase | Days | Cumulative | Deliverable | Gate |
|---|---|---|---|---|
| **V0** Scaffolding | 2-3 | 3 | CMake skeleton; GLFW window; ImGui; CLI parses | `--help` works; empty window |
| **V1** Scene framework + hull + starfield | 3-4 | 7 | Free-fly camera; hull; 10K stars; time decoupling | Fly around hull in starfield |
| **V2** libastra_nexus extraction + math bridge | 3-4 | 11 | Lib extracted; physics math reachable; state display | State matches `astra_nexus.exe` to 6 sig figs |
| **V3** CUDA-GL interop | 2-3 | 14 | Trivial CUDA-to-3D-texture path works | Evolving volume visible; interop solid |
| **V4** Scenes 1-3 | 4-5 | 19 | S01 REST + S02/S03 STL recede; starfield Doppler | 12 assertions PASS |
| **V5** CFD-RBF + Scenes 4-5 (THE PAYOFF) | 5-6 | 25 | RBF synth; volume render; S04 charge; **S05 orbit reversal** | **Operator confirms visual orbit reversal** |
| **V6** Lensing + Cherenkov + Scenes 6-7 | 4-5 | 30 | NEW `compute_cherenkov_angle()` in libastra; lensing post-pass; S06 + S07 | **Cherenkov gap closed in code** |
| **V7** Chaos + Reflex + Scenes 8-10 | 5-6 | 36 | Chaos PDE; PID Reflex; S08 + S09 + S10 | Regime composition + Reflex feedback visible |
| **V8** Wake + split + eye-ear + Scenes 11-12 | 4-5 | 41 | Wake trail; split-screen; S11 + S12 | All 12 scenes work; eye-ear decoupling reads as designed |
| **V9** Validation infra + CI | 3-4 | 45 | Goldens locked; JSON report; CI gate | CI green |
| **V10** Polish + docs | 2-3 | 48 | README/BUILD/SCENES/VALIDATION/KNOWN_ISSUES | Release-quality binary |

**Total: 41-48 days ≈ 7-9 weeks** for competent agent + LLM pair-programming.
**Solo dev with operator review cycles: 9-12 weeks.**

### Critical-path items (do FIRST in their phases)

- **V2 libastra_nexus extraction** — gates V4-V10
- **V3 CUDA-GL interop** — gates V5+; must work day 1
- **V5 CFD-RBF** — gates V6, V7, V8
- **V6 Cherenkov implementation** — closes 5D-F4 gap
- **V5 Scene 5 orbit reversal** — operator sign-off required; project payoff

### Items deferrable to v1.1 if calendar tight

- S11 split-screen, S12 eye-ear (calendar pressure)
- Linux build (Windows-first if pressed)
- Hot-shader-reload (F5), MP4 capture

---

## 11. Risk assessment

### 11.1 Technical risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| CUDA-GL interop driver bugs | Low | Mature API; NVIDIA `simpleGL` reference; fallback to CUDA-only if needed |
| RBF + spatial-hash slow at 1080p | Medium | Profile early; shared memory; reduce node count |
| Cherenkov tuning takes many iterations | High | Live-tunable coefficients; budget extra V6 time |
| Newton-Raphson diverges at edge cases | Low | Clamp iterations; closed-form fallback for static bodies |
| Chaos PDE instability near critical α | Medium | CFL guard; explicit RK2; cap α_eff |
| GPU driver crashes on long runs | Low | Defensive `cudaGetLastError()`; clean restart |
| Cross-build to Linux breaks | Medium | Test Linux CI from V0; CMake portable patterns |

### 11.2 Scope risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| V6 or V8 more complex than estimated | Medium | Defer cosmetic refinement (S11/S12) to v1.1 |
| S12 eye-ear hard in static screenshot | Low | Document as "dynamic only"; defer if needed |
| >12 scenarios scope creep | Medium | Hard cap at 12 for v1 |
| UI polish takes too long | Low | Use ImGui defaults; no custom styling |

### 11.3 Validation risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Visual tests subjective | High | Golden RMSE catches regression; human review for first scenes |
| Math right, visual wrong; ambiguity | Medium | Log to KNOWN_ISSUES.md; each inconsistency is §15.4 candidate |
| Performance misses on some hardware | Medium | Document min-hardware; provide quality tier setting |
| Goldens too brittle | Medium | RMSE tolerance (1% mean); operator sign-off for regen |

---

## 12. Predicted §15.4 spec revision candidates

Per §15.4 the testbed IS a closed-loop measurement; findings justify v0.130 revisions:

| Predicted finding | Spec section affected |
|---|---|
| Cherenkov implementation produces visible cone; formula confirmed | §6 step 10 + Appendix B (closes 5D-F4) |
| Warp wake trail is visually compelling AND physically motivated | §3.6 + §6 (NEW sub-section: wake as canon) |
| `t_source_start` per-body schema concretized (S07 forces issue) | §3.11 (audit R4) |
| α_lens lensing coefficient empirically tuned to ~3-5 | Appendix B |
| n(W) refractive index function empirically tuned | §6 step 10 + Appendix B |
| Chaos PDE α_base + k_coupling empirically tuned | §7.1 + Appendix B |
| Reflex PID gains tuned (informational; real Reflex is trained) | §2.3.1 advisory |
| Eye-ear decoupling at warp egress visually compelling (or jarring) | §6.3 + §8.3 |
| `WarpFieldSample` struct field set right or needs additions | §6 line 1139 |
| Smooth-min `k` parameter for SDF blending empirically settled | §6 step 4 + Appendix B |

Each finding lands in `docs/KNOWN_ISSUES.md`; per §15.4 operator decides
which justify spec revisions.

---

## 13. Coding-agent handoff brief

### 13.1 14 things to know

1. **Spec basis:** `docs/spec-v0.129-tentative-2026-05-16.md`. Spec wins when in doubt.
2. **Math basis:** `proto/astra_nexus.cpp`. Every numeric traces here. **V0 task: extract as libastra_nexus.**
3. **Vision basis:** This document. WHAT to build; not HOW to write the C++.
4. **Scenes are NOT equal effort.** S01-S03 + S10-S11 straightforward; S04-S08-S09 medium; **S05, S06, S07, S12 are hardest.**
5. **CUDA-GL interop is #1 bug source.** Test trivial cases on day 1 of V3 BEFORE building scenes.
6. **Three-layer validation is load-bearing.** Don't skip pixel assertions.
7. **Headless mode not optional.** Maintain through every scene addition.
8. **Goldens are canon.** Once approved, locked; regen requires operator sign-off.
9. **Don't reinvent the math.** Every numeric traces to a `libastra_nexus` call.
10. **Cross-platform:** Windows 11 primary; Linux x86_64 secondary. Test both every phase. **No Apple anywhere.**
11. **C/C++ only.** No Python; no Python build scripts; CMake only.
12. **Cherenkov gap closes here.** `compute_cherenkov_angle()` in libastra_nexus; 3+ new assertions; C++ count 66→69+.
13. **Warp wake is §15.4 finding candidate.** Document empirical reading in KNOWN_ISSUES.md.
14. **S05 operator sign-off is the project payoff.** Schedule synchronous review at end of V5. **Until then, project is incomplete.**

### 13.2 Where to look when stuck

| Problem | First-look reference |
|---|---|
| Math wrong | `proto/astra_nexus.cpp` source + assertion outputs |
| Physics unclear | `docs/spec-v0.129-tentative-2026-05-16.md` then v0.128 |
| Visual mismatch | This document, scene's "Expected visuals" section |
| CUDA-GL interop hanging | NVIDIA CUDA sample `simpleGL` |
| <60 FPS | Performance overlay; NVIDIA Nsight Graphics |
| Pixel assertion failing | Print expected vs measured; check tolerance |
| ImGui unresponsive | Verify `ImGui_ImplGlfw_NewFrame()` + `ImGui_ImplOpenGL3_NewFrame()` per frame |
| Linux build fails | CUDA architecture; nvcc version; pthread linking |
| Cherenkov wrong angle | Verify `n(W) = 1 + W` default; verify β is effective velocity |
| Headless differs from interactive | Missing `glFinish()` before `glReadPixels`; ImGui state polluting |

### 13.3 Acceptance criteria

The testbed is **v1 complete** when:

1. ✓ Builds on Windows 11 + MSVC 2022 + CUDA 12.x + CMake 3.24+
2. ✓ Builds on Linux x86_64 + gcc 13+ + CUDA 12.x + CMake 3.24+
3. ✓ All 12 scenarios load and run without crashing
4. ✓ Each scenario produces visuals matching §6 criteria
5. ✓ State display matches `proto/astra_nexus.cpp` to 6+ sig figs
6. ✓ Per-pass GPU timing visible in profiler
7. ✓ F12 saves PNG + JSON state dump
8. ✓ 60 FPS at 1080p on RTX 4070
9. ✓ Golden RMSE < 1% for all 12 scenes
10. ✓ Documentation complete: README/BUILD/SCENES/VALIDATION/KNOWN_ISSUES
11. ✓ doctest unit tests pass for: rbf_eval, chaos_pde_step, cherenkov_math, observation_calc, reflex_stub, rbf_network, wake_field
12. ✓ No Python; no Apple; no UE5 dependency
13. ✓ `compute_cherenkov_angle()` in libastra_nexus with 3+ assertions; C++ count ≥ 69
14. ✓ **Operator has watched S05 and CONFIRMED orbit appears to run backward at v_app=2c**

---

## 14. Open questions for operator

1. **`proto/constants.toml` integration?** YES if it lands before V0; NO if testbed proceeds first (defer to v1.1).
2. **`WarpFieldSample` shared header?** YES. Define once in `libastra_nexus/include/astra_nexus/types.h`; testbed + future UE5 plugin consume same definition.
3. **S12 Eye-Ear in v1 or v1.1?** v1. Cleanest §6.3 demonstration; aligned with book canon.
4. **Comparison mode (split-screen) in v1?** v1. Needed for S11; reused by S12. ~3 days extra.
5. **History timeline scrubber?** NO at v1. Pause + reset + screenshot suffice.
6. **Separate repo?** Initially `proto/visualizer/`; split to separate repo at v1.x stability.
7. **Hull mesh source?** Generic low-poly placeholder for v1; commission proper hull for v1.x.
8. **Real audio for S12?** NO at v1. UI frequency display only.
9. **Linux build priority?** From V0. CMake cheap if upfront.
10. **MP4 video capture?** PNG sequences in v1; MP4 is operator post-processing.
11. **Reference RBF source?** Synthetic for v1; real CFD output deferred to v1.x.
12. **Cherenkov closure location?** In libastra_nexus with C++ assertions. Math layer; visualizer just calls.
13. **Goldens regeneration policy?** Strict. Operator sign-off via commit message marker.

---

## 15. The deeper structural value

### 15.1 It IS rig 3 per spec §15.8 + 3B-U3

Spec §15.8 names three rigs (physics binary / LLM bundle / engine — deferred).
Discovery 3B's U3 added rig 4 (prose canon) and rig 5 (spec audit).
**`astra_visualizer.exe` IS rig 3.** The engine-side verification instrument
the spec called for but didn't have a path to. **Doesn't wait for UE5.**

### 15.2 It de-risks UE5 integration

When UE5 Phase E2-E5 lands, every visual effect has been previously
validated in the visualizer. **UE5 surprises become localizable:**
"math + bare OpenGL produces correct visuals; UE5 wraps that same math +
fancier renderer; mismatches are UE5 wrapper bugs, not math bugs."

**Visualizer's golden PNGs become the canonical reference for UE5's rendering.**

### 15.3 It is a publishable artifact

A standalone Windows .exe demonstrating retarded-time orbit reversal at
v_app > c is a compelling proof-of-concept. Ships with the GitHub repo as
"see the physics" demo. Referenceable in academic discussions. **First
publicly-shareable artifact while the main game is pre-Phase-E0.**

### 15.4 It is implementation #1 of dual-implementation discipline (§15.7)

Per spec §15.7: testbed is implementation #1 of the visual side; UE5
plugin is implementation #2. Both consume the same `libastra_nexus` math,
the same `WarpFieldSample` types, and produce visuals that should agree.
**Visualizer's output IS canonical reference for what UE5 should produce.**

### 15.5 It runs §15.10 audit cadence on the visual axis

Per spec §15.10 (NEW v0.129): each major math change triggers a testbed
run; visual regression triggers spec or code revision.

---

## 16. Summary

| Phase | Weeks | What lands |
|---|---|---|
| V0 | 0.5 | Scaffolding + CLI + CMake |
| V1 | 0.5-1 | Scene framework + hull + starfield |
| V2 | 0.5-1 | **libastra_nexus extraction + math bridge** |
| V3 | 0.5 | CUDA-GL interop foundation |
| V4 | 1 | Scenes 1-3 (REST + STL recede) |
| V5 | 1-1.5 | **CFD-RBF + Scenes 4-5 (orbit reversal — operator confirms)** |
| V6 | 1 | **Lensing + Cherenkov + Scenes 6-7 (Cherenkov gap closed in code)** |
| V7 | 1-1.5 | Chaos + Reflex + Scenes 8-10 |
| V8 | 1 | Wake + split + Scenes 11-12 |
| V9 | 0.5-1 | Validation infrastructure + CI |
| V10 | 0.5 | Polish + docs + release |

**Total: 7-9 weeks competent agent + LLM pair-programming.**
**9-12 weeks solo with operator review cycles.**

---

## 17. Closing

The testbed is the **first visual closed-loop** for ASTRA-7's physics.
The C++ assertions prove the math is internally consistent; the
textverse bench proves the LLM substrate produces correct behavior;
**THIS testbed proves the math produces the right visual phenomena.**

Per spec §15.4: "the next findings worth a spec revision come from the
closed loop." This testbed is a closed loop the spec hasn't had. Running
it will surface findings the math-only assertion suite cannot — five
classes of them (§2 above).

Per spec §15.7 dual-implementation: testbed is implementation #1 of the
visual side; UE5 plugin is #2. Both consume `libastra_nexus` math + shared
`WarpFieldSample` types. **Testbed's visual output IS canonical reference
for UE5.**

Per spec §15.10 audit cadence: testbed becomes the 6th rig (alongside
physics binary, textverse bench, UE5 engine, book canon, spec audit).

The testbed is small (~48 days), bounded (12 scenes), and high-leverage.
The operator gets a Windows .exe demonstrating: warp field, Cherenkov
cone, retarded-time reversal, photon-source-history disappearance,
Hubble-horizon freeze, geometric lensing, chaos instability, Reflex
stabilization, regime contrast, eye-ear decoupling, warp wake — all
rendered, interactive, live-tunable. **That's the conversion of months
of paper-physics into eye-visible truth.**

The math is locked. The visual claims are testable. A coding agent ships
this in 7-9 weeks. Validation is mechanical. Closure is empirical.
The Cherenkov gap closes. **The operator sees orbit reversal with their
own eyes.**

Build it.

— Plan v2 FINAL, 2026-05-16 —

---

*v2 FINAL changes from v1: integrated five-finding-class taxonomy; added
S12 Eye-Ear Decoupling; split Hubble (S10) from photon-source-history (S07);
added risk assessment table; added predicted §15.4 findings; per-pass GPU
budget at 1080p RTX 4070; clarified Reflex-as-PID-stub; framed warp wake
as §15.4 candidate; added `WarpFieldSample` shared header; reordered phases
(math bridge V2 before CUDA interop V3); tightened effort to 7-9 weeks.*

*Note: this file is a polish-pass alternative to `ASTRA_VISUALIZER_PLAN_2026-05-16_v2.md`
which was authored by a parallel session with similar integration. Operator
chooses which to keep. Both reach equivalent conclusions through slightly
different organizations; the existing `_v2.md` has stronger phasing details
(16-week realistic with V0-V7 breakdown), this `_v2_FINAL.md` has the
five-finding-class taxonomy section + explicit risk + predicted-findings
sections more prominently. Combine the two if desired — they are
complementary.*
