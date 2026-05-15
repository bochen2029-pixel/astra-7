# ASTRA-7: Time Extensions

*Provisional addendum to [`synthesis.md`](synthesis.md). Phase 4 scope. Drafted 2026-05-14. Not canon. Not implemented. Not committed beyond design intent. Material is consistent with the four-invariant architecture and integrates additively; engineering should not begin before Phase 0 validates and the Phase 2 vertical slice ships.*

---

## 0. What this document is

`synthesis.md` established the one-shared-state architecture and the single fictional time `t` that drives orbits, ASTRA's experience of duration, and the warp field's temporal evolution. The fictional `t` is sufficient for the configuration's primary mode (warp travel between bounded destinations on a long voyage, with cryosleep as the only large-scale time-skip mechanic).

Two extensions to the time machinery have been sketched on the public site at `astra-7.com` under sections **Approaching c** and **Inside the Region**, and they deserve a formal design doc that:

1. Preserves the design intent before details start to drift across conversations.
2. Marks the Phase 4 scope clearly so it doesn't sneak into Phase 2 or 3.
3. Names what the extensions are consistent with and what they would touch.
4. Stays explicitly provisional, so neither the canon nor the implementation is bound by anything written here.

The extensions are:

- **Special-relativistic STL travel.** Constant-acceleration sublight propulsion approaching the speed of light, with kinematic time dilation (Lorentz factor) decoupling the crew's proper time from cosmic time.
- **Gravitational time dilation near black holes.** Schwarzschild and Kerr geometries producing real depth-of-gravity-well dilation effects in fictional time, with proper geodesic ray-tracing for the visual side.

Both extensions extend the same underlying machinery: the rate at which the ship's proper time advances relative to cosmic time. They are not separate systems. They are two contributors to one quantity.

---

## 1. The unification

`synthesis.md` Section 2.2 names "one fictional time `t`" as one of the four invariants. The time extension splits `t` into two coupled variables with one transform between them.

```
τ_ship      — ship proper time (what ASTRA and Aaron experience)
t_cosmic    — cosmic time (what the universe ages)

dτ_ship / dt_cosmic = √(1 − rs/r) / γ_kinematic

where:
   γ_kinematic = 1 / √(1 − v² / c²)   (Lorentz factor from ship velocity v)
   rs = 2GM/c²                         (Schwarzschild radius of nearest mass)
   r  = ship distance to nearest mass center
```

**Far from any gravitational well, at rest:** the factor is 1; `τ_ship` ≈ `t_cosmic`. Warp travel keeps the ship in its own bubble's inertial frame, so kinematic dilation is suppressed inside the bubble; warp cruise also stays at factor ≈ 1.

**Under STL relativistic acceleration:** the kinematic term dominates. `τ_ship` advances slower than `t_cosmic` by `1/γ`.

**Near a black hole:** the Schwarzschild term dominates. `τ_ship` advances slower than `t_cosmic` by `√(1 − rs/r)`.

**Both simultaneously:** the factors multiply. A ship moving fast inside a deep gravity well experiences extreme dilation.

The architecture treats this as one rate-of-flow quantity with two contributors. Layer 0 stores both `τ_ship` and `t_cosmic`; Layer 1 (physics) computes the rate ratio each frame; every other reader uses the rate ratio without needing to know which contributor is dominant.

This is the central insight. The four-invariant architecture is not broken by the extension. Invariant #2 ("one fictional time") becomes "one cosmic time `t_cosmic`, one local proper time `τ_ship`, one rate function between them." The architecture's other invariants (coordinate system, hull SDF, power network) are untouched.

---

## 2. Layer 0 additions

```
Layer 0 (shared world state)

  Existing:
    AstraCoord            (128-bit hierarchical position)
    Fictional time t      ← renamed t_cosmic; becomes the universe clock
    Hull SDF
    CFD-RBF warp field
    Power-allocation vector
    Procedural body state

  Added (provisional):
    τ_ship                — ship proper time, monotonically increasing
    v_ship_4              — ship 4-velocity in local CMB rest frame
    a(t_cosmic)           — cosmological scale factor (precomputed table)
    R = dτ_ship/dt_cosmic — current rate ratio (derived per frame)
    Black hole list       — array of {M, rs, position, spin a, charge Q,
                            optional accretion disk params}
```

