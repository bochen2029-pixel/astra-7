# ASTRA-7 Visualizer 02

Standalone Windows 11 native CUDA + OpenGL visual physics testbed for the ASTRA-7
14-equation framework. Renders the warp field, Cherenkov cone, retarded-time orbit
reversal, photon-source-history disappearance, Hubble-horizon freeze, geometric lensing,
chaos field instability + Reflex stabilization, regime contrast, and eye-ear decoupling —
12 distinct scenes — with pixel-level assertions that mechanically verify rendered output
against canonical math from `proto/astra_nexus.cpp`.

**Status:** V10 SHIPPED — astra_visualizer v0.1.0 (2026-05-16). All 10 phases V0-V10 green.
12 / 12 scenes live. CI: `119 / 119 PASS` (75 libastra + 32 scene + 12 golden_diff at
mean=0.0000), `exit 0`. Docs: [BUILD.md](BUILD.md) · [SCENES.md](SCENES.md) ·
[VALIDATION.md](VALIDATION.md) · [KNOWN_ISSUES.md](KNOWN_ISSUES.md) ·
[BUILD_LOG.md](BUILD_LOG.md). Single-file `build\astra_visualizer.exe` (~1.7 MB; static
CUDA + MSVC runtime; no Redist required). **One outstanding item:** operator-visual
sign-off on Scene S05 (the orbit-reversal payoff) per [KNOWN_ISSUES.md](KNOWN_ISSUES.md).

---

## For the operator (Bo)

