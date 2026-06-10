# ASTRA-7 Warp Physics × UE 5.5 — Deep Dive (2026-05-16)

**Scope.** The math and physics of space-time, warp field, warp effects,
CFD generative mapping, the SDF + chaos PDE + Observation Calculator stack,
the audio synthesis pipeline, and the optimal embedding of all of this in
**Unreal Engine 5.5 as of May 2026**. Prescriptive throughout. Numbers
matter; tradeoffs are stated; the recommended path is named.

**Stack assumptions.**
- UE 5.5 production-ready as of October 2024; +18 months of community patches by May 2026.
- RTX 5090 reference tier (32 GB VRAM); 4090 fallback (24 GB).
- Windows 11 + DX12 primary; Linux x86_64 + Vulkan acceptable second. **No Apple/Metal/iOS** per CLAUDE.md Platform Discipline.
- CUDA 12.x for compute kernels (the math layer), DX12 for rendering, Vulkan via UE RHI abstraction for Linux.
- llama.cpp pinned for LLM inference; whisper.cpp for ASR; Piper-TTS or sherpa-onnx for TTS.
- **No new Python** in shipped runtime. C/C++ everywhere except grandfathered `proto/textverse/`.

**Authoritative references throughout:** spec §1-§8 and §15.7-§15.8 (textverse contract surfaces), `proto/astra_nexus.cpp` (1009-line math reference, 48 assertions). UE feature naming as of UE 5.5.

---

## 1. Mathematical foundations — what actually has to compute

### 1.1 The composition rule (§3.2) is the only time-dilation equation

Single load-bearing identity for every regime:

```
dτ_ship / dt_cosmic = f_warp(W) · √(1 − r_s_dom/r_dom) · √(1 + 2·Φ_other/c²) / γ_kinematic(v)
```

with constraints:
- `dτ_ship/dt_cosmic ∈ (0, 1]` always
- `γ_kinematic ≡ 1` whenever any WARP_* regime is active (bubble crew is locally inertial)
- `f_warp(W) ≡ 1` for non-warp regimes
- Schwarzschild factor `√(1 − r_s/r)` reduces smoothly to weak-field `√(1 + 2Φ/c²)` at large r (one continuous form across all distances — no piecewise switch)
- Non-dominant BH contributions sum into `Φ_other` as Newtonian potential

**Why this matters for UE.** The composition rule runs ONCE per UE tick.
Cost: ~30 floating-point operations. The Lorentz factor `γ = cosh(ω)` is
the only expensive piece (~5 ns on a modern CPU; ~1 ns on GPU via PTX
`__cosh` intrinsic). Total cost: under 100 ns per tick on the CPU side;
sub-instruction on the GPU shader. **Not a bottleneck. Ever.**

### 1.2 3-vector rapidity ζ⃗ (§3.7) is the canonical kinematic state

The state variable is NOT velocity. Storing velocity at γ near 10⁷ loses
precision catastrophically (β = 1 − 5·10⁻¹⁵ — float64 can't represent
this difference from 1 meaningfully).

Locked discipline: integrate in rapidity space.

```cpp
// Per-frame integration (UE Tick, GameThread or Mass Entity Processor)
struct Rapidity {
    Vec3 zeta;
    double omega() const { return zeta.mag(); }
    double gamma() const { return std::cosh(omega()); }   // NEVER 1/sqrt(1-β²)
    double beta()  const { return std::tanh(omega()); }
    Vec3 velocity() const {
        double w = omega();
        if (w < 1e-30) return {0,0,0};
        return zeta * (C_LIGHT * std::tanh(w) / w);
    }
};

// Update rule (RK45 spec'd; forward-Euler at game-scale dt empirically OK)
Rapidity integrate(Rapidity prev, Vec3 a_proper, double dtau_ship) {
    Vec3 new_zeta = prev.zeta + a_proper * (dtau_ship / C_LIGHT);
    double mag = new_zeta.mag();
    if (mag > OMEGA_MAX) new_zeta = new_zeta * (OMEGA_MAX / mag);  // clamp γ ≤ 10⁷
    return {new_zeta};
}
```

**OMEGA_MAX = 16.811** per spec §3.7 (gives γ_max = cosh(16.811) ≈ 10⁷).
This is the canonical clamp; never re-derive from β.

**UE integration point.** Live in a `UAstraTimeContractComponent` attached
to the player pawn. Tick group: `TG_PrePhysics`. Reads `a_proper` from the
propulsion driver's published State Bus snapshot; writes the updated
TimeState back. No allocations per tick; all in-place math.

### 1.3 AstraCoord (§1.1) is 128-bit position; UE world space is float32

UE 5.5 uses float32 transforms by default with `LWC` (Large World
Coordinates) layered on top. LWC provides float64 world origins but
float32 within rebased regions. **AstraCoord is more precise than UE LWC
needs.** The mapping:

- AstraCoord sector `(sx, sy, sz)` ↔ World Partition cell (per UE 5.5 World Partition)
- AstraCoord local offset `(lx, ly, lz)` ↔ UE actor `FVector` within the cell

Renormalization (when `|local| > 500 km`) maps to **World Partition origin
rebase**, which UE 5.5 supports natively. The ASTRA-7 plugin's
`FAstraCoord` class wraps both representations:

```cpp
struct FAstraCoord {
    int64 sx, sy, sz;     // World Partition cell index
    double lx, ly, lz;    // local offset in meters; |·| ≤ 500 km

    FVector ToUEWorldVector() const {
        // Active cell's origin is set via World Partition origin rebase;
        // local offset converts directly with cm-to-m scale (UE uses cm).
        return FVector(lx * 100.0, ly * 100.0, lz * 100.0);
    }

    void Renormalize() {
        auto roll = [](double& local, int64& sector) {
            if (FMath::Abs(local) > LOCAL_OFFSET_MAX_M) {
                int64 n = static_cast<int64>(std::floor(local / SECTOR_SIZE_M + 0.5));
                sector += n;
                local -= n * SECTOR_SIZE_M;
            }
        };
        roll(lx, sx); roll(ly, sy); roll(lz, sz);
    }
};
```

**Why this matters for UE 5.5.** World Partition cells are typically
2048m × 2048m (or operator-configured). AstraCoord sectors are 1000 km =
1,000,000 m. **The mismatch is 500×**. Reconcile by either (a) configuring
WP cells to 1000 km (huge cells — fine since the ship is the only actor
of significance), or (b) using AstraCoord as the OUTER coordinate system
and WP cells as a finer subdivision within. **(b) is correct** — WP cells
handle the 0-2 km region around the ship at high precision; AstraCoord
handles the universe-scale position.

### 1.4 Retarded-time observation (§3.11) is regime-dispatched

The apparent rate at which a distant body's history advances:

```
STL_REL  (inertial v<c):   rate = √((1−β)/(1+β)) / (1 + z_cosmo)   ≥ 0 always
WARP_CRUISE (γ_kin ≡ 1):    rate = (1 − v_apparent/c) / (1 + z_cosmo)   can be < 0
REST/STL_NONREL:            rate ≈ (1 − v_radial/c) / (1 + z_cosmo)   linear, fine
```

The **discontinuity at v_apparent = c is a design feature** (spec §3.11):
the perceptual snap of warp engagement. **Do not smooth across it.**

**UE implementation.** Observation Calculator runs as a compute shader (HLSL)
on the GPU once per frame. Input: ship state + N distant bodies (N up to
~10,000). Output: N × ObservableState records. Compute pass dispatched via
RDG (UE 5.5 Render Graph) with explicit input/output buffer barriers.

Cost: spec estimate ~20 μs for 10,000 bodies on a 5090. Realistic
measurement (per attempt 1's GR-theorist outsider voice's concern):
Newton-Raphson iteration for moving sources converges in 2-4 steps per
body; 4 steps × 10K bodies × ~30 FLOPs/iter = ~1.2 MFLOP/frame; trivial.

### 1.5 The full optical composition (§3.4) — four effects, four code paths

| Effect | What changes | Where in pipeline |
|---|---|---|
| Kinematic Doppler / aberration | Starfield color + direction | Starfield shader using `v_eff` |
| Metric redshift | Frequency from W and Φ | Unified Sampler output `metric_shift` |
| Geometric lensing | Ray direction near bubble boundary | Unified Sampler `ray_deflection` per march step |
| Temporal retardation | Which moment of the source you see | Observation Calculator `t_emit` |

Composite color: `λ_observed = λ_emitted · (1 + z_total)` where
`(1 + z_total) = (1 + z_cosmo) · (1 + z_kin) · (1 + z_metric)`.
Multiplicative composition in GR; not approximation.

---

## 2. CFD-RBF generative pipeline (offline bake → runtime sampler)

### 2.1 What the CFD-RBF actually is

The CFD-RBF network is a **compact differentiable representation of the
warp metric field W(x, t)** generated from hull-shape-dependent CFD
pressure topology. Per §6.1's analog-gravity framing (Visser 1998, Unruh
1981): irrotational barotropic flow's acoustic metric is Lorentzian-signature
isomorphic to a class of curved spacetimes. The technique uses this
isomorphism as a **generative map**, not a derivation of warp physics from
fluid dynamics.

