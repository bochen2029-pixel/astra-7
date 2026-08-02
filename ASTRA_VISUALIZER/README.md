# ASTRA-7 Visual Physics Testbed

A standalone Windows 11 / Linux executable that renders 12 visual physics scenes demonstrating ASTRA-7 spec v0.129's claimed phenomena. Engine-agnostic ground-truth between the math (`libastra_nexus`) and the eventual UE5 rendering.

**Status: SUPERSEDED — read for provenance only.** Active work moved to the sibling `ASTRA_VISUALIZER_02/`, which shipped v0.1.0 on 2026-05-16.

*(Corrected 2026-08-02. This line previously read "specification phase," which was never true after the first build session: implementation reached **V1.13 = 12/12 scenes, 100/100 assertions, complete spec coverage**, then V1.14 QC + bubble alpha polish on 2026-05-17. The README was simply never updated post-build. See `BUILD_LOG.md` for the actual arc.)*

Remaining open items from this rig, carried forward rather than finished here: operator S05 sign-off, Layer-2 heatmap-diff, golden capture, optional CUDA port of the S09 chaos PDE. Two spec-revision empirical findings originated here and still stand: the Cherenkov "narrows→opens" wording (V0) and the linear kin-redshift model (V1.7).

---

## What this is

This is a research instrument. Its job: show that the math in `proto/astra_nexus.cpp` actually produces the visual phenomena the spec describes — a warp bubble, a Cherenkov cone, an orbit running backward at v_app > c, geometric lensing, chaos field instability, eye-ear decoupling at warp egress.

The math is proven (66 C++ assertions in `astra_nexus`). The visuals are not. This testbed is the visual proof.

It is also **rig 3** per spec §15.8 (engine-side rendering verification), implementing closure of the **AUDIT 5D-F4 Cherenkov gap** by adding `compute_cherenkov_angle()` to a copy of `astra_nexus` extracted INTO this sandbox as `libastra_nexus`.

---

## Quick start (after implementation lands)

### Prerequisites
- Visual Studio 2022 17.8+ with MSVC 14.43 toolset
- CUDA Toolkit 12.4+ (13.x preferred)
- CMake 3.27+
- NVIDIA GPU with compute capability ≥ 8.9 (RTX 40-series Ada or newer)

### Build (Windows 11)
```bat
:: From "x64 Native Tools Command Prompt for VS 2022"
cd /d C:\ASTRA-7\ASTRA_VISUALIZER

cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

### Run interactive
```bat
.\build\astra_visualizer.exe
```

A window opens; ImGui scene selector on the left; viewport in the center; live state + validation overlay on the right.

### Run headless (CI)
```bat
.\build\astra_visualizer.exe --headless --scene=all --output=ci_results\
```

Dumps 12 PNGs + `report.json`. Exit code 0 iff all assertions PASS.

### Jump to specific scene
```bat
.\build\astra_visualizer.exe --scene=S05_WarpCruise2c
```

---

## Controls (interactive mode)

| Key | Action |
|---|---|
| WASD | Camera move (free mode) |
| Q/E | Camera up/down |
| Mouse drag | Camera look |
| 1-9 | Select scenarios 1-9 |
| Shift+1, +2, +3 | Scenarios 10, 11, 12 |
| Space | Pause/resume |
| R | Reset current scenario |
| F1 | Help overlay |
| F12 | Screenshot (PNG + JSON state) |
| Esc | Quit |

---

## The 12 scenes

| # | Name | Tests | Spec section |
|---|---|---|---|
| S01 | RestBaseline | render works; libastra agrees | §1.1, §1.2 |
| S02 | StlRecede05c | SR Doppler at β=0.5 | §3.4 |
| S03 | StlRecede09c | SR Doppler at β=0.9; aberration | §3.4 |
| S04 | WarpCharge | bubble forms over W=0→1 ramp | §6 step 4 |
| **S05** | **WarpCruise2c** | **orbit reversal at v_app=2c** ← THE PAYOFF SCENE | §3.11 |
| S06 | WarpCruise10cCherenkov | 9× reverse + Cherenkov cone | §6 step 10 (closes 5D-F4) |
| S07 | Warp8000cHistoryBound | source disappears (not faded) | §3.11 |
| S08 | WarpGravityWell | composition rule visible | §3.2, §7.1, §7.4 |
| S09 | ChaosInstabilityReflex | chaos blooms; Reflex damps | §7.1, §2.3.1 |
| S10 | HubbleHorizon | body frozen + dim | §3.12 |
| S11 | SplitScreenStlVsWarp | regime-dispatch real | §3.11 |
| S12 | EyeEarDecoupling | endogenous vs exogenous | §6.3, §8.3 |

Scene S05 requires final operator sign-off for v1.0 release (operator personally watches the orbit reversal and confirms).

---

## Three-layer validation

1. **Pixel-level scalar assertions** — `glReadPixels` at canonical pixel; compare against `libastra_nexus` math; PASS/FAIL.
2. **Heatmap diff** — full PNG vs golden reference; mean-pixel-diff < 1% tolerance.
3. **Side-by-side numeric overlay** — live ImGui display of rendered value vs libastra value vs diff with PASS/FAIL color.

CI mode writes JSON test report; exit code gates on `summary.scenes_failed == 0`.

---

## Documentation

- [CLAUDE.md](CLAUDE.md) — operating contract for the coding agent (sandbox rules, mission, authority, build pipeline, done criteria)
- [DESIGN_SPEC.md](DESIGN_SPEC.md) — technical specification (~2000 lines)
- [BUILD_LOG.md](BUILD_LOG.md) — append-only log of build sessions
- [docs/SCENES.md](docs/SCENES.md) — per-scene walkthroughs (written during implementation)
- [docs/VALIDATION.md](docs/VALIDATION.md) — three-layer methodology details
- [docs/BUILD.md](docs/BUILD.md) — detailed Windows + Linux build instructions
- [docs/KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) — findings surfaced; v0.130 spec-revision candidates
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — per-phase landings

---

## Position in canon

Sibling to `C:\Buddhabrot_CUDA\` — same autonomous-build pattern, same operator-sovereignty discipline, same MIT/Apache-2-on-decision licensing path. Same CLAUDE.md / DESIGN_SPEC.md / BUILD_LOG.md / BUILD_COMPLETE.md flow.

ASTRA-7 spec basis: `C:\ASTRA-7\docs\spec-v0.129-tentative-2026-05-16.md`. Math basis: `C:\ASTRA-7\proto\astra_nexus.cpp` (extracted INTO this sandbox as `libastra_nexus/`).

---

## License

To be selected at v1.0 ship (operator decision: MIT or Apache 2.0; likely Apache 2.0 per cross-canon discussion).

---

**Operator:** Bo Chen — Arlington, Texas