This folder contains the complete spec to hand off to a coding agent. The agent will read
`CLAUDE.md` first (operating contract), then `DESIGN_SPEC.md` (technical/physics), then
begin implementation inside this folder. Work is scope-locked to `C:\ASTRA-7\ASTRA_VISUALIZER_02\`
only — the agent reads outside (canon, sibling projects, parent ASTRA-7 spec) but does
NOT write outside this folder.

### Hand-off command (paste into a fresh Claude Code session opened at this folder)

```
Read CLAUDE.md and DESIGN_SPEC.md in full. Execute the V0 Cold Start protocol per
CLAUDE.md §1. Then begin V0 implementation. Phase deliverables and gates are
documented in CLAUDE.md §7. Log every session in BUILD_LOG.md per §9.
Scope boundary: never write outside C:\ASTRA-7\ASTRA_VISUALIZER_02\.
```

---

## For the future coding agent

You're inside `C:\ASTRA-7\ASTRA_VISUALIZER_02\`. Read these in order:

1. **`CLAUDE.md`** — operating contract; authority levels; build pipeline; the 12 scenes summary; done criteria.
2. **`DESIGN_SPEC.md`** — full physics + architecture spec; per-scene details; algorithm code references.
3. **`BUILD_LOG.md`** — what prior sessions did (append-only).
4. **`BLOCKERS.md`** — unresolved issues, if any.

Then read these in `C:\ASTRA-7\` (READ-ONLY from your perspective):

- `docs/spec-v0.129-tentative-2026-05-16.md` — the physics canon
- `proto/astra_nexus.cpp` — the 1009-line C++ math reference with 66 assertions
- `ASTRA_VISUALIZER_PLAN_2026-05-16_v2_FINAL.md` — the source plan this CLAUDE.md operationalizes

Plus these reference implementations (proven working on this machine):

- `C:\Buddhabrot_CUDA\CLAUDE.md` + `DESIGN_SPEC.md` + `CMakeLists.txt` — the sibling
  project's autonomous-build pattern. Copy CMake invocations, FetchContent declarations,
  static-linkage settings, and helper script structure directly.
- `C:\Buddhabrot_CUDA\BUILD_LOG.md` — the gotchas they solved (most still apply).

---

## What it does (when built)

| Mode | CLI | What happens |
|---|---|---|
| Interactive | `astra_visualizer.exe` | GLFW window opens; scene picker; live parameter sliders; ImGui state display |
| Headless | `--headless --scene=all --output=results\` | Hidden window; renders each scene; dumps PNG + JSON test report; exits 0 iff all assertions PASS |
| Single-scene | `--scene=S05` | Interactive, jumps to specified scene |
| Goldens regen | `--headless --scene=all --regenerate-goldens --output=results` | Overwrites `assets/reference_renders/*.png`; operator commit-marker sign-off required (see CLAUDE.md §11.2) |
| Smoke bench | `--bench=N` | Runs N frames with VSync off; prints FPS stats; exits |
| Math diff | `--verify-math` | Dumps the canonical voyage table for diffing against `proto/astra_nexus` |
| Help | `--help` | Full CLI listing |

Run `astra_visualizer.exe --help` for the full flag list.

---

## Controls (interactive mode)

| Input | Action |
|---|---|
| **W / A / S / D** | Free-fly camera (forward / left / back / right) |
| **Q / E** (or **Ctrl / Space**) | Camera down / up |
| **Shift** (held) | Boost camera speed 10x |
| **Right mouse drag** | Mouse-look |
| **1 - 9** | Switch to scene S01 - S09 |
| **Shift + 1 / 2 / 3** | Switch to scene S10 / S11 / S12 |
| **P** | Pause / resume sim |
| **F12** | Screenshot PNG (saved next to the exe, dated) |
| **Esc** | Quit |

Per-scene parameter sliders appear in the left panel; state readout + assertion PASS/FAIL
in the right panel.

---

## The 12 scenes (one-line summary)

| # | Name | What you'll see |
|---|---|---|
| S01 | RestBaseline | Hull + starfield + sun + Earth at rest |
| S02 | STL Recede 0.5c | Stars + planet redshifted; mild SR aberration |
| S03 | STL Recede 0.9c | Dramatic redshift + forward-aberration |
| S04 | Warp Charge | Bubble forms over 5s; W ramps 0→1 |
| S05 | **Warp Cruise 2c** | **Planet behind ship orbits BACKWARDS** (operator confirms) |
| S06 | Warp Cruise 10c + Cherenkov | Orbit reverses 9× speed; Cherenkov cone visible |
| S07 | Photon-Source History | Source DISAPPEARS (not faded) when ship overtakes its photons |
| S08 | Warp + Gravity Well | Bubble near BH; chaos field intensifies; lensing visible |
| S09 | Chaos + Reflex | Fisher-KPP chaos grows; PID Reflex damps; emergency dump |
| S10 | Hubble Horizon | Body beyond c/H₀ rendered FROZEN at horizon-crossing |
| S11 | STL vs WARP split-screen | Same v_radial; different apparent_rate per regime |
| S12 | Eye-Ear Decoupling | Warp egress: visual lags audio (book-canon-aligned) |

---

## Build (Windows 11)

Requirements:
- Visual Studio 2022 (Community edition fine)
- CUDA Toolkit 12.x or 13.x
- An NVIDIA driver that supports your GPU (RTX 40-series or 50-series)
- `cmake` 3.27+ (VS-bundled works fine)
- `git` for FetchContent

```bat
:: From "x64 Native Tools Command Prompt for VS 2022":
cd C:\ASTRA-7\ASTRA_VISUALIZER_02
cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release

.\build\astra_visualizer.exe
```

Or use the helper script (once V0 lands): `tools\build.bat`.

First configure: `cmake` pulls GLFW 3.4, GLAD v2.0.6, Dear ImGui 1.91+, GLM, stb,
nlohmann/json, doctest via FetchContent. Subsequent builds are fast.

---

## What it doesn't do

This is a diagnostic instrument, not a game. Explicit non-goals:

- No Unreal Engine / Unity / Godot / etc. integration. **Engine-agnostic by design.**
- No LLM / persona / Narrator features. Pure physics → pixels.
- No audio synthesis playback (UI frequency display only for S12). Real audio is a sibling testbed.
- No NNE / TensorRT real Reflex inference. PID stub validates the contract, not weights.
- No save/load persistence. Scenarios start fresh each launch.
- No network features at runtime (per parent CLAUDE.md Privacy Contract).
- No production rendering quality (no TSR, Lumen, Nanite, DLSS).
- No macOS / iOS / Android. **Windows 11 + NVIDIA only.**
- No Python anywhere. C/C++/CUDA/GLSL only.

---

## Position in canon

This is **rig 3 (engine-side rendering verification)** per parent project spec §15.8 +
discovery 3B-U3. Sibling to:

- **Rig 1:** `proto/astra_nexus.cpp` — the 1009-line C++ math reference with 66 assertions (mathematical truth)
- **Rig 2:** `proto/textverse/` — the LLM bundle bench with 9-gate LCP (persona truth)
- **Rig 4:** `book/CANON.md` + `book/negative_space.md` — literary canon
- **Rig 5:** `AUDIT_*.md` + `DISCOVERY_*.md` — spec audit cadence

This is implementation #1 of the dual-implementation discipline (§15.7) for the visual
axis. UE5 plugin (per `WARP_PHYSICS_UE55_DEEPDIVE_2026-05-16.md`) will be implementation
#2. Both consume the same canonical math; both must produce identical visuals.

---

## License + distribution

Inherits parent ASTRA-7 license (MIT or Apache 2 — pending operator decision). Single-file
distributable: `astra_visualizer.exe` + `assets/` folder + this `README.md`. No telemetry,
no analytics, no network at runtime.

---

**Operator:** Bo Chen, Arlington, Texas
**Substrate:** Native Windows 11 + NVIDIA RTX 40/50-series, single-operator, locally deployed
**Authored:** 2026-05-16