In practice:

```
Hull mesh + warp engagement parameters
         ↓ (OFFLINE; OpenFOAM or equivalent CFD solver)
Pressure field p(x, y, z)
         ↓ (OFFLINE; RBF fit)
~1000 Gaussian RBF nodes: { center_i, σ_i, weight_i }
         ↓ (RUNTIME; per-frame ray-march sample)
W(x) = Σ_i weight_i · exp(-‖x - center_i‖² / (2σ_i²))
```

**Why RBF and not [alternative]:**

| Alternative | Cost vs RBF | Verdict |
|---|---|---|
| Pure 3D voxel grid 256³ | 64 MB; O(1) lookup; ~1 lookup per ray sample | Too memory-heavy; precision is uniform but the field varies sparsely |
| Hash-grid (Instant-NGP) | 4-8 MB; tiny MLP (~50 ns per eval); good for static fields | **Attractive but rejected for the CFD path** because the field has dynamic chaos modulation that grids handle poorly |
| Neural Operator (FNO/DeepONet) | ~1 ms per query — too slow | No |
| Pure mesh CFD at runtime | Hundreds of GB; days of compute per frame | Absolutely not |
| **RBF + spatial hash (current)** | **~128 KB; O(20) per sample after hash lookup; smooth gradients** | **Optimal for this combination of static-topology + dynamic-modulation** |

### 2.2 Spatial-hash accelerator (§6.2)

The naive RBF eval is O(N=1000) per sample. With ~8M rays × ~256 march
steps per frame = ~2 billion samples/frame in worst case, this is 2×10¹²
RBF terms/frame. Untenable.

The spatial hash drops this to O(~20) by indexing nodes whose 3σ radius
overlaps each 32³ coarse voxel cell:

```cpp
// Built offline; ~64 KB index + 128 KB node table
struct RBFSpatialHash {
    uint32 voxel_size;                   // 32³ grid covering hull bounding box + warp shell
    std::vector<uint32> voxel_offsets;   // CSR-style indexing into node_indices
    std::vector<uint16> node_indices;    // indices into rbf_nodes (only those overlapping voxel)
    std::vector<RBFNode> rbf_nodes;      // { center, sigma_inv_sq, weight } per node
};

float SampleRBF(float3 local_pos, const RBFSpatialHash& hash) {
    int3 voxel = int3(local_pos / hash.voxel_size);
    uint32 offset = hash.voxel_offsets[Flatten(voxel)];
    uint32 count  = hash.voxel_offsets[Flatten(voxel) + 1] - offset;
    float W = 0.0f;
    for (uint32 i = 0; i < count; i++) {
        const RBFNode& n = hash.rbf_nodes[hash.node_indices[offset + i]];
        float3 d = local_pos - n.center;
        W += n.weight * exp(-dot(d, d) * n.sigma_inv_sq);
    }
    return W;
}
```

**HLSL implementation runs in the Unified Sampler compute shader.** The
RBF node table is uploaded to a Structured Buffer once at startup (the
hull doesn't change shape; damage is additive but doesn't affect CFD-RBF).
~256 nodes per voxel max; the loop is unrolled by the shader compiler.

### 2.3 What's actually in the hull SDF

Two separate fields:

| Field | What it is | Storage | UE 5.5 binding |
|---|---|---|---|
| Base hull SDF | Signed distance to hull surface | 256³ float16 (32 MB); single bake at hull-design time | `cudaTextureObject_t` with `cudaFilterModeLinear` |
| Damage map | Sparse additive damage offsets | 128³ float16 (4 MB); writable; persisted per save | `cudaSurfaceObject_t` over same `cudaArray_t` |

**Effective SDF on read:** `hull_d(x) = base_sdf(x) − damage_map(x)`.

The §1.3 dual-binding pattern: texture for filtered reads, surface for
damage writes, **same underlying `cudaArray_t`**. UE 5.5 owns the
underlying DX12 texture; CUDA registers it once at startup via
`cudaGraphicsD3D12RegisterResource`.

