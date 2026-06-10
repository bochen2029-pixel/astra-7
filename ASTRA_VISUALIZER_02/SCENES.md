# SCENES.md — operator walkthrough

The visualizer ships 12 scenes (S01 — S12). Each is a focused demonstration of one physics phenomenon from the ASTRA-7 14-equation framework. All scenes share the same UI shell (scene picker top-left; per-scene parameter panel; state-display + PASS/FAIL panel on the right; global PhysicsCalc bottom-left).

Navigation: `1`-`9` selects S01-S09; `Shift+1` / `Shift+2` / `Shift+3` selects S10 / S11 / S12. Click the dropdown for any scene.

Each scene's `value_assertions()` evaluates every frame (live in the right-side panel). `pixel_assertions()` fire only in `--headless` mode (camera snapped to canonical pose). Golden-image diff is also headless-only.

---

## S01 — RestBaseline

**Spec:** §1.1 AstraCoord, §1.2 two-clock, §3.3 REST regime.

**What you see:** Hull (procedural blended-wing-body, 4096 tris), 10K-star backdrop, sun + planet billboards.

**Numerics:** γ = 1.000000, β = 0.000, dτ/dt = 1.000000, regime = REST (0x00).

**Assertions (4):** gamma_at_rest = 1; beta_at_rest = 0; dtau_dt_at_rest = 1; sun pixel R >= 0.7.

---

## S02 — STL Recede 0.5c

**Spec:** §3.4 four optical effects, §3.7 rapidity, §3.11 apparent_rate STL_REL path.

**What you see:** Same shell as S01; planet billboard mildly redshifted (R bright, B suppressed) reflecting `z_kin(0.5c) ~ 0.732`; starfield warped by SR aberration toward forward direction.

**Numerics:** apparent_rate = √(1/3) ≈ 0.5774, γ = cosh(atanh(0.5)) ≈ 1.1547, z_kin ≈ 0.732.

**Tunable:** `beta` slider in [-0.99, 0.99].

**Assertions (5):** apparent_rate matches SR Doppler formula; γ matches canon; regime dispatch (STL ≠ WARP at same v); planet R high; planet B suppressed.

---

## S03 — STL Recede 0.9c

**Spec:** §3.11 + §3.4 at dramatic β.

**What you see:** Planet deep red, B-channel suppressed to ~0.02; starfield more compressed forward (stronger aberration).

**Numerics:** apparent_rate ≈ 0.2294, γ ≈ 2.294, z_kin ≈ 3.36.

**Tunable:** `beta` slider in [-0.99, 0.999].

**Assertions (4):** apparent_rate matches formula; γ matches; planet R high; planet B near zero.

---

## S04 — Warp Charge

**Spec:** §3.3 regime transitions, §6 step 4 smooth-min blend, §6.1 CFD validity.

**What you see:** Warp bubble fades in over `charge_duration_s` (default 5s) — violet-blue volume with cyan boundary at high |∇W|. Regime ramps from WARP_CHARGE (W < 1) to WARP_CRUISE (W == 1).

**Numerics:** dτ/dt at W=1 = `f_warp(1) * grav * 1/γ_kin = 0.5 * 1 * 1 = 0.5`.

**Tunables:** charge duration, bubble radius (m). Reset clock button.

**Assertions (1):** composition rule canon — `dtau_dt_cosmic(1.0, 1.0, 1.0, true) = 0.5`.

---

## S05 — Warp Cruise 2c — **THE PAYOFF (operator sign-off pending)**

**Spec:** §3.11 retarded-time observation; §6.3 ObservableState; §10 validation row "Retarded-time orbit reversal"; canon test at `proto/astra_nexus.cpp:639-677`.

**What you see:** Rear-view ship at v_app = 2c receding. Sun billboard at infinity. A planet orbits the sun on a visualization-scaled ring (8.6° angular radius for visibility; real 1 AU orbit at 1 ly is ~1e-5 rad). **At v_app = 2c the orbit visibly runs BACKWARDS** because apparent_rate = -1.0 makes `d(t_emit)/d(t_cosmic) = -1`. Slide v_app to 0 — orbit forward. To +1c — frozen. To -2c — forward at +3x.

**Numerics:** apparent_rate = -1.0000 (exact); planet orbital phase advances negatively at one cosmic-year per wallclock-second-of-sim (default sim_speedup = 1 day/sec).

**Tunables:** v_app (c), orbit period, sim speed (cosmic seconds per wallclock second), W, reset clock.

**Assertions (2):** apparent_rate at canonical 2c = -1; slider-driven rate matches `compute_apparent_rate`.

**Operator sign-off:** required per CLAUDE.md §3.2 + §7. Run the scene; confirm the seven-point checklist in `BUILD_LOG.md [V5]`; record sign-off line at the bottom of `BUILD_LOG.md`. Until then, V5 is mechanically green but not canonically complete.

---

## S06 — Warp Cruise 10c + Cherenkov

**Spec:** §6 step 10 Cherenkov formula; AUDIT 5D-F4 closure (math in V0; visual in V6).

**What you see:** Side-view ship + bubble + a translucent cyan-blue cone opening forward along the ship velocity axis. Cone half-angle = `acos(1 / (n * |β|))` with `n(W) = 1 + W`. At W=1, β=10 → angle ≈ 87.13°. Slider β below threshold → "Cherenkov inactive".

**Numerics:** apparent_rate at v=10c = -9.0; cone angle at canonical (W=1, β=10) = 1.52078 rad.

**Tunables:** v_app, W, bubble radius, cone length.

**Assertions (3):** apparent_rate at v=10c = -9; cone angle = `acos(1/20)` exactly; inactive sentinel = -1 below threshold.

---

