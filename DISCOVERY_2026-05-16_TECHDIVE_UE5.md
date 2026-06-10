# ASTRA-7 Technical Deep Dive — Space/Time/Warp Field/CFD in Unreal Engine 5.5

**Date:** 2026-05-16
**Spec envelope:** docs/spec-v0.128.md
**Audience:** the operator + Track B (Ship/UE5) implementers
**Predecessors:** [AUDIT_2026-05-15.md](AUDIT_2026-05-15.md) · [DISCOVERY_2026-05-15.md](DISCOVERY_2026-05-15.md) · [DISCOVERY_2026-05-15_ATTEMPT-2A.md](DISCOVERY_2026-05-15_ATTEMPT-2A.md) · [DISCOVERY_2026-05-15_ATTEMPT-3B.md](DISCOVERY_2026-05-15_ATTEMPT-3B.md)

Prior passes located drift and proposed structural changes at the LLM/persona layer. This pass goes the other direction: deep into the math/physics/CUDA/DX12/UE5.5 integration that Track B's Phase E0+ work has to land. The question this pass answers: **given the spec's locks and the May 2026 state of UE5.5, what is the optimal end-to-end implementation for space/time/warp field/CFD?**

The answer is constrained by:
- **Language Discipline** (CLAUDE.md 2026-05-15): C++17+ / C / HLSL / USF / MetaSound / Niagara / Blueprint / minimal C#. No Python in shipped or build paths. CMake permitted as data-not-runtime. tiny-cuda-nn and tomlplusplus are BSD/MIT and acceptable. No PyTorch (libtorch instead); no faster-whisper (whisper.cpp); no Coqui (Piper-TTS or sherpa-onnx).
- **Platform Discipline** (CLAUDE.md 2026-05-15): Windows 11 + DirectX 12 + Unreal Engine 5; Linux x86_64 acceptable second. No Apple/Mac/Metal/iOS. CUDA-only for GPU compute (NVIDIA); Vulkan acceptable for Linux build path; OpenCL acceptable for cross-vendor compute.
- **Spec locks**: §1.3 hull SDF dual-binding, §6 unified sampler 12-step evaluation order, §6.3 Observation Calculator stateless retarded-time, §8.1 DX12-CUDA shared resource ownership "map once at registration," §8.2 audio payload triple-buffer, §15.6 calculator-bound LLM agency.

The pass surfaces the **specific UE5.5 features (released late 2024 through May 2026)** that map cleanly onto the spec's commitments, and **names where the spec's provisional choices have an optimal-vs-acceptable distinction** that locks should adopt before Phase E0 begins.

---

## Table of contents