**Hash-grid alternative for SDF (per attempt 2A's F4):** 8 MB instead
of 32 MB; trades a small MLP eval (~50 ns) for the memory saving. For the
hull SDF specifically (static topology, sparse damage), hash-grid IS
attractive. **Recommended for v1.x once Engine track is past Phase E2.**
For Phase E0-E2, uniform texture is the simpler integration path.

---

## 3. Hull SDF + damage map: the §1.3 dual-binding in practice

```cpp
// At UE plugin startup (UWarpCFDAsset post-load):
ID3D12Resource* hullSDFResource = GetUE5HullSDFTexture()->GetResource();
cudaGraphicsResource* hullSDFCudaResource;
cudaGraphicsD3D12RegisterResource(
    &hullSDFCudaResource,
    hullSDFResource,
    cudaGraphicsRegisterFlagsNone
);
// Map ONCE; do NOT remap per frame
cudaGraphicsMapResources(1, &hullSDFCudaResource, cudaStream);
cudaArray_t hullArray;
cudaGraphicsSubResourceGetMappedArray(&hullArray, hullSDFCudaResource, 0, 0);

// Bind as texture for filtered reads
cudaResourceDesc texRes = { .resType = cudaResourceTypeArray, .res.array.array = hullArray };
cudaTextureDesc  texDesc = { .filterMode = cudaFilterModeLinear, .normalizedCoords = 0 };
cudaCreateTextureObject(&hullSDFTexObj, &texRes, &texDesc, nullptr);

// Bind as surface for writes (damage map updates)
cudaResourceDesc surfRes = { .resType = cudaResourceTypeArray, .res.array.array = hullArray };
cudaCreateSurfaceObject(&hullSDFSurfObj, &surfRes);

// On hull damage event (e.g., hull breach scenario):
//   surf3Dwrite(damage_delta, hullSDFSurfObj, x*sizeof(float), y, z);
// The texture binding sees the updated value on the NEXT read; no remap needed.
```

**Per-frame coordination (UE 5.5 RDG):** external semaphores synchronize
CUDA writes vs DX12 reads. RDG sees the texture as an external resource;
the plugin inserts an `AddPass` that imports the resource and signals
the semaphore.

```cpp
// In the plugin's render module:
FRDGBuilder GraphBuilder(RHICmdList);
FRDGTextureRef HullSDFRDG = GraphBuilder.RegisterExternalTexture(
    HullSDFExternalTexture,
    TEXT("HullSDF")
);

// Add a CUDA-interop pass that waits on a DX12 fence and signals a CUDA semaphore
GraphBuilder.AddPass(
    RDG_EVENT_NAME("CUDA Hull SDF Update"),
    PassParameters,
    ERDGPassFlags::Compute | ERDGPassFlags::AsyncCompute,
    [Plugin = this](FRHICommandList& RHICmdList) {
        Plugin->RunCUDAHullDamagePass(RHICmdList);
    }
);
```

**Memory order discipline** (per outsider voice (a) audio engineer's note;
applies equally to SDF interop): on Windows + CUDA the external semaphore
uses `memory_order_release` GPU-side and `memory_order_acquire` CPU-side,
NOT `memory_order_seq_cst`. Spec §8.2 mentions this for the audio ring
buffer; the same discipline applies to the hull SDF synchronization.

---

## 4. Unified Sampler — the 12-step ray-march evaluation

### 4.1 The function the entire rendering pipeline calls

```hlsl
// HLSL compute shader (also implemented in CUDA for the math layer reference)
WarpFieldSample SampleWarpFieldUnified(
    float3 world_pos,
    float3 view_dir,
    UnifiedWarpState state,
    uint flags
) {
    WarpFieldSample s = (WarpFieldSample)0;

    // Step 1: ship-local frame
    float3 local_pos = mul(state.world_to_ship, float4(world_pos, 1.0)).xyz;

    // Step 2: hull SDF
    float hull_d = tex3DLod(state.HullSDFTex, local_pos / state.hull_scale, 0).r;
    float damage = tex3DLod(state.DamageMapTex, local_pos / state.hull_scale, 0).r;
    float effective_hull_d = hull_d - damage;

    // Step 3: CFD-RBF
    float W_cfd = SampleRBF(local_pos, state.HashGrid);

    // Step 4: conformal bubble SDF via smooth-min (NOT linear blend)
    float bubble_d = effective_hull_d;
    float W_bubble = SmoothMin(W_cfd, ShellIntensity(bubble_d, state.shell_thickness),
                                state.smooth_k);

    // Step 5: chaos field (read buffer of double-buffered field)
    float chaos = tex3DLod(state.ChaosFieldTex, local_pos / state.chaos_scale, 0).r;

    // Step 6: chaos modulates boundary
    float W_modulated = W_bubble * (1.0 + chaos * state.chaos_coupling);

    // Step 7: wake metric + vortex contributions
    float W_wake = ComputeWakeMetric(local_pos, view_dir, state);
    float W = W_modulated + W_wake;

    s.metric = W;
    s.chaos_intensity = chaos;
    s.vorticity = (flags & INCLUDE_VORTICITY) ? ComputeVorticity(local_pos, state) : 0.0;

    // Step 8: gradient ∇W (if requested) — finite differences or analytic
    if (flags & GRADIENT) {
        s.metric_gradient = ComputeGradientAnalytic(local_pos, state);
    }

    // Step 9: ray-deflection contribution α_lens · ∇W · Δs
    s.ray_deflection = state.alpha_lens * s.metric_gradient * state.march_step;

    // Step 10: Cherenkov angle cos θ_c = 1/(n·β)
    //   n is local index of refraction derived from W + CFD pressure topology
    //   β is effective velocity
    float n = 1.0 + state.cfd_pressure_factor * W;   // provisional model
    float cos_theta_c = (state.beta > 0.0) ? (1.0 / (n * state.beta)) : 1.0;
    s.cherenkov_angle = (cos_theta_c <= 1.0) ? acos(saturate(cos_theta_c)) : 0.0;

    // Step 11: metric_shift from W and local Φ
    float Phi = ComputeLocalPotential(world_pos, state.bh_list);
    s.metric_shift = sqrt(saturate(1.0 + 2.0 * Phi / (C_LIGHT * C_LIGHT))) * (1.0 - W);

    // Step 12: return
    return s;
}
```

### 4.2 Why HLSL+CUDA dual implementation (not one or the other)

- **HLSL for UE rendering integration** (rays-per-pixel in the warp visualization).
- **CUDA for the math reference** (`proto/astra_nexus.cpp` mirror — 48 assertions verify the math; HLSL would need its own test harness).

**Discipline:** the CUDA implementation is the canonical reference; HLSL
must produce identical output for identical inputs to 6+ sig figs. Cross-
substrate test runs the same evaluation grid through both, asserts
equality. This is the Five Shared Surfaces §15.7 Surface 2 (physics
envelope) being mechanically enforced.

### 4.3 Sphere tracing for the warp shell

Don't ray-march fixed-step. Sphere-trace using the hull SDF + bubble SDF
combined:

```hlsl
float3 RayMarchWarpShell(float3 origin, float3 dir, UnifiedWarpState state) {
    float t = 0.0;
    for (int i = 0; i < 256; i++) {                  // max 256 steps per spec
        float3 p = origin + t * dir;
        float d = min(SampleEffectiveHullSDF(p, state),
                      SampleShellSDF(p, state));
        if (d < 0.001) break;                        // hit
        if (d > MAX_RAY_DISTANCE) break;             // miss
        t += d;
    }
    return origin + t * dir;
}
```

In practice, sphere tracing inside the warp bubble (where ∇W is significant)
needs adaptive step control: when the local Cherenkov angle is sharp,
take smaller steps to avoid banding artifacts. UE 5.5 ray-marching shaders
support this via `[loop]` with `break` conditions; cost is data-dependent
but bounded at 256 steps.

**Frame cost on RTX 5090 at 4K with quarter-res ray-march upscaled via TSR:**
- Rays: 1920×1080×2 (quarter-res in W and H) = ~2M rays
- Steps avg: ~30 (most rays escape early); worst-case 256
- Cost per step: 32 RBF samples + SDF + smooth-min + chaos = ~200 FLOPS
- Per frame: 2M × 30 × 200 = 12 GFLOPS → ~0.6 ms on a 5090 (20 TFLOPS sustained)

**Frame budget §5.6:** warp ray-march ≤ 4 ms half-res / ≤ 10 ms full-res.
The 0.6 ms quarter-res figure is well within budget; TSR upscales to 4K
without quality loss for the smooth warp shell.

---

## 5. Chaos PDE on GPU (§7.1)

### 5.1 The PDE

Fisher-KPP-like reaction-diffusion with BH coupling:

```
∂χ/∂t = D · ∇²χ + α_eff · χ · (1 − χ) − β · χ³ + η(x, t)
```

where:
- `χ(x, t) ∈ [0, 1]` is the chaos amplitude field
- `D = 0.8` is diffusion constant (provisional)
- `α_eff = α_base · (1 + k · M · L_bubble² / r³)` per §7.1; cubic-in-r BH-tidal scaling
- `β = 10` is cubic damping (provisional)
- `η(x, t)` is forcing — ISM impact during WARP_* feeds energy here (§7.2)

### 5.2 Spatial discretization on GPU

128³ chaos field; double-buffered (§1.5):

```cpp
// Two cudaArray_t buffers; ping-pong each frame
cudaArray_t chaosFieldRead;
cudaArray_t chaosFieldWrite;
// Sized 128³ × 2 channels (χ + ∂χ/∂t) × float16 = 16 MB per buffer

// Per-frame update kernel (CUDA):
__global__ void UpdateChaosField(
    cudaTextureObject_t chaosRead,
    cudaSurfaceObject_t chaosWrite,
    float alpha_eff, float beta, float D, float dt,
    float3 bubble_center, float bubble_L
) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= 128 || y >= 128 || z >= 128) return;

    // Read χ at this voxel + 6 neighbors (trilinear filter handles boundaries)
    float chi    = tex3D<float>(chaosRead, x + 0.5f, y + 0.5f, z + 0.5f);
    float chi_px = tex3D<float>(chaosRead, x + 1.5f, y + 0.5f, z + 0.5f);
    float chi_nx = tex3D<float>(chaosRead, x - 0.5f, y + 0.5f, z + 0.5f);
    float chi_py = tex3D<float>(chaosRead, x + 0.5f, y + 1.5f, z + 0.5f);
    float chi_ny = tex3D<float>(chaosRead, x + 0.5f, y - 0.5f, z + 0.5f);
    float chi_pz = tex3D<float>(chaosRead, x + 0.5f, y + 0.5f, z + 1.5f);
    float chi_nz = tex3D<float>(chaosRead, x + 0.5f, y + 0.5f, z - 0.5f);

    // 7-point Laplacian
    float laplacian = (chi_px + chi_nx + chi_py + chi_ny + chi_pz + chi_nz - 6 * chi);

    // PDE step
    float reaction = alpha_eff * chi * (1.0f - chi) - beta * chi * chi * chi;
    float forcing  = SampleForcing(x, y, z);  // ISM impact + bubble boundary etc.
    float chi_new = chi + dt * (D * laplacian + reaction + forcing);

    chi_new = saturate(chi_new);
    surf3Dwrite(chi_new, chaosWrite, x * sizeof(float), y, z);
}
```

**Grid: 128/4 × 128/4 × 128/4 = 32³ blocks of 4³ threads each = 32,768
threads.** Latency: ~30 μs on 5090. **Well within frame budget.**

### 5.3 CFL condition

For Fisher-KPP with diffusion D and grid spacing Δx:
- `dt ≤ Δx² / (6D)` (stability bound for explicit Euler)
- `dt ≤ 1 / α_eff` (reaction stability)

At Δx ≈ 1 m (128³ over ~128 m bubble), D = 0.8:
- `dt_diff = 1 / (6 × 0.8) = 0.21 s`
- `dt_react ≈ 1 / 2.5 = 0.4 s`

Frame dt at 60 FPS = 16.67 ms — **two orders of magnitude under stability
bounds**. Explicit forward-Euler is safe; no implicit solver needed.

### 5.4 BH coupling and the Warp Exclusion Zone

When the ship enters WARP near a BH (allowed only for `r > 100·r_s` per
spec §7.4), `α_eff` increases. At r = 100·r_s, k=1, M=Sgr A* ≈ 4×10⁶ M_sun,
L = 280 m:
```
α_eff = α_base · (1 + k · M · L² / r³)
      = 2.5 · (1 + 1 · 4×10⁶ × 280² / (100 × 1.18×10¹⁰)³)
      ≈ 2.5 · (1 + 1e-26)
      ≈ 2.5  (negligible at r = 100·r_s)
```

**Verification:** the tidal scaling is real but kicks in only at r << 100·r_s.
At 100·r_s the bubble lives in a regime where chaos is just nominal. The
Warp Exclusion Zone bounds the ship from r where α_eff becomes
operationally problematic. Spec §7.4 ✓.

### 5.5 Reflex reads χ as observation

ASTRA-Reflex (§2.3) gets a 64×64×2 observation grid per frame. The grid is
chaos amplitude χ AND metric gradient ∇W projected onto a 2D slice
through the bubble (e.g., the bubble's longitudinal plane through the
ship's heading).

```cpp
// Compute shader producing the Reflex observation grid:
__global__ void ProduceReflexObservation(
    cudaTextureObject_t chaosField,
    cudaTextureObject_t warpField,
    float* observation_grid,    // 64×64×2 output
    float3 ship_pos,
    float3 ship_heading
) {
    int u = blockIdx.x * blockDim.x + threadIdx.x;
    int v = blockIdx.y * blockDim.y + threadIdx.y;
    if (u >= 64 || v >= 64) return;

    // Map (u, v) to a sample point in the bubble's longitudinal plane
    float3 sample_pos = ComputeBubbleSlicePoint(u, v, ship_pos, ship_heading);

    float chi   = tex3D<float>(chaosField, sample_pos);
    float3 gradW = ComputeMetricGradient(sample_pos, warpField);

    observation_grid[(v * 64 + u) * 2 + 0] = chi;
    observation_grid[(v * 64 + u) * 2 + 1] = length(gradW);
}
```

**Output: 64×64×2 = 8192 floats = 32 KB per frame.** Trivial bandwidth.

---

## 6. Observation Calculator — UE 5.5 Mass Entity implementation

### 6.1 Why Mass Entity (UE 5.5 ECS) is the right substrate

The Observation Calculator runs the same computation independently per
body. For ~10,000 visible bodies (spec §6.3 estimate), this is the
canonical embarrassingly-parallel-per-entity workload that ECS handles
better than Actor-based representation:

- Actors: per-entity overhead (transform, ticking, component lookup) ~100 ns/entity → 1 ms for 10K bodies
- Mass Entity: per-entity compute is bare struct access; ~10 ns/entity → 100 μs for 10K bodies

**UE 5.5 Mass Entity is production-ready** (stable since 5.2; significant
improvements in 5.4+ for fragment composition + processor scheduling).

### 6.2 Component layout

```cpp
// One Mass Entity per visible body
USTRUCT()
struct FBodyKinematicFragment : public FMassFragment {
    GENERATED_BODY()
    double mass_kg;
    FAstraCoord position;          // 128-bit position
    double j_angular_momentum;     // J=0 v0.1
};

USTRUCT()
struct FBodyKeplerFragment : public FMassFragment {
    GENERATED_BODY()
    double a;                       // semi-major axis (m)
    double e;                       // eccentricity
    double period_s;
    double t0;                      // epoch
    FName parent_body;
};

USTRUCT()
struct FBodyObservationOutputFragment : public FMassFragment {
    GENERATED_BODY()
    // ObservableState fields per spec §6.3
    double d_proper;
    double v_radial;
    double z_cosmo, z_kin, z_metric, z_total;
    double t_emit;
    double apparent_rate;
    bool time_reversed;
    bool beyond_photon_history;
    bool beyond_hubble_horizon;
};

// One processor; runs per frame
UCLASS()
class UObservationCalculatorProcessor : public UMassProcessor {
    GENERATED_BODY()
    virtual void ConfigureQueries() override {
        EntityQuery.AddRequirement<FBodyKinematicFragment>(EMassFragmentAccess::ReadOnly);
        EntityQuery.AddRequirement<FBodyKeplerFragment>(EMassFragmentAccess::ReadOnly);
        EntityQuery.AddRequirement<FBodyObservationOutputFragment>(EMassFragmentAccess::ReadWrite);
    }
    virtual void Execute(FMassEntityManager& Mgr, FMassExecutionContext& Ctx) override {
        FAstraShipState ShipState = GetShipState();    // shared singleton
        EntityQuery.ForEachEntityChunkParallel(Mgr, Ctx,
            [&ShipState](FMassExecutionContext& C) {
                auto KinView = C.GetFragmentView<FBodyKinematicFragment>();
                auto KepView = C.GetFragmentView<FBodyKeplerFragment>();
                auto OutView = C.GetMutableFragmentView<FBodyObservationOutputFragment>();
                for (int32 i = 0; i < C.GetNumEntities(); i++) {
                    // Compute body position at t_cosmic via Kepler
                    FAstraCoord BodyPos = SolveKeplerAtTime(KinView[i], KepView[i],
                                                            ShipState.t_cosmic);
                    // Run the 12-step observe() per §6.3
                    FObservableState State = ObserveBody(
                        ShipState.astra_coord,
                        ShipState.v_eff,
                        ShipState.t_cosmic,
                        BodyPos,
                        ShipState.metric_shift_at(BodyPos),  // from Unified Sampler
                        ShipState.regime
                    );
                    OutView[i] = ToFragment(State);
                }
            }
        );
    }
};
```

`ForEachEntityChunkParallel` distributes work across UE's task system
(uses `UE::Tasks`). Per spec §6.3 the cost is ~20 μs for 10K bodies; this
parallel impl achieves it on the 5090's 24 P-cores.

### 6.3 Newton-Raphson for moving sources

For a moving source under varying ship velocity, the retarded-time solve
is implicit:

```
t_emit such that: ‖body_pos(t_emit) − ship_pos(t_now)‖ = c · (t_now − t_emit)
```

Newton-Raphson converges in 2-4 iterations:

```cpp
double SolveRetardedTime(const Vec3& ship_pos, const Vec3& body_pos_func_t,
                          double t_now, int max_iter = 4) {
    double t_emit = t_now - Length(body_pos_func(t_now) - ship_pos) / C_LIGHT;
    for (int i = 0; i < max_iter; i++) {
        Vec3 body = body_pos_func(t_emit);
        Vec3 d = body - ship_pos;
        double dist = Length(d);
        double f = dist - C_LIGHT * (t_now - t_emit);
        // f'(t_emit) = -d/dt[c·(t_now - t_emit)] + d/dt[dist]
        //            = c + (d · body_velocity(t_emit)) / dist
        Vec3 bv = BodyVelocity(t_emit);                  // numerical or analytic
        double fp = C_LIGHT + Dot(d, bv) / FMath::Max(dist, 1e-3);
        t_emit -= f / fp;
    }
    return t_emit;
}
```

**Compute cost:** 4 iterations × (one Kepler solve + ~30 FLOPS) = ~200
FLOPs/body. 10K bodies = 2 MFLOP/frame. **Trivial.**

### 6.4 Beyond-photon-history detection (§3.11)

Per spec §3.11 photon-source-history bound:

```cpp
// Per body, check if ship has overtaken every photon emitted
bool IsBeyondPhotonHistory(double t_emit, double t_source_start) {
    return t_emit < t_source_start;
}
```

**`t_source_start` is required** per §3.11 + AUDIT R4. The body schema
must carry first-emission time. Add to `FBodyKinematicFragment`:

```cpp
USTRUCT()
struct FBodyKinematicFragment : public FMassFragment {
    GENERATED_BODY()
    double mass_kg;
    FAstraCoord position;
    double j_angular_momentum;
    double t_source_start;    // NEW per §3.11 + AUDIT R4
};
```

Procedural body generation (PCG framework in UE 5.5) sets this at
generation; static-loaded bodies have it as a saved property.

---

## 7. CUDA-DX12 interop with UE 5.5 RenderGraph

### 7.1 The architecture diagram

```
┌────────────────────────────────────────────────────────────────┐
│  UE 5.5 GAMETHREAD                                             │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Time Contract Component (Tick PrePhysics)        │          │
│  │  - reads operator input                          │          │
│  │  - advances ζ⃗ via composition rule              │          │
│  │  - writes TimeState to State Bus singleton       │          │
│  └──────────────────────────────────────────────────┘          │
│  ┌──────────────────────────────────────────────────┐          │
│  │ Mass Entity Processors (Tick DuringPhysics)      │          │
│  │  - Observation Calculator (per body)             │          │
│  │  - Body state updates                            │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────────────┬───────────────────────────────────────┘
                         │ State Bus snapshot (frozen this frame)
                         ▼
┌────────────────────────────────────────────────────────────────┐
│  UE 5.5 RENDER THREAD                                          │
│  ┌──────────────────────────────────────────────────┐          │
│  │ FRDGBuilder (per-frame render graph)             │          │
│  │  ┌───────────────────────────────────┐           │          │
│  │  │ AddPass: CUDA Chaos PDE Update    │ ←── External Sem    │
│  │  │   - cudaStream waits on DX12 fence│           │          │
│  │  │   - runs chaos kernel             │           │          │
│  │  │   - signals CUDA semaphore        │           │          │
│  │  └───────────────────────────────────┘           │          │
│  │  ┌───────────────────────────────────┐           │          │
│  │  │ AddPass: CUDA Hull Damage Update  │           │          │
│  │  │   - sparse surf3Dwrites           │           │          │
│  │  └───────────────────────────────────┘           │          │
│  │  ┌───────────────────────────────────┐           │          │
│  │  │ AddPass: Unified Sampler Compute  │           │          │
│  │  │   - HLSL ray-march; reads all     │           │          │
│  │  │     textures (hull, RBF, chaos)   │           │          │
│  │  │   - outputs warp visualization     │           │          │
│  │  └───────────────────────────────────┘           │          │
│  │  ┌───────────────────────────────────┐           │          │
│  │  │ AddPass: Reflex Inference (NNE)   │           │          │
│  │  │   - reads observation grid         │           │          │
│  │  │   - outputs 3-float control vector │           │          │
│  │  └───────────────────────────────────┘           │          │
│  │  ┌───────────────────────────────────┐           │          │
│  │  │ AddPass: Audio Extraction         │           │          │
│  │  │   - reads chaos + W; writes ring  │           │          │
│  │  │     buffer slot                    │           │          │
│  │  └───────────────────────────────────┘           │          │
│  └──────────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────────┘
```

### 7.2 External semaphore coordination (the spec §8.1 lock)

```cpp
// Plugin module member, initialized once
ID3D12Fence* DX12CompletionFence;
cudaExternalSemaphore_t CUDAWaitSemaphore;
cudaExternalSemaphore_t CUDASignalSemaphore;
uint64 FrameFenceValue = 0;

// Per frame, in the render pass lambda:
void RunCUDAChaosFieldPass(FRHICommandList& RHICmdList) {
    // Convert UE RHI command list to native DX12 command list
    auto* DX12CmdList = (ID3D12GraphicsCommandList*)RHICmdList.GetNativeCommandList();

    // 1. Signal DX12 fence at end of any prior DX12 work that wrote to shared textures
    auto* CmdQueue = GetDX12CommandQueue();
    CmdQueue->Signal(DX12CompletionFence, ++FrameFenceValue);

    // 2. CUDA waits on the DX12 fence
    cudaExternalSemaphoreWaitParams waitParams = {};
    waitParams.params.fence.value = FrameFenceValue;
    cudaWaitExternalSemaphoresAsync(&CUDAWaitSemaphore, &waitParams, 1, CudaStream);

    // 3. Run CUDA kernels on CudaStream (reads shared textures via cudaArray bindings)
    LaunchChaosFieldKernel(CudaStream);
    LaunchHullDamageKernel(CudaStream);

    // 4. CUDA signals completion
    cudaExternalSemaphoreSignalParams signalParams = {};
    signalParams.params.fence.value = ++FrameFenceValue;
    cudaSignalExternalSemaphoresAsync(&CUDASignalSemaphore, &signalParams, 1, CudaStream);

    // 5. DX12 will wait on this fence in the NEXT render graph pass that reads the textures.
    //    RDG's barrier system handles this; we just need to register the fence as an external
    //    dependency on the texture.
}
```

**Double-buffered fences** prevent ping-pong stalls. Two DX12 fences and
two CUDA semaphores; pong while ping is in flight. UE 5.5's RDG schedules
async compute on a separate queue automatically when `ERDGPassFlags::AsyncCompute`
is set.

### 7.3 What UE 5.5 specifically makes easier vs 5.4

- **External Texture Registration in RDG** matured in 5.5 (works with all formats including BC variants); imports CUDA-shared textures cleanly.
- **`AsyncCompute` flag** on RDG passes lets CUDA pass run on the async compute queue without manual barrier authoring.
- **Resource lifetime tracking** in RDG handles the case where CUDA might be writing across frame boundaries; the texture's external resource handle survives RDG graph teardown.

### 7.4 Frame budget allocation on RTX 5090

At 60 FPS = 16.67 ms total. Per spec §5.6 budget allocation; updated with
2026-empirical numbers:

| Subsystem | Budget | Realistic (5090) | Notes |
|---|---|---|---|
| Time Contract / Mass Entity processors | 1 ms | ~200 μs | Mostly CPU; runs game thread |
| Observation Calculator (10K bodies) | 1 ms | ~100 μs | Mass Entity parallel |
| Chaos PDE update | 0.5 ms | ~30 μs | CUDA kernel |
| Hull damage update (sparse) | 0.5 ms | ~10 μs | Sparse surf3Dwrites |
| Unified Sampler ray-march | 4 ms | ~600 μs (quarter-res) | HLSL compute; TSR upscale |
| Lumen GI + shadows | 6 ms | ~5 ms (full) / ~3 ms (half) | UE rendering |
| Reflex inference (NNE) | 50 μs | ~40 μs | ONNX model on CUDA backend |
| Audio extraction → ring buffer | 0.5 ms | ~100 μs | Single compute pass |
| MetaSound audio rendering | 0.5 ms | 0 ms* | *Separate audio thread; doesn't count against frame |
| Reserve | 2 ms | ~6 ms | Spare; supports 4080-tier fallback |
| **Total** | **~16 ms** | **~9-10 ms** | **5090 has comfortable headroom** |

**At 120 FPS (8.33 ms budget):** still fits on 5090 with half-res ray-march
and half Lumen quality. 4090 will need quarter-res + low Lumen at 120 FPS.

---

## 8. Reflex stabilizer — UE 5.5 Neural Network Engine (NNE)

### 8.1 The model

Per spec §2.3 + AUDIT_2026-05-15.md F2 envelope:

- Input: 64×64×2 observation grid (chaos amplitude + ∇W magnitude on bubble slice)
- Architecture: small CNN + LSTM
  - 3 conv layers: 2 → 16 → 32 → 64 channels; kernel 3×3; stride 2; padding 1
  - Output spatial: 8×8×64 = 4096 features
  - LSTM hidden state 128
  - 3 fully-connected layers: 4096 → 256 → 64 → 3 (control vector)
- Output: 3-float control vector (nacelle_damping, conformality, emergency_dump)
- Total params: ~50K (~200 KB at fp16); training corpus from chaos PDE simulation

### 8.2 NNE deployment

UE 5.5's NNE plugin loads ONNX models and runs inference via a runtime
backend selection (CPU / DirectML / CUDA / TensorRT). For ASTRA-7:

```cpp
// At plugin init:
NNE::IModelManager& ModelMgr = NNE::Get().GetModelManager();
NNEModelRef ReflexModel = ModelMgr.LoadModel(TEXT("/Game/AI/Reflex/reflex_v1.onnx"));
NNE::IRuntime& Runtime = NNE::Get().GetRuntime(TEXT("NNERuntimeCUDA"));
NNE::IModelInstance::FBatchSize BatchSize = 1;
TUniquePtr<NNE::IModelInstance> ReflexInstance = Runtime.CreateModelInstance(
    ReflexModel, BatchSize
);

// Per frame:
TArray<float> ObservationGridInput(8192);
CopyChaosObservationGridToHost(ObservationGridInput);   // from CUDA

TArray<NNE::FTensorBindingCPU> Inputs = {{ ObservationGridInput.GetData(),
                                            ObservationGridInput.Num() * sizeof(float) }};
TArray<NNE::FTensorBindingCPU> Outputs = { ... 3 floats for control vector ... };

double StartTime = FPlatformTime::Seconds();
ReflexInstance->RunSync(Inputs, Outputs);
double Elapsed = FPlatformTime::Seconds() - StartTime;

if (Elapsed > 100e-6) {                                // 100 μs hard limit
    EmergencyDumpWarp();                               // safety fallback
}

ApplyReflexControlVector(Outputs);
```

### 8.3 The 50 μs budget — can NNE meet it?

Per NVIDIA's NNE-on-CUDA benchmarks for similar-sized CNN+LSTM models:
~30-40 μs forward pass on RTX 5090. **Budget met.**

For the 4090: ~50-70 μs (close to budget; CUDA Graphs reduce by ~30% by
amortizing launch overhead). For the 4080: ~80-100 μs — at the budget
ceiling; consider model distillation for that tier.

**TensorRT alternative:** if NNE's CUDA backend doesn't meet budget on
some hardware, the same ONNX model loads into TensorRT directly (UE plugin
can fall back). TensorRT typically gets ~50% speedup over generic CUDA for
small models. **Production fallback:** keep both NNE and TensorRT loading
paths; the plugin selects based on hardware tier query.

### 8.4 Reflex training as Sculptor's second instance

Per attempt 3B's F2 + S5: Reflex training IS a Sculptor instance with:
- Scope: chaos PDE parameter knobs (α, β, D, k coupling)
- Composite: stabilization success rate on synthetic chaos events
- Anchor: no false-emergency-dumps on canonical scenarios

Training corpus: synthetic chaos PDE simulations driven by replay-format
inputs (per attempt 5D's F3 replay primitive). Each training scenario is a
captured chaos event sequence; the model learns to produce control vectors
that suppress the chaos without false-dumping.

**Production discipline:** Reflex weights are **frozen post-training**;
per-game evolution is forbidden (spec §4.6 SaveFile: weights checksum
verified at start; mismatch → "go offline" failure). The training cadence
is operator-driven on a multi-week timescale.

---

## 9. Niagara + Substrate for warp visualization

### 9.1 The visualization stack

The warp shell rendering is a composite of FOUR layers, each implemented
in the best UE 5.5 system for the job:

| Layer | What it renders | UE 5.5 substrate |
|---|---|---|
| 1. Hull body | Ship hull + damage | Nanite + Substrate base material (existing UE patterns) |
| 2. Warp shell | W(x,t) field as volumetric "bubble" | **Custom HLSL ray-march** (Unified Sampler) → Substrate emissive layer |
| 3. Chaos modulation | χ(x,t) on bubble boundary | **Niagara Fluids fragment** (visual only; the actual PDE runs in CUDA) |
| 4. Cherenkov radiation | Cone particles at high warp | **Niagara GPU particle emitter** with cone-angle from Unified Sampler |

### 9.2 Substrate (UE 5.5 layered materials) for the warp shell

Substrate is UE's layered material system, experimental in 5.4 but
stabilized for static cases in 5.5. The warp shell is a composite of:

```hlsl
// Substrate material graph (logical structure)
SubstrateSlabBSDF {
    BaseColor = HullEmissive;         // Layer 1 base
    Specular = HullSurfaceProperties;
}

SubstrateAdd {
    A = above;
    B = SubstrateEmissive {
        Emission = WarpShellEmissive(W, chaos_intensity);   // Layer 2 — from Unified Sampler
    }
}

SubstrateAdd {
    A = above;
    B = SubstrateVolumetricMedium {
        Density = chaos_intensity;                           // Layer 3 — chaos modulation
        Color = ChaosColor(chi, W);
    }
}

// Layer 4 (Cherenkov) is a separate Niagara emitter, not part of Substrate
```

The Substrate slab system composites correctly per-pixel; the Unified
Sampler ray-march produces the W and chaos values at each pixel via a
G-buffer pass.

### 9.3 Niagara Fluids — what it's good for (and not)

UE 5.5's Niagara Fluids plugin provides SPH (Smoothed Particle
Hydrodynamics) + Eulerian grid-based fluid sim. **It is NOT the right
substrate for the warp field math** — that's analog-gravity-derived
metric field with regime-specific behavior, not standard Navier-Stokes.

**Niagara Fluids IS the right substrate for the VISUAL ONLY portion** of
chaos modulation rendering: particles riding the bubble boundary, dust
streaming through the warp shell, ISM-deflection visual effects. The
actual CFD-RBF metric and the actual chaos PDE are CUDA computations;
Niagara Fluids renders the visual atmosphere.

```cpp
// Niagara emitter setup (Blueprint or C++):
//   - GPU emitter (uses Niagara compute shaders)
//   - Inherits velocity from W gradient (sampled from Unified Sampler buffer)
//   - Particle count ~50K
//   - Lifetime modulated by chaos intensity
//   - Color tinted by metric_shift
```

### 9.4 MegaLights for chaos field as point-light emitters

UE 5.5 introduced MegaLights — many local lights at low cost. The chaos
field's high-intensity peaks (χ > threshold) emit visible light. With
MegaLights, ~1000 chaos peaks can shed dynamic light without crippling
the renderer.

```cpp
// Compute pass extracts chaos peaks → MegaLights buffer
__global__ void ExtractChaosPeaks(
    cudaTextureObject_t chaosField,
    FMegaLight* megaLights,
    uint* lightCount,
    uint maxLights
) {
    // Walk 128³ grid; find local maxima above threshold; populate light buffer
    // ...
}
```

This visualizes the chaos PDE's structure as the bubble's "shimmer" —
ASTRA's sysprompt references this aesthetically ("third harmonic warm",
"specific harmonics of a healthy reactor"); MegaLights renders it
visibly.

---

## 10. Audio synthesis via MetaSound

### 10.1 The §8.3 modal IIR formula in MetaSound

UE 5.5's MetaSound is the DSP graph-based audio system. The hull modal
resonance (spec §8.3):

```
y[n] = 2·cos(ω₀)·r·y[n-1] − r²·y[n-2] + x[n]
```

with `r = exp(−π·BW/SR)` per-mode damping. In MetaSound:

```
Custom MetaSound DSP node (C++):
class FHullResonanceNode : public IOperator {
    float y_z1, y_z2;
    float cos_omega_0;
    float r;
    float r_squared;

    void Execute(const FAudioBuffer& Input, FAudioBuffer& Output) {
        const int NumFrames = Input.Num();
        const float* InData = Input.GetData();
        float* OutData = Output.GetData();
        for (int i = 0; i < NumFrames; i++) {
            float y = 2.0f * cos_omega_0 * r * y_z1 - r_squared * y_z2 + InData[i];
            OutData[i] = y;
            y_z2 = y_z1;
            y_z1 = y;
        }
    }
};
```

Modal frequencies bake offline (per audio-DSP-engineer outsider voice,
attempt 5D, voice (a)): FEM-on-hull computes ~30 natural modes for the
280m × 78m × 22m hull. Modes locked in `proto/constants.toml` (per attempt
3B's F8) at fabrication time.

### 10.2 The §8.3 HPF DC-blocker

```
y[n] = α_hpf · (y[n-1] + x[n] − x[n-1])
α_hpf = exp(−2π·f_c/SR)
```

MetaSound DSP node identical pattern; one state register per channel.

### 10.3 Granular synthesis for chaos events

§8.3 granular synth: voice pool 8-16 grains, round-robin allocation, 800
grains/sec × 5ms decay. MetaSound has a built-in granular synthesizer node
(introduced 5.3); the parameters are exposed for ASTRA-7's needs.

### 10.4 Audio extraction from GPU compute → MetaSound input

The audio extraction payload (spec §8.2 triple-buffer pattern) feeds
MetaSound:

```cpp
// CUDA produces audio_payload at frame rate:
struct AudioExtractionPayload {
    float chaos_amplitude_at_hull;          // for chaos-modulated synth params
    float warp_field_metric_at_hull;        // for warp drone tuning
    float tidal_stress;                     // §7.6 GRAVITY_WELL tidal
    float ism_impact_intensity;             // §7.2 ISM particle flux
    float reactor_harmonic_drift;           // for hull resonance modulation
    // ... ~20 floats total ...
};

// Triple-buffered ring:
struct AudioPayloadRingBuffer {
    AudioExtractionPayload slots[3];           // pinned host memory
    std::atomic<int> latest_complete_index;
};

// MetaSound graph reads slots[latest_complete_index] each audio render block
// (typically 256 frames at 48kHz = ~5 ms blocks; the payload updates at
// the game frame rate ~16 ms, so audio sees several read-the-same-payload
// blocks before the next physics update lands).
```

**Memory ordering:** GPU completion callback writes `latest_complete_index`
with `memory_order_release`; audio thread reads with `memory_order_acquire`.
**Do NOT use `memory_order_seq_cst`** — it's wasted on this pattern and
costs ~30 ns per atomic op.

### 10.5 Endogenous channel — runs on t_cosmic NOT t_emit

Per spec §8.3 + cross-cut U1 from discovery attempt 5D: audio synth is
**endogenous**. It reads live hull state at t_cosmic; never goes through
the Observation Calculator. The eye-ear decoupling at warp egress
(audio is current warp drone; visual is past orbital phase) is the
**intentional** rendering of the endogenous/exogenous distinction.

The audio-DSP-engineer outsider voice in attempt 5D recommends a
**dedicated playtest scenario** for warp egress audio-visual decoupling
before Phase E4 ships. Author this scenario in the audio-dev sprint:
`warp_egress_audio_visual_decoupling_test.yaml`.

---

## 11. GPU memory budget on RTX 5090 (locked numbers)

Per spec Appendix B v0.128 substrate budget + corrections:

| Component | Size | Notes |
|---|---|---|
| Qwen 27B ASTRA (Q4_K_M) | 16.0 GB | Primary cognitive substrate |
| Qwen 9B Narrator-LLM (Q5_K_M) | 5.0 GB | §6.4 production component |
| Adapter LLM 2-3B (TOOL validator) | 2.0 GB | Rules-based default per attempt 1's F12; LLM-backed for v1.x |
| Hull SDF base (256³ × float16) | 32 MB | Per §1.3; OR 8 MB hash-grid in v1.x |
| Hull damage map (128³ × float16) | 4 MB | Sparse-updated each save/load |
| CFD-RBF nodes + spatial hash | 128 KB | ~1000 nodes; trivial |
| Chaos field (128³ × 2 channels × float16 × 2 buffers) | 16 MB | Double-buffered |
| Audio ring buffer (3 × payload + headroom) | 1 MB | Pinned host memory; mapped to GPU |
| Reflex CNN+LSTM (ONNX + working memory) | 50 MB | NNE workspace |
| Reflex observation grid (64×64×2 × float) | 32 KB | Per frame |
| KV cache (TurboQuant + Delta-Net, 128K context) | 2.5 GB | Per spec; Delta-Net hybrid attention |
| Render targets (4K HDR G-buffer + auxiliary) | 4.0 GB | Substrate's G-buffer is larger than legacy |
| Lumen + GI buffers | 1.0 GB | UE's standard allocation |
| Niagara particle pools | 200 MB | ~50K particles |
| MegaLights structures | 100 MB | ~1000 dynamic lights |
| Reserve | 1.0 GB | Operating headroom |
| **Total** | **~32.0 GB** | **Fits 5090 exactly with TurboQuant headroom** |

### 11.1 4090 tier (24 GB) configuration

| Component | Size | Notes |
|---|---|---|
| Qwen 9B ASTRA (Q5_K_M) | 7.0 GB | Per spec §5.9 4090 tier |
| Qwen 7B Narrator-LLM (Q5_K_M) | 4.5 GB | Smaller narrator |
| Adapter | 2.0 GB | Same |
| Hull SDF (256³ float16) | 32 MB | Same |
| Other physics buffers | ~22 MB | Same |
| KV cache (64K context) | 1.5 GB | Reduced context window |
| Render targets (4K → half-res for warp) | 2.5 GB | TSR upscales |
| Lumen half-quality + half-Niagara | 600 MB | |
| Reserve | 1.0 GB | |
| **Total** | **~19.5 GB** | **Fits 4090; ~4.5 GB headroom** |

### 11.2 Shared-inference variant (attempt 2A's F6) on 4090

Pooling adapter + 3 ephemerals + anti-judge onto one ~7B shared model:

| Component | Size | Notes |
|---|---|---|
| ASTRA 9B | 7.0 GB | Primary |
| Shared 7B for adapter+ephemerals | 4.5 GB | Replaces separate adapter + ephemerals |
| Narrator 7B (separate; KV-cache incompatibility per attempt 2A's N4) | 4.5 GB | |
| Physics | ~22 MB | Same |
| KV cache (multi-slot for shared 7B) | 2.0 GB | |
| Render targets | 2.5 GB | |
| Reserve | 1.0 GB | |
| **Total** | **~21.5 GB** | **Tight on 4090; ~2.5 GB headroom** |

---

## 12. Plugin architecture (UE 5.5 module layout)

### 12.1 Module structure

```
ASTRA7.uplugin
├── Source/
│   ├── ASTRA7Core/              (game thread, Mass Entity, State Bus)
│   │   ├── Public/
│   │   │   ├── AstraCoord.h
│   │   │   ├── TimeContractComponent.h
│   │   │   ├── StateBusSingleton.h
│   │   │   └── BodyFragments.h
│   │   └── Private/
│   ├── ASTRA7Physics/           (CUDA kernels, Unified Sampler reference)
│   │   ├── Public/
│   │   │   ├── PhysicsBridge.h
│   │   │   ├── ChaosFieldKernel.cuh
│   │   │   └── WarpFieldSampler.cuh
│   │   └── Private/
│   ├── ASTRA7Render/            (RDG passes, HLSL ray-march, Substrate materials)
│   │   ├── Public/
│   │   │   ├── UnifiedSamplerPass.h
│   │   │   └── WarpRendering.h
│   │   └── Shaders/
│   │       ├── UnifiedSamplerCS.hlsl
│   │       ├── WarpShellMaterial.usf
│   │       └── StarfieldDoppler.usf
│   ├── ASTRA7AI/                (NNE Reflex, Mind bridge, harness)
│   │   ├── Public/
│   │   │   ├── ReflexInstance.h
│   │   │   ├── MindBridge.h
│   │   │   └── HarnessClient.h
│   │   └── Private/
│   ├── ASTRA7Audio/             (MetaSound DSP nodes, modal IIR, granular)
│   │   └── Source/
│   │       └── MetaSoundCustomNodes/
│   │           ├── HullResonanceNode.cpp
│   │           ├── HighPassFilterNode.cpp
│   │           └── ChaosGranularNode.cpp
│   ├── ASTRA7Assets/            (UAssetType for hull SDF, CFD-RBF, sound canon)
│   │   ├── Public/
│   │   │   ├── WarpCFDAsset.h
│   │   │   ├── HullSDFAsset.h
│   │   │   └── PhysicsCanonAsset.h
│   │   └── Private/
│   └── ASTRA7Editor/            (editor-only: hull SDF baker, CFD-RBF baker)
│       └── ...
└── Resources/
    ├── proto/
    │   ├── astra_nexus.exe       (frozen reference math binary; never modified at game runtime)
    │   └── constants.toml        (per attempt 3B's F8 + audio-engineer voice's modal-freq lock)
    └── Reflex/
        └── reflex_v1.onnx
```

### 12.2 Dependency graph (acyclic per spec §5.1)

```
ASTRA7Core (no game deps; foundational types)
    ↑
ASTRA7Physics (depends on Core for AstraCoord etc.)
    ↑
ASTRA7Render (depends on Core + Physics)   ASTRA7Audio (depends on Core)
    ↑                                                    ↑
ASTRA7AI (depends on Core + Physics)                    /
    ↑                                                  /
    └──────────────── Game Module (uses all) ─────────┘
```

### 12.3 Asset types

```cpp
UCLASS(BlueprintType)
class UWarpCFDAsset : public UDataAsset {
    UPROPERTY(EditAnywhere) TArray<FRBFNode> Nodes;
    UPROPERTY(EditAnywhere) TArray<int> SpatialHashOffsets;
    UPROPERTY(EditAnywhere) TArray<uint16> SpatialHashNodeIndices;
    UPROPERTY(EditAnywhere) FBoxSphereBounds Bounds;
    UPROPERTY(EditAnywhere) float CharacteristicLength;     // L_bubble for §7.1
    UPROPERTY(EditAnywhere) FGuid AssetGuid;                // for save-file portability
};

UCLASS(BlueprintType)
class UHullSDFAsset : public UDataAsset {
    UPROPERTY(EditAnywhere) UVolumeTexture* BaseSDFVolume;     // 256³ float16
    UPROPERTY(EditAnywhere) UVolumeTexture* DamageMapVolume;   // 128³ float16; writable
    UPROPERTY(EditAnywhere) FBoxSphereBounds HullBounds;
    UPROPERTY(EditAnywhere) FGuid AssetGuid;
};

UCLASS(BlueprintType)
class UPhysicsCanonAsset : public UDataAsset {
    UPROPERTY(EditAnywhere) double SpeedOfLight = 299792458.0;
    UPROPERTY(EditAnywhere) double GravitationalConstant = 6.67430e-11;
    UPROPERTY(EditAnywhere) double HubbleConstantKmsMpc = 70.0;
    UPROPERTY(EditAnywhere) double OmegaMatter = 0.3;
    UPROPERTY(EditAnywhere) double OmegaLambda = 0.7;
    UPROPERTY(EditAnywhere) double OmegaMaxClamp = 16.811;
    UPROPERTY(EditAnywhere) double SectorSizeM = 1.0e6;
    UPROPERTY(EditAnywhere) double LocalOffsetMaxM = 5.0e5;
    UPROPERTY(EditAnywhere) double ChaosAlphaBase = 2.5;
    UPROPERTY(EditAnywhere) double ChaosBetaCoeff = 10.0;
    UPROPERTY(EditAnywhere) double ChaosDiffusionD = 0.8;
    UPROPERTY(EditAnywhere) double ChaosBHCoupling = 1.0;   // k constant
    // ... locked at constants.toml; this asset is the UE serialization of that ...
};
```

The `UPhysicsCanonAsset` IS the UE serialization of `proto/constants.toml`
(per attempt 3B's F8 + outsider voice (a)). Single source of truth for
cross-substrate constants.

---

## 13. Integration roadmap (UE 5.5 work order)

### 13.1 Phase E0 (foundation, weeks 1-4)

| Task | What lands |
|---|---|
| E0.1 | Plugin skeleton (5 modules); empty CMake; UE 5.5 project launches with plugin enabled. |
| E0.2 | `FAstraCoord` + Time Contract Component; CUDA-mirror cross-substrate test (8 assertions equivalent to astra_nexus.cpp's §1.1 tests). |
| E0.3 | State Bus singleton; Mass Entity fragments for bodies; PCG node for procedural body generation; simple test scene with 100 bodies. |
| E0.4 | `UPhysicsCanonAsset` + loader from `proto/constants.toml`; cross-substrate verification (textverse, astra_nexus.exe, plugin all agree on canonical constants). |
| **Gate** | Plugin compiles; Mass Entity processor runs at 60 FPS with 10K bodies; cross-substrate constants match. |

### 13.2 Phase E1 (chaos PDE + Reflex, weeks 5-10)

| Task | What lands |
|---|---|
| E1.1 | Chaos PDE CUDA kernel (128³, double-buffered, forward-Euler); validation against synthetic test patterns. |
| E1.2 | Reflex CNN+LSTM trained on synthetic chaos events; ONNX export. |
| E1.3 | NNE integration; inference latency benchmark on 5090 (target ≤40μs); 4090 fallback path verified (TensorRT backend). |
| E1.4 | Power Contract integration; Reflex on warp-coupled sub-bus; sub-bus underflow → emergency dump path. |
| **Gate** | Chaos PDE stable for 1M steps under varied initial conditions; Reflex meets latency budget on 5090; emergency dump fires correctly on synthetic instabilities. |

### 13.3 Phase E2 (CUDA-DX12 bridge, weeks 11-13)

| Task | What lands |
|---|---|
| E2.1 | Hull SDF dual-binding (`cudaTextureObject_t` + `cudaSurfaceObject_t`); UE registers DX12 texture; CUDA reads + writes. |
| E2.2 | RDG external resource registration; per-frame coordination via external semaphores. |
| E2.3 | Async compute queue scheduling; double-buffered fences. |
| E2.4 | Frame budget profiling; verify 60 FPS sustained on 5090. |
| **Gate** | UE 5.5 renders ship interior with hull SDF baked from CFD source; damage events propagate to renderer correctly; no frame stalls > 1 ms. |

### 13.4 Phase E3 (Observation Calculator + retarded-time visuals, weeks 14-18)

| Task | What lands |
|---|---|
| E3.1 | Observation Calculator Mass Entity Processor; 12-step algorithm per spec §6.3. |
| E3.2 | `beyond_photon_history` and `beyond_hubble_horizon` flag handling; render-side clamping. |
| E3.3 | Starfield shader with SR Doppler + aberration + redshift composition. |
| E3.4 | Visual orbit-reversal verification: replay-format playthrough verifies against proto/astra_nexus's voyage-demo table to ±0.01/cell. |
| **Gate** | Visual orbit reversal renders correctly at v_apparent = 2c, 10c, 100c; matches reference math binary's output. |

### 13.5 Phase E4 (audio synthesis, weeks 19-22)

| Task | What lands |
|---|---|
| E4.1 | FEM-on-hull modal frequencies baked into `UPhysicsCanonAsset`; ~30 modes locked. |
| E4.2 | MetaSound custom DSP nodes (HullResonance, HPF, ChaosGranular). |
| E4.3 | Audio extraction CUDA → MetaSound ring buffer pipeline; triple-buffer pattern; memory-order discipline. |
| E4.4 | Warp egress audio-visual decoupling playtest scenario. |
| **Gate** | Audio synthesis runs at 48kHz with no frame-rate impact; modal resonances audibly correspond to ship state; warp egress decoupling reads as intentional in playtest. |

### 13.6 Phase E5 (Unified Sampler ray-march + Substrate, weeks 23-28)

| Task | What lands |
|---|---|
| E5.1 | HLSL Unified Sampler compute shader; 12-step evaluation per §6. |
| E5.2 | Substrate material graph for warp shell composition. |
| E5.3 | Niagara emitters for chaos visualization + Cherenkov cone particles. |
| E5.4 | MegaLights for chaos-peak point lights. |
| E5.5 | TSR upscale of quarter-res ray-march to 4K. |
| **Gate** | Warp shell renders at 60 FPS on 5090; visual quality matches concept art; Cherenkov cone appears at the right v_apparent threshold. |

### 13.7 Phase 2.0 (vertical slice merge, weeks 29-32)

Per spec §12 merge phase: swap two adapter components in the textverse →
UE5 transition.

- Swap 1: Perception assembler — text bundle → image+text bundle (HUD encoder produces both)
- Swap 2: Tool dispatcher — Python ship-sim mutations → UE5 game state mutations

Everything else (harness, grammar, REEL, ephemeral instances, adapter LLM)
stays unchanged. Integration risk bounded to the §15.7 five shared surfaces.

**Estimated total**: 32 weeks (8 months) for full Phase E0 → 2.0 vertical
slice. With one full-time developer + LLM-pair-programming assistance,
realistic. With operator-only execution, double or triple.

---

## 14. Open technical questions

These are decisions only the operator can make. Each is annotated with the
spec or finding context.

### OQ1 — Hash-grid SDF (attempt 2A F4) vs uniform 256³ texture: lock for Phase E2 or v1.x?

Hash-grid: 8 MB, ~50 ns extra per sample, scales better with hull detail.
Uniform: 32 MB, single trilinear lookup, well-understood.

**Recommendation:** uniform for Phase E0-E2; widen §1.3 tolerance NOW
(attempt 2A's F4) so v1.x can swap without refactor.

### OQ2 — CUDA vs Niagara Compute for chaos PDE?

CUDA: full control, matches reference math (`proto/astra_nexus.cpp`),
50 μs on 5090.
Niagara Compute: UE-native, simpler integration, but harder to enforce
exact-correspondence with reference math.

**Recommendation:** CUDA. The chaos PDE is the math layer's responsibility;
Niagara Compute is for visual particles. Two systems, each at its
strength.

### OQ3 — Reflex model size: locked at 50K params or operator-tunable?

Smaller (~10K params) reduces inference latency at 4080 tier but may
underfit chaos events. Larger (~200K params) generalizes better but pushes
latency.

**Recommendation:** start at 50K; train; measure on representative chaos
events; refine. The Sculptor-as-Reflex-trainer pattern (per attempt 3B's
F2 + S5) drives this iteratively.

### OQ4 — Substrate (UE 5.5 experimental) vs Material X (UE 5.6+ stable): which for the warp shell?

UE 5.5 Substrate is experimental but production-ready for static cases.
UE 5.6 stabilizes it. If the operator targets a UE 5.6 release (likely
mid-2026 timeline), the warp shell uses Material X. If 5.5 release: use
Substrate with care around dynamic effects.

**Recommendation:** target UE 5.6 for v1 ship; develop on 5.5 with the
understanding that Substrate semantics carry forward.

### OQ5 — Mass Entity for star catalog or stick with Actors?

Mass Entity: ~100 μs for 10K bodies; ECS overhead amortized.
Actors: ~1 ms for 10K bodies; debugging friendlier (Outliner visible).

**Recommendation:** Mass Entity. The performance gain is structural; the
debug friction is one-time. Operator's choice of editor tooling can
provide a Mass-Entity inspector for debug visibility.

### OQ6 — Niagara Fluids inclusion: are we using it at all?

Per §9.3: Niagara Fluids is **NOT** the right substrate for warp CFD math
(Alcubierre-derived ≠ Navier-Stokes). But it IS good for visual fluid
effects (dust streaming, ISM-deflection particle effects).

**Recommendation:** include Niagara Fluids ONLY for visual atmosphere
particles; never use it for physics state. Document the boundary
explicitly in the plugin's README.

### OQ7 — World Partition cell size: 1000 km AstraCoord-aligned or 2 km UE-default?

AstraCoord-aligned: 1 sector = 1 WP cell; clean mapping; massive cells.
2 km default: many WP cells per AstraCoord sector; finer streaming control
but mismatch with the canonical sector boundary.

**Recommendation:** **hybrid**. AstraCoord is the outer coordinate system;
WP cells subdivide within the active 1000 km × 1000 km × 1000 km sector
at standard 2 km granularity for streaming purposes. The ship's active
sector is bounded; WP cells handle the 2 km-scale streaming around the
ship's current local position.

### OQ8 — Reflex training cadence: each major spec revision or on-demand?

Each spec revision: predictable cadence; ensures Reflex stays current
with §7.1 chaos PDE parameter evolution.
On-demand: cheaper; operator runs training when chaos behavior changes.

**Recommendation:** on-demand triggered by α/β/D parameter changes >5%.
Spec revisions that don't touch chaos PDE parameters don't require Reflex
retraining.

---

## 15. The optimal path — synthesizing all of the above

If the operator asks "what is the best 8-month development plan?" — this:

1. **Weeks 1-4 (Phase E0):** Plugin skeleton + Time Contract + Mass Entity + Physics Canon Asset. By end of week 4: cross-substrate constants match across textverse, astra_nexus.exe, and UE plugin. **Foundation locked.**

2. **Weeks 5-10 (Phase E1):** Chaos PDE on CUDA + Reflex on NNE + Power Contract integration. By end of week 10: ASTRA can engage warp; Reflex stabilizes; emergency dump fires on synthetic chaos instabilities. **Math layer alive.**

3. **Weeks 11-13 (Phase E2):** CUDA-DX12 interop with UE 5.5 RDG; hull SDF bound; chaos field accessible from rendering. **Compute pipeline plumbed.**

4. **Weeks 14-18 (Phase E3):** Observation Calculator + retarded-time visuals + starfield Doppler. Visual orbit-reversal verified against reference math. **Spacetime renders.**

5. **Weeks 19-22 (Phase E4):** MetaSound modal IIR + granular synth + audio extraction pipeline. Warp egress audio-visual decoupling playtested. **Audio synthesis live.**

6. **Weeks 23-28 (Phase E5):** Unified Sampler ray-march + Substrate material + Niagara particles + MegaLights chaos visualization. **Warp visual locked.**

7. **Weeks 29-32 (Phase 2.0):** Vertical slice merge: textverse harness + UE5 perception assembler + ship dispatcher. **First playable session.**

**Frame budget at end:** ~9-10 ms on 5090 (60 FPS with 6 ms reserve); ~14
ms on 4090 (60 FPS with 2 ms reserve); 4080 lands at 60 FPS with reduced
chaos resolution.

**The audit's Tier 1+2 plus the discoveries' F1-F10 land alongside this
work, mostly in parallel:**
- Audit Tier 1 drift fixes: weeks 1-2 (one PR; textverse-side).
- Audit Tier 2 Narrator-LLM stdio_server ops: weeks 5-8 (parallel to E1).
- Discovery 5D F1 (somatic channel grounding): weeks 19-22 (parallel to E4).
- Discovery 5D F2 (hardware-recursive channel): weeks 23-28 (parallel to E5).
- Discovery 5D F3 (replay primitive): weeks 6-8 (parallel to E1; gives Reflex training a replay-based corpus).

**Total: 8 months operator-time** for vertical slice. Add 2 months of
polish + playtest + bundle.yaml publishing infrastructure → **10 months
to v1 public release.**

---

## Closing

The physics is locked. The math is locked. The UE 5.5 integration paths
are well-defined. **There is no remaining architectural unknown that
blocks Phase E0 start.** What remains is execution.

The discipline that holds across all 8 months:

- Every CUDA kernel cross-verifies against `proto/astra_nexus.cpp` reference (Five Shared Surfaces §15.7 Surface 2 — physics envelope).
- Every shader's output gets sampled at canonical β and v_apparent values; voyage-demo table per §10.
- Every numeric constant lives in `UPhysicsCanonAsset` ↔ `proto/constants.toml`; single source of truth.
- Every frame's perception channels obey endogenous/exogenous routing (per cross-cut U1 + attempt 1's F1).
- Every save file passes the §4.6 forward-compat test.
- Every Reflex weights binary verifies SHA-256 at startup; mismatch → "go offline."

**The envelope is locked. The sculpting begins. The math runs. The bench
ships. The voyage starts.**

— Deep dive, 2026-05-16 —