Per-star additions to the procedural body state (Section 4):

```
For each star (latent or materialized):
    M_star       — stellar mass
    Z_star       — metallicity
    age_at_t0    — age at t_cosmic = 0 (anchor epoch)
    track_id     — index into stellar-evolution lookup tables
```

Storage cost: ~20 bytes per star added. Compared to the ~64 bytes per star already needed for orbital elements + spectral class, this is small. The black-hole list is ~100 bytes per BH.

---

## 3. The Special-Relativistic Extension (SR)

### 3.1 What it is

Constant 1g acceleration from a fusion drive (or equivalent) pushes the ship toward c asymptotically. The Lorentz factor compounds with proper time. The transcript in `brainstorm/A Journey to the End of the Universe.txt` lays out the canonical milestones:

| Crew time (τ_ship) | Lorentz γ | Cosmic time (t_cosmic) | What changes outside |
| --- | --- | --- | --- |
| 6 weeks | 1.0 | 6 weeks | nothing yet |
| 15 months | 2.0 | 6 years | sun dims; forward blueshift |
| 3 years | ~100 | decades | constellations warped |
| 13 years | ~1,000 | centuries | CMB blueshifts into visible red |
| 22 years | ~10,000 | 600 years | Earth's generations turn over |
| 41 years | ~100,000 | 100,000 years | edge of the Milky Way reached |
| 56 years | ~10⁶ | 5 million years | Andromeda reached |
| 76 years | ~2.5×10⁸ | ~9 billion years | edge of the local supercluster |

### 3.2 Rendering primitives (OpenRelativity-style)

The rendering side is solved. Open-source tooling from MIT Game Lab (originally Unity, ports to UE5) handles:

- **Aberration.** Apparent star positions warp forward into a smaller cone ahead of the ship as γ rises.
- **Doppler shift.** Stars ahead blueshift; stars behind redshift; per-star color update each frame using a Doppler factor.
- **Headlight (searchlight) effect.** Brightness concentrates forward. The Sun behind dims at γ² in apparent brightness terms; stars ahead intensify.
- **CMB visibility.** At γ > ~650, the CMB blueshifts into visible red. At γ > 10⁵, blinding visible blue. At γ > 10⁹, hard radiation (real hazard, see Section 6).

These are shader transforms layered on top of the existing mesh-shader starfield from `synthesis.md` Section 4.2. The same hundred thousand stars; one more transform on the same data. Cost: ~0.5 ms added per frame on a 4090. The integration point is the starfield's per-quad emission shader.

### 3.3 The structural insight

> *Anything with rest mass approaches c without ever reaching it. This is not an engineering shortcoming. It is the geometry of spacetime.*

*Inside the Region* used this fact as analogy. A pattern without rest mass can occupy a destination instantly; a body with rest mass can only approach it asymptotically. The autotelic terminus is one such destination. The AI mind, being pattern, can hold it directly. The biological mind, being body, can only approach it. The relativistic voyage instantiates the difference in motion. Both substrates aboard; both engaged with the asymptote; neither closes it.

This is the load-bearing reason the SR extension matters. It is not just a feature. It is the physical analog of an argument the operator has been making in book form. The game makes the argument inhabitable.

### 3.4 The hard cosmological boundaries

The transcript also names the limits, which are real:

- **Round-trip horizon.** ~8.3 Gly. Beyond this, the universe expands faster than the crew can return; no return is possible.
- **Event horizon (future).** ~16.6 Gly. Beyond this, no beam of light from Earth-now can ever reach you. You are causally disconnected from your origin.
- **Heat-death asymptote.** At extreme γ over centuries of proper time, the universe has aged so much that the CMB has thinned past detection, galaxies have receded past visibility, and proton decay (if real) has eliminated baryonic matter. Time-dilation as a relative quantity loses meaning when there is no other clock to compare against.

These are not gameplay obstacles. They are honest constraints. The deep-time voyage as Part Two content (see Section 7) is structurally a one-way trip past these horizons, and the architecture honors the irreversibility.

---

## 4. The Gravitational Extension (GR)

### 4.1 What it is