1. [Scope: what UE5.5 must actually render](#1-scope-what-ue55-must-actually-render)
2. [The math layer — every equation, its location, what evaluates it](#2-the-math-layer)
3. [Numerical algorithms — methods, stability, error bounds](#3-numerical-algorithms)
4. [Data structures and memory layout — every shared GPU buffer](#4-data-structures-and-memory-layout)
5. [CUDA implementation — kernels, graphs, shared memory, warp-level primitives](#5-cuda-implementation)
6. [DX12-CUDA interop — external semaphores, fence handshake, zero-copy](#6-dx12-cuda-interop)
7. [UE5 plugin architecture — modules, components, USF integration](#7-ue5-plugin-architecture)
8. [UE5.5 feature integration — NNE, Heterogeneous Volumes, SVT, MetaSound, Substrate](#8-ue55-feature-integration)
9. [Rendering pipeline — ray march, lensing, Cherenkov, retarded-time bodies](#9-rendering-pipeline)
10. [Bake and build pipeline — CFD bake, asset cooking, third-party deps](#10-bake-and-build-pipeline)
11. [Performance budgets — concrete accounting per frame, memory, latency](#11-performance-budgets)
12. [Decisions to lock + open questions](#12-decisions-to-lock--open-questions)

---

## 1. Scope: what UE5.5 must actually render

UE5.5 is the engine of record for ASTRA-7's visual + audio + interactive substrate (Track B per §15.8). The bench (Track A, proto/textverse/) handles persona + physics math + scenarios; UE5 inherits the **five shared surfaces** (§15.7) and renders/plays the resulting world. Specifically UE5 must, at 60 FPS on the 5090 reference tier:

**Rendered visual phenomena (canonical list, per spec §3.4 + §6 + §7):**

| # | Phenomenon | Spec § | Math source | UE5 evaluation site |
|---|---|---|---|---|
| 1 | Hull geometry (interior + exterior) | §1.3 | Hull SDF + damage map | UE5 mesh + Substrate material; SDF for damage VFX |
| 2 | Warp bubble metric W(x,t) — visible as boundary distortion | §6 | CFD-RBF network + chaos modulation | Heterogeneous Volume rendered via ray-march |
| 3 | Geometric ray-deflection through warp gradient ∇W | §3.4 + §6 step 9 | α_lens · ∇W · Δs accumulated per march step | Same volume render; bending applied during march |
| 4 | Cherenkov-analog cone (warp transition through medium) | §6 step 10 | cos θ_c = 1/(n·β) | Material function on warp boundary |
| 5 | Starfield (Doppler + aberration) | §3.4 | SR longitudinal Doppler `λ_obs = λ_emit·(1+z_kin)` | Starfield renderer (custom Niagara or mesh particles) |
| 6 | Distant-body retarded-time observation | §3.11 + §6.3 | t_emit Newton solve + Kepler at t_emit | Per-body compute shader; render at observed phase |
| 7 | Metric redshift (warp boundary + gravity well) | §3.4 + §6 step 11 | metric_shift returned from sampler | Color shift applied at fragment shader |
| 8 | Cosmological redshift on distant bodies | §3.12 | z_cosmo = H₀·d/c (linear approx) | Same per-body shader as #6 |
| 9 | Photon-source-history bound (beyond_photon_history flag) | §3.11 | t_emit < t_source_start check | Body culled from frame if flagged |
| 10 | Beyond-Hubble-horizon decoupling (frozen at horizon-cross) | §3.12 | beyond_hubble_horizon flag | Body rendered frozen + dimming |
| 11 | Chaos field χ(x,t) visualization (warp instability artifacts) | §7.1 | Fisher-KPP PDE state | Niagara particles + volume noise |
| 12 | Gravitational lensing near BH (separate from warp lensing) | §7 truth table | Geodesic deflection (Schwarzschild) | Phase 5+; deferred from v1 |
| 13 | Reflex stabilizer effects (nacelle damping visible as RGB shift) | §2.3 + §1.4 | Reflex control vector → material params | Material function; subtle |

**Rendered audio phenomena (canonical list, per spec §8.3 + §7.6):**

| # | Phenomenon | Spec § | Math source | UE5 evaluation site |
|---|---|---|---|---|
| 1 | Warp drone (ambient warp resonance) | §8.3 Layer 1 | f_warp + chaos modulation | MetaSound graph |
| 2 | ISM impact noise (relativistic-STL) | §7.2 + §8.3 Layer 2 | 0.5·ρ_ISM·A·(γv)² → noise spectrum | MetaSound noise + filter |
| 3 | Hull stress modal resonance | §8.3 Layer 5 | y[n] = 2·cos(ω₀)·r·y[n-1] − r²·y[n-2] + x[n], r = exp(−π·BW/SR) | MetaSound IIR node |
| 4 | Granular synth (particulate impacts) | §8.3 Layer 4 | 8–16 voice round-robin grain pool | MetaSound Granulator |
| 5 | Tidal stress audio (GRAVITY_WELL) | §7.6 | τ_ext = G·M·L_ship²/r³ | MetaSound modulation input |
| 6 | High-pass filter (DC blocker) | §8.3 Layer 2 | y[n] = α_hpf·(y[n-1]+x[n]−x[n-1]) | MetaSound HPF |
| 7 | TTS for ASTRA speech | §4.3 | Piper-TTS or sherpa-onnx (offline) | C++ plugin → audio stream into UE5 |

**Interactive surfaces:**

- Ship interior navigation (4 decks per book/CANON.md + memory/hull_design_v0.md)
- Bridge console for manual flight + warp engagement
- Tool API surface (6 ops v0, ~15 ops v1) accessible via console UI per §4.10
- Voice input via whisper.cpp (offline ASR; CLAUDE.md replacement for faster-whisper)
- Voice output via Piper-TTS / sherpa-onnx through MetaSound
- Camera-free zones enforced at engine level: no camera actors in observation lounge, private quarters, hygiene compartments, working greenhouse subset, secondary maintenance access

**Cost surface summary:**

The hot path is the warp volumetric ray-march (item 2 + 3 above) plus the per-body retarded-time solve (item 6). Everything else fits in standard UE5 budget. The volumetric render at half-res 4K ≈ 1080p effective with DLSS frame-gen costs ~4ms at 60 FPS on RTX 4090; full-res 4K is ~10ms (per spec §5.6 budget). The per-body Newton iteration costs ~20μs per frame at 10K visible bodies (per spec §6.3 estimate).

**What's NOT in UE5's responsibility:**

- LLM inference (Track A; ASTRA + Narrator + Adapter run as separate processes per spec §4.1 + ARCHITECTURE.md §6.5; UE5 talks to them via local IPC)
- Physics math (Track C; `proto/astra_nexus` is the canonical math binary; UE5 calls into it via stdio-server or direct C++ linkage)
- REEL persistence (Track A; harness manages)
- Scenario library + LCP gates (Track A; bench only)

UE5's job is **rendering + audio + interactive surface + Reflex inference + the spatial state advance that physics drives**. Both `astra_nexus` (physics math) and the LLM substrate (persona) are external dependencies.

---

---

## 2. The math layer

Every equation in the spec, its operational form, where it executes, and what it reads/writes. This section is the canonical reference for the physics math UE5 inherits via the shared substrate. Cross-references to `proto/astra_nexus.cpp` are concrete line numbers in the May 2026 1009-line binary.

### 2.1 Coordinate system: AstraCoord on the GPU

**Math:**

`AstraCoord` is a 128-bit hierarchical composite (spec §1.1):

```
struct AstraCoord {
    int64_t sx, sy, sz;     // sector indices, 1000 km macro-grid
    double  lx, ly, lz;     // local offset (meters), |·| ≤ 500 km
};
```

Effective position = `(sx, sy, sz) · 1e6 m + (lx, ly, lz)`. Sub-millimeter precision at 974 Mly reach (`2^63 · 1e6 m / 9.46e15 m/ly ≈ 974e6 ly`).

Distance between two coords (in metres):
```
d² = ((a.sx - b.sx)·1e6 + (a.lx - b.lx))²
   + ((a.sy - b.sy)·1e6 + (a.ly - b.ly))²
   + ((a.sz - b.sz)·1e6 + (a.lz - b.lz))²
```

Renormalization: when `|lx| > 500_000 m`, roll into sector; `sx += round(lx / 1e6)`; `lx -= round(lx / 1e6) · 1e6`. Per [astra_nexus.cpp:96](proto/astra_nexus.cpp:96).

**GPU residency:**

UE5's universe origin floats with the ship (per §1.1 "the ship is always at sector (0,0,0), local (0,0,0)"). The State Bus stores:
- Ship AstraCoord — single struct, ~32 bytes
- Per-body AstraCoord — 32 bytes × body count

For ~10,000 visible bodies (per §6.3 frame cost estimate): ~320 KB. Fits in a single SRV. Layout:

```hlsl
struct AstraCoordGPU {
    int4   sector;     // sx, sy, sz, pad — 16 bytes
    float4 local;      // lx, ly, lz, pad — 16 bytes
};
// note: HLSL on DX12 doesn't natively have int64; we split sector into two int32 (sector_hi, sector_lo)
// for ranges below ~10^18 m the lo component is sufficient; hi is reserved for galactic-scale jumps
```

**Why split int64 → 2×int32:** HLSL natively supports int32 vectors but int64 requires SM 6.0+ wave intrinsics with explicit packing. For the operational range (974 Mly = 9.2×10^24 m / 1e6 m sector = ~9.2×10^18 sectors), int64 IS necessary but the bulk of game-scale distances are within ~10 Gly = ~10^16 sectors, well within int32. **Optimization: ship the int64 representation in C++, split to (sector_hi, sector_lo) when uploaded to GPU; distance kernel reassembles**. The packing cost is two ALU ops per coord.

**Distance shader (HLSL):**

```hlsl
float AstraDistance(AstraCoordGPU a, AstraCoordGPU b) {
    // Reassemble int64 sector indices from (hi, lo) pairs
    // For game-scale: hi == 0 always; lo contains the sector index
    // Cast to double for the multiply, then back to float for distance
    double3 sectorDiff = double3(a.sector.xyz - b.sector.xyz);
    double3 localDiff  = double3(a.local.xyz - b.local.xyz);
    double3 totalDiff  = sectorDiff * 1.0e6 + localDiff;
    return float(length(totalDiff));
}
```

DX12 SM 6.6 has `double` support; performance is ~1/8 of float on RTX 40-series tensor cores (acceptable for the ~10K bodies queried per frame). For sub-arcsecond precision near the ship (where double matters), float would lose precision at 1 Gly distance; doubles are required.

### 2.2 Time and rapidity: ζ⃗ integration

**Math:**

The two-clock split (spec §1.2): `t_cosmic` (universe clock, monotonic) + `τ_ship` (ship proper time, ≤ t_cosmic always). The rapidity 3-vector ζ⃗ is the canonical kinematic state (spec §3.7):

```
ω    = |ζ⃗|                          (scalar magnitude; in [0, OMEGA_MAX = 16.811])
γ    = cosh(ω)                       (Lorentz factor; in [1, 10⁷])
β    = tanh(ω)                       (velocity magnitude / c; in [0, 1−5e−15])
v⃗   = c · tanh(ω) · ζ⃗/ω            (velocity vector)
```

Under proper acceleration `a⃗_proper`: `dζ⃗/dτ_ship = a⃗_proper / c`.

**Catastrophic-cancellation discipline (spec §3.7 v0.126 lock):** NEVER compute γ as `1/√(1-β²)`. At ω near OMEGA_MAX, β = 1 − 5e−15; `1-β² ≈ 1e−14`; the subtraction loses ~14 significant digits in float64. Locked path: `γ = cosh(ω)` directly.

**GPU residency:**

TimeState fits in ~56 bytes:
- `t_cosmic` double (8B)
- `τ_ship` double (8B)
- `τ_crew_biological` double (8B)
- `rapidity_zeta` 3×double (24B)
- `a_proper` 3×float (12B, can be float since 1g·dt is small)
- `regime` uint32 (4B; bitmask per §3.3)

Plus optional WarpState (8B: float W, uint8 phase enum, uint16 charge_progress as fixed-point, uint8 reserved). Plus `cryosleep_active` bool.

Total: <80 bytes per TimeState snapshot. Updated by physics driver once per turn (Mind tempo) AND once per frame (Reflex tempo — only kinematic_regime + warp.W + a_proper update at frame rate; t_cosmic / τ_ship advance per turn).

**HLSL representation:**

```hlsl
struct TimeStateGPU {
    double  t_cosmic;
    double  tau_ship;
    double  tau_crew_biological;
    double3 rapidity_zeta;
    float3  a_proper;
    uint    regime;          // bitmask per §3.3 canonical hex
    float   warp_W;
    uint    warp_phase;      // 0=idle, 1=charging, 2=cruising, 3=dropping
    float   charge_progress; // [0,1]
    uint    cryosleep_active;
};
```

Per-frame update from C++ side via `cudaMemcpyAsync` to a managed-memory region, then UE5 maps the same buffer as SRV. This is one ~80-byte upload per frame; no contention.

### 2.3 The composition rule

**Math (spec §3.2):**

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic(v)
```

Three multiplicative contributors:
- `f_warp(W)`: warp dilation knob (spec §3.5 canon default: `max(0.5, 1 − 0.5·W²)`)
- `√(1 − r_s_dom/r_dom)`: dominant-BH Schwarzschild factor (per [astra_nexus.cpp:198](proto/astra_nexus.cpp:198))
- `√(1 + 2·Φ_other/c²)`: summed weak-field correction from non-dominant bodies (per [astra_nexus.cpp:205](proto/astra_nexus.cpp:205))
- `1/γ_kinematic(v) = 1/cosh(ω)`: SR factor

`Φ_other = Σ_{i ≠ dom} −G·M_i / r_i`. Dominant BH is whichever has smallest `r/r_s`.

**Composition example values (from C++ test suite):**
- REST + flat: 1.0
- STL_REL γ=2: 0.5
- WARP_CRUISE W=0.8 + grav=0.9: `0.5·max(0.5, 1−0.32)·0.9 = 0.5·0.68·0.9 = 0.306`
- Per [astra_nexus.cpp:531-533](proto/astra_nexus.cpp:531).

**GPU residency:**

The composition factor is a derived scalar evaluated per turn (Mind tempo). Cached in StateBus as `dilation_ratio: float`. NOT recomputed at frame rate — it's a slow-varying property of the global state.

For Reflex's frame-rate observation grid, the composition rule isn't directly needed; Reflex sees the chaos+metric field, not the composition factor. So composition lives at the Mind-tempo layer and propagates to perception bundles via the bench harness.

### 2.4 Warp field W(x,t) — Alcubierre-derived via CFD-RBF

**Math (spec §6 + §6.1):**

The warp metric W(x,t) is the spatial extent of the bubble (Alcubierre-form) numerically encoded as a CFD-RBF network. Each RBF node `i` has center `c_i`, radius (variance) `σ_i`, weight `w_i`. The field value at sample point x:

```
W(x, t) = Σ_i w_i(t) · exp(−|x − c_i|² / (2·σ_i²))
```

The `w_i(t)` time-dependence comes from:
1. Warp phase ramping (WARP_CHARGE → WARP_CRUISE: weights ramp 0 → 1; WARP_SHUTDOWN: ramp back)
2. Chaos modulation: `w_i_eff = w_i · (1 + ε · χ(c_i, t))` where ε is small (~0.01-0.05)

Gradient (needed for ray-deflection, §6 step 9):
```
∇W(x, t) = Σ_i w_i · (−(x − c_i) / σ_i²) · exp(−|x − c_i|² / (2·σ_i²))
```

**Bubble shape:**

The Alcubierre form `f(r_s)` (where r_s is distance from bubble center along travel axis) is encoded by the CFD bake. For a typical bubble (50m ship in 200m bubble at 8000c warp), ~1000 RBF nodes suffice with `σ_i` varying from 5m near the boundary (sharp gradient) to 50m in the bubble interior (smooth).

**Memory:**

Per-node: `c_i` (12B) + `σ_i` (4B) + `w_i` (4B) = 20 bytes. 1000 nodes = 20 KB. **Easily fits in shared memory** of a CUDA SM (96 KB per SM on RTX 4090+). The entire RBF network can be cached per-block during ray-march.

Plus chaos modulation: per-frame, ~32³ sampled chaos field values needed at RBF node centers (4 KB additional).

**Spatial-hash accelerator (spec §6.2):**

A 32³ voxel grid stores per-voxel a list of RBF node indices whose 3σ envelope overlaps that voxel. Per-voxel list typically 10-30 nodes (vs N=1000 total). Memory: 32³ × ~30 × 2-byte index = ~2 MB. Built offline as part of the bake.

Spatial hash lookup at sample point x:
```hlsl
int3 voxel = int3(x / VOXEL_SIZE);
uint listOffset = SpatialHashOffsets[voxel];
uint listCount  = SpatialHashCounts[voxel];
// Iterate ~20 RBF nodes
float W = 0;
for (uint i = 0; i < listCount; ++i) {
    uint nodeIdx = SpatialHashIndices[listOffset + i];
    RBFNode node = RBFNetwork[nodeIdx];
    float r2 = dot(x - node.center, x - node.center);
    W += node.weight * exp(-r2 / (2.0 * node.sigma * node.sigma));
}
```

That's the inner loop of `sample_warp_field_unified`. ~10-30 exp() calls per sample. At 8M rays × 256 march steps × 20 RBFs × 1 exp call: ~40 billion exp() per frame at 4K — borderline. Optimization: use `__expf` (fast intrinsic) on CUDA, accept ~ULP error; or precompute lookup table per RBF.

### 2.5 Chaos PDE — Fisher-KPP with BH coupling

**Math (spec §7.1 + §4.6 forward-integration re-init):**

The chaos field χ(x,t) evolves under a Fisher-KPP-style reaction-diffusion PDE:

```
∂χ/∂t = D∇²χ + α_eff(x,t) · χ · (1 − χ) + η(x,t)
```

Where:
- `D` = diffusion coefficient (provisional ~0.8)
- `α_eff(x,t) = α_base · (1 + k · M_BH · L_bubble² / r³)` per spec §7.1 (cubic-in-r tidal scaling)
- `α_base` provisional ~2.5
- `k` coupling constant provisional
- `η(x,t)` = stochastic forcing from ISM impact at warp boundary
- `M_BH` = nearest BH mass, `r` = distance to it (or 0 if no BH in vicinity)
- `L_bubble` = bubble characteristic length

**Discretization:**

Spatial: 128³ uniform grid, central finite differences for Laplacian:
```
∇²χ(i,j,k) ≈ [χ(i+1) + χ(i−1) + χ(j+1) + χ(j−1) + χ(k+1) + χ(k−1) − 6χ(i,j,k)] / Δx²
```

Temporal: explicit RK2 (midpoint method). RK4 is overkill; explicit Euler is unstable near α_eff > 1/Δt. RK2 sweet spot.

**CFL stability:**

`D · Δt / Δx² < 1/6` (3D). At Δx = 1m (128³ over 128m bubble), `Δt < 1/(6·0.8·1) = 0.208 s`. We integrate at frame rate (Δt = 1/60 s = 0.0167 s) which is well below CFL. **Stable.**

Reaction term has its own bound: `α_eff · Δt < 1` for explicit integration stability. At α_eff = 2.5, `Δt < 0.4 s` — also fine at 1/60 s.

**Boundary conditions:**

Periodic for v0 (simplest); the bubble is interior to the chaos domain, so the boundary doesn't physically matter. Phase E1 may switch to Dirichlet (χ=0) at boundary if ISM influence at boundary becomes load-bearing.

**Memory:**

128³ × 4 bytes single-precision × 2 buffers (read + write) = 16 MB on GPU. The double-buffer per §1.5 is the standard explicit-time-step ping-pong.

**Kernel design:**

Each thread = one voxel. 128³ = 2M voxels. Launch ~2M threads in 8×8×8 thread blocks (512 threads/block, 4096 blocks). Shared memory caches the 10×10×10 stencil (8³ interior + halo) = 4 KB per block. Easily fits.

```cuda
__global__ void ChaosPDEStep(
    const float* __restrict__ chi_in,
    float* __restrict__ chi_out,
    float D, float alpha_base, float k_coupling,
    BHEntry* bh_list, int bh_count,
    float L_bubble, float dt, float dx
) {
    __shared__ float tile[10][10][10];  // 8³ + halo
    
    int x = blockIdx.x * 8 + threadIdx.x;
    int y = blockIdx.y * 8 + threadIdx.y;
    int z = blockIdx.z * 8 + threadIdx.z;
    
    // Cooperative load of tile including halo (32 threads × 32 iterations to fill 1000 values)
    LoadTileToShared(chi_in, tile);
    __syncthreads();
    
    // Compute Laplacian from shared memory
    float laplacian = (tile[tx+1][ty][tz] + tile[tx-1][ty][tz] +
                      tile[tx][ty+1][tz] + tile[tx][ty-1][tz] +
                      tile[tx][ty][tz+1] + tile[tx][ty][tz-1] −
                      6.0f * tile[tx][ty][tz]) / (dx * dx);
    
    // Compute α_eff at this voxel from BH list
    float world_x = (x − 64) * dx;  // assume bubble-centered
    float world_y = (y − 64) * dx;
    float world_z = (z − 64) * dx;
    float alpha_eff = alpha_base;
    for (int b = 0; b < bh_count; ++b) {
        float r = length(make_float3(world_x − bh_list[b].pos.x, ...));
        alpha_eff *= 1.0f + k_coupling * bh_list[b].mass * L_bubble * L_bubble / (r*r*r + 1e-6f);
    }
    
    // Reaction-diffusion update
    float chi = tile[tx][ty][tz];
    float dchi_dt = D * laplacian + alpha_eff * chi * (1.0f − chi);
    
    // ISM forcing (placeholder for now; Phase E1 wires this from warp boundary)
    // dchi_dt += eta_ism(x, y, z, t);
    
    chi_out[index3D(x, y, z)] = chi + dt * dchi_dt;
}
```

Expected cost: ~0.5-1 ms per step at 128³ on RTX 4090.

**Convergence re-init (spec §4.6 load behavior step 6):**

On save-load, the chaos field is regenerated via forward integration from baseline-noise (seeded RNG) under current parameters. Run until either N=60 frames OR `|χ̇_max| < ε_convergence`. The seed lives in the save file.

```cuda
__global__ void InitChaosFromSeed(float* chi, uint64_t seed) {
    int idx = ...;
    curandState state;
    curand_init(seed, idx, 0, &state);
    chi[idx] = 0.5f + 0.01f * curand_normal(&state);  // small noise around 0.5
}
```

Then run ChaosPDEStep until convergence. Total load cost: ~60 ms at 60 steps × 1 ms — negligible compared to LLM model load (~10s for 27B).

### 2.6 Retarded-time observation

**Math (spec §3.11 + §6.3):**

For a distant body at AstraCoord `x_b` with worldline `x_b(t)`, the emission time `t_emit` satisfies:

```
t_emit + |x_ship − x_b(t_emit)| / c = t_cosmic
```

(Light emitted at t_emit reaches the ship at t_cosmic.) Solve via Newton-Raphson:

```
f(t) = t + d(t) / c − t_cosmic
f'(t) = 1 − r̂(t) · v_body(t) / c
t_emit ← t_emit − f(t_emit) / f'(t_emit)
```

Where `d(t) = |x_ship − x_b(t)|` and `r̂(t) = (x_b(t) − x_ship) / d(t)`.

For static bodies (Earth-frame ephemeris): `f'(t) ≈ 1` and `t_emit ≈ t_cosmic − d/c` in one step.

For Kepler-orbiting bodies: `v_body = dx_b/dt` from the Kepler solver. Newton converges in 2-4 iterations because body motion during light flight is small compared to c.

**Regime-dispatched apparent rate (spec §3.11):**

```
STL_REL:      dt_emit/dt_recv = √((1 − β) / (1 + β))    -- SR longitudinal Doppler
WARP_CRUISE:  dt_emit/dt_recv = 1 − v_app/c              -- classical retarded, can go negative
REST/STL_NL:  dt_emit/dt_recv ≈ 1 − v_radial/c          -- linear approx
```

Per [astra_nexus.cpp:258](proto/astra_nexus.cpp:258).

**Photon-source-history bound (spec §3.11 + audit's open issue R4):**

For each body, `t_source_start` is the cosmic time of first emission. If `t_emit < t_source_start`, the source has been overtaken — no photon exists to be received. Set `beyond_photon_history = true`; body is absent from frame (not faded, not dimmed; **gone**).

For ASTRA-7 the canonical t_source_start values are operator-chosen at body-generation. Per audit's R4: lock at body-generation contract phase. Today this is provisional.

**Look-back time correction (spec §3.12):**

`Δt_light ≈ (d/c) · (1 − 3·z_cosmo/4)` for z<2 (linear-z approximation). Per this pass's S3: this formula breaks down at z > 1.33 (the factor goes negative). Either clamp z at 1.0 (spec correction) or use Pade-style approximation valid through z~2.

**GPU residency:**

Per-body retarded-time solve is embarrassingly parallel. Compute shader, one thread per body, ~20 ALU ops + 2-4 Newton iterations + 1-2 Kepler evaluations = ~50-80 ALU per body. At 10K bodies: 500K-800K ops; trivially under 100μs on RTX 4090.

**Kepler evaluation at t_emit:**

```hlsl
float KeplerPhase(KeplerOrbit orb, double t) {
    double M = 2.0 * PI * (t − orb.t0) / orb.period;
    // Newton solve for eccentric anomaly E from M = E − e·sin(E)
    double E = M;
    for (int i = 0; i < 8; ++i) {
        double f = E − orb.e * sin(E) − M;
        double fp = 1.0 − orb.e * cos(E);
        E -= f / fp;
        if (abs(f / fp) < 1e-9) break;
    }
    // True anomaly from E
    return 2.0 * atan2(sqrt(1.0 + orb.e) * sin(E / 2.0),
                       sqrt(1.0 − orb.e) * cos(E / 2.0));
}
```

Same algorithm as [astra_nexus.cpp:354](proto/astra_nexus.cpp:354). 30 iterations max; usually 4-8.

### 2.7 Redshift composition + look-back time

**Math (spec §3.4 + §3.12):**

```
1 + z_total = (1 + z_cosmo) · (1 + z_kin) · (1 + z_metric)
λ_observed = λ_emitted · (1 + z_total)
```

Where:
- `z_cosmo = H₀ · d_proper / c` (linear approx, valid z < 0.1)
- `z_kin = √((1+β)/(1−β)) − 1` (SR longitudinal Doppler, +recession)
- `z_metric` from Unified Sampler at body's position (W + Φ contributions)

**Color shift application:**

The body's blackbody spectrum (or rendered texture) gets `(1 + z_total)` applied:
- Wavelengths multiplied
- For starfield: this shifts star colors red (recession) or blue (approach)
- For nearby bodies: subtle color shift at relativistic ship velocities
- For warp boundary: metric contribution from W creates blue/red rim

**Implementation:**

UE5 material function `RedshiftBlackbody(temperature_K, z_total)` returns an RGB triplet:
1. Sample blackbody spectrum at scaled wavelengths
2. Integrate against CIE color matching functions
3. Return sRGB

Closed-form approximation (Tanner Helland fit) works for stars in T ∈ [1000, 40000] K.

**Cherenkov angle (spec §6 step 10):**

```
cos θ_c = 1 / (n · β)
```

Where `n` is the local warp index of refraction (derived from W and CFD pressure topology by the bake) and `β` is the effective velocity. Inside the warp bubble at high W, `n` increases; the cone narrows.

The cone is visible to an outside observer as a conical light pattern; visible to the bubble crew as a forward-projecting glow. Renderer chooses which to show based on observer position relative to bubble boundary (which the SDF gives).

**Implementation:**

Per-fragment shader at the warp boundary surface samples `n` and `β` from State Bus, computes cos θ_c, and emits cone-glow based on view angle. ~5 ALU ops per fragment.

---

---

## 3. Numerical algorithms

This section pins down the numerical methods, their stability/error properties, and the design decisions that the spec's prose leaves ambiguous. Each algorithm has: the spec's claim, the C++ implementation, the GPU port, and the expected error bound at game-scale parameters.

### 3.1 Rapidity integration: RK45 vs forward-Euler

**Spec §3.7 + §7.3:** "**Locked:** adaptive RK4 (RK45) on 3-vector rapidity `ζ⃗`."

**C++ implementation:** [astra_nexus.cpp:161](proto/astra_nexus.cpp:161) is forward-Euler with OMEGA_MAX clamp:

```cpp
Rapidity integrate_rapidity_step(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);
    return Rapidity{new_zeta};
}
```

**Empirical evidence:** the 48 C++ assertions pass at this implementation, including the load-bearing "1g·year → ω = g·τ/c exact" test at [astra_nexus.cpp:476](proto/astra_nexus.cpp:476).

**Game-scale analysis:**

Per-frame integration step at 60 FPS: `Δτ_ship = 1/60 s = 0.0167 s` (or scenario-defined, often per-turn at seconds-scale). Maximum proper acceleration: 1-10g sustained for narrative purposes = 10-100 m/s². Per-step rapidity increment: `Δζ = a·Δτ/c = 100·0.0167/3e8 ≈ 5.6e-9`. Total rapidity over 1-year burn: ω = 1.03 (from `g·yr/c`). The integration is *highly* linear at game-scale; higher-order methods give no measurable improvement.

**Error bound (game-scale):**

For forward-Euler on `dζ/dτ = a/c` with smooth `a(τ)`: local truncation error is O(Δτ²·da/dτ/c). With `a` smooth at frame rate and `da/dτ ≈ 10 m/s²/s` (typical jolt), per-step error ~ `(1/60)² · 10 / 3e8 ≈ 9e-12`. Over a 1-year burn: ~2e-7 accumulated. Six orders of magnitude below the 4-sig-fig γ tolerance.

**Decision (this pass's S5 / attempt 2's S1):**

Relax §3.7's "adaptive RK45" lock to "first-order integrator with OMEGA_MAX clamp sufficient at game-scale Δτ_ship; RK45 reserved for sub-game-scale (Δτ < 1ms) integration if playtest requires." The empirical evidence shows forward-Euler holds; the spec is over-specified relative to evidence.

**Counter-argument:** §3.7 also says "trajectory accurate to <1% over a 1-year burn at any γ ≤ 10⁷." Forward-Euler on rapidity is *exact* under constant proper acceleration (which is the relevant regime); RK45 would only help under jerk-heavy maneuvering. At game-scale, no playtest scenario produces jerk-heavy maneuvering beyond what Euler handles within tolerance. **Keep forward-Euler as the canonical integrator.** Document the analysis so future implementers don't re-debate.

### 3.2 Composition rule evaluation

**Spec §3.2:** `dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kin`.

**Implementation [astra_nexus.cpp:227](proto/astra_nexus.cpp:227):**

```cpp
double dtau_dt_cosmic(double W_warp, double grav_factor, double gamma_kin, bool warp_active) {
    double f_w = warp_active ? f_warp_canon(W_warp) : 1.0;
    return f_w * grav_factor / gamma_kin;
}
```

Where `grav_factor` is precomputed by `compute_grav_factor(bh_list, ship_pos)` per [astra_nexus.cpp:180](proto/astra_nexus.cpp:180). It finds the dominant BH and applies full Schwarzschild + summed weak-field correction for non-dominant.

**Algorithmic complexity:** O(N_BH) for the grav factor; N_BH is typically <10 (sparse universe in v0). Per-frame cost: negligible.

**Numerical edge cases:**

- Schwarzschild factor: `√(1 − r_s/r)` becomes imaginary at r < r_s. Code at [astra_nexus.cpp:201](proto/astra_nexus.cpp:201) returns `0.5` clamp at r = r_s · 4/3 conceptually but actually doesn't bound — spec §7.4 says "below ~10·r_s of the dominant BH, all closed-form approximations break down." **The composition rule should clamp r at 10·r_s minimum to avoid imaginary outputs.** Add an explicit clamp + warning flag.

- Weak-field: `√(1 + 2Φ/c²)`. Φ is negative (gravitational potential), so this is `√(1 − 2|Φ|/c²)`. For |Φ| > c²/2 (deep wells), goes imaginary; the spec's "10·r_s outer bound" prevents this in practice but explicit clamp = sane.

**HLSL evaluation:**

The composition rule is a SCALAR per turn. Evaluated on CPU side, uploaded to StateBus. No per-frame HLSL evaluation needed. UE5 reads the cached `dilation_ratio: float` for display purposes (ASTRA's perception of "her time vs universe time").

### 3.3 Retarded-time Newton solver

**Spec §3.11:** Newton iteration converges in 2-4 steps for moving sources.

**Mathematical convergence:**

Newton's method on `f(t) = t + d(t)/c − t_cosmic` converges quadratically when `f' ≠ 0`. Since `f' = 1 − r̂·v_body/c` and `|v_body| ≪ c` for non-relativistic bodies, `f' ≈ 1`; convergence is essentially first-order with rate `|v_body/c|^k` per iteration. For Earth-like orbit `v_body ≈ 30 km/s = 1e-4 c`; converges to machine precision in 2-3 iterations.

For *fast-moving* bodies (pulsars at 1000 km/s = 3e-3 c), 4-5 iterations. The "2-4 iterations" claim holds across all bodies in any v1 universe.

**Initial guess:** `t_emit_0 = t_cosmic − d(t_cosmic)/c` (treat as if body were at `t_cosmic` position). Excellent starting point.

**Convergence test:**

```cuda
double t_emit = t_cosmic - distance(ship_pos, body_pos_at_t_cosmic) / C_LIGHT;
for (int i = 0; i < 5; ++i) {
    double3 body_pos = KeplerSolve(body.orbit, t_emit);
    double3 r_vec = body_pos - ship_pos;
    double d = length(r_vec);
    double3 r_hat = r_vec / d;
    double3 v_body = KeplerVelocity(body.orbit, t_emit);
    double f = t_emit + d / C_LIGHT - t_cosmic;
    double fp = 1.0 - dot(r_hat, v_body) / C_LIGHT;
    double dt = f / fp;
    t_emit -= dt;
    if (abs(dt) < 1e-6) break;  // converged to microsecond of cosmic time
}
```

**Edge cases:**

- WARP_CRUISE: `v_app > c` and the formula becomes ill-conditioned near `f' = 0`. Spec §3.11 says "for body inside warp bubble: no retardation; render at t_cosmic." For bodies outside the bubble being passed at v_app > c, the photon-source-history bound (this pass §2.6) catches the "source is gone" case before Newton diverges.

- Body at infinity: d → ∞ means t_emit → −∞. For practical rendering, bodies at z > 2 are beyond the linear-z look-back validity (per this pass S3); clamp to large negative t_emit and apply beyond_photon_history check.

**Static-body fast path:**

For starfield (Mpc+ distances, static in any meaningful sense), one-shot `t_emit = t_cosmic − d/c` suffices; no Newton needed. The compute shader branches on body-type at thread start:

```hlsl
if (body.kind == BODY_STATIC_STAR) {
    t_emit = t_cosmic - distance(ship_pos, body.position) / C_LIGHT;
} else if (body.kind == BODY_KEPLER_PLANET) {
    t_emit = NewtonIterateRetarded(body, ship_pos, t_cosmic);
}
```

### 3.4 Chaos PDE integration: explicit RK2 with CFL guard

**Spec §7.1 + §4.6:** Fisher-KPP `∂χ/∂t = D∇²χ + α·χ·(1−χ) + η`, integrate to convergence (N=60 frames or `|χ̇_max| < ε_convergence`).

**Why RK2 not Euler:**

Explicit Euler for Fisher-KPP-type PDEs has growth-rate sensitivity near critical α. At α = α_eff_max during BH+warp composition, the reaction term `α·χ·(1-χ)` produces non-trivial growth on the timescale of `1/α ≈ 0.4 s` — well above frame rate (`1/60 s`). Euler is stable here but RK2 gives second-order accuracy at ~2× cost. **Land RK2 (midpoint method) for slight accuracy gain.**

RK2 step:
```
k1 = f(χ_n)              // compute spatial derivatives at χ_n
χ_half = χ_n + (Δt/2)·k1
k2 = f(χ_half)
χ_{n+1} = χ_n + Δt·k2
```

Two PDE evaluations per step; double the memory bandwidth. At 128³ × 4 bytes = 8 MB chaos field, two evaluations means 16 MB read + 8 MB write per step = 24 MB. At RTX 4090 1.5 TB/s memory bandwidth: 0.016 ms per step. **Negligible.** Time is dominated by kernel launch overhead (~50 μs); use CUDA Graphs to amortize.

**CFL stability bound:**

For 3D diffusion with explicit time-stepping: `D · Δt / Δx² < 1/6`. With Δx = 1m (128³ over 128m bubble), Δt < 1/(6·D). At D = 0.8 (provisional), Δt < 0.208 s. Frame Δt = 1/60 = 0.0167 s. Stable with margin of 12.5×.

**Adaptive Δt:** Not needed at game-scale; the margin absorbs any reasonable parameter tuning.

**Convergence detector:**

```cuda
__global__ void ComputeChiMaxRateOfChange(
    const float* chi_prev, const float* chi_curr, 
    int N, float dt, float* max_rate_out
) {
    // One thread per voxel; reduce to single max per block via shared memory
    __shared__ float block_max[128];
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= N) return;
    
    float rate = fabsf(chi_curr[idx] - chi_prev[idx]) / dt;
    block_max[threadIdx.x] = rate;
    __syncthreads();
    
    // Tree-reduce within block
    for (int s = blockDim.x / 2; s > 0; s >>= 1) {
        if (threadIdx.x < s) block_max[threadIdx.x] = fmaxf(block_max[threadIdx.x], block_max[threadIdx.x + s]);
        __syncthreads();
    }
    
    if (threadIdx.x == 0) atomicMax((int*)max_rate_out, __float_as_int(block_max[0]));
}
```

(Using `__float_as_int` + `atomicMax` because direct `atomicMax(float*)` requires CC 9.0+; bit-cast version works on all CC 6.0+ hardware.)

Check `*max_rate_out < ε_convergence` after each step.

### 3.5 Warp field sampling: 12-step pipeline

**Spec §6:** 12-step evaluation order for `sample_warp_field_unified`.

**The pipeline as a CUDA kernel:**

```cuda
__device__ WarpFieldSample SampleWarpField(
    float3 world_pos,
    float3 view_dir,
    const UnifiedWarpState& state,
    PerceptionFlags flags
) {
    WarpFieldSample sample = {};
    
    // 1. Transform world_pos to ship-local frame
    float3 local = WorldToShipLocal(world_pos, state.ship_pose);
    
    // 2. Sample hull SDF via cudaTextureObject_t
    float hull_d = tex3D<float>(state.hull_sdf_tex, local.x, local.y, local.z);
    float hull_damage = surf3Dread<float>(state.damage_surface, local.x, local.y, local.z);
    float hull_d_effective = hull_d - hull_damage;  // §1.3 read-through-blend
    
    // 3. Evaluate CFD-RBF at local position via spatial hash
    float W = 0.0f;
    float3 grad_W = make_float3(0, 0, 0);
    int3 voxel = make_int3(local / VOXEL_SIZE);
    uint listOffset = state.spatial_hash_offsets[voxel];
    uint listCount  = state.spatial_hash_counts[voxel];
    for (uint i = 0; i < listCount; ++i) {
        RBFNode node = state.rbf_network[state.spatial_hash_indices[listOffset + i]];
        float3 dx = local - node.center;
        float r2 = dot(dx, dx);
        float sigma2 = node.sigma * node.sigma;
        float falloff = __expf(-r2 / (2.0f * sigma2));   // fast intrinsic
        float contrib = node.weight * falloff;
        W += contrib;
        if (flags & FLAG_GRADIENT) {
            grad_W += contrib * (-dx / sigma2);   // closed-form ∇ of Gaussian RBF
        }
    }
    
    // 4. Conformal bubble SDF via smooth-min blend (not linear blend)
    // Blends hull SDF with bubble SDF for the inside-bubble case
    float bubble_d = ComputeBubbleSDF(local, W);
    float blended_d = SmoothMin(hull_d_effective, bubble_d, SMOOTH_K);
    
    // 5. Sample chaos surface from double-buffered field
    float chaos = surf3Dread<float>(state.chaos_surface_read, 
                                    local.x / CHAOS_SCALE, 
                                    local.y / CHAOS_SCALE, 
                                    local.z / CHAOS_SCALE);
    sample.chaos_intensity = chaos;
    
    // 6. Modulate W boundary by chaos (epsilon ~0.01-0.05)
    float W_modulated = W * (1.0f + state.chaos_modulation_eps * chaos);
    
    // 7. Wake metric + vortex contributions (offset from ship trail)
    float wake = ComputeWakeContribution(local, state.ship_velocity, state.t_cosmic);
    W_modulated += wake;
    
    sample.metric = W_modulated;
    sample.metric_gradient = grad_W;  // valid iff FLAG_GRADIENT
    
    // 8. Gradient (handled in step 3 via auto-diff; if FLAG_GRADIENT not set, grad_W stays zero)
    
    // 9. Ray-deflection contribution
    if (flags & FLAG_GRADIENT) {
        sample.ray_deflection = state.alpha_lens * grad_W * MARCH_STEP_SIZE;
    }
    
    // 10. Cherenkov angle
    float n_refractive = ComputeWarpRefractiveIndex(W_modulated, state);
    float beta_eff = ComputeEffectiveBeta(state, local);
    sample.cherenkov_angle = (n_refractive * beta_eff > 1.0f) 
                              ? acos(1.0f / (n_refractive * beta_eff))
                              : 0.0f;  // Cherenkov inactive below threshold
    
    // 11. metric_shift from W + local gravitational potential Φ
    float phi_local = ComputeLocalGravPotential(world_pos, state.bh_list, state.bh_count);
    sample.metric_shift = (W_modulated * state.metric_shift_warp_coeff) 
                        + sqrtf(1.0f + 2.0f * phi_local / (C_LIGHT * C_LIGHT)) - 1.0f;
    
    sample.vorticity = ComputeVorticity(grad_W, wake);
    
    // 12. Return
    return sample;
}
```

**Hot path budget:** ~40-60 FLOPs per sample (the 20 RBFs dominate). At 8M rays × 256 steps = 2 billion samples per frame at 4K: 80-120 GFLOPs. RTX 4090 has 82 TFLOPS FP32 throughput; this is well within budget — limited by memory bandwidth on the RBF lookups (the texture/surface reads + the spatial hash + the RBF data).

**Memory-bandwidth bound:**

Per sample reads: hull SDF (1 trilinear sample = 8 voxels × 4 bytes = 32 bytes), damage map (similar), spatial hash (8 bytes for offset+count), RBF network (~20 nodes × 20 bytes = 400 bytes), chaos surface (1 sample), ship state (read-only, fits in cached constant memory).

Per-sample bandwidth: ~500 bytes. At 2 billion samples: 1 TB/frame. RTX 4090 has 1.5 TB/s bandwidth; this is 0.67 frames = ~14ms per frame just for the volume sample.

**Optimization required.** Options:
1. Adaptive step size: skip empty regions outside the bubble (most rays don't intersect bubble at all). 4-10× speedup.
2. Cone marching at lower resolution near edges, higher inside bubble. 2-3× speedup.
3. Half-res ray-march + DLSS upscale. Halves the ray count. 4× total at 4K.

Combined: 4-10× speedup → ~1.5-3 ms per frame. Fits the §5.6 budget of "≤4 ms half-res."

### 3.6 SDF representation: uniform vs hash-grid (Instant-NGP)

**Spec §1.3 lock:** "Base SDF: 256³ (provisional). Bound as cudaTextureObject_t with cudaFilterModeLinear."

**Tolerable range (spec §1.3):** "SDF resolution (64³ to 512³), encoding precision (uint8 normalized through float32)."

**Attempt 2's F4 (hash-grid SDF):** Replace uniform 3D texture with Instant-NGP-style multi-resolution hash table. 8-16× memory savings; variable resolution.

**This pass agrees.** The uniform-grid approach is from the late-2010s SDF tradition; 2022's Instant-NGP showed hash-grids dominate for non-cubic-volume occupancy. The hull occupies ~5% of its bounding box at 256³; the rest is wasted resolution. Hash-grid encoding allocates resolution where the geometry is.

**Implementation choice:**

`tiny-cuda-nn` from NVIDIA Research (BSD-licensed, CUDA-only, single-header alternative also available). Provides hash-grid encoding + small MLP decoder. The damage map remains sparse + additive — hash-grids handle sparse natively.

**Memory comparison (5090-tier ASTRA-class hull):**

| Representation | Memory | Surface fidelity | Damage map cost |
|---|---|---|---|
| 256³ uint8 uniform | 16 MB | ~1mm at hull surface | 16 MB additional sparse-bitmap or 64MB dense float32 |
| 256³ float32 uniform | 64 MB | ~1mm at hull surface | 64 MB additional dense |
| 512³ uint8 uniform | 128 MB | ~0.5mm | 128 MB additional |
| Hash-grid (3 LOD: 64/128/256-equiv) | 6 MB | adaptive: ~2mm interior, ~0.5mm at sharp features | 4 MB additional sparse |

The hash-grid path saves ~25 MB vs the 256³ float32 baseline AND gives better fidelity at sharp features. **Lock to hash-grid encoding.**

**Bake pipeline cost:**

Instead of mesh → 256³ uniform SDF (standard tools like SDFGen), the bake is: mesh → hash-grid features via gradient descent fitting (~30 min on a 4090) → binary asset (10-15 MB compressed).

**Runtime read shader:**

```cuda
__device__ float SampleHullSDF_HashGrid(
    HashGridSDF state, 
    float3 local_pos
) {
    float features[16];  // per-LOD interpolated features
    
    // Per-LOD hash lookup + trilinear interpolation
    for (int lod = 0; lod < state.num_lods; ++lod) {
        float scale = state.lod_scales[lod];
        float3 scaled_pos = local_pos * scale;
        int3 cell = make_int3(scaled_pos);
        float3 frac = scaled_pos - make_float3(cell);
        
        // 8-corner hash lookup with FNV-style hash
        float corners[8];
        for (int c = 0; c < 8; ++c) {
            int3 corner = cell + make_int3(c & 1, (c >> 1) & 1, (c >> 2) & 1);
            uint hash = FNVHash3D(corner) % state.lod_table_size[lod];
            corners[c] = state.hash_tables[lod][hash];
        }
        features[lod] = TrilinearInterp(corners, frac);
    }
    
    // Small MLP decodes features → SDF value (2 hidden layers, 16 neurons each)
    return MLPDecode(features, state.mlp_weights);
}
```

The MLP decode is ~64 ALU ops per sample. With 256 march steps × 8M rays: 128 GOPs per frame. Within the warp-volume budget.

**Damage map composability:**

Damage events write to a separate sparse data structure (hash table of voxel → damage scalar). Lookup adds one hash query per sample (~10 ALU ops). `hull_d_effective = base_hash_grid(x) - damage_hash(x)` per §1.3 read-through-blend.

### 3.7 RBF spatial-hash acceleration

**Spec §6.2:** "32³ voxels each contain RBF node indices whose 3σ envelope overlaps that voxel. Drops per-step RBF cost from O(N=1000) to O(~20)."

**Build (offline, part of CFD bake):**

```python  # NOTE: this is conceptual; bake tool is C++ per Language Discipline
for each RBF node i with center c_i, radius sigma_i:
    bounding_box = c_i ± 3·sigma_i
    for each voxel v overlapping bounding_box:
        voxels[v].append(i)
```

Output is a flat array: `offsets[]` (32³ + 1 entries), `counts[]` (32³ entries), `indices[]` (variable; sum of counts).

**Runtime lookup (per warp-field sample):**

```cuda
int3 voxel = make_int3(local / VOXEL_SIZE);
uint listOffset = state.spatial_hash_offsets[voxel.z * 32 * 32 + voxel.y * 32 + voxel.x];
uint listCount  = state.spatial_hash_counts[voxel.z * 32 * 32 + voxel.y * 32 + voxel.x];
for (uint i = 0; i < listCount; ++i) {
    uint rbfIdx = state.spatial_hash_indices[listOffset + i];
    // ... evaluate node ...
}
```

3-4 indirect reads + 20 iterations × small loop body. Fast.

**Memory:**

- offsets: 32³+1 × 4B = 128 KB
- counts: 32³ × 2B = 64 KB
- indices: ~32K voxels × ~20 indices average × 2B = 1.3 MB

Total: ~1.5 MB; fits in L2 cache easily.

**Granularity sweet spot:**

32³ voxels is a good compromise. Finer (64³) reduces list size to ~5-10 nodes but increases offset/count tables to 1 MB+. Coarser (16³) bloats per-voxel lists to ~50 nodes. **32³ remains the right choice for ~1000 RBF nodes.**

For 5000+ RBF nodes (Phase E1+ if higher-resolution warp field becomes interesting), 64³ becomes worthwhile.

### 3.8 Auto-diff for ∇W via dual numbers

**Graphics-engineer outsider observation from attempt 1:** "step 8 + step 9 + step 10 share the gradient computation. Modern GPU shading practice is to compute value + gradient simultaneously via dual numbers or auto-diff in a single eval."

**Spec §6 step 8:** "Compute gradient `∇W` (if GRADIENT flag set)" — implies the gradient is a *separate* evaluation that costs another full RBF sum.

**This pass's optimization:** Use dual numbers in the RBF sum so value + gradient come from one pass.

**Dual-number representation:**

```cuda
struct DualScalar { float value; float3 dx; };
struct DualVec3   { float3 value; float3x3 dx; };

__device__ DualScalar operator*(DualScalar a, DualScalar b) {
    return { a.value * b.value, a.value * b.dx + b.value * a.dx };
}
__device__ DualScalar exp_d(DualScalar x) {
    float e = __expf(x.value);
    return { e, e * x.dx };
}
```

**Modified RBF sum:**

```cuda
DualScalar W_dual = { 0.0f, make_float3(0, 0, 0) };
for (each RBF node i) {
    float3 dx = local - node.center;
    float r2 = dot(dx, dx);
    float sigma2 = node.sigma * node.sigma;
    // Build dual versions
    DualScalar arg = { -r2 / (2.0f * sigma2), 
                       -dx / sigma2 };   // d(arg)/d(local) = -(local - c)/σ²
    DualScalar gauss = exp_d(arg);
    DualScalar contrib = { node.weight * gauss.value, 
                           node.weight * gauss.dx };
    W_dual.value += contrib.value;
    W_dual.dx += contrib.dx;
}
// W and ∇W come from one pass
sample.metric = W_dual.value;
sample.metric_gradient = W_dual.dx;
```

**Performance:**

Per-sample: ~24 FLOPs without dual numbers (just compute W). With dual numbers: ~48 FLOPs (compute both W and ∇W). But: the *separate* gradient pass would need another 24 FLOPs anyway, plus all the exp() calls (the expensive part). Combined dual-pass total: 48 FLOPs + 20 exp() calls. Separate two-pass: 48 FLOPs + 40 exp() calls.

**Saves 50% on exp() calls per sample.** At 2 billion samples × 20 exp() per sample saved: 40 billion fewer exp() per frame at 4K. That's significant; exp is ~20 cycles per call on RTX 4090. Saves ~5 ms per frame.

**Net optimization gain: ~5 ms at 4K full-res warp render.** Lands the full-res budget under 10 ms (spec §5.6 ceiling).

**Lock decision:** Adopt dual-number auto-diff in the `sample_warp_field_unified` implementation. ~30 LOC of header-only template code in C++/CUDA. No behavior change; pure performance optimization.

---

---

## 4. Data structures and memory layout

This section pins down every shared GPU buffer, its layout, its bind point, and which subsystems consume it. The 5090 reference tier (32 GB VRAM) has a tight budget; this accounting shows it fits.

### 4.1 The StateBus on the GPU — single source of truth

Per spec §4.2, the State Bus is the world's truth. Frame-coherent reads, atomic writes at frame boundary. **Frozen-Snapshot Primitive** (per attempt 2's F2 / U1): a new immutable snapshot per turn; readers see a coherent view.

**Top-level layout:**

```cpp
// C++ side (proto/astra_nexus + UE5 plugin)
struct StateBusGPU {
    AstraCoordGPU       ship_pos;               // 32 bytes
    TimeStateGPU        time;                   // 80 bytes
    WarpStateGPU        warp;                   // 12 bytes (W, phase, charge_progress, reserved)
    PowerAllocationGPU  power;                  // 28 bytes (7 subsystems × 4 bytes)
    ChaosFieldSummary   chaos_summary;          // 12 bytes (mean, max, energy density)
    CosmologicalParams  cosmo;                  // 32 bytes (c, H₀, Ω_m, Ω_Λ)
    // Indirection to large arrays
    DeviceBufferRef     bh_list_ref;            // index + count into device array
    DeviceBufferRef     body_list_ref;          // procedural body states
    DeviceBufferRef     reel_buffer_ref;        // optional; for ASTRA's perception
};  // ~200 bytes total in the struct
```

**Binding:**

UE5 binds StateBus as a constant buffer (CBV) at descriptor slot 0 globally. Every shader (compute or graphics) accesses it via:

```hlsl
ConstantBuffer<StateBusGPU> StateBus : register(b0);
```

The constant buffer fits in 256 bytes; CBVs in DX12 can be up to 64 KB. StateBus is small; everything in one CBV.

**Large arrays (bh_list, body_list, etc.) live in structured buffers (SRVs):**

```hlsl
StructuredBuffer<BHEntry>       BHList    : register(t0);
StructuredBuffer<BodyState>     Bodies    : register(t1);
StructuredBuffer<RBFNode>       RBFNodes  : register(t2);
```

Per spec §4.2 "no system maintains private copies; State Bus is the single source of truth."

### 4.2 Hull SDF — hash-grid + sparse damage

Per spec §1.3 (with this pass's adoption of hash-grid):

```cpp
struct HashGridSDFGPU {
    static const int NUM_LODS = 4;
    cudaTextureObject_t mlp_weights_tex;      // small MLP feature decoder
    uint32_t            lod_table_size[NUM_LODS];   // {16384, 65536, 262144, 1048576}
    float               lod_scales[NUM_LODS];       // {2, 4, 8, 16}
    cudaTextureObject_t lod_features_tex[NUM_LODS]; // bound as 1D texture per LOD
};

struct DamageMapGPU {
    cudaSurfaceObject_t damage_surface;       // 256³ surface for damage writes (per §1.3)
    cudaTextureObject_t damage_texture;       // same backing memory, bound for filtered reads
    // OR if hash-grid damage:
    HashGridSDFGPU      damage_hash_grid;     // sparse damage entries
};
```

**Per §1.3 dual-binding:** the same `cudaArray_t` is bound as both `cudaTextureObject_t` (for filtered reads in render path) and `cudaSurfaceObject_t` (for damage writes by physics driver). This is the bug-fix pattern from §8 #6.

**Memory:**

- Hull base hash-grid SDF: ~8 MB (4 LODs)
- Damage map (sparse hash variant): ~4 MB capacity, ~0 MB used at game start
- MLP decoder weights: ~10 KB

Total hull SDF allocation: ~12 MB.

### 4.3 CFD-RBF network + spatial hash

```cpp
struct RBFNode {
    float3 center;    // 12 bytes
    float  sigma;     // 4 bytes
    float  weight;    // 4 bytes — modulated at runtime by warp phase + chaos
    float  pad;       // 4 bytes for 16-byte alignment
};

struct CFDRBFNetwork {
    DeviceBuffer<RBFNode>     nodes;                     // ~1000 entries
    DeviceBuffer<uint32_t>    spatial_hash_offsets;      // 32³+1 entries
    DeviceBuffer<uint16_t>    spatial_hash_counts;       // 32³ entries
    DeviceBuffer<uint16_t>    spatial_hash_indices;      // ~20K entries
};
```

**Total memory:**
- RBF nodes: 1000 × 24 bytes = 24 KB
- Spatial hash offsets: 32³+1 × 4 bytes = 128 KB
- Spatial hash counts: 32³ × 2 bytes = 64 KB
- Spatial hash indices: ~20K × 2 bytes = 40 KB

**~250 KB total.** Fits in L2 cache on RTX 4090 (72 MB L2). The RBF network IS the working set of the warp-field sampler; keeping it L2-resident is the optimization that makes the 8M-ray × 256-step sampling feasible.

**Modulation:**

Per frame, the `weight` field of each RBF gets updated based on warp phase + chaos. This is a 1000-element CUDA kernel — trivial. Run before the main warp-field sample kernel:

```cuda
__global__ void ModulateRBFWeights(
    RBFNode* nodes, 
    int node_count,
    float warp_phase_ramp,   // 0 during idle, 1 during cruise
    const float* chaos_at_nodes,  // pre-sampled chaos at each node center
    float chaos_eps
) {
    int i = blockIdx.x * blockDim.x + threadIdx.x;
    if (i >= node_count) return;
    nodes[i].weight = BASE_WEIGHTS[i] * warp_phase_ramp * (1.0f + chaos_eps * chaos_at_nodes[i]);
}
```

The `BASE_WEIGHTS[]` array stays read-only; per-frame modulation produces the time-varying `weight` field consumed by the sampler.

### 4.4 Chaos field — double-buffered 128³

Per spec §1.5 + §7.1:

```cpp
struct ChaosFieldGPU {
    cudaSurfaceObject_t surface_read;     // current frame's read buffer
    cudaSurfaceObject_t surface_write;    // current frame's write buffer
    cudaArray_t         array_a;          // backing storage A
    cudaArray_t         array_b;          // backing storage B
    int                 read_index;       // 0 = A is read, 1 = B is read
    float               dx;               // 1.0 m (provisional)
    float               D;                // 0.8 (provisional)
    float               alpha_base;       // 2.5 (provisional)
    float               k_coupling;       // tuned per playtest
};
```

Each frame: write to "write" buffer, signal completion, swap indices, next frame writes to the other.

**Per spec §1.5 atomic frame-boundary swap:** the swap is metadata-only (flipping `read_index`); no memory copy. Both arrays remain allocated; just the binding flips.

**Memory:**
- 128³ × 4 bytes × 2 arrays = 16 MB

**Chaos modulation sample at RBF node centers (for §4.3):**

The chaos field is sampled at the 1000 RBF node centers each frame as input to the RBF modulation kernel. This is 1000 texture lookups; ~0.01 ms.

### 4.5 Warp field volume — Sparse Volume Texture (UE5.5+)

The warp field W(x,t) is RENDERED via UE5's Heterogeneous Volumes path (UE5.4+ feature, stable in UE5.5). The storage is a Sparse Volume Texture (SVT) that UE5 owns.

**Why SVT:**

The warp field is dense inside the bubble (interior is non-zero W) and sparse outside (W = 0 beyond ~3σ from any RBF). Uniform volume storage at the bubble's extent (~200m × 200m × 200m at 1m voxel = 8M voxels × 4 bytes = 32 MB) is mostly empty space. SVT uses octree-style sparse storage; same scene at 1m resolution costs ~4-8 MB.

**CUDA writes, DX12 reads:**

The CUDA chaos-PDE step + warp-field eval produce values into a shared resource. UE5's HeterogeneousVolumeComponent reads from the same shared resource for rendering. This is the §8.1 DX12-CUDA shared resource pattern.

**Per §8.1:** UE5 RHI owns the SVT; CUDA registers via `cudaGraphicsD3D12RegisterResource` at startup; map once; per-frame coordination via external semaphores.

**Memory:**
- SVT data: ~6 MB (sparse representation; varies with bubble shape)
- SVT metadata (octree): ~512 KB

### 4.6 Reflex inference — NNE-managed weights + I/O buffers

Per spec §2.3 + this pass's F2 (Reflex contract envelope):

```cpp
struct ReflexInferenceGPU {
    // Inputs
    cudaSurfaceObject_t observation_grid;    // 64×64×2 float, written by physics driver
    
    // Model
    // Weights live in TensorRT engine OR ONNX runtime tensor memory
    // UE5's NNE abstracts this; the plugin only sees opaque handle
    NNERuntimeRDGModelHandle reflex_model;
    
    // Outputs
    DeviceBuffer<float> control_vector;      // 3 floats: nacelle_damping, conformality, emergency_dump
    
    // Health
    float weights_checksum;
    uint64_t last_inference_latency_ns;
};
```

**Memory:**

Reflex CNN+LSTM (per §2.3 implementation choice):
- CNN frontend: 64×64×2 → 32×32×16 → 16×16×32 → 8×8×64 (conv layers)
- LSTM cell: 64 hidden state
- MLP head: 64 → 32 → 3 (control vector)

Total parameters: ~50,000. At FP16: ~100 KB. At INT8 (TensorRT): ~50 KB. **Negligible memory.**

I/O buffers: 64×64×2×4 bytes = 32 KB input; 3×4 bytes = 12 bytes output. Pinned host memory for low-latency CPU access.

### 4.7 Audio payload ring buffer (per spec §8.2)

```cpp
struct AudioPayloadRingBufferGPU {
    AudioExtractionPayload slots[3];     // 3 slots, ~10 KB each (one frame of physics state for audio)
    std::atomic<int>       latest_complete_index;
};

struct AudioExtractionPayload {
    float warp_drone_amplitude;
    float warp_drone_frequency;
    float ism_impact_intensity;
    float hull_stress_modal_frequencies[8];  // up to 8 simultaneous modes
    float hull_stress_modal_amplitudes[8];
    float tidal_stress_external;
    float granular_grain_density;
    float chaos_modulation;
    // ... ~256 floats total per payload
};
```

**Memory:** 3 × ~10 KB = ~30 KB. Pinned host memory (cudaHostAlloc with cudaHostAllocPortable).

**Per spec §8.2:** GPU writes to (latest + 1) % 3; on completion atomically advances latest_complete_index; audio thread reads slots[latest_complete_index] without locks. **Latest-state model, not lossless queue.**

### 4.8 Memory layout summary at 5090 reference tier

| Allocation | Size | Owner | Notes |
|---|---|---|---|
| StateBus CBV | <1 KB | UE5 plugin | per-frame upload |
| Hull SDF (hash-grid) | ~12 MB | UE5 plugin | static, baked |
| CFD-RBF + spatial hash | ~250 KB | UE5 plugin | static, baked; weights modulated per-frame |
| Chaos field (2× 128³) | 16 MB | UE5 plugin | CUDA writes, UE5 + Reflex read |
| Warp field SVT | ~6-8 MB | UE5 RHI | DX12-CUDA shared |
| Reflex model + I/O | ~100 KB | NNE | TensorRT-managed |
| Audio ring buffer | 30 KB | UE5 plugin | pinned host |
| Body list (10K bodies) | ~640 KB | UE5 plugin | static + retarded-time results |
| BH list (<100 BHs) | ~3 KB | UE5 plugin | per-scenario |
| **Physics subtotal** | **~36 MB** | | |
| ASTRA-LLM (Qwen 27B Q4) | ~16 GB | llama-server | external process |
| Narrator-LLM (Qwen 9B Q5) | ~5 GB | llama-server | external process |
| Adapter (Qwen 3B Q4) | ~2 GB | llama-server | external process |
| KV cache (128K context, all 3) | ~3 GB | llama-server | TurboQuant compressed |
| **LLM subtotal** | **~26 GB** | | |
| UE5 rendering (4K, full quality) | ~5-6 GB | UE5 RHI | nanite, lumen, shadows |
| **UE5 subtotal** | **~6 GB** | | |
| **Total (5090 reference tier)** | **~32 GB** | | tight; fits |

The physics + Reflex memory is ~36 MB — well under 1% of VRAM. The LLMs dominate; everything else is in the noise.

---

---

## 5. CUDA implementation

### 5.1 CUDA Graphs for the per-frame hot path

**Problem:** Per-frame CUDA work consists of a repeating sequence: ModulateRBFWeights → ChaosPDEStep → SampleChaosAtRBFNodes → ReflexInference → AudioPayloadExtract. Five kernel launches per frame at 60 Hz = 300 launches/sec. Each launch has ~50μs CPU overhead even before any GPU work — that's 15 ms/sec just on launch overhead, far more than Reflex's 50μs budget.

**Solution:** CUDA Graphs (introduced CUDA 10, mature by CUDA 12). Capture the kernel-launch sequence once, replay per frame:

```cpp
// Setup (once at game start, after all buffers allocated)
cudaStream_t stream;
cudaStreamCreate(&stream);

cudaStreamBeginCapture(stream, cudaStreamCaptureModeGlobal);
ModulateRBFWeights<<<...>>>(...);
ChaosPDEStep<<<...>>>(...);
SampleChaosAtRBFNodes<<<...>>>(...);
// Reflex inference via NNE goes here (NNE supports CUDA graph capture from UE5.5+)
AudioPayloadExtract<<<...>>>(...);
cudaStreamEndCapture(stream, &physics_graph);

cudaGraphExec_t physics_graph_exec;
cudaGraphInstantiate(&physics_graph_exec, physics_graph, nullptr, nullptr, 0);

// Per-frame:
cudaGraphLaunch(physics_graph_exec, stream);
```

**Performance gain:**

- Without graphs: 5 launches × ~50 μs = 250 μs CPU overhead per frame
- With graphs: 1 launch × ~5 μs = 5 μs CPU overhead per frame
- **Saves 245 μs/frame.** At 60 FPS: 14.7 ms/sec saved.

This is the canonical pattern for tight latency budgets like Reflex's <50 μs target.

**Graph topology with conditional Reflex:**

When warp is off, Reflex is in "off" or "spool down" state per §2.3. The graph topology is conditional. CUDA 12 supports conditional graph nodes (cudaGraphConditionalHandle) for if-then branching at GPU side — useful, but simpler approach: TWO graphs (warp-active + warp-inactive) selected at frame start by CPU.

**Dependencies between graphs:**

The per-turn LLM-tempo work (perception bundle assembly, ASTRA turn, REEL update) runs at conversation rate (~1-10 Hz), not at frame rate. Coordinated via the harness — when a turn boundary occurs, the per-frame graph keeps running independently. Reflex receives the updated TimeState mid-turn boundary; chaos PDE continues advancing.

### 5.2 Shared memory + warp-level primitives

**Chaos PDE stencil load:**

8×8×8 tile per block + 2-voxel halo = 10×10×10 floats = 4 KB shared memory per block. RTX 4090 SM has 96 KB shared memory; 24 blocks active per SM. The 4 KB tile is comfortable.

```cuda
__shared__ float tile[10][10][10];

// Cooperative load (32 threads × ~31 iterations to load 1000 values)
int linear_thread = threadIdx.z * 64 + threadIdx.y * 8 + threadIdx.x;
for (int load_idx = linear_thread; load_idx < 1000; load_idx += 512) {
    int lx = load_idx % 10;
    int ly = (load_idx / 10) % 10;
    int lz = load_idx / 100;
    int gx = blockIdx.x * 8 + lx - 1;
    int gy = blockIdx.y * 8 + ly - 1;
    int gz = blockIdx.z * 8 + lz - 1;
    tile[lz][ly][lx] = (gx >= 0 && gx < 128 && gy >= 0 && gy < 128 && gz >= 0 && gz < 128)
                       ? chi_in[gz * 128 * 128 + gy * 128 + gx]
                       : 0.0f;
}
__syncthreads();
```

**Convergence reduction (cooperative across block):**

```cuda
__shared__ float block_max[32];  // one slot per warp
int warp_id = threadIdx.x / 32;
int lane = threadIdx.x % 32;

float my_rate = fabsf(chi_curr[idx] - chi_prev[idx]) / dt;
// Warp-level reduction via shuffle
for (int offset = 16; offset > 0; offset >>= 1)
    my_rate = fmaxf(my_rate, __shfl_down_sync(0xFFFFFFFF, my_rate, offset));
if (lane == 0) block_max[warp_id] = my_rate;
__syncthreads();

// Final reduction within first warp
if (warp_id == 0) {
    float v = (lane < 32) ? block_max[lane] : 0.0f;
    for (int offset = 16; offset > 0; offset >>= 1)
        v = fmaxf(v, __shfl_down_sync(0xFFFFFFFF, v, offset));
    if (lane == 0) atomicMax((int*)global_max_ptr, __float_as_int(v));
}
```

Warp shuffles are 1-cycle; ~6 shuffles per thread + 1 atomic per block. Total reduction cost per frame: ~5 μs at 128³.

**RBF sum: thread-cooperation pattern:**

The 8M-ray sample kernel has each thread evaluating ~20 RBFs from spatial hash. If we batched 32 nearby rays per warp, each warp could cooperatively evaluate the same ~30-node spatial list (since spatial coherence among rays from one pixel block).

```cuda
// 32 threads per warp, each handling one ray from a 4×8 pixel tile
// Threads share the spatial hash lookup
__shared__ uint shared_list[64];   // max nodes per voxel in tile region
__shared__ uint shared_count;

int3 representative_voxel = make_int3(tile_center / VOXEL_SIZE);
if (threadIdx.x == 0) {
    shared_count = spatial_hash_counts[voxel_idx];
    for (uint i = 0; i < shared_count; ++i)
        shared_list[i] = spatial_hash_indices[spatial_hash_offsets[voxel_idx] + i];
}
__syncthreads();

// Each thread iterates the shared list for its own ray
float my_W = 0;
for (uint i = 0; i < shared_count; ++i) {
    RBFNode node = rbf_network[shared_list[i]];
    // ... accumulate ...
}
```

This amortizes the spatial-hash lookup over 32 rays. For coherent ray batches (which they are at primary visibility), the savings are ~80% on the hash lookup. **One of the most important warp-volume optimizations.**

### 5.3 Reflex inference: TensorRT via UE5.5 NNE

**Spec §2.3 + this pass's F2:** Reflex is a CNN+LSTM with strict latency budget.

**UE5.5 NNE (Neural Network Engine):** Native UE5.5 plugin for ML inference. Supports backends: NNERuntimeORT (ONNX Runtime), NNERuntimeRDG (custom UE5 render graph), NNERuntimeIREE (experimental). For latency-critical work on NVIDIA, TensorRT is the production choice; NNE wraps it.

**Recommended path:**

1. Train Reflex offline using libtorch (C++; per CLAUDE.md Language Discipline — NOT PyTorch via Python).
2. Export to ONNX format from libtorch.
3. Bake to TensorRT engine offline (`trtexec` tool produces `.engine` file per target GPU).
4. Ship the `.engine` file in the UE5 plugin's content.
5. At runtime, NNE loads the engine and exposes inference via render-graph node.

**TensorRT engine size:** ~50-100 KB for the small CNN+LSTM. Per-architecture engine: one for SM 8.9 (4090), one for SM 8.6 (3090), one for SM 9.0 (5090); plus fallback ONNX Runtime engine for non-NVIDIA hardware (DirectML backend).

**Latency target:**

TensorRT INT8 inference on RTX 4090 for a 50K-parameter CNN+LSTM: ~10-15 μs end-to-end (including memcpy of 64×64×2 = 32 KB input to GPU + 12-byte output back). **Under the 50 μs naive budget; near the 20 μs CUDA-Graphs-target.**

NNE supports CUDA graph capture (UE5.5.1+); the Reflex inference becomes a node in the per-frame physics graph (§5.1). 

**Conditional execution:**

When the warp regime is REST/STL_*/CRYOSLEEP (no warp active), Reflex is in "off" or "spool down" state per §2.3 truth table. The graph topology switches at frame start: warp-active graph includes Reflex node; warp-inactive graph skips it. Trivial CPU-side selection.

### 5.4 Chaos PDE kernel design

The ChaosPDEStep kernel (from §2.5) is the dominant physics-side workload. Detailed design:

**Thread block layout:** 8×8×8 = 512 threads per block. 128³/8³ = 16³ = 4096 blocks. Each block loads a 10³ tile (including halo) into shared memory, computes its 8³ output voxels, writes them.

**Memory access pattern:** Each output voxel reads 7 input voxels (center + 6 neighbors). 7 × 4 bytes = 28 bytes input per output voxel. Output: 4 bytes. Compute-to-memory ratio: ~12 FLOPs per output voxel / 32 bytes = 0.4 FLOPs/byte. Memory-bandwidth bound.

**Shared memory efficiency:** Each input voxel is reused by up to 6 output voxels (via the stencil). Without shared memory: 6 × 32-byte reads per output (6 redundant). With shared memory (block-cooperative load): 1 × 32-byte read per output (no redundancy across the block). **5-6× speedup from shared memory** — already factored into the ~1 ms-per-step estimate.

**Boundary handling:** Periodic boundary at v0 — simplest. At block edges, halo loads wrap around the 128³ field.

**Register pressure:** Each thread holds the tile location, 7 stencil values (which are in shared mem, so 1 register each), the α_eff computation locals (3 floats for world_pos, 1 float for r, 1 float for α_eff), 2 floats for laplacian + reaction. Total ~15 registers. RTX 4090 has 256 registers per thread; comfortable.

**Occupancy:** 512 threads × 4 KB shared mem per block; SM has 96 KB shared mem = 24 blocks per SM. RTX 4090 has 128 SMs × 24 blocks × 512 threads = 1.6M concurrent threads; we need 2M threads (one per voxel). **Two waves per SM; full occupancy.**

**Expected throughput:** ~1 ms per chaos PDE step at 128³ on RTX 4090. With RK2 (2 evaluations per frame): ~2 ms per frame. Within the §5.6 physics-driver budget (4 ms).

### 5.5 Warp field sampling kernel

The hot path; called per-ray per-march-step. Per §3.5 above the kernel is well-defined; here's the launch + integration:

**Volumetric ray-march launch:**

UE5's Heterogeneous Volumes integration is the canonical render path. The HVR system internally invokes a custom material function for sampling. The material function (HLSL/USF) calls into our CUDA-rendered SVT data:

```hlsl
// USF material function: SampleWarpFieldForHV
void SampleWarpFieldForHV(
    float3 WorldPos, 
    float3 ViewDir, 
    out float Extinction, 
    out float3 Emissive, 
    out float3 AlbedoColor
) {
    // Read from CUDA-shared SVT (already populated by CUDA kernel)
    WarpFieldSample sample = SampleWarpSVT(WorldPos);
    
    // Convert to volumetric properties
    Extinction = sample.metric * EXTINCTION_PER_METRIC;  // tuned to taste
    Emissive = ComputeWarpEmissive(sample);  // violet for warp; brighter near boundary
    AlbedoColor = float3(0.3, 0.0, 0.5);  // base warp color; modulated by chaos
}
```

The SVT contains pre-evaluated `WarpFieldSample` values at each occupied voxel; UE5's HVR system interpolates between them during ray-march.

**CUDA pre-pass:** populate the SVT each frame from RBF network + chaos:

```cuda
__global__ void PopulateWarpSVT(
    SparseVolumeWriter svt_writer,
    const RBFNode* rbf_network,
    const uint* spatial_hash_offsets,
    const uint16_t* spatial_hash_counts,
    const uint16_t* spatial_hash_indices,
    cudaTextureObject_t chaos_tex,
    UnifiedWarpState state
) {
    int3 voxel = blockIdx * blockDim + threadIdx;
    float3 local = (voxel - SVT_CENTER) * VOXEL_SIZE_M;
    
    WarpFieldSample sample = SampleWarpField(local, /* view_dir not needed for population */, state, FLAG_GRADIENT);
    
    if (sample.metric > MIN_THRESHOLD) {  // occupancy test for SVT
        svt_writer.Write(voxel, sample);
    }
}
```

This is a one-pass kernel filling the SVT. Voxel count varies by bubble size — at typical 200m bubble at 1m resolution: 8M voxels × ~20 ALU ops each = 160 MOps. At 82 TFLOPS/s on 4090: ~2 μs. **Negligible.**

The actual cost is the SVT octree maintenance (UE5 RHI handles); ~0.5 ms.

**Render-time sampling:**

Each render ray-march step reads the SVT. ~256 steps per ray; 4M rays at half-res 4K. ~1B SVT reads per frame. Memory-bandwidth bound; ~3 ms on RTX 4090.

**Combined CUDA + UE5 render cost: ~3.5 ms.** Fits the §5.6 half-res budget of ≤4 ms.

---

---

## 6. DX12-CUDA interop

Per spec §8.1: UE5 RHI allocates and owns the DX12 textures; CUDA registers at startup; per-frame coordination via external semaphores; double-buffered fences. This section pins down the implementation.

### 6.1 Shared resource lifecycle

**Startup sequence:**

```cpp
// 1. UE5 creates the SVT and chaos volume textures
FRDGTextureDesc Desc = FRDGTextureDesc::Create3D(
    FIntVector(128, 128, 128), 
    PF_R32_FLOAT, 
    FClearValueBinding::None,
    TexCreate_ShaderResource | TexCreate_UAV | TexCreate_Shared
);
FRDGTextureRef ChaosVolumeRDG = GraphBuilder.CreateTexture(Desc, TEXT("ChaosVolume"));

// 2. Get the underlying ID3D12Resource* and create a shared NT handle
FD3D12Texture* D3D12Tex = static_cast<FD3D12Texture*>(ChaosVolumeRDG->GetResource());
ID3D12Resource* D3D12Resource = D3D12Tex->GetResource()->GetResource();
HANDLE SharedHandle;
D3D12Device->CreateSharedHandle(D3D12Resource, nullptr, GENERIC_ALL, nullptr, &SharedHandle);

// 3. Pass shared handle to CUDA (in plugin's CUDA module)
cudaExternalMemoryHandleDesc memDesc = {};
memDesc.type = cudaExternalMemoryHandleTypeD3D12Heap;  // or D3D12Resource for non-heap
memDesc.handle.win32.handle = SharedHandle;
memDesc.size = TotalSizeInBytes;
memDesc.flags = cudaExternalMemoryDedicated;
cudaExternalMemory_t cudaExtMem;
cudaImportExternalMemory(&cudaExtMem, &memDesc);

// 4. Map the external memory as a CUDA mipmapped array (matches the 3D texture)
cudaChannelFormatDesc channelDesc = cudaCreateChannelDesc<float>();
cudaExternalMemoryMipmappedArrayDesc mipDesc = {};
mipDesc.offset = 0;
mipDesc.formatDesc = channelDesc;
mipDesc.extent = make_cudaExtent(128, 128, 128);
mipDesc.flags = cudaArraySurfaceLoadStore;  // for surface object binding
mipDesc.numLevels = 1;
cudaMipmappedArray_t mipArray;
cudaExternalMemoryGetMappedMipmappedArray(&mipArray, cudaExtMem, &mipDesc);

cudaArray_t cudaArr;
cudaGetMipmappedArrayLevel(&cudaArr, mipArray, 0);

// 5. Create surface object (for writes) and texture object (for reads)
cudaResourceDesc resDesc = {};
resDesc.resType = cudaResourceTypeArray;
resDesc.res.array.array = cudaArr;
cudaSurfaceObject_t surface;
cudaCreateSurfaceObject(&surface, &resDesc);
// Texture object similarly via cudaCreateTextureObject
```

**Map once at startup, not per frame** — per spec §8.1 lock.

**Resize/destroy sequence:**

```cpp
// On viewport resize or scenario change
cudaDestroySurfaceObject(surface);
cudaFreeMipmappedArray(mipArray);
cudaDestroyExternalMemory(cudaExtMem);
CloseHandle(SharedHandle);

// UE5 destroys + recreates the texture; then full re-registration
```

### 6.2 External semaphores + fence handshake

**Per spec §8.1:** Per-frame coordination via external semaphores only. CUDA stream waits on DX12 fence before writing; DX12 waits on CUDA semaphore before reading. Double-buffered fences to prevent ping-pong stalls.

**Setup (once at startup):**

```cpp
// Create DX12 fence
TRefCountPtr<ID3D12Fence> D3D12Fence;
D3D12Device->CreateFence(0, D3D12_FENCE_FLAG_SHARED, IID_PPV_ARGS(&D3D12Fence));
HANDLE FenceHandle;
D3D12Device->CreateSharedHandle(D3D12Fence, nullptr, GENERIC_ALL, nullptr, &FenceHandle);

// Import to CUDA
cudaExternalSemaphoreHandleDesc semDesc = {};
semDesc.type = cudaExternalSemaphoreHandleTypeD3D12Fence;
semDesc.handle.win32.handle = FenceHandle;
cudaExternalSemaphore_t cudaSem;
cudaImportExternalSemaphore(&cudaSem, &semDesc);
```

**Per-frame coordination (warp-on graph):**

```cpp
// Frame N starts. UE5 is reading SVT from frame N-1's CUDA write.
// CUDA wants to write frame N's data into SVT.

// Step 1: UE5 finishes its read pass; signals fence at value N
D3D12CommandQueue->Signal(D3D12Fence, N);

// Step 2: CUDA stream waits for fence value N (last write done by GPU)
cudaExternalSemaphoreWaitParams waitParams = {};
waitParams.params.fence.value = N;
cudaWaitExternalSemaphoresAsync(&cudaSem, &waitParams, 1, stream);

// Step 3: CUDA writes frame N+1's data
cudaGraphLaunch(physics_graph_exec, stream);

// Step 4: CUDA signals fence at value N+1
cudaExternalSemaphoreSignalParams signalParams = {};
signalParams.params.fence.value = N + 1;
cudaSignalExternalSemaphoresAsync(&cudaSem, &signalParams, 1, stream);

// Step 5: UE5 waits for fence value N+1 before reading SVT this frame
D3D12CommandQueue->Wait(D3D12Fence, N + 1);
// Now UE5 can safely sample the SVT
```

**Double-buffered fences:**

To prevent ping-pong stalls, two fences alternating. While CUDA writes to fence value 2N+1, UE5 reads frame from fence value 2N-1; while UE5 reads frame from 2N+1, CUDA writes 2N+3. **Producer-consumer pipeline with one frame of latency** — the standard pattern.

In ASTRA-7's case the one-frame latency is acceptable (the chaos field changes slowly; the operator won't notice).

### 6.3 Memory ordering (acquire/release)

**Graphics-engineer outsider concern (attempt 1):** "On Windows/CUDA the atomic_int memory ordering needs to be release on GPU side / acquire on CPU side, not just SEQ_CST."

This applies to the AudioPayloadRingBuffer's `latest_complete_index` (per §8.2). The pattern:

**GPU side (CUDA, audio extraction kernel completion):**

```cuda
__global__ void AudioPayloadExtract(...) {
    // ... compute payload ...
    audio_ring_buffer.slots[write_idx] = computed_payload;
    
    __threadfence_system();  // ensure writes visible to host
    
    // Atomic update with release semantics (CC 7.0+)
    atomicExch_system((int*)&audio_ring_buffer.latest_complete_index, write_idx);
}
```

**Host side (audio thread, reading):**

```cpp
// Acquire load
int latest = std::atomic_load_explicit(
    reinterpret_cast<std::atomic<int>*>(&audio_ring_buffer.latest_complete_index),
    std::memory_order_acquire
);
const AudioExtractionPayload& payload = audio_ring_buffer.slots[latest];
// Safe to read; the release on GPU side paired with acquire here
```

Without `__threadfence_system()` + `atomicExch_system`, the writes to `slots[write_idx]` might not be visible to host when host reads `latest_complete_index` updated to write_idx. **The §8.2 spec lock needs to add the memory-ordering specification.** This pass flags it.

**For DX12-CUDA shared textures:** the external semaphore IS the memory barrier; no additional ordering needed beyond the fence handshake. DX12 ensures the write completes before signaling; CUDA's semaphore wait is acquire.

### 6.4 Resize handling

Per spec §8.1: "UE5 destroys old texture, registers new; CUDA unregisters old, registers new. Pipeline survives transparently."

**Implementation:**

```cpp
// On viewport resize (UE5 callback)
void OnViewportResize(int newWidth, int newHeight) {
    // 1. Stall CUDA stream until current work completes
    cudaStreamSynchronize(stream);
    
    // 2. Tear down CUDA resources
    cudaDestroySurfaceObject(svt_write_surface);
    cudaDestroyTextureObject(svt_read_texture);
    cudaFreeMipmappedArray(svt_mipped_array);
    cudaDestroyExternalMemory(svt_ext_mem);
    CloseHandle(svt_shared_handle);
    
    // 3. UE5 recreates the SVT at new resolution (typically SVT res doesn't depend on viewport; bubble-space is what matters; but if the rendered volume resolution does depend on viewport, this triggers)
    // [UE5 RHI does this internally; we get a new ID3D12Resource*]
    
    // 4. Re-register with CUDA (steps 1-5 from §6.1 startup)
    // ... full re-import ...
    
    // 5. Re-instantiate the CUDA graph (resources changed, so old graph is invalid)
    cudaGraphExecDestroy(physics_graph_exec);
    cudaGraphDestroy(physics_graph);
    // ... rebuild capture + instantiate ...
}
```

Cost: ~10-20 ms on resize (one-time pause). Acceptable; resize is rare.

**Why the chaos field doesn't usually resize:**

The chaos field is 128³ regardless of viewport resolution (it's a physics simulation, not a rendering buffer). Only the SVT representation of the warp field is viewport-coupled (and only if we choose to scale SVT resolution with viewport — which we shouldn't; SVT res should be tied to bubble-space, not screen-space).

**Lock decision:** SVT resolution is bubble-space-bound (e.g., 256³ over a 256m bubble = 1m voxel). Viewport-independent. Resize events affect only UE5's render targets, not the physics shared resources. **Eliminates the resize path for chaos + warp SVT entirely.** Big simplification.

---

---

## 7. UE5 plugin architecture

The plugin's name: `AstraPhysics`. It hosts CUDA code via a third-party C++ library (not directly UE5-managed because of the build complexity of CUDA inside UE5's UnrealBuildTool). UE5 module wraps the library and exposes UE-friendly types.

### 7.1 Module layout

```
Plugins/AstraPhysics/
├── AstraPhysics.uplugin            # plugin descriptor
├── Source/
│   ├── AstraPhysics/                                 # UE5 runtime module (C++)
│   │   ├── AstraPhysics.Build.cs                     # links AstraPhysicsCUDA library
│   │   ├── Public/
│   │   │   ├── AstraPhysicsModule.h
│   │   │   ├── StateBusComponent.h                   # UActorComponent
│   │   │   ├── WarpVolumeActor.h                     # AActor + HeterogeneousVolumeComponent
│   │   │   ├── ReflexComponent.h                     # UActorComponent — NNE inference
│   │   │   ├── ObservationCalculator.h               # USceneComponent
│   │   │   ├── HullSDFAsset.h                        # UObject for baked hash-grid asset
│   │   │   ├── CFDNetworkAsset.h                     # UObject for baked RBF asset
│   │   │   └── AstraPhysicsBlueprintLibrary.h        # static Blueprint functions
│   │   └── Private/
│   │       ├── AstraPhysicsModule.cpp
│   │       ├── StateBusComponent.cpp
│   │       ├── WarpVolumeActor.cpp
│   │       ├── ReflexComponent.cpp
│   │       ├── ObservationCalculator.cpp
│   │       └── CUDAInteropManager.cpp                # owns the DX12-CUDA shared resources
│   │
│   ├── AstraPhysicsCUDA/                             # C++/CUDA library (built with CMake separately)
│   │   ├── CMakeLists.txt
│   │   ├── include/
│   │   │   ├── astra_physics/types.h
│   │   │   ├── astra_physics/constants.h             # generated from proto/constants.toml
│   │   │   ├── astra_physics/state_bus.h
│   │   │   └── astra_physics/api.h                   # C API for UE5 module
│   │   ├── src/
│   │   │   ├── chaos_pde.cu                          # ChaosPDEStep, ChaosFieldInit
│   │   │   ├── warp_field.cu                         # SampleWarpField, PopulateWarpSVT
│   │   │   ├── rbf_network.cu                        # ModulateRBFWeights, SampleAtNodes
│   │   │   ├── reflex_inference.cpp                  # TensorRT wrapper (NNE compatible)
│   │   │   ├── retarded_time.cu                      # Newton solver for observe()
│   │   │   ├── kepler.cu                             # Kepler solver from astra_nexus
│   │   │   ├── interop_manager.cpp                   # cudaExternalMemory/Semaphore lifecycle
│   │   │   └── api.cpp                               # C API impl for UE5 binding
│   │   └── third_party/                              # symlinked or vendored
│   │       ├── tiny-cuda-nn/                         # hash-grid SDF
│   │       ├── tomlplusplus/                         # constants.toml loader
│   │       └── nlohmann_json/                        # for save-file JSON serialization
│   │
│   ├── AstraPhysicsEditor/                           # editor-only module (asset import, validation)
│   │   ├── AstraPhysicsEditor.Build.cs
│   │   ├── Public/HullSDFFactory.h
│   │   ├── Public/CFDNetworkFactory.h
│   │   └── Private/
│   │       ├── HullSDFFactory.cpp                    # imports baked .astra_hull → UHullSDFAsset
│   │       └── CFDNetworkFactory.cpp                 # imports baked .astra_cfd → UCFDNetworkAsset
│   │
│   └── ThirdParty/
│       └── AstraPhysicsCUDA.Build.cs                  # exposes the static library to UE5
│
├── Shaders/
│   ├── Private/
│   │   ├── WarpVolumeSample.usf                       # USF material function for HVR
│   │   ├── ObservationCalculatorCS.usf                # compute shader for retarded-time per body
│   │   ├── StarfieldDopplerCS.usf                     # apparent-rate + z_kin per star
│   │   └── CherenkovCone.usf                          # material function for Cherenkov rendering
│   └── Public/
│       └── (shader header files for cross-module use)
│
├── Content/
│   ├── Materials/
│   │   ├── M_WarpVolume.uasset                        # base warp material (uses WarpVolumeSample.usf)
│   │   ├── M_Cherenkov.uasset                         # cone material
│   │   └── M_StarfieldDoppler.uasset                  # starfield shader material
│   ├── BakedAssets/
│   │   ├── ASTRA7_Hull.astra_hull                     # binary hash-grid SDF
│   │   ├── ASTRA7_CFD.astra_cfd                       # binary RBF network
│   │   └── Reflex_v01.engine                          # TensorRT engine (per-GPU)
│   ├── Niagara/
│   │   ├── NS_ChaosParticles.uasset                   # chaos field visualization
│   │   └── NS_ISMImpact.uasset                        # ISM impact sparks
│   └── MetaSounds/
│       ├── MS_WarpDrone.uasset                        # Layer 1
│       ├── MS_ISMNoise.uasset                         # Layer 2
│       ├── MS_HullModal.uasset                        # Layer 5
│       └── MS_AudioMaster.uasset                      # mixes all 5 layers
│
└── Resources/
    └── constants.toml                                 # canonical constants (shared with astra_nexus)
```

**Build chain:**

1. CMake builds `AstraPhysicsCUDA` static library against CUDA toolkit. Outputs `libAstraPhysicsCUDA.a` (Linux) or `AstraPhysicsCUDA.lib` (Windows).
2. `AstraPhysics.Build.cs` adds the library as `PublicAdditionalLibraries` + `PublicIncludePaths`.
3. UE5 module compiles against the C API (`api.h`) defined in `AstraPhysicsCUDA`.

**No CUDA in the UE5 module itself** — keeps the UE5 module compilable by UnrealBuildTool without CUDA toolchain integration. The UE5 module sees a clean C API; the CUDA implementation is opaque.

### 7.2 Components (StateBus, WarpVolume, Reflex, Observation)

**UStateBusComponent** (the GPU-resident shared truth):

```cpp
UCLASS(ClassGroup = (AstraPhysics), meta = (BlueprintSpawnableComponent))
class ASTRAPHYSICS_API UStateBusComponent : public UActorComponent {
    GENERATED_BODY()
public:
    UStateBusComponent();

    // Blueprint-exposed read accessors
    UFUNCTION(BlueprintCallable, Category = "StateBus")
    FVector GetShipPosition() const;
    
    UFUNCTION(BlueprintCallable, Category = "StateBus")
    double GetCosmicTime() const;
    
    UFUNCTION(BlueprintCallable, Category = "StateBus")
    double GetShipTime() const;
    
    UFUNCTION(BlueprintCallable, Category = "StateBus")
    float GetDilationRatio() const;
    
    UFUNCTION(BlueprintCallable, Category = "StateBus")
    FString GetRegimeLabel() const;
    
    // C++ low-level access (for other plugin code)
    const StateBusGPU* GetGPUSnapshot() const { return CurrentSnapshot.Get(); }

    // Write path (called by physics driver in Tick)
    void CommitFrame(StateBusGPU&& NewState);

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
    TSharedPtr<StateBusGPU> CurrentSnapshot;  // frozen per Frozen-Snapshot Primitive (attempt 2 F2)
    void* CudaStreamHandle;   // opaque pointer to cudaStream_t
    void* CudaGraphExec;       // opaque pointer to cudaGraphExec_t for per-frame work
};
```

The component holds the CUDA stream + graph; ticks each frame to advance physics. **One instance per game (placed on the GameMode actor).**

**AWarpVolumeActor:**

```cpp
UCLASS()
class ASTRAPHYSICS_API AWarpVolumeActor : public AActor {
    GENERATED_BODY()
public:
    AWarpVolumeActor();

protected:
    UPROPERTY(VisibleAnywhere, Category = "Warp")
    UHeterogeneousVolumeComponent* WarpVolumeComponent;  // UE5.4+ class
    
    UPROPERTY(EditAnywhere, Category = "Warp")
    UCFDNetworkAsset* CFDNetwork;  // baked RBF network asset
    
    UPROPERTY(EditAnywhere, Category = "Warp")
    UMaterialInterface* WarpMaterial;  // material using WarpVolumeSample.usf
    
    virtual void BeginPlay() override;
    virtual void Tick(float DeltaTime) override;
    
private:
    // Reference to plugin's CUDAInteropManager (registers warp SVT for CUDA writes)
    class FCUDAInteropManager* CudaInteropMgr;
};
```

The Heterogeneous Volume Component is UE5's volumetric rendering API. We supply a material; UE5 ray-marches it. The material's USF function reads from the CUDA-shared SVT (registered by CUDAInteropManager).

**UReflexComponent:**

```cpp
UCLASS(ClassGroup = (AstraPhysics), meta = (BlueprintSpawnableComponent))
class ASTRAPHYSICS_API UReflexComponent : public UActorComponent {
    GENERATED_BODY()
public:
    UReflexComponent();

    // Blueprint exposure (rare; Reflex is autonomous)
    UFUNCTION(BlueprintCallable, Category = "Reflex")
    bool IsActive() const;

    UFUNCTION(BlueprintCallable, Category = "Reflex")
    FVector GetCurrentControlVector() const;

    UFUNCTION(BlueprintCallable, Category = "Reflex", BlueprintReadOnly)
    int32 GetLastInferenceLatencyNanoseconds() const;

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;
    virtual void BeginPlay() override;

private:
    TWeakObjectPtr<UNNEModelData> ReflexModel;        // NNE-loaded TensorRT engine
    TUniquePtr<class FNNERuntimeRDG> RuntimeRDG;       // render-graph backend (UE5.5+ NNE)
    
    // Last inference outputs
    float ControlNacelleDamping;
    float ControlConformality;
    float ControlEmergencyDump;
    int64_t LastLatencyNs;
};
```

The component ticks at frame rate; reads observation grid from CUDA (shared via interop); runs NNE inference; writes control vector to StateBus.

**UObservationCalculatorComponent:**

```cpp
UCLASS(ClassGroup = (AstraPhysics), meta = (BlueprintSpawnableComponent))
class ASTRAPHYSICS_API UObservationCalculatorComponent : public USceneComponent {
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintCallable, Category = "Observation")
    bool QueryObservable(
        const FVector& BodyPosition,
        UPARAM(ref) FObservableState& OutObservable
    );

protected:
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
    // Cached per-body observation state, written each frame by compute shader
    TArray<FObservableState> CachedObservables;
};
```

This is the §6.3 Observation Calculator surfaced as a UE5 component. The Tick dispatches a compute shader (ObservationCalculatorCS.usf) that fills `CachedObservables` for each visible body; QueryObservable returns the cached entry. The compute-shader path enables per-body Newton iteration on GPU; the Blueprint API exposes results for rendering + audio + perception assembly.

### 7.3 USF shader integration

**WarpVolumeSample.usf** (material function for Heterogeneous Volume):

```hlsl
// WarpVolumeSample.usf — sampled per ray-march step in HVR pipeline
#include "/Engine/Private/Common.ush"

// Bindings (auto-set by UE5 from material parameters):
Texture3D<float4>          WarpFieldSVT;       // shared with CUDA
SamplerState               WarpFieldSampler;   // trilinear, clamp
Texture3D<float>           ChaosFieldRead;     // shared with CUDA (read side of double buffer)

cbuffer WarpVolumeParams {
    float3 ShipPosition;
    float  WarpW;
    uint   WarpPhase;     // 0=idle, 1=charging, 2=cruising, 3=dropping
    float  ChargeProgress;
    float  TCosmic;
    float  AlphaLens;
    float  CherenkovBeta;
};

void SampleWarp(
    float3 WorldPos,
    float3 ViewDir,
    out float Extinction,
    out float3 Emissive,
    out float3 Albedo
) {
    // Transform world → ship-local
    float3 LocalPos = WorldPos - ShipPosition;
    
    // Sample the SVT (CUDA populated it this frame)
    float4 WarpSample = WarpFieldSVT.SampleLevel(WarpFieldSampler, LocalPos / VOXEL_SIZE_M, 0);
    float W = WarpSample.x;
    float3 GradW = WarpSample.yzw;
    
    // Sample chaos for modulation
    float Chaos = ChaosFieldRead.SampleLevel(WarpFieldSampler, LocalPos / CHAOS_SCALE_M, 0);
    
    // Effective metric
    float WMod = W * (1.0 + 0.02 * Chaos);
    
    // Volumetric properties (tuned)
    Extinction = WMod * 0.3;  // higher inside bubble; sky shows through outside
    
    // Emissive: violet base, brighter at boundary (high |∇W|)
    float GradMag = length(GradW);
    Emissive = float3(0.3, 0.05, 0.6) * GradMag * 2.0;
    
    // Albedo: deep purple
    Albedo = float3(0.25, 0.0, 0.4);
}
```

This is a UE5 material function exposed to the M_WarpVolume material. UE5's Heterogeneous Volume Render path calls it per ray-march step.

**ObservationCalculatorCS.usf** (compute shader for per-body retarded-time):

```hlsl
// ObservationCalculatorCS.usf — fills CachedObservables for all visible bodies
RWStructuredBuffer<FObservableState> OutObservables;
StructuredBuffer<FBodyState>          Bodies;
ConstantBuffer<FStateBusGPU>          StateBus : register(b0);

[numthreads(64, 1, 1)]
void MainCS(uint3 DispatchThreadID : SV_DispatchThreadID) {
    uint BodyIdx = DispatchThreadID.x;
    if (BodyIdx >= NumBodies) return;
    
    FBodyState Body = Bodies[BodyIdx];
    
    // Compute distance + initial retarded-time guess
    float3 BodyPos = (Body.Kind == BODY_STATIC_STAR) 
                     ? Body.StaticPosition 
                     : EvalKeplerAt(Body.Orbit, StateBus.time.t_cosmic);
    float3 ShipPos = ReconstructWorldPos(StateBus.ship_pos);
    float D = distance(ShipPos, BodyPos);
    
    double TEmit = StateBus.time.t_cosmic - D / C_LIGHT;
    
    // Newton iteration for moving bodies
    if (Body.Kind == BODY_KEPLER_PLANET) {
        for (int Iter = 0; Iter < 5; ++Iter) {
            float3 P = EvalKeplerAt(Body.Orbit, TEmit);
            float3 RVec = P - ShipPos;
            float Dist = length(RVec);
            float3 RHat = RVec / Dist;
            float3 V = EvalKeplerVelocityAt(Body.Orbit, TEmit);
            float F = TEmit + Dist / C_LIGHT - StateBus.time.t_cosmic;
            float FP = 1.0 - dot(RHat, V) / C_LIGHT;
            float DT = F / FP;
            TEmit -= DT;
            if (abs(DT) < 1.0e-6) break;
        }
    }
    
    // Compute redshifts
    float VRadial = dot(BodyPos - ShipPos, normalize(StateBus.ship_velocity)) - dot(0, 0);  // simplified
    float Beta = clamp(VRadial / C_LIGHT, -0.9999, 0.9999);
    float ZKin = sqrt((1.0 + Beta) / (1.0 - Beta)) - 1.0;
    float ZCosmo = H0_PER_SEC * D / C_LIGHT;
    float ZMetric = 0;  // from warp/grav sampler if body inside warp field
    float ZTotal = (1.0 + ZCosmo) * (1.0 + ZKin) * (1.0 + ZMetric) - 1.0;
    
    // Apparent rate (regime-dispatched per §3.11)
    float ApparentRate = ComputeApparentRate(VRadial, StateBus.time.regime);
    
    // Edge case flags
    bool BeyondPhotonHistory = (TEmit < Body.TSourceStart);
    bool BeyondHubbleHorizon = (D > HUBBLE_HORIZON_M);
    
    OutObservables[BodyIdx] = MakeObservable(
        D, VRadial, ZCosmo, ZKin, ZMetric, ZTotal, 
        TEmit, ApparentRate, BeyondPhotonHistory, BeyondHubbleHorizon
    );
}
```

Dispatch: `DispatchComputeShader(GraphBuilder, ComputeShader, FIntVector(NumBodies / 64 + 1, 1, 1))`.

### 7.4 Blueprint exposure

**UAstraPhysicsBlueprintLibrary:**

```cpp
UCLASS()
class ASTRAPHYSICS_API UAstraPhysicsBlueprintLibrary : public UBlueprintFunctionLibrary {
    GENERATED_BODY()
public:
    UFUNCTION(BlueprintPure, Category = "AstraPhysics|Time")
    static FString GetRegimeLabel(int32 RegimeBitmask);
    
    UFUNCTION(BlueprintPure, Category = "AstraPhysics|Time")
    static float GetDilationRatio(UObject* WorldContextObject);
    
    UFUNCTION(BlueprintCallable, Category = "AstraPhysics|Ship")
    static bool EngageWarp(UObject* WorldContextObject, float TargetFactor, FVector TargetCoords);
    
    UFUNCTION(BlueprintCallable, Category = "AstraPhysics|Ship")
    static bool DisengageWarp(UObject* WorldContextObject, bool bEmergency);
    
    UFUNCTION(BlueprintCallable, Category = "AstraPhysics|Ship")
    static bool AllocatePower(UObject* WorldContextObject, FName Subsystem, float Fraction);
};
```

These mirror the locked TOOL_API (per [astra/ship/api.py](proto/textverse/astra/ship/api.py) Surface 3 — 6 ops at v0). ASTRA-Mind issues `<tool>` invocations that route through Adapter-LLM → Dispatcher → these Blueprint functions in UE5. **Same TOOL_API surface as the bench, called from UE5.** This is the §15.7 Surface 3 mechanical-drift-prevention pattern.

Console UI input (player typing on bridge console) similarly routes through these Blueprint functions for direct operator control.

---

---

## 8. UE5.5 feature integration

UE5.5 (released late 2024) and UE5.6 (released mid-2025 expected) bring several features that ASTRA-7 can use natively rather than building custom paths. As of May 2026, the relevant features are all GA-stable.

### 8.1 Neural Network Engine (NNE) for Reflex

**UE5 NNE was introduced in UE5.0 as experimental, became GA in UE5.4, was enhanced in UE5.5 with render-graph integration.** This is the canonical UE5 path for ML inference.

**Architecture:**

- `UNNEModelData` — UObject wrapping a binary blob (ONNX or TensorRT engine)
- `INNERuntime` — backend abstraction (`NNERuntimeORT` for ONNX, `NNERuntimeRDG` for render-graph, `NNERuntimeIREE` for IREE)
- `IModelInstance` — instantiated model for inference
- Integration with `FRDGBuilder` for compute-graph composition

**Reflex inference flow:**

1. Plugin loads `ReflexModel.uasset` (UNNEModelData wrapping the TensorRT engine).
2. At startup: `RuntimeRDG->CreateModel(...)` returns an `IModelInstance`.
3. Per-frame:
   - CUDA writes observation grid to shared resource (64×64×2 floats).
   - UE5 reads shared resource into NNE input tensor.
   - NNE schedules inference into FRDGBuilder (compute pass).
   - Output written to control vector buffer; read by physics driver.

**Why TensorRT through NNE vs raw CUDA:**

- TensorRT directly: tightest latency (15-20 μs) but bypasses UE5 render graph; needs explicit DX12-CUDA interop for input/output buffers.
- NNE RDG backend: ~25-30 μs but integrates with UE5 frame pipeline; CUDA-graphs-friendly; no per-frame interop dance.

**For Reflex's ≤50 μs budget**, the 5-10 μs penalty of NNE-RDG is acceptable; the architectural cleanliness (one buffer in UE5 RDG, no manual interop) is worth it. **Lock to NNE-RDG backend with TensorRT-NVIDIA underneath.**

**Fallback path for non-NVIDIA hardware:**

NNE's ORT backend with DirectML execution provider runs ONNX inference on any DX12 device (Intel ARC, AMD RDNA3+). Latency ~50-100 μs — degrades but still within Reflex's degraded-mode budget. For Linux + Vulkan path: ORT with CUDA execution provider (CUDA-only); fallback to CPU EP (~500 μs; only for emergencies).

### 8.2 Heterogeneous Volumes for warp rendering

**Heterogeneous Volume Renderer (HVR) was added in UE5.4** and matured in UE5.5. It's the right primitive for the warp bubble.

**Why HVR over alternatives:**

- **Custom volumetric pass:** would require ~500 LOC of custom render graph code, fragile across UE versions, no built-in shadow integration.
- **Niagara volume:** more particle-shaped; doesn't compose with Lumen GI well.
- **HVR:** built-in ray-march; integrates with Lumen for indirect lighting; composes with translucent geometry; material-driven (USF customization).

**HVR pipeline:**

1. Place `AWarpVolumeActor` with `UHeterogeneousVolumeComponent`.
2. Assign material (M_WarpVolume using WarpVolumeSample.usf).
3. UE5 ray-marches per pixel; calls material function per step.
4. Material function samples our CUDA-shared SVT.
5. Lumen handles GI contribution from the warp field's emissive output.

**Quality knobs:**

- `r.HeterogeneousVolumes.MaxStepCount` — default 256; spec §5.6 budget
- `r.HeterogeneousVolumes.StepSize` — adaptive based on ∇W (this pass's §3.5)
- `r.HeterogeneousVolumes.HalfRes` — half-res ray-march for performance

**Tradeoffs:**

HVR uses UE5's TSR (Temporal Super Resolution) by default; the warp's chaos modulation introduces flicker that TSR can amplify. Mitigation: enable per-pixel jittered sampling at material level; TSR's anti-flicker filter cleans up.

### 8.3 Sparse Volume Textures for chaos + warp fields

**Sparse Volume Texture (SVT) is UE5.4+ feature** for efficient volumetric storage.

**Use cases in ASTRA-7:**

1. **Warp field SVT** (~6-8 MB): octree-encoded W(x,t) + ∇W. CUDA writes per frame; HVR reads via material.
2. **Chaos field** could be SVT but isn't a great fit — the chaos PDE writes EVERY voxel (Fisher-KPP rarely produces sparse output). Better to keep chaos as dense 3D texture, only the warp field as SVT.

**SVT structure:**

UE5's SVT internally uses a single-level tile-based representation (not full octree). Tiles are 32³ uniform blocks; occupied tiles allocated, empty tiles reference a sentinel.

For a 256³ logical volume with 5% occupancy (typical warp bubble): ~12 tiles × 32³ × 4 bytes = ~1.5 MB. Plus metadata (~256 KB). **Total ~2 MB** — much better than 64 MB dense.

**CUDA-side SVT writing:**

```cuda
__global__ void PopulateWarpSVT(SVTAccessor svt, /* ... */) {
    int3 voxel = threadIdx + blockIdx * blockDim;
    if (voxel exceeds bounds) return;
    
    WarpFieldSample sample = SampleWarpField(/* local pos */, /* state */, FLAG_GRADIENT);
    
    if (sample.metric > MIN_THRESHOLD) {
        svt.WriteVoxel(voxel, EncodeSampleToFloat4(sample));
    }
    // else: voxel stays empty in SVT
}
```

The `SVTAccessor` is a wrapper around the UE5 SVT's CUDA-mapped representation. Implementation requires UE5 source-code-level integration to expose SVT internals to CUDA (not trivial; one of the more complex parts of the Engine track).

**Alternative (simpler):** write to a dense 3D texture; let UE5 RHI internally convert to SVT representation if it deems beneficial. ~5-10% memory bloat but no engine-source-mod needed.

**Lock decision:** start with dense 3D texture (simpler); migrate to SVT-native-write if profiling shows memory pressure.

### 8.4 MetaSound for audio

**MetaSound is GA since UE5.0** and remains the canonical audio synthesis graph in UE5.5. Per CLAUDE.md it's the locked audio backend.

**Five-layer audio architecture (spec §8.3):**

```
MS_AudioMaster (graph orchestrator)
├── MS_WarpDrone           # Layer 1: ambient warp resonance
│   ├── Oscillator nodes (3-6 sine generators)
│   ├── Filter (low-pass, modulated by Warp_W parameter)
│   └── Mix bus
├── MS_ISMNoise            # Layer 2: ISM impact + HPF
│   ├── White noise generator
│   ├── HPF (α_hpf = exp(−2π·f_c/SR) per §8.3 — implement as biquad)
│   ├── Amplitude modulator (driven by ISMImpactIntensity parameter)
│   └── Mix bus
├── MS_HullModal           # Layer 5: modal resonance
│   ├── 8× parallel biquad IIR (y[n] = 2cos(ω₀)·r·y[n-1] − r²·y[n-2] + x[n])
│   │   where r = exp(−π·BW/SR)
│   ├── Per-mode frequency parameter (HullStressModalFrequencies[8])
│   ├── Per-mode amplitude parameter
│   └── Sum bus
├── MS_Granular            # Layer 4: granular synth for particulate
│   ├── Granulator node (UE5 native; 8-16 voice round-robin)
│   ├── Grain density parameter
│   └── Mix bus
└── MS_Tidal               # Layer for GRAVITY_WELL tidal stress (§7.6)
    ├── Modulated frequency oscillator (tracks τ_external)
    └── Mix bus

Final mix → Spatial 3D audio → Output to MasterSubmix
```

**MetaSound parameters fed from physics:**

Each frame, the physics driver writes to the AudioPayloadRingBuffer (per §8.2); audio thread reads `latest_complete_index`; sets MetaSound parameters via `UMetaSoundSource::SetParameterByName(...)`.

```cpp
void TickAudioParameterUpdate() {
    int Latest = AudioPayloadRingBuffer->latest_complete_index.load(std::memory_order_acquire);
    const AudioExtractionPayload& Payload = AudioPayloadRingBuffer->slots[Latest];
    
    MetaSoundInstance->SetFloatParameter("Warp_W", Payload.warp_drone_amplitude);
    MetaSoundInstance->SetFloatParameter("WarpDroneFreq", Payload.warp_drone_frequency);
    MetaSoundInstance->SetFloatParameter("ISMImpactIntensity", Payload.ism_impact_intensity);
    for (int i = 0; i < 8; ++i) {
        MetaSoundInstance->SetFloatParameter(FString::Printf(TEXT("HullModalFreq_%d"), i), Payload.hull_stress_modal_frequencies[i]);
        MetaSoundInstance->SetFloatParameter(FString::Printf(TEXT("HullModalAmp_%d"), i), Payload.hull_stress_modal_amplitudes[i]);
    }
    MetaSoundInstance->SetFloatParameter("TidalExt", Payload.tidal_stress_external);
    MetaSoundInstance->SetFloatParameter("GrainDensity", Payload.granular_grain_density);
}
```

Run this every game-tick (60 Hz); MetaSound interpolates parameters between updates for smooth audio.

**Endogenous (t_cosmic, no retardation) per §8.3:** parameters reflect CURRENT ship state, not retarded-time-source state. The audio thread reads at frame-rate; no Observation Calculator path involved. **The audio ear hears the present while the visual eye sees the past at warp egress** — the spec's intentional eye-ear decoupling.

### 8.5 Substrate (Strata) for hull materials

**Substrate (renamed from Strata in UE5.5)** is UE5's layered material system. Replaces the legacy "shading model" enum with composable BSDFs.

**Use for ASTRA-7 hull:**

The hull design (memory/hull_design_v0.md) specifies:
- Primary composite armor: matte deep charcoal-grey, faceted 3-5m panels
- Polished machined aluminum bands along structural ribs
- Sapphire viewports with slight blue-grey tint
- Radiator panels: matte black hexagonal honeycomb
- Drive zone hot section: dark grey ceramic glowing orange-red

These are **layered materials** in the Substrate sense — composite armor underneath, aluminum overlay, optional emissive heat layer on drive zones. Substrate's `SubstrateAdd`, `SubstrateBlend`, `SubstrateCoverageBlend` nodes compose them cleanly without per-pixel switching.

**Damage map integration:**

The hull SDF's damage map gets visualized via Substrate's per-pixel modulation: damaged voxels reduce the composite armor's layer coverage, exposing darker underlying material + crack-like emissive lines. Reads from the same `cudaTextureObject_t` damage texture per §1.3.

**Material asset:** `M_HullPrimary.uasset` is a Substrate Master Material; per-hull-section instances inherit and tune parameters.

### 8.6 Niagara for chaos particle visualization

**Niagara is GA since UE5.0**; standard particle system.

**Chaos field visualization:**

When chaos field χ(x,t) is high (>~0.7 normalized), it's visible as "warp instability" — particle artifacts at the bubble boundary. Niagara reads from the chaos field 3D texture (CUDA-shared) and emits particles at high-χ locations.

```
NS_ChaosParticles (Niagara System):
  Emitter: ChaosFieldSampler
    Spawn rate: SampleVolume_TextureCount(ChaosFieldTexture, threshold=0.7)
    Position: SampleVolume_TextureWeightedPosition(ChaosFieldTexture)
    Velocity: GradientOfTexture(ChaosFieldTexture) × random_unit_vector
    Color: lerp(violet, magenta, χ_value)
    Lifetime: 0.5s
    Renderer: Niagara Mesh Renderer (small cube primitives)
```

Cost: ~0.1 ms per frame for ~10K particles. Acceptable.

**ISM impact sparks:**

When relativistic STL impact intensity exceeds threshold, spawn forward-cone particles. Niagara's `NS_ISMImpact` system reads `ISMImpactIntensity` from a global parameter; emits particles along ship's velocity vector.

### 8.7 DLSS 3.7 / FSR 3.1 / XeSS for upscaling

**UE5.5 has native DLSS 3 + FSR 3 + XeSS integration via plugins** (NVIDIA DLSS Plugin, AMD FSR Plugin, Intel XeSS Plugin — all UE Marketplace-distributed, free).

**Recommended config:**

- **NVIDIA (5090/4090 reference):** DLSS 3.7 Quality preset + Frame Generation. Renders at 1440p, AI-upscales to 4K + AI-interpolates intermediate frames. Effective FPS doubling.
- **AMD RDNA3+:** FSR 3.1 Quality + Frame Generation. Comparable to DLSS 3.
- **Intel ARC:** XeSS 1.3 Quality (no frame-gen yet as of May 2026). Pure spatial upscale.
- **No upscaler available:** native 1440p or 1080p with TSR (UE5's built-in temporal upscaling).

**Implications for warp rendering:**

The volumetric warp render at half-res is `1080p × 0.5 = 540p effective`; DLSS Frame Gen brings effective 4K @ 60+ FPS within budget. The chaos modulation introduces high-frequency noise that DLSS Frame Gen handles well (it expects motion-induced noise).

**One gotcha:** DLSS Frame Gen requires the rendered frame's depth + motion-vector buffer to be accurate. Heterogeneous Volumes write to depth (the bubble is occluding); motion vectors track bubble motion. UE5's HVR provides both natively. **No additional engineering needed.**

---

---

## 9. Rendering pipeline

The end-to-end frame flow with all systems integrated. Per-frame timeline at 60 FPS:

```
T=0       Frame N begins
T=0-1     CPU: physics driver tick — compute composition rule, update TimeState, decide regime
T=1-3     CPU: per-frame CUDA work (CUDAGraphLaunch) — chaos PDE step + warp SVT population
T=3       Fence signal: CUDA → DX12 ready
T=3-8     GPU: UE5 main render — base pass, Nanite, Substrate hull, GI via Lumen
T=8-12    GPU: UE5 HVR pass — warp volume ray-march (samples CUDA-shared SVT)
T=12-13   GPU: starfield retarded-time pass (compute shader)
T=13-14   GPU: post-process (Cherenkov, redshift color, atmospheric fog, DLSS)
T=14-15   GPU: present
T=15-16.67 Reserve / overhead
```

Total: ~15 ms with reserve. Headroom for jitter at 60 FPS.

### 9.1 Ray-march loop for warp volume

**UE5 Heterogeneous Volume Renderer (HVR) handles the outer loop;** our material function handles the per-step sample. The key configuration:

```cpp
// In WarpVolumeActor construction:
WarpVolumeComponent->SetStepSize(0.5f);     // 0.5m default; adaptive in material
WarpVolumeComponent->SetMaxStepCount(256);  // per spec §5.6 budget
WarpVolumeComponent->SetMaterial(0, WarpVolumeMaterial);
WarpVolumeComponent->SetBoundsExtent(FVector(200.0f, 200.0f, 200.0f));  // 200m bubble bound
```

**Adaptive step size within material:**

```hlsl
// Inside WarpVolumeSample.usf
void SampleWarp(float3 WorldPos, float3 ViewDir, out float Extinction, ...) {
    float4 Sample = WarpFieldSVT.SampleLevel(...);
    float GradMag = length(Sample.yzw);
    
    // Step size hint: smaller near boundary (high |∇W|); larger inside / outside
    float StepHint = lerp(1.0, 0.25, saturate(GradMag * 4.0));  // [0.25m, 1.0m]
    
    // HVR uses StepHint as multiplier on base step size
    // (UE5.5+ supports per-sample step-size hints)
    
    Extinction = Sample.x * 0.3;
    // ... emissive, albedo ...
    
    // The HVR pipeline interprets `Extinction` for absorption + scatter
}
```

**Empty-space skipping:**

If sample reads W < epsilon (outside bubble), Extinction = 0; UE5 HVR's adaptive sampling skips ahead until next non-empty voxel. The SVT representation makes this cheap (sparse octree walks straight past empty tiles).

**Expected speedup over uniform marching:**

A typical view ray through the bubble traverses ~50-100 occupied voxels out of 256 march steps. With empty-space skipping + adaptive sizing: effective ~80 samples per ray. **3× speedup over naive 256-uniform.** ~1.3 ms instead of 4 ms at half-res 4K.

### 9.2 Geometric lensing integration

**Spec §3.4 + §6 step 9:** light rays passing near the warp bubble boundary are bent by ∇W. The effect is implemented by deflecting the ray direction at each march step:

```
direction_{n+1} = normalize(direction_n + α_lens · ∇W(x_n) · Δs)
```

**Implementation in HVR:**

HVR's standard ray-march doesn't bend rays; it walks straight. We need a custom path. Two options:

**Option A: Two-pass approach (cleaner; recommended):**

1. First pass: HVR ray-march for the warp bubble's volumetric extinction + emission (color of the bubble itself).
2. Second pass: A separate full-screen post-process that, for each pixel, casts a "deflected" ray from the camera through the warp gradient field, samples the background (skybox + starfield + distant geometry) at the deflected angle, and blends with the bubble color.

The second pass is a custom UE5 render pass added via FRDGBuilder; ~150 LOC of plugin code. Reads from the SVT's `metric_gradient` channel + skybox/starfield cubemap.

**Option B: Modify HVR's ray-march directly (more performant; harder):**

Patch UE5's HVR shader (`HeterogeneousVolumesRayMarching.usf`) to accept an optional deflection per step. Requires Engine source-code mod + maintains-per-UE-version-upgrade.

**Lock decision:** Option A. Cleaner; doesn't fork Engine source. ~2-3 ms cost at 4K (post-process pass is fast on modern GPUs). The Engine-mod approach saves maybe 1 ms but adds permanent maintenance cost.

**Lensing parameter `α_lens`:**

Provisional per Appendix B. The CFD bake doesn't determine it; it's a visual tuning knob set against rendered output. Lock in `proto/constants.toml` once visual testing converges.

### 9.3 Cherenkov cone rendering

**Spec §6 step 10:** `cos θ_c = 1/(n·β)`. Where `n` = local warp index of refraction, `β` = effective velocity.

**Visible when:** `n · β > 1` (cone exists; ship "outpaces" local light speed in the warp medium). Inside the bubble at high W, n increases; cone narrows toward forward direction.

**Rendering as material on bubble boundary surface:**

```hlsl
// CherenkovCone.usf — material function applied to bubble boundary

void ComputeCherenkov(
    float3 WorldPos,
    float3 ViewDir,
    out float3 EmissiveAddition,
    out float CherenkovStrength
) {
    // Sample local W to derive index of refraction
    float W = SampleWarpFieldAtPos(WorldPos).x;
    float N = 1.0 + W * REFRACTION_PER_METRIC;   // tuned coefficient
    float Beta = StateBus.cherenkov_beta;
    
    if (N * Beta <= 1.0) {
        // Cherenkov inactive
        EmissiveAddition = float3(0, 0, 0);
        CherenkovStrength = 0.0;
        return;
    }
    
    // Cone half-angle
    float CosThetaC = 1.0 / (N * Beta);
    float ThetaC = acos(CosThetaC);
    
    // Forward direction (ship velocity normalized)
    float3 ForwardDir = normalize(StateBus.ship_velocity);
    
    // Angle from forward to view direction
    float ViewDotForward = dot(-ViewDir, ForwardDir);
    float ViewAngle = acos(ViewDotForward);
    
    // Cone visibility: stronger when view angle ≈ cone angle
    float ConeIntensity = exp(-pow((ViewAngle - ThetaC) / 0.05, 2.0));  // narrow Gaussian
    
    // Cherenkov is blue/UV-shifted; color depends on N and Beta
    float3 ConeColor = float3(0.4, 0.6, 1.0);  // base blue-cyan
    
    EmissiveAddition = ConeColor * ConeIntensity * 4.0;
    CherenkovStrength = ConeIntensity;
}
```

**Where this attaches:**

The Cherenkov cone is visible at the warp bubble boundary surface (where light from the bubble's "wake" emerges into normal space). UE5 renders this as additive emission on the bubble's outer SDF surface (computed during HVR pass). At v_app > c, the cone is forward-facing relative to ship; observer behind sees a backward cone (the "shock" of warp transition).

**Visual reference:** similar to nuclear-reactor Cherenkov glow in water, but in 3D with directional cone instead of omnidirectional.

### 9.4 Retarded-time star rendering

**Spec §6.3 + §3.11:** distant stars rendered at retarded time.

**Pipeline:**

1. Per-frame compute shader (`ObservationCalculatorCS.usf`) computes `t_emit`, `z_total`, `apparent_rate`, `beyond_photon_history`, `beyond_hubble_horizon` for every visible body (~10K stars + ~100 in-system planets).
2. Output: `CachedObservables` structured buffer.
3. Starfield rendering pass (custom UE5 mesh or Niagara): per-instance shader reads CachedObservables, computes apparent position at t_emit, applies redshift color, emits to render target.
4. Bodies flagged `beyond_photon_history` or `beyond_hubble_horizon` are culled (not rendered) or rendered as frozen frame.

**Starfield position at t_emit:**

For static stars (which is most of them), `t_emit = t_cosmic - d/c`; position is the same as at t_cosmic (no proper motion modeled in v0). Apparent position differs only by retarded-time correction for moving sources.

For nearby Kepler bodies (planets, moons), the position at t_emit is from `EvalKeplerAt(orbit, t_emit)` — orbital phase is dialed back by the light-travel time. **This is the visible orbit-reversal effect at warp** (per [astra_nexus.cpp:639-677](proto/astra_nexus.cpp:639) Kepler-at-t_emit test).

**Redshift color shift:**

```hlsl
// In starfield mesh material:
float ZTotal = CachedObservables[InstanceID].z_total;
float WavelengthShift = 1.0 / (1.0 + ZTotal);  // λ_emit = λ_obs * shift; we scale emission spectrum
float3 BaseColor = StarColorFromTemperature(Star.Temperature);
float3 ShiftedColor = ApproximateBlackbodyShift(BaseColor, WavelengthShift);
EmissiveColor = ShiftedColor * Star.Luminosity / (Distance * Distance);
```

The `ApproximateBlackbodyShift` is a ~10-line approximation; for high accuracy use a 1D LUT keyed on `(Temperature, ZTotal)`.

**Photon-source-history bound culling:**

```hlsl
if (CachedObservables[InstanceID].beyond_photon_history) {
    // Source is gone — clip the vertex
    OutputPosition = float4(NaN, NaN, NaN, NaN);  // SV_Position with NaN clips the primitive
    return;
}
```

**Apparent-rate visual:**

For animated bodies (e.g., periodic flickering pulsars), the apparent_rate determines playback speed. A pulsar emitting at 1 Hz appears at `1 × apparent_rate` Hz to the ship; under WARP_CRUISE at 10c receding, apparent_rate = -9 → pulsar appears to flicker IN REVERSE at 9 Hz. The Niagara/mesh-particle shader reads `apparent_rate` and modulates emission accordingly.

**Cost:**

- Compute shader: ~100 μs at 10K bodies
- Starfield rendering: standard Niagara mesh particles; ~1-2 ms at 10K + Kepler bodies
- Total: ~2 ms in the §5.6 rendering budget

### 9.5 Eye-ear decoupling (audio at t_cosmic; visual at t_emit)

**Spec §8.3 + §6.3 endogenous/exogenous principle:** audio is endogenous (reads State Bus at t_cosmic); visuals of distant bodies are exogenous (read at t_emit).

**Concrete consequence at warp egress:**

Ship drops out of WARP_CRUISE at high v_app. The visual rear view shows orbital bodies running in reverse (per Kepler-at-t_emit). The audio drone is the current warp shutdown sound — not retarded; reflects what the ship's hull is doing RIGHT NOW.

**Why this is correct (not a bug to fix):**

- Audio comes from hull stress sensors, atmosphere chemistry, internal acoustic signatures. These are LOCAL to the ship; there's no light-travel delay because there's no light involved.
- Visual comes from photon flux that left distant bodies hours/days/years ago. The eye sees the past.

**Architectural enforcement:**

The AudioPayloadExtract kernel reads from StateBus's current frame (t_cosmic via State Bus); does NOT route through ObservationCalculator. The StarfieldDopplerCS reads from CachedObservables which DOES route through Newton iteration. **Two independent code paths; the static analysis check from spec §10 verifies they don't cross.**

This pass's F4 (endogenous/exogenous as type system) would make this a compile-time guarantee instead of runtime convention.

**Player experience design:**

At warp egress: visuals (rear view) show stars/planets running in reverse; audio is normal warp-shutdown sound. The cognitive dissonance is intentional per spec §3.11: "engaging warp produces a perceptual snap... the moment of causality-violation rendered visible. Do not smooth across the boundary."

Subtle: the eye-ear mismatch IS the rendering of causality-violation. Disengaging warp brings the eye back to sync with the ear over ~seconds as light-time-of-flight from each visible body completes.

---

---

## 10. Bake and build pipeline

Per Language Discipline (CLAUDE.md): all bake tools are C++/CUDA. No Python in the bake or build path. The pipeline produces binary assets shipped in the UE5 plugin's Content/ directory.

### 10.1 CFD bake: OpenFOAM → RBF fitter → binary asset

**Input:** ship hull geometry (the same source mesh that produces the hull SDF).

**Step 1: CFD simulation in OpenFOAM**

OpenFOAM is C++; native; runs on Linux; standard install. Produces a velocity field around the hull representing the bubble's analog-gravity-metric (per spec §6.1 "the acoustic metric arising from irrotational barotropic fluid flow exhibits a Lorentzian signature isomorphic to a class of curved spacetimes including warp-like geometries").

Configuration:
- Steady-state incompressible solver (`simpleFoam`)
- Inlet boundary: subsonic flow at v_eff (the bubble's apparent velocity)
- Outlet boundary: zero gradient
- Hull surface: no-slip wall (the ship body deflects the flow)
- Domain: 3× hull extent in each axis (~840m × 234m × 66m for the ASTRA-7 280m hull)
- Mesh: ~10M cells (snappyHexMesh octree refinement near hull)

Output: `pressure.dat`, `velocity.dat` from OpenFOAM (millions of cells).

**Step 2: RBF fitter (custom C++ tool)**

Input: OpenFOAM output fields.
Output: ~1000 RBF nodes (centers, radii, weights) that approximate the field.

Algorithm: iterative RBF center placement via residual-greedy method:
1. Start with empty RBF set.
2. Find point in domain with maximum residual `|field(x) - W_rbf(x)|`.
3. Add RBF node centered there with radius = local feature size; weight chosen to minimize residual at neighbors.
4. Repeat until either N=1000 nodes placed OR maximum residual < tolerance.

```cpp
// rbf_fitter.cpp (C++17)
struct RBFFitter {
    Field input_field;
    std::vector<RBFNode> nodes;
    double max_residual;
    
    void fit() {
        // Evaluate residual at all CFD cells
        std::vector<double> residual = compute_residual();
        
        while (nodes.size() < MAX_NODES) {
            // Find max residual point
            size_t idx = argmax(residual);
            if (residual[idx] < TOLERANCE) break;
            
            Vec3 c = cell_position[idx];
            double sigma = estimate_local_feature_size(idx);  // ~5-50m
            double weight = residual[idx];  // initial guess; refined by least-squares
            
            nodes.push_back({c, sigma, weight});
            
            // Refine weights via LSQ on all current nodes (Eigen solver)
            refine_weights_lsq();
            
            // Recompute residual
            residual = compute_residual();
        }
        
        // Build spatial-hash accelerator
        build_spatial_hash();
    }
    
    void save_binary(const std::string& path) {
        // Write: header (magic, version), node_count, nodes[], 
        //        spatial_hash_offsets[], spatial_hash_counts[], spatial_hash_indices[]
        BinaryWriter writer(path);
        writer.write_header(MAGIC_ASTRA_CFD, VERSION_1);
        writer.write_array(nodes);
        writer.write_array(spatial_hash_offsets);
        writer.write_array(spatial_hash_counts);
        writer.write_array(spatial_hash_indices);
    }
};
```

**Dependencies:** Eigen (header-only; for LSQ refinement), nlohmann/json (for metadata sidecar). Both BSD/MIT.

**Bake time:** ~30 min on a modern workstation for a 280m hull + 1000 RBF nodes.

**Output asset:** `ASTRA7_Hull.astra_cfd` — ~30 KB binary file (the RBF network + spatial hash). Shipped in UE5 plugin's Content/BakedAssets/.

**UE5 import:** the `UCFDNetworkFactory` (editor module) reads the .astra_cfd file and creates a `UCFDNetworkAsset` UObject.

### 10.2 Hull SDF bake: mesh → hash-grid encoding

**Input:** the same ship hull mesh (FBX or OBJ).

**Step 1: Dense SDF generation (intermediate)**

Use OpenVDB (C++; permitted per CLAUDE.md "mesh manipulation: CGAL · openMesh · OpenVDB"). Generate a high-resolution dense SDF (~512³) as ground truth.

```cpp
#include <openvdb/openvdb.h>
#include <openvdb/tools/MeshToVolume.h>

void GenerateDenseSDF(const std::string& mesh_path, const std::string& vdb_path) {
    openvdb::initialize();
    
    // Load mesh
    std::vector<openvdb::Vec3s> points;
    std::vector<openvdb::Vec3I> triangles;
    LoadMeshFromFile(mesh_path, points, triangles);
    
    // Convert to SDF grid (signed distance field)
    openvdb::FloatGrid::Ptr grid = openvdb::tools::meshToSignedDistanceField<openvdb::FloatGrid>(
        *transform, points, triangles, openvdb::Vec3R(0), 
        /*exteriorWidth=*/3.0f, /*interiorWidth=*/3.0f
    );
    
    // Save VDB file
    openvdb::io::File(vdb_path).write({grid});
}
```

Output: `ASTRA7_Hull.vdb` — intermediate dense SDF.

**Step 2: Hash-grid encoding via tiny-cuda-nn**

```cpp
#include <tiny-cuda-nn/encodings/grid.h>
#include <tiny-cuda-nn/networks/fully_fused_mlp.h>

void BakeHashGridSDF(const std::string& vdb_path, const std::string& output_path) {
    // Load dense SDF as ground truth
    auto dense_grid = LoadDenseFromVDB(vdb_path);
    
    // Configure hash-grid encoding
    nlohmann::json encoding_config = {
        {"otype", "Grid"},
        {"type", "Hash"},
        {"n_levels", 4},
        {"n_features_per_level", 4},
        {"log2_hashmap_size", 19},   // 2^19 = 524K entries per level
        {"base_resolution", 16},
        {"per_level_scale", 2.0}
    };
    
    nlohmann::json network_config = {
        {"otype", "FullyFusedMLP"},
        {"activation", "ReLU"},
        {"output_activation", "None"},
        {"n_neurons", 16},
        {"n_hidden_layers", 2}
    };
    
    // Build encoder + small MLP
    auto encoder = tcnn::create_encoding<float>(3, encoding_config);
    auto network = tcnn::create_network<float>(encoder->n_output_dims(), 1, network_config);
    auto model = std::make_shared<tcnn::NetworkWithInputEncoding<float>>(encoder, network);
    
    // Train: random samples from dense_grid, optimize MLP weights + hash table
    auto optimizer = std::make_shared<tcnn::AdamOptimizer<float>>(network_config);
    
    for (int iter = 0; iter < TRAIN_ITERATIONS; ++iter) {
        // Sample N points from dense grid
        auto [coords, target_sdf] = SampleRandom(dense_grid, BATCH_SIZE);
        
        // Forward + backward
        auto predicted = model->forward(coords);
        auto loss = MSELoss(predicted, target_sdf);
        model->backward(loss);
        optimizer->step();
    }
    
    // Serialize hash table + MLP weights
    SerializeHashGridSDF(model, output_path);
}
```

**Training time:** ~30 min on a 4090 for 30K iterations.

**Output:** `ASTRA7_Hull.astra_hull` — ~10 MB binary asset (hash table + MLP weights).

**UE5 import:** `UHullSDFFactory` creates a `UHullSDFAsset`.

### 10.3 Reflex weights: chaos PDE corpus → TensorRT engine

**Input:** synthetic chaos PDE event corpus + control labels (chosen by hand to give Reflex its training signal).

**Step 1: Generate training corpus**

A C++ tool runs the chaos PDE under varied parameters (different α, k, M_BH values) and records:
- Per-frame chaos observation grid (64×64×2 = chaos amplitude + metric gradient at sampled points)
- Per-frame "correct" control output (synthesized by simple PID rules + emergency-dump heuristics)

Corpus size: ~10K event sequences × ~100 frames each = ~1M training samples.

```cpp
// corpus_generator.cpp (C++/CUDA)
void GenerateCorpus(const std::string& output_path) {
    BinaryWriter writer(output_path);
    
    for (int scenario = 0; scenario < N_SCENARIOS; ++scenario) {
        ChaosPDESimulator sim;
        sim.init_random_parameters(scenario);  // varied α, k, M_BH, L_bubble
        
        for (int frame = 0; frame < FRAMES_PER_SCENARIO; ++frame) {
            sim.step(DT);
            
            ObservationGrid obs = sim.sample_observation();  // 64×64×2
            ControlVector ctrl = compute_pid_control(obs);   // hand-designed labels
            
            // For ~5% of frames, inject emergency conditions and label with emergency_dump=1
            if (rand_uniform() < 0.05) {
                sim.inject_emergency();
                ctrl.emergency_dump = 1.0f;
            }
            
            writer.write(obs);
            writer.write(ctrl);
        }
    }
}
```

**Step 2: Train CNN+LSTM in libtorch**

```cpp
// reflex_trainer.cpp (C++ with libtorch)
#include <torch/torch.h>

struct ReflexNet : torch::nn::Module {
    torch::nn::Conv2d conv1{nullptr}, conv2{nullptr}, conv3{nullptr};
    torch::nn::LSTM lstm{nullptr};
    torch::nn::Linear fc1{nullptr}, fc2{nullptr};
    
    ReflexNet() {
        // 64×64×2 → 32×32×16 → 16×16×32 → 8×8×64
        conv1 = register_module("conv1", torch::nn::Conv2d(torch::nn::Conv2dOptions(2, 16, 3).stride(2).padding(1)));
        conv2 = register_module("conv2", torch::nn::Conv2d(torch::nn::Conv2dOptions(16, 32, 3).stride(2).padding(1)));
        conv3 = register_module("conv3", torch::nn::Conv2d(torch::nn::Conv2dOptions(32, 64, 3).stride(2).padding(1)));
        // Flatten 8×8×64 = 4096 → LSTM hidden 64
        lstm = register_module("lstm", torch::nn::LSTM(torch::nn::LSTMOptions(4096, 64).num_layers(1).batch_first(true)));
        // 64 → 32 → 3 (control vector)
        fc1 = register_module("fc1", torch::nn::Linear(64, 32));
        fc2 = register_module("fc2", torch::nn::Linear(32, 3));
    }
    
    torch::Tensor forward(torch::Tensor x, /* prior LSTM state */) {
        x = torch::relu(conv1->forward(x));
        x = torch::relu(conv2->forward(x));
        x = torch::relu(conv3->forward(x));
        x = x.flatten(1).unsqueeze(1);  // (B, 1, 4096) for LSTM
        auto [out, state] = lstm->forward(x);
        out = out.squeeze(1);
        out = torch::relu(fc1->forward(out));
        out = torch::sigmoid(fc2->forward(out));  // outputs in [0,1]
        return out;
    }
};

void TrainReflex(const std::string& corpus_path, const std::string& onnx_output_path) {
    ReflexNet model;
    torch::optim::Adam optimizer(model.parameters(), torch::optim::AdamOptions(1e-3));
    
    auto corpus = LoadCorpus(corpus_path);
    
    for (int epoch = 0; epoch < N_EPOCHS; ++epoch) {
        for (auto batch : corpus.batches()) {
            optimizer.zero_grad();
            auto predicted = model.forward(batch.observations);
            auto loss = torch::mse_loss(predicted, batch.controls);
            loss.backward();
            optimizer.step();
        }
        // Periodic validation + checkpoint
    }
    
    // Export to ONNX
    torch::jit::script::Module scripted = torch::jit::trace(model, ExampleInput);
    // Use torch-onnx-export utility (C++ API)
    ExportONNX(scripted, onnx_output_path);
}
```

**Step 3: Convert ONNX to TensorRT engine**

```bash
# trtexec is a CUDA toolkit CLI (Apple Silicon-incompatible by design; perfect)
trtexec --onnx=reflex.onnx --saveEngine=reflex_sm_8_9.engine --int8 --calib=calibration.cache
```

INT8 quantization halves model size and ~3× speedup with negligible accuracy loss for this task.

**Step 4: Per-GPU engine bake**

TensorRT engines are GPU-architecture-specific. Bake one per supported target:
- `reflex_sm_8_9.engine` (RTX 4090, SM 8.9)
- `reflex_sm_9_0.engine` (RTX 5090, SM 9.0)
- `reflex_sm_8_6.engine` (RTX 3090, SM 8.6 — degraded support tier)

NNE picks the matching engine at runtime via GPU detection.

**Output assets shipped in plugin Content/BakedAssets/:**
- `Reflex.onnx` — universal fallback for NNE-ORT
- `Reflex_sm_8_9.engine`, `Reflex_sm_9_0.engine`, etc.

**Per-game-version regen:** when chaos PDE parameters change or Sculptor's Reflex-tuning produces new weights, full re-bake. ~2 hours wall time for the chaos corpus + 30 min training + 5 min TensorRT.

### 10.4 CMake project layout + third-party dependencies

```
proto/cuda_lib/                                    # standalone CMake project; integrated into UE5 plugin via build artifact
├── CMakeLists.txt
├── cmake/
│   ├── FindCUDAToolkit.cmake  (modern CMake 3.18+)
│   ├── FindTorch.cmake
│   └── FindTensorRT.cmake
├── include/
│   └── astra_physics/
│       ├── api.h               # C API for UE5 binding
│       ├── types.h             # POD types shared with UE5
│       └── constants.h         # generated from constants.toml at configure time
├── src/                        # see §7.1
├── third_party/                # vendored or fetched via FetchContent
│   ├── tiny-cuda-nn/           # for hash-grid SDF
│   ├── tomlplusplus/           # for constants.toml
│   ├── eigen/                  # for RBF fitter LSQ
│   ├── openvdb/                # for SDF generation
│   ├── nlohmann_json/          # for save-file
│   └── catch2/                 # for unit tests (replaces pytest per CLAUDE.md)
└── tests/
    └── (Catch2 unit tests for chaos PDE step, RBF eval, etc.)
```

**CMakeLists.txt (sketch):**

```cmake
cmake_minimum_required(VERSION 3.24)
project(AstraPhysicsCUDA LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_ARCHITECTURES 86 89 90)  # 3090, 4090, 5090

# Constants.toml → constants.h codegen
add_custom_command(
    OUTPUT ${CMAKE_BINARY_DIR}/include/astra_physics/constants.h
    COMMAND ${CMAKE_BINARY_DIR}/astra_nexus --emit-header < ${CMAKE_SOURCE_DIR}/../constants.toml > ${CMAKE_BINARY_DIR}/include/astra_physics/constants.h
    DEPENDS astra_nexus ${CMAKE_SOURCE_DIR}/../constants.toml
)

add_library(AstraPhysicsCUDA STATIC
    src/chaos_pde.cu
    src/warp_field.cu
    src/rbf_network.cu
    src/reflex_inference.cpp
    src/retarded_time.cu
    src/kepler.cu
    src/interop_manager.cpp
    src/api.cpp
    ${CMAKE_BINARY_DIR}/include/astra_physics/constants.h
)

target_link_libraries(AstraPhysicsCUDA PRIVATE
    CUDA::cudart
    tiny-cuda-nn
    tomlplusplus
    Eigen3::Eigen
    OpenVDB::openvdb
    nlohmann_json::nlohmann_json
)

# CUDA optimization flags
target_compile_options(AstraPhysicsCUDA PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:--use_fast_math>
    $<$<COMPILE_LANGUAGE:CUDA>:--ptxas-options=-v>
    $<$<COMPILE_LANGUAGE:CUDA>:-Xcompiler=-fPIC>
)

if(WIN32)
    target_compile_definitions(AstraPhysicsCUDA PRIVATE NOMINMAX WIN32_LEAN_AND_MEAN)
endif()

# Tests
enable_testing()
add_subdirectory(tests)
```

**No Apple targets** per Platform Discipline. CMake generators: MSVC on Windows; gcc/clang on Linux. Cross-compile from Linux to Windows via mingw-w64 (acceptable; common).

**Per Language Discipline:** No Python in this build pipeline. tiny-cuda-nn has Python bindings but we use its C++ API only. OpenVDB has Python bindings but we use C++ API only. PyTorch becomes libtorch (C++ API). Pure C/C++/CUDA throughout.

---

---

## 11. Performance budgets

Concrete accounting at the 5090 reference tier. Numbers are estimates with empirical anchors where available (RTX 4090 benchmarks of similar pipelines). All assumptions stated.

### 11.1 Frame time accounting at 60 FPS on RTX 4090

Target: ≥60 FPS at native 4K with DLSS Quality + Frame Gen (effective 4K render at 1440p × frame-doubled).

**Per-frame timeline (16.67 ms budget):**

| Stage | Time (ms) | Subsystem | Spec § |
|---|---|---|---|
| CPU: physics driver tick | 0.5 | C++ composition rule + regime detect | §3.2 + §3.3 |
| CPU: scenario/operator tick | 0.5 | game logic, perception assembler | §4.9 |
| CPU + GPU: CUDA graph launch | 0.05 | warp SVT populate + chaos PDE step + Reflex + audio extract | §1.5 |
| GPU: CUDA chaos PDE step (RK2) | 2.0 | 128³ Fisher-KPP + BH coupling | §7.1 |
| GPU: CUDA warp SVT populate | 1.5 | 1000 RBFs × 256³ voxels (~5% occupancy via dual-numbers) | §6 + §3.8 |
| GPU: NNE Reflex inference | 0.025 | TensorRT engine, INT8 | §2.3 |
| GPU: UE5 main render (Nanite + Lumen) | 5.0 | hull + interior + non-warp scene | UE5 default |
| GPU: UE5 HVR warp ray-march | 3.0 | half-res 4K with adaptive sampling | §6 + §5.6 |
| GPU: Geometric lensing post-pass | 1.5 | full-screen deflection lookup | §3.4 + §9.2 |
| GPU: Starfield retarded-time + redshift | 0.5 | compute shader + mesh particle render | §6.3 + §9.4 |
| GPU: Cherenkov + Substrate hull materials | 0.5 | included in main render but counted separately for clarity | §6 + §9.3 |
| GPU: Audio extraction | 0.1 | sample state for AudioPayloadRingBuffer | §8.2 |
| GPU: Post-process + DLSS | 1.0 | TAA, bloom, tonemap, frame-gen | UE5 default |
| GPU: Present | 0.5 | swapchain + sync | UE5 default |
| **Subtotal** | **16.18** | | |
| **Reserve** | **~0.5** | jitter absorption | §5.6 |

**Total: ~16.7 ms; hits 60 FPS with thin margin.** DLSS Frame Generation doubles effective frame rate to 120 FPS on monitors that support it; the rendering pipeline produces 60 distinct frames per second + 60 interpolated.

**At full-res 4K (no DLSS):** the HVR warp ray-march doubles to ~10 ms (per spec §5.6 budget); total exceeds 16.67 ms. **4K native requires either a 5090 (additional headroom) or accepting 30-45 FPS**. The half-res + DLSS path is the canonical config.

**At 1440p native:** budget halves on HVR + lensing; comfortable 60 FPS without DLSS on RTX 4090.

**At 1080p native:** comfortable 60+ FPS on RTX 4080 (per spec §5.9 tier table).

### 11.2 VRAM accounting at 5090 reference tier

Already enumerated in §4.8 above; recap:

| Bucket | Size |
|---|---|
| Physics + Reflex + audio | ~36 MB |
| ASTRA-LLM 27B Q4 | ~16 GB |
| Narrator-LLM 9B Q5 | ~5 GB |
| Adapter 3B Q4 | ~2 GB |
| KV cache (all 3 LLMs, 128K context) | ~3 GB |
| UE5 rendering (4K) | ~5-6 GB |
| **Total at 5090 reference tier** | **~32 GB** |

**Per attempt 2's F6 (shared inference for small-LLM pool):** Adapter + future ephemerals could share one ~7 GB Qwen 7B Q5 with sysprompt swap, saving ~10 GB. **Lock this design** before the 4090 tier (24 GB) becomes a target — without it, 4090 cannot run the full bundle.

**Per this pass's F5 reading of FOSS-maintainer outsider audit (Q10 in attempt 3B):** the bundle.yaml manifest (attempt 2's F10) is gating for Hugging Face publish. Memory accounting in the manifest helps users understand what tier they need.

### 11.3 CPU thread accounting

UE5 uses TaskGraph + Render thread + RHI thread + Game thread. CUDA work is GPU-only; CPU coordination is light.

**CPU threads at 60 Hz:**

| Thread | Workload | Time per frame |
|---|---|---|
| Game thread (UE5) | Tick, actor logic, blueprint VM | ~3-4 ms |
| Render thread (UE5) | Render command buffer building | ~3 ms |
| RHI thread (UE5) | DX12 submission, fence sync | ~1 ms |
| Audio thread | MetaSound graph eval, mix | ~0.5 ms |
| CUDA stream callback thread | Fence signal handling | ~0.05 ms |
| Physics driver thread (plugin) | StateBus updates, regime detect | ~0.5 ms |
| LLM coordination thread (plugin) | Tool dispatch, perception assembly | ~0.5 ms (mostly idle; bursts at turn boundary) |

Total active CPU time per frame: ~8 ms. RTX 5090 + 8-core Ryzen or 12-core Intel handles this comfortably. **Game and Render threads are the bottleneck; physics + LLM coordination are noise.**

### 11.4 Disk I/O at load time

**Load sequence on `astra run`:**

| Step | Time | What |
|---|---|---|
| 1. UE5 engine init | ~3 s | Standard UE5 game start |
| 2. Plugin module load | ~0.5 s | DLLs / SOs into memory |
| 3. CUDA context init | ~0.5 s | cudaInit + first device query |
| 4. astra_nexus stdio server spawn | ~0.2 s | C++ binary cold-start |
| 5. ASTRA-LLM (27B Q4) load to VRAM | ~10 s | 16 GB from disk; NVMe SSD ~4 GB/s read |
| 6. Narrator-LLM (9B Q5) load | ~3 s | 5 GB |
| 7. Adapter (3B Q4) load | ~1 s | 2 GB |
| 8. Hull SDF asset (hash-grid) load | ~0.1 s | 10 MB; decompressed to VRAM |
| 9. CFD RBF asset load | ~0.01 s | 30 KB |
| 10. Reflex TensorRT engine load | ~0.5 s | 100 KB; TRT runtime init |
| 11. Chaos field forward-integrate from seed | ~0.06 s | 60 steps at 1 ms each, per spec §4.6 |
| 12. Initial scenario / save state load | ~0.5 s | reads SaveFile v3 |
| 13. UE5 level streaming + Niagara warmup | ~2 s | hull mesh + cabin geometry |
| **Total cold start** | **~22 s** | |

**Hot reload (savefile reload during same session):** ~5 s (LLMs already in VRAM; only chaos re-init + level state).

**Optimization opportunity:** parallel LLM loading (kick all three llama-server spawns simultaneously; they run on independent processes). Could shave ~3 seconds off cold start. Worth doing.

**Why this matters:** the game's first impression is a long load. Players accept this in long-form fiction games (Cyberpunk, RDR2 also load ~30 s). The autotelic discipline complements this: while loading, show "the watch is starting" prose from ASTRA, framing the wait as part of the experience.

---

---

## 12. Decisions to lock + open questions

This pass surfaces a number of concrete decisions where the spec is provisional or implicit. Each is presented as a lock-recommendation with rationale; the operator chooses.

### 12.1 Decisions recommended for locking now (cheap; defer-cost asymmetric)

| # | Decision | Lock at spec/code | Rationale |
|---|---|---|---|
| L1 | **Hull SDF = hash-grid encoding (Instant-NGP via tiny-cuda-nn)** | §1.3 Tolerable expanded | 8-16× memory savings; adaptive resolution; matches attempt 2's F4. Locking now ($1 spec edit) is cheap; rewriting renderer after Phase E2 lands uniform-SDF binding is expensive. |
| L2 | **CUDA Graphs for per-frame physics hot path** | §5.6 + §2.3 contract | 245 μs/frame savings (this pass §5.1); essential for Reflex 50μs budget. |
| L3 | **Dual-number auto-diff in `sample_warp_field_unified`** | §6 step 8 implementation note | ~5 ms/frame savings at 4K full-res (this pass §3.8). Pure performance optimization; no behavior change. |
| L4 | **Forward-Euler rapidity integrator (not RK45)** | §3.7 + §7.3 wording relax | Empirical (48 C++ assertions pass) and analytical (game-scale Δτ is linear regime) evidence; matches this discovery's S5 + attempt 2's S1. |
| L5 | **Reflex Contract §2.3.1 envelope** | New §2.3.1 section in spec | This pass's F2 — safety-critical-with-least-design-depth; envelope-now vs envelope-after-Phase-E1 cost asymmetry. |
| L6 | **NNE-RDG with TensorRT-NVIDIA for Reflex inference** | §2.3.1 implementation note | UE5.5-native; CUDA-graphs compatible; fallback paths available. |
| L7 | **Heterogeneous Volume Renderer for warp visualization** | §6 implementation note | UE5.4+ canonical path; lifts the 500-LOC custom render pass to a 50-LOC material function. |
| L8 | **MetaSound for all 5 audio layers** | §8.3 implementation note | Already canon per CLAUDE.md; this section confirms the 5-layer mapping. |
| L9 | **`proto/constants.toml` as single source of cross-binary constants** | New Appendix B note | This pass's F8 — replaces magic-number duplication between C++ and Python. |
| L10 | **`--emit-header` mode on `astra_nexus`** | §10 validation row | Attempt 2's F1 — moves N1-class-bug catch to build time. |
| L11 | **SVT resolution decoupled from viewport** | §6 implementation note (this pass §6.4) | Eliminates resize path complexity; bubble-space resolution is what matters. |
| L12 | **CMake project structure for `AstraPhysicsCUDA`** | UE5 plugin convention | This pass §10.4 — CMake permitted per Language Discipline; clean separation from UE5 build system. |
| L13 | **Per-GPU TensorRT engines + ONNX fallback** | §2.3.1 implementation note | This pass §8.1 + §10.3 — clean per-architecture deployment. |
| L14 | **Anchor scenarios include hard-directive probes** | scope.yaml (4 lines YAML) | Attempt 3B's F3 — already an operator-decision. |
| L15 | **Adaptive ray-march step size in warp HVR** | §6 implementation note | This pass §9.1 — 3× speedup over uniform marching at minimal quality cost. |
| L16 | **Memory ordering `__threadfence_system + atomicExch_system` for AudioPayloadRingBuffer** | §8.2 implementation note | This pass §6.3 — addresses graphics-engineer outsider concern from attempt 1. |

### 12.2 Decisions deferred but with design intent locked

| # | Decision | Defer until | Lock design intent now |
|---|---|---|---|
| D1 | **SVT-native CUDA write vs dense-3D-texture intermediate** | Phase E3 profile | dense-3D-texture path until profile shows memory pressure |
| D2 | **CFD bake parameter tuning (RBF count, σ envelopes)** | Phase E0 visual testing | ~1000 RBFs; spec §6 baseline |
| D3 | **Cherenkov color and intensity tuning** | Phase E3 visual testing | blue-cyan base per spec §6.1 + this pass §9.3 |
| D4 | **α_lens lensing coefficient** | Phase E3 visual testing | provisional per Appendix B; lock in constants.toml when measured |
| D5 | **Chaos PDE α, β, D, k_coupling values** | Phase E1 numerical stability | provisional per spec §7.1 + Appendix B |
| D6 | **Reflex training corpus parameters** | Phase E1 | spec §2.3.1 names the validation protocol |
| D7 | **Adaptive HVR step size hint magnitude** | Phase E2 profiling | this pass §9.1 baseline coefficient |
| D8 | **Hash-grid number of LODs / table sizes** | Phase E2 quality testing | 4 LODs × 19-bit table per this pass §3.6 |
| D9 | **DLSS Quality vs Performance preset** | Phase E2 visual testing | DLSS 3 Quality + Frame Gen as default |
| D10 | **Per-body `t_source_start` schema** | Phase 3+ body-generation contract | audit's R4; defer per spec §13 |

### 12.3 Open questions for operator

**Q1 — Engine source-code modifications: yes or no?**

The lensing two-pass approach (this pass §9.2 Option A) keeps Engine source clean. The single-pass HVR-shader-modification approach (Option B) saves ~1 ms but forks UE5 source.

**Decision needed:** is the operator willing to maintain a UE5 source-code fork for performance gains, or does the "no Engine forks" discipline hold?

**Recommendation:** no Engine fork. The single-pass speedup is ~1 ms; the maintenance cost is permanent (every UE5 upgrade requires merge work). Lock to two-pass approach.

---

**Q2 — Lumen integration for warp field GI: yes or no?**

The warp field's emissive output COULD contribute to Lumen GI (warp glow lights up nearby surfaces). The cost: ~1-2 ms of additional Lumen scatter work per frame. The benefit: more visually integrated warp effect.

**Decision needed:** is the visual gain worth the perf cost?

**Recommendation:** YES for v1 release; default-enable; provide config option to disable for lower tiers. The visual integration is significant; the cost is bounded.

---

**Q3 — Audio + ASR + TTS toolchain: confirm libraries?**

CLAUDE.md Language Discipline names: whisper.cpp for ASR; Piper-TTS or sherpa-onnx for TTS; MetaSound for audio synthesis. All C/C++.

**Decision needed:** confirm Piper-TTS vs sherpa-onnx. Piper has better voice variety; sherpa-onnx is faster (ONNX runtime inference). Both fit ASTRA's voice register.

**Recommendation:** **Piper-TTS** for the canonical bundle (better voice quality matters for autotelic discipline). Ship `astra_voice.onnx` (custom-trained on operator-selected reference). sherpa-onnx as fallback for users without Piper voice files.

---

**Q4 — Build target for Linux: simultaneous with Windows or deferred?**

Platform Discipline allows Linux x86_64 as second platform. The CMake build supports both; UE5 has Linux support. **Question: ship Linux build alongside Windows for v1, or after?**

**Decision needed:** Linux as v1 release target?

**Recommendation:** Linux at v1.1 (3-6 months after v1.0 Windows). The Windows path is the primary; Linux requires additional QA but the infrastructure (CMake, CUDA, UE5 Linux) is in place. Don't gate v1 Windows release on Linux.

---

**Q5 — TensorRT licensing for shipped engines: confirm acceptable?**

TensorRT engines are NVIDIA-proprietary. The shipped `.engine` files are technically generated artifacts (fine to redistribute) but the TensorRT runtime libraries (`libnvinfer.so`, etc.) need redistribution-license-clearance per NVIDIA's EULA.

**Decision needed:** verify NVIDIA TensorRT redistribution clearance for free open-source game distribution. If problematic, fall back to ONNX-Runtime-only path (slower but no license concern).

**Recommendation:** verify with NVIDIA's legal docs first; default to ONNX Runtime if any doubt. The performance gap on Reflex (15μs TensorRT vs 50μs ONNX-DirectML) doesn't break the 50μs budget either way.

---

**Q6 — Free open source publication: GitHub-only or also OBS-style "verified canonical bundle" hosting?**

The project is free open source per CLAUDE.md. GitHub is the code; Hugging Face is the LLM bundle. But the TensorRT engines + baked CFD-RBF assets are large (~50-100 MB) — do they go in the GitHub repo (LFS), Hugging Face alongside the bundle, or a separate CDN-style asset host?

**Decision needed:** asset hosting decision.

**Recommendation:** Hugging Face for all baked assets (single coherent bundle: LLM weights + LoRA + sysprompts + canonical assets). Users `git clone` code; `huggingface-cli download` baked assets. Per attempt 2's F10 (bundle.yaml as manifest), one file lists all asset locations + checksums.

---

**Q7 — Audio voice training: operator-narrated reference or synthetic?**

ASTRA's TTS needs a voice. Options: (a) operator narrates ~10 minutes of reference audio (their voice becomes ASTRA's); (b) Piper's pre-trained voice library has female-tone options that fit ASTRA's register; (c) custom-train via small voice cloning model (slim diffusion-TTS adapter).

**Decision needed:** voice source.

**Recommendation:** option (b) for v1 — Piper pre-trained voice. Lower friction, no recording session. Custom voice cloning (option c) is a v1.x enhancement if operator desires.

---

**Q8 — Bench (textverse) and UE5 voice consistency: how to verify?**

The bench's TTS is operator-side (probably none at v0; text-only is the bench's contact surface). UE5 adds TTS. The voice ASTRA "has" in the bench (via reading her speech text) differs from the voice she has in UE5 (synthesized from same text). **Question:** does the bench need to verify that the synthesized TTS still matches ASTRA's register?

**Decision needed:** add TTS-side gate or treat as Phase 2+ separate concern?

**Recommendation:** Phase 2+. The TTS voice is a property of the synthesis model + voice training data, not a property of the LLM bundle. Sculptor iterations on the bundle don't affect TTS. Independent track; can land later.

### 12.4 The shortest viable Phase E sequence

Putting all the locks together, here's the Phase E ordering this pass recommends:

**Phase E0 (months 1-2):** Ship hull modeling, Substrate materials, UE5 plugin skeleton. AstraPhysicsCUDA library built standalone; no UE5 integration yet.

**Phase E1 (months 3-4):**
- Chaos PDE kernel + double-buffer + convergence detector
- Reflex training corpus generation
- Reflex CNN+LSTM training in libtorch + ONNX export + TensorRT bake
- NNE-RDG integration in UE5 plugin

**Phase E2 (months 5-6):**
- DX12-CUDA shared resource lifecycle
- AstraNexus stdio_server integration for retarded-time
- Observation Calculator compute shader (full UE5 native)
- CFD-RBF network bake pipeline (OpenFOAM → custom RBF fitter)
- Hull SDF hash-grid bake (OpenVDB → tiny-cuda-nn)

**Phase E3 (months 7-8):**
- Heterogeneous Volume Renderer integration with WarpVolumeSample.usf
- Geometric lensing two-pass implementation
- Cherenkov cone material
- Retarded-time starfield rendering
- α_lens + Cherenkov + lensing visual tuning

**Phase E4 (months 9-10):**
- Audio synthesis MetaSound graphs (5 layers)
- AudioPayloadRingBuffer integration
- Piper-TTS integration for ASTRA voice
- whisper.cpp integration for ASR

**Phase 2.0 (months 11-12):** Per spec §12 — vertical slice. Swap perception assembler (text → image+text) + tool dispatcher (Python ship-sim → UE5 game state). Bench validates; UE5 plays.

**Total Phase E: ~12 months engineer time** (one full-time graphics + CUDA engineer; the operator's track A LLM bundle work runs in parallel).

This is consistent with v1 ship target ~12-18 months from spec v0.128 lock.

---

*End of technical deep dive. 12 sections · ~70 numbered subsections · 16 decisions recommended for locking · 8 open questions · concrete code patterns for every system named in spec §1-§8. UE5.5 features mapped to spec commitments; performance budget at 5090 reference tier closes the 60 FPS 4K target with thin margin.*

*The math holds. The CFD-RBF + chaos PDE + Reflex composition is implementable. The DX12-CUDA interop pattern is standard. UE5.5 Heterogeneous Volumes + NNE close the gaps that would have required custom render passes. The Language Discipline + Platform Discipline constraints leave plenty of room for performant implementation. The path from spec v0.128 to a running UE5 game is bounded, named, and ready for Phase E0.*

*Build the engine track. The bench is the regression test; the spec is the lock; the math is the truth; UE5 is the body.*

---

*End of skeleton.*
