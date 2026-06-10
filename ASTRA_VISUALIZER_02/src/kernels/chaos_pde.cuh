// chaos_pde.cuh - host-callable Fisher-KPP step (explicit forward-Euler with
// 6-point central-difference Laplacian, ping-pong surfaces).
// PDE: dchi/dt = D * nabla^2(chi) + alpha_eff * chi * (1 - chi) - beta * chi^3
// per spec §7.1. CFL bound: dt <= Δx^2 / (6D). Forward-Euler instead of RK2
// for V7 simplicity; numerical accuracy is fine for visualization.
//
// The seed kernel initialises the field with a centred Gaussian bump so the
// reaction term has something to grow from on the first frame.
#pragma once

#include <cuda_runtime.h>

namespace astra_viz {

struct ChaosPDEParams {
    float alpha_eff;   // reaction coefficient (Reflex modulates via sign/magnitude)
    float beta;        // cubic damping
    float D;           // diffusion coefficient
    float dt;          // integration step
};

cudaError_t launch_chaos_pde_step(cudaSurfaceObject_t chi_in,
                                  cudaSurfaceObject_t chi_out,
                                  int N,
                                  const ChaosPDEParams& p);

// One-shot kernel: writes a centred Gaussian seed (peak `amp` at the centre,
// radius scaled by `sigma_voxels`). Used by ChaosField::seed() and emergency
// dumps that need to re-seed a small clean signal.
cudaError_t launch_chaos_seed_kernel(cudaSurfaceObject_t chi,
                                     int N, float amp, float sigma_voxels);

// Clears the field to zero. Used by emergency dump.
cudaError_t launch_chaos_clear_kernel(cudaSurfaceObject_t chi, int N);

} // namespace astra_viz