## S07 — Photon-Source-History

**Spec:** §3.11 photon-source-history bound; ObservableState.beyond_photon_history flag.

**What you see:** Star at 1 ly behind ship; ship moves +z at v_app = 8000c. As cosmic time advances, t_emit drops faster than t_cosmic until t_emit < the star's `t_source_start` epoch. At that instant the star **DISAPPEARS** from the frame — discrete, not faded. The state panel flips `beyond_photon_history = TRUE`.

**Numerics:** Discrete transition aligned with the canon flag.

**Tunables:** v_app, t_source_start (years relative to scenario start), sim speed.

**Assertions (2):** the flag's true/false transitions correctly across the canonical reference observations.

---

## S08 — Warp + GravityWell

**Spec:** §3.3 regime composition; §7.1 chaos `α_eff = α_base · (1 + k·M·L²/r³)`; §7.4 Warp Exclusion Zone.

**What you see:** Warp bubble + state panel showing composite regime bitmask `WARP_CRUISE | GRAVITY_WELL = 0x28`. Schwarzschild factor √(1 - r_s/r) live in the panel. α_eff live too. (V1 omits the BH disc render; deferred to v1.1.)

**Numerics:** at r = 100 r_s, M = 10 M_sun: grav = √(1 - 1/100) ≈ 0.99499; dτ/dt_cosmic at W=1, grav=0.995 = 0.5 * 0.995 ≈ 0.49749.

**Tunables:** BH mass (M_sun), ship r (in r_s units), L lengthscale, α_base, k coupling, W.

**Assertions (3):** Schwarzschild identity; regime bitmask = 0x28; composition rule.

---

## S09 — Chaos + Reflex

**Spec:** §7.1 chaos PDE (Fisher-KPP); §2.3.1 Reflex Contract (v0.129 NEW); §1.5 double-buffered field.

**What you see:** 128³ chaos scalar field rendered via heat colormap (purple → red → yellow). Toggle "Reflex enabled" off → chaos grows unbounded; toggle on → PID controller computes β cubic damping → field shrinks toward setpoint. Manual injection slider adds new seeds. Emergency dump fires + clears when χ ≥ 0.90 threshold.

**Numerics:** Real Fisher-KPP forward-Euler step at 1/60 s, D ≤ 1, CFL-safe.

**Tunables:** Reflex enabled, Emergency armed, α_base, D, manual_inject.

**Assertions (1):** regime bit value witness. Live PDE behaviour is operator-visual.

---

## S10 — Hubble Horizon

**Spec:** §3.12 cosmological expansion; ObservableState.beyond_hubble_horizon flag.

**What you see:** Distant body rendered with extreme redshift tint. At `distance < 13.8 Gly` (Hubble horizon @ H₀=70), the tint smoothly redshifts with z_cosmo. At `distance > 13.8 Gly`, the body locks at the horizon-crossing dim-red tint — FROZEN — per spec.

**Numerics:** beyond_hubble_horizon flag matches canon §3.12 reference observations.

**Tunables:** distance (Gly).

**Assertions (2):** flag true at 100 Gly; flag false at 1 Gly.

---

## S11 — STL vs WARP Split-Screen

**Spec:** §3.11 regime dispatch; §10 validation row "STL_REL formula was NOT 1/γ"; voyage-demo anchor at `proto/astra_nexus.cpp:537-588`.

**What you see:** Screen split in half. Left = STL_REL ship at v_radial=0.5c, planet mildly redshifted, starfield aberrated. Right = WARP_CRUISE ship at v_app=0.5c, warp bubble visible, planet white. State panel shows both apparent_rates side-by-side: 0.5774 (STL) vs 0.5000 (WARP). The gap proves regime dispatch.

**Numerics:** STL = √(1/3) = 0.5774; WARP = 1 - 0.5 = 0.5; |Δ| = 0.0774.

**Tunables:** v_radial.

**Assertions (3):** both formulas exact at canonical v=0.5c; gap > 0.05.

---

## S12 — Eye-Ear Decoupling

**Spec:** §6.3 + §8.3 endogenous/exogenous; book `CANON.md` cycle 1 endogenous/exogenous vocabulary.

**What you see:** Rear-view ship at WARP_CRUISE 2c. State panel shows TWO clocks:

- **AUDIO (t_cosmic = NOW):** live warp drone frequency in Hz.
- **VISUAL (t_emit, retarded):** t_emit (~1 yr ago at 1 ly + warp recession).

Press the "Disengage warp (emergency)" button. AUDIO Hz **snaps** immediately to shutdown drone. VISUAL t_emit continues at the retarded value until light catches up. The book canon endogenous/exogenous gap is now visually concrete.

**Numerics:** at WARP 2c with 1 ly geometry, t_cosmic - t_emit ≈ 3.156e7 s (1 cosmic year).

**Tunables:** v_app, sim speed, audio drone Hz, audio shutdown Hz, disengage/re-engage warp.

**Assertions (2):** lookback ≈ 1 yr at 1 ly; apparent_rate at v=2c WARP = -1.

---

## Picking a scene to start with

- **First time:** S01 (sanity), S02 (the SR Doppler tint), S05 (THE PAYOFF — orbit reversal), S11 (regime-dispatch proof).
- **Math gut-check:** open the PhysicsCalc panel (bottom-left); pick a preset; watch ObservableState change live.
- **Stress test:** S09 with Reflex disabled + manual injection slider cranked; emergency dump trigger.
- **Book-canon read:** S12 with sim_speedup set lower so you can watch the audio Hz snap while the visual t_emit lags.

---

**Operator:** Bo Chen
**Sign-off pending:** Scene S05 visual confirmation (the orbit running backwards at v_app=2c).
