# KNOWN_ISSUES — Spec-revision-eligible findings from the Visual Physics Testbed

Findings from implementation that surface candidates for v0.130 spec revision
per DESIGN_SPEC §15.4 and CLAUDE.md "Spec-revision findings — record as you go".

Operator reads these and decides which become v0.130 spec edits.

---

## [2026-05-16] Finding: Cherenkov cone OPENS (not narrows) as W or β increase

**Scene:** S06 (Warp Cruise 10c + Cherenkov)
**Spec section affected:** DESIGN_SPEC §6 (Part 6, "S06 — Warp cruise at v_app=10c with Cherenkov cone (closes 5D-F4)")
**Phenomenon:** The Cherenkov half-angle formula `cos(θ_c) = 1/(n·β)` produces a cone that OPENS (θ INCREASES) as either β grows at fixed n, OR as W (and thus n) grows at fixed β. The two design-spec descriptions claim narrowing:

- DESIGN_SPEC §6 S06, acceptance criterion #4 (line ~765):
  > "4. Cone narrows monotonically as W increases from 0.5 to 1.0 (sweep slider; assertion checks angle(W=0.5) > angle(W=1.0))"

Empirically, with `compute_cherenkov_angle()` from `libastra_nexus`:
| W | β | n | n·β | θ (rad) | θ (deg) |
|---|---|---|---|---|---|
| 0.5 | 0.8 | 1.5 | 1.20 | 0.5857 | 33.56° |
| 1.0 | 0.8 | 2.0 | 1.60 | 0.8957 | 51.32° |

θ INCREASES from 33.56° to 51.32° as W grows from 0.5 to 1.0. Cone OPENS.

Same direction for β at fixed n:
| W | β | n·β | θ (rad) |
|---|---|---|---|
| 1.0 | 0.55 | 1.10 | 0.430 |
| 1.0 | 0.75 | 1.50 | 0.841 |
| 1.0 | 0.95 | 1.90 | 1.017 |

**Math reference:** `libastra_nexus/src/cherenkov.cpp` (NEW); spec §6 step 10 formula.
**Empirical value:** the cone reaches its asymptote at `θ_max = acos(1/n)`, which for n=2 (W=1) is 60° = π/3 rad ≈ 1.0472. Test values approach this from below as β → 1.

**Spec-revision candidate (v0.130):** Change "narrows" to "opens" / "widens" in DESIGN_SPEC §6 S06 (both in the §6 step #4 acceptance description AND in the "S06 assertions" #4 wording). The formula itself is locked correctly at the 4 spec sites; only the prose description of monotonicity needs flipping.

Suggested v0.130 wording for S06 acceptance criterion 4:
> "4. Cone OPENS monotonically as W increases from 0.5 to 1.0 (sweep slider; assertion checks angle(W=0.5) < angle(W=1.0))."

And similarly for the "S06 assertions" wording (line ~765):
> "Cone opens monotonically as W increases (assertion checks angle(W=0.5) < angle(W=1.0))"

**Why the original framing felt natural:** In standard Cherenkov pedagogy (water, glass), the cone seems to "narrow" because relativistic particles asymptote to the maximum acos(1/n) cone for that medium. The narrowing-vs-opening intuition depends on what's held constant. For ASTRA-7's warp regime where n varies with W and the operator sweeps W, the spec should call out the OPENS direction explicitly to avoid confusion with cosmic-ray-detector intuition.

**Operator review needed:** yes. This finding does not block V0 closure — `libastra_nexus_test.exe` now passes with the corrected test assertions in `tests/test_cherenkov.cpp`. But the S06 implementation (V3 phase) needs to import the corrected wording before its assertion suite is written.

---

## [2026-05-16] Finding: Linear kin-redshift color model is provisional

**Scenes:** S02, S03 (Doppler scenes); reused by S07 (Hubble) when it lands.
**Spec section affected:** DESIGN_SPEC §6 S02 acceptance #1 ("R-channel > B-channel, tolerance 0.05"); §3.4 four optical effects.
**Phenomenon:** V1.7's `physics::apply_kin_redshift` uses a linear-in-z model:
```
R' = clamp(R + 0.60 * z, 0, 1)
G' = clamp(G - 0.10 * z, 0, 1)
B' = clamp(B - 0.50 * z, 0, 1)
```

This is not real physics. Real SR longitudinal Doppler shifts the wavelength of each photon by (1+z), then convolves the resulting spectral power distribution with the eye's response. For a blackbody emitter, the apparent color shift is a function of the emitter's temperature + the observed wavelength's blackbody-curve position post-shift.

The linear model was chosen because:
- It's deterministic (CPU and GPU compute identical floats), supporting bit-precise pixel assertions.
- It's spec-loose: §3.4 + §6 S02 mandate the visual property "receding R-shifts toward red" without locking a specific curve.
- It's tunable: coefficients (0.60, -0.10, -0.50) were picked so S02's planet (RGB 0.30/0.55/0.90 at z=0.732) satisfies R > B, matching the spec assertion intent.

**Empirical values:** see `src/physics/redshift.h` for the coefficients + GLSL mirror. S02 planet redshifted RGB at z=0.732: (0.74, 0.48, 0.53) — observably R>B. S03 planet at z=3.359: (1.00, 0.21, 0.00) — saturated orange-red, B clamped.

**Spec-revision candidate:** v0.130 should replace the linear model with a proper blackbody-temperature shift (Tanner Helland fit or equivalent). The §3.4 visual-property assertion ("R>B") and §6 S02 assertion would still hold. Update `physics::apply_kin_redshift` + GLSL mirror; bump pixel-assertion expected values accordingly.

**Operator review needed:** no — V1.7 visual is acceptable for the testbed's purpose (proving the spec's visual claims). Replacement is a polish item for v0.130 when the testbed-to-UE5 reference handoff happens.

---