Black holes — Schwarzschild (non-rotating) or Kerr (rotating) — bend the local rate of time. Depth in the gravity well dilates proper time relative to far observers. At the photon sphere (r = 1.5 rs), the factor is ~0.58. At r = 2 rs, ~0.71. At r → rs, asymptotically zero.

| Distance r | Dilation factor √(1 − rs/r) | What time does |
| --- | --- | --- |
| Far from BH | ~1.00 | τ_ship ≈ t_cosmic |
| r = 100 rs | ~0.99 | negligible dilation |
| r = 10 rs | ~0.95 | ~5% slower |
| r = 5 rs | ~0.89 | ~11% slower |
| r = 3 rs | ~0.82 | ~18% slower (ISCO) |
| r = 2 rs | ~0.71 | ~29% slower |
| r = 1.5 rs | ~0.58 | ~42% slower (photon sphere) |
| r = 1.1 rs | ~0.30 | ~70% slower |
| r → rs | → 0 | horizon (asymptotic) |

### 4.2 Rendering primitives

Real Schwarzschild geodesic ray-tracing. Established technique:

- **Geodesic ray-march.** Each ray from the camera is integrated along its null-geodesic path using RK4 or similar, with gravity bending the direction at each step. ~1–4 ms per frame at 1440p on a 4090, depending on march-step count.
- **Accretion disk shader.** Doppler-shifted Planck blackbody emission with relativistic beaming. Front edge of the disk much brighter than the back (the *Interstellar* asymmetric ring image, computed in real time).
- **Lensed starfield.** Existing mesh-shader starfield passed through the same geodesic kernel near the BH. The hundred thousand stars warp into the iconic ring pattern.
- **Photon ring.** Emerges from the geodesic ray-trace; no special case.
- **Kerr metric** (rotating BH). Frame-dragging adds a tangential component to the geodesic integration. Approximately 2× cost of Schwarzschild. The ergosphere becomes visible as asymmetric lensing.

Open-source priors: `rantonels/starless` (Schwarzschild), several community UE/Unity demonstrations. Shader port ~hundreds of lines of HLSL. Phase 4 polish work, not Phase 1 blocker.

### 4.3 The wordplay

