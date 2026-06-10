# KNOWN_ISSUES.md — accepted gaps + deferred work + spec candidates

Honest accounting of what V1 ships without, what's deferred to which future phase, and what should be promoted to a v0.130 spec revision candidate per parent project's §15.4 discipline ("revise on findings"). Per CLAUDE.md §9 / BUILD_LOG.md.

---

## Open hard gate

### V5 operator sign-off on Scene S05 — STILL PENDING

The S05 mechanical gate is green (apparent_rate = -1.0 exact; the orbit-phase math runs backward). The **visual** confirmation by the operator is the hard gate per CLAUDE.md §3.2 + §7. Until the operator personally watches S05 and confirms the orbital ring runs backward at v_app=+2c, V5 is mechanically green but not canonically complete.

**Sign-off checklist** lives in `BUILD_LOG.md` under the V5 entry. Run `build\astra_visualizer.exe --scene=S05`, follow the 7 steps, append `[YYYY-MM-DD V5-SIGN-OFF] S05 orbit reversal confirmed` at the bottom of `BUILD_LOG.md`.

---

## Deferred to v1.1+

### Full FBO-based gravitational lensing (S08)

V8 ships **lensing-lite**: a per-channel RGB ray-offset in the warp_volume fragment shader that creates a subtle chromatic shimmer at the bubble boundary. The shimmer suggests refraction but is not a true ray-deflection-through-gradient post-pass.

**Path forward:** add an FBO render target that captures the scene to a color texture, then a post-pass fragment shader that samples the FBO at deflected positions based on `∇W` from the warp_volume 3D texture. This needs FBO infrastructure (deferred from V9 too because the hidden-window framebuffer was sufficient for goldens). When V10/V11 polish lands FBO scaffolding, lensing slots in cleanly.

### Real CFD-baked RBF warp field (replaces analytical bubble)

V5 ships an analytical Alcubierre-shape approximation: `W(r) = max(0, 1 - r²/R²)²`. DESIGN_SPEC §1.2 names this as v1.1 territory. A real CFD-baked RBF network (50-200 Gaussian nodes from OpenFOAM output) would replace `kernels/warp_field.cu`'s body without touching the host-side `WarpFieldParams` struct or any scene code.

### NNE / TensorRT real Reflex inference (replaces PID stub)

V7's ReflexStub is a host-side PID controller. The eventual real Reflex is a small ONNX / TensorRT model loaded at startup, called with the chaos amplitude vector, returning a control vector. DESIGN_SPEC §1.2 non-goal. PID stub validates the CONTRACT (input/output shapes, feedback closes the loop visibly); the inference backend is independent.

### S08 black-hole disc render + true gravitational lensing

V7 ships the regime composition + α_eff display in S08 but NOT the BH disc. DESIGN_SPEC scene S08 calls for "BH as black disc with subtle gravitational lensing." This wants the FBO post-pass (above), plus a black sphere render. Polish-tier work.

### Doctest unit test layer

CLAUDE.md §14 done criteria item 15 lists doctest tests for: pixel_sampler, rbf_eval, chaos_pde_step, observation_calc_kernel, cherenkov_math_bridge. Each is currently tested indirectly:

- `pixel_sampler`: exercised in headless mode (12 scene runs)
- `rbf_eval`: not present (analytical bubble; deferred)
- `chaos_pde_step`: exercised in S09 (visible feedback loop) + headless smoke
- `observation_calc_kernel`: tested in libastra_nexus (75 assertions); the GPU version doesn't exist yet
- `cherenkov_math_bridge`: tested in libastra_nexus (4 Cherenkov assertions) + S06 scene

A standalone doctest suite for these would be redundant given the integration tests. Documenting as accepted gap; if a regression motivates per-module unit tests, add them then.

### Real audio synthesis for S12

DESIGN_SPEC §1.2 non-goal: "Audio synthesis (sibling testbed; UI audio-frequency display only for S12)." V8's S12 renders the Hz value as a UI numeric. A miniaudio-based actual playback layer is a sibling-project concern; the eye/ear decoupling effect is fully visible without audio.

### MP4 video recording (`--record=png-seq` etc.)

README mentions `--record=png-seq` but it's not implemented; F12 single-shot screenshot is the V1 mechanism. PNG sequences can be assembled via ffmpeg externally if needed.

### Hash-grid SDF for hull (Instant-NGP style)

DESIGN_SPEC §8 stretch. V1 ships a procedural blended-wing-body mesh; instant-NGP-style spatial hash is a memory-savings optimization for high-poly meshes that isn't relevant at our 4096-tri scale.

### Linux x86_64 build path

Parent Platform Discipline allows Linux as the permitted second platform; V1 ships Windows only. `tools/build.bat` is Windows-specific; an equivalent `tools/build.sh` + cross-platform OS detection in `util/log.cpp::exe_directory()` (currently `#ifdef _WIN32` only) would unlock the Linux path. ~1 day of work.

### Performance profiler panel

CLAUDE.md §14 item 7 lists "per-pass GPU timing visible in profiler panel". V1 ships frame-time + FPS in the State panel; per-pass GPU timings via cuEvent / GL queries are doable but absent.

---

## Findings → v0.130 spec revision candidates

Per parent project §15.4 ("revise on findings"), the V0-V9 implementation surfaced these spec-amendable items. Forward to operator for v0.130 review:

### DESIGN_SPEC §4.5 Cherenkov-cone monotonicity wording (V0 finding)

Original spec text asserted "cone narrows as W increases at fixed beta." Physics is the opposite: `cos(theta_c) = 1/(n*beta)` with higher W → higher n → larger nβ → smaller cos → LARGER theta. Cone WIDENS. Spec amended in V0; v0.130 candidate to mirror upstream.

### Float-slider → double-promotion tolerance standard (V4 finding)

ImGui SliderFloat constraints make scene-tunable values float; `(double)0.9f` differs from literal `0.9` at ~1e-7. Cross-evaluation tolerance for slider-driven assertions adopted as **1e-6 absolute**, distinct from libastra-internal 1e-9 / 1e-12. Worth documenting in spec §10 validation methodology.

### Float-precision sqrt path divergence (V7 finding)

`std::sqrt(1.0 - 1.0/100.0)` vs the multi-step Schwarzschild path through `compute_grav_factor` diverge at ~2e-11 due to intermediate reorder. Same 1e-9 tolerance standard applies. Documented in S08 assertion code.

### V3 CUDA-GL interop pattern (recorded V3, refined V7)

The `cudaGraphicsMapResources` / `cudaCreateSurfaceObject` / launch / destroy / unmap sequence is now standard in WarpVolume, ChaosField. Worth promoting to a spec §8 ("subsystems") code-pattern entry rather than each new subsystem re-discovering it.

---

## Things NOT in this list (= shipped clean)

- Math layer: libastra_nexus, 75 / 0
- Renderer: hull + starfield + warp volume + chaos field + Cherenkov cone + named bodies + wake trail + split-screen
- All 12 scenes ship with assertions
- Headless mode + JSON report + 12 golden PNGs + CI script
- Static linkage: no DLL deps beyond Windows OS + NVIDIA driver
- Build clean under VS 2022 + CUDA 13.1 + MSVC 14.43
- BLOCKERS.md absent (no unresolved blockers)

---

**Operator:** Bo Chen
**Last review:** 2026-05-16 (V10 docs pass)