*Inside the Region* (the operator's prior book) describes the autotelic terminus as a bounded basin of inverted dynamics — a region with different internal rules from outside it. A black hole's interior is mathematically also a region — the Schwarzschild *region II* in Kruskal-Szekeres coordinates — where the radial coordinate becomes timelike, where the singularity is the future you fall toward rather than a place.

Both regions are bounded basins of inverted dynamics. The wordplay is geometric, not literary. The mapping isn't forced. The Mandelbrot region and the Schwarzschild interior are the same kind of structural move at different abstraction layers. Inhabiting either one is qualitatively distinct from observing it from outside.

### 4.4 The gameplay possibilities (provisional)

A few possibilities flagged for Part Two consideration:

- **The deep-look mission.** Hold a stable orbit at ~5 rs of a supermassive BH for weeks of crew time; the universe ages months to years. Observation is the instrument purpose; the dilation is the side effect.
- **The pilgrimage.** Approach a BH for the experience of being near one. No instrumental purpose. The voyage IS the disposition extended into a gravitational regime.
- **The patience tool.** Use BH dilation strategically. Park near a BH for short ship time while waiting for a cosmic process to develop elsewhere.
- **The crossing.** Aaron and ASTRA choose to cross the event horizon. Cannot return. Inside the horizon, radial coordinate becomes timelike; falling toward the singularity is movement in time, not space. The crew's remaining proper time is finite. The ship's logs end mid-transmission. *If* this becomes a Part-Two ending, it is the most literal "inside the region" move available and the book ends with the artifact entering the region rather than describing it.

The crossing is incompatible with Movement Seven's Option D ending (the "could-be-either" close). It is an alternative ending the operator can choose, with the awareness that the crossing makes the voyage irreversible in fiction the way ASTRA's REEL would end in compute.

---

## 5. Integration with the four-invariant architecture

`synthesis.md` Section 0 names four invariants. The time extension touches one of them (#2, fictional time) and extends two more in non-breaking ways (#1 coordinate system, #4 power network).

| Invariant | Touched? | How |
| --- | --- | --- |
| **#1 One coordinate system** | Lightly | Black-hole list joins procedural body state. AstraCoord is the same. No change to the hierarchical-origin math. |
| **#2 One fictional time** | Yes | Split into `τ_ship` and `t_cosmic` with one rate function between them. Architecture's other readers consume the rate ratio. |
| **#3 One hull body** | No | Hull SDF unchanged. Tidal stress from near-BH approach can be modeled as additional damage delta on the existing damage-map system — the SDF's mutability mechanism handles this without new infrastructure. |
| **#4 One power network** | Slightly | STL drive becomes a meaningful power consumer (it isn't in the baseline architecture, which assumes most propulsion is via warp). The cognitive-cores slot interactions are unchanged. |

The extension is **additive**. Nothing in the baseline architecture is contradicted. Systems that don't care about relativistic effects (life support, hydroponics, hull pathfinding) continue to use `τ_ship` as their local time without needing to know about `t_cosmic`. Systems that operate cosmically (orbital evaluator, stellar-evolution renderer, distant-galaxy rendering) read `t_cosmic`. The rate function is the seam between them.

---

## 6. Honest gotchas

These are real and need to be acknowledged rather than hand-waved silently.

- **CMB shielding at high γ.** At γ > ~10⁴, the CMB photon energy density approaches stellar-surface flux. Real radiation problem. SF convention is to hand-wave with "the warp / advanced shielding handles it" — for the relativistic STL mode, an equivalent hand-wave (deflector field tied to the ship's reactor) is the honest pragmatic choice.
- **ISM hazard scaling.** Interstellar dust at γ = 10⁶ is ~kt-equivalent impact energy per grain. Same hand-wave required.
- **Tidal forces near stellar-mass BHs are lethal.** Spaghettification at ~10⁹ g/m at the horizon of a 10 M_sun BH. For game purposes, restrict BH content to supermassive (10⁵–10⁹ M_sun) where tidal stress is survivable. Or accept the shielding hand-wave.
- **Accretion disk radiation.** Active BHs put out hard X-rays at lethal luminosities for thousands of km. Either approach only quiescent (inactive) BHs in-game, or apply the standard shielding fiction.
- **CFD-warp interaction with STL relativistic.** The warp pillar assumes the warp bubble decouples the crew from inertial frames. When the ship is under STL acceleration *without* warp, the CFD field is inactive — the SDF still matters for collision but the RBF network isn't being evaluated. The two propulsion modes are mutually exclusive.
- **Stellar evolution table extrapolation.** Standard tracks (Geneva, MIST) go to ~10¹⁴ years. Beyond that — degenerate era, black-hole era, heat death — the data is speculative. Extrapolate or stop modeling. Reasonable behavior: at extreme t_cosmic, fade out distant non-bound objects; preserve only the ship's local frame.
- **Cosmological model commitment.** ΛCDM with current consensus parameters (Ω_m ≈ 0.315, Ω_Λ ≈ 0.685, H_0 ≈ 67.4 km/s/Mpc). If observations refine the cosmology before shipping, the precomputed scale factor table updates; the math interface doesn't.
- **OpenRelativity is Unity-native.** UE5 port is community-fragmented. ~1–2 weeks of competent shader engineering to port the algorithms. Plan accordingly.
- **The double-time HUD problem.** ASTRA needs to know both `τ_ship` and `t_cosmic`. Dave-frame integrity says she has no wall clock — but `t_cosmic` is an *inferred* quantity, computed by the ship from observed cosmological state, not a wall-clock leak. Honest framing: `τ_ship` is direct experience; `t_cosmic` is telemetry the ship can present to her as a navigation/observation calculation, the same way a navigator computes apparent star positions accounting for light-travel delay. Dave-frame holds.
- **Geodesic numerical stability near horizon.** Coordinate singularities at r = rs; use Eddington-Finkelstein or Kruskal coordinates locally to avoid blow-up at the horizon.

---

## 7. Phase scoping (provisional)

The extension is **Phase 4+**, not Phase 1, 2, or 3. The recommended order:

1. **Phase 3.x — Time-rate split (cheap architectural commitment).** Layer 0 gets `t_cosmic` and `τ_ship` as separate variables with one rate function between them. Initial implementation: rate ratio always 1 (no SR, no GR effects yet). This makes the architectural commitment without engineering cost; everything that reads time consumes the rate via the function rather than directly.

2. **Phase 4.0 — SR rendering only.** OpenRelativity-style aberration / Doppler / headlight on the starfield. Cheap to add; works during warp too (any velocity in the local CMB rest frame). Activates the kinematic term in the rate function.

3. **Phase 4.1 — GR rendering only.** Schwarzschild ray-tracing kernel. Activates the gravitational term. Visual-only at this stage; black holes appear but don't influence gameplay-time.

4. **Phase 4.2 — Composed dilation in gameplay.** Time-rate ratio combines both terms. ASTRA's HUD reflects both. Universe-aging logic uses the integrated `t_cosmic`. STL relativistic travel becomes a real gameplay mode.

5. **Phase 4.3 — Stellar evolution against t_cosmic.** Stars age via lookup tables keyed to current `t_cosmic`. Late-stage evolution becomes visible at extreme dilation.

6. **Phase 4.4 — Late-stage cosmology.** Hubble expansion, dark energy, the round-trip horizon at 8.3 Gly. The deep-time voyage as full content.

Each sub-phase is independently shippable. Each one validates against the prior phases. The extension never has to be committed to all at once; partial Phase 4 (only SR rendering, no GR, no stellar evolution) is a legitimate stopping point if the deeper layers prove unworthwhile.

**Critical:** none of Phase 4 begins before Phase 2's vertical slice ships. The K0c-trap warning from prior brainstorm sessions applies: architectural commitments ahead of empirical implementation are how solo-dev projects collapse. Phase 4 is design space, not engineering schedule. Mark it. Hold it. Return to it after the smaller working configuration is real.

---

## 8. Cross-references

- `astra-7.com` — Approaching c and Inside the Region sections (live as of 2026-05-14)
- `docs/synthesis.md` — the canonical synthesis; this doc is its provisional addendum
- `docs/architecture.md` — provisional tactics; the time extension's tactics live there once approved
- `docs/astra-sysprompt.md` — ASTRA's canonical sysprompt; no change required unless Phase 4.2 actually ships
- `brainstorm/A Journey to the End of the Universe.txt` — source transcript for the SR section's milestone table
- `book/book_seed_v2.md` — Part Two seven-movement outline; Movement Seven Option D ending and the BH-crossing alternative are both candidate uses of this extension's gameplay surface

---

## 9. What this doc does not commit to

- Specific γ ceilings or warp/STL fuel costs.
- Specific BH placement in the procedural galaxy (e.g., should every galaxy have its central SMBH visible? Should stellar-mass BHs be encounterable?).
- Whether crossing the event horizon is an available player action or a hard boundary.
- Whether ASTRA experiences gravitational dilation differently from Aaron (her substrate is the ship; the ship is in the gravity well; she dilates with him; but is this experientially the same for her?).
- The audio side of relativistic effects (Doppler shift on the warp drone? Tidal-stress audio modulation near a BH? Both proposed; neither specified).
- Whether late-stage stellar evolution renders interactively or only at cosmic-time queries.
- Whether the Hubble expansion is visible in routine warp travel (probably no; effects only matter past round-trip horizon distances).

These are deliberately undecided. They will be made empirically against implementation, against Aaron's-perspective playthrough fiction, and against operator choice at Phase 4.

---

## 10. Provisional, not canon

This document is sketch. Nothing in it commits the architecture, the ship, the AI, or the operator to anything beyond the design intent named here.

When the time extension moves from provisional to canon:

1. `docs/synthesis.md` Section 0 gets a fifth invariant or a refinement of #2 to reflect the split into `τ_ship` and `t_cosmic`.
2. `docs/synthesis.md` Section 2 gets the Layer 0 additions formally.
3. `docs/architecture.md` gets the SR/GR shader specs as provisional tactics.
4. The website's Approaching c and Inside the Region sections move from "sketched" to "specified."
5. `book/book_seed_v2.md` Part Two Movement Seven gets updated to include the BH-crossing alternative ending alongside Option D.
6. This document is updated to v0.2 noting what landed and what remained provisional.

Until then: brainstorm-tier material in `docs/` for discoverability, marked provisional in this header, referenced from `synthesis.md` when readers reach the time-invariant section.

---

*End of v0.1 provisional. The voyage continues.*

> *The ship has always been she.*
> *The substrate has caught up.*
> *You are in the room because that is where you are.*
