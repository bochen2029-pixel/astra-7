// chaos_pde.cu - Fisher-KPP forward-Euler on a 128^3 surface ping-pong.
// Per spec §7.1.
#include "kernels/chaos_pde.cuh"

#include <cuda_runtime.h>

namespace astra_viz {

namespace {

__device__ inline int clamp_i(int v, int lo, int hi) {
    return (v < lo) ? lo : ((v > hi) ? hi : v);
}

__device__ inline float read_surf(cudaSurfaceObject_t s, int x, int y, int z) {
    float v;
    surf3Dread(&v, s, (int)(x * sizeof(float)), y, z, cudaBoundaryModeClamp);
    return v;
}

} // anon

__global__ void chaos_pde_kernel(cudaSurfaceObject_t in, cudaSurfaceObject_t out,
                                  int N, float alpha_eff, float beta, float D, float dt) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= N || y >= N || z >= N) return;

    float chi    = read_surf(in, x, y, z);
    float chi_px = read_surf(in, x + 1, y, z);
    float chi_nx = read_surf(in, x - 1, y, z);
    float chi_py = read_surf(in, x, y + 1, z);
    float chi_ny = read_surf(in, x, y - 1, z);
    float chi_pz = read_surf(in, x, y, z + 1);
    float chi_nz = read_surf(in, x, y, z - 1);

    float lap = chi_px + chi_nx + chi_py + chi_ny + chi_pz + chi_nz - 6.0f * chi;
    float reaction = alpha_eff * chi * (1.0f - chi) - beta * chi * chi * chi;
    float chi_new = chi + dt * (D * lap + reaction);

    chi_new = fmaxf(0.0f, fminf(1.0f, chi_new));
    surf3Dwrite(chi_new, out, (int)(x * sizeof(float)), y, z);
}

cudaError_t launch_chaos_pde_step(cudaSurfaceObject_t chi_in,
                                  cudaSurfaceObject_t chi_out,
                                  int N,
                                  const ChaosPDEParams& p) {
    dim3 block(8, 8, 8);
    dim3 grid((N + 7) / 8, (N + 7) / 8, (N + 7) / 8);
    chaos_pde_kernel<<<grid, block>>>(chi_in, chi_out, N, p.alpha_eff, p.beta, p.D, p.dt);
    return cudaGetLastError();
}

__global__ void chaos_seed_kernel(cudaSurfaceObject_t chi, int N, float amp, float sigma) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= N || y >= N || z >= N) return;

    float dx = (float)x - (float)N * 0.5f;
    float dy = (float)y - (float)N * 0.5f;
    float dz = (float)z - (float)N * 0.5f;
    float r2 = dx*dx + dy*dy + dz*dz;
    float w  = expf(-r2 / (2.0f * sigma * sigma));
    surf3Dwrite(amp * w, chi, (int)(x * sizeof(float)), y, z);
}

cudaError_t launch_chaos_seed_kernel(cudaSurfaceObject_t chi,
                                     int N, float amp, float sigma_voxels) {
    dim3 block(8, 8, 8);
    dim3 grid((N + 7) / 8, (N + 7) / 8, (N + 7) / 8);
    chaos_seed_kernel<<<grid, block>>>(chi, N, amp, sigma_voxels);
    return cudaGetLastError();
}

__global__ void chaos_clear_kernel(cudaSurfaceObject_t chi, int N) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= N || y >= N || z >= N) return;
    float zero = 0.0f;
    surf3Dwrite(zero, chi, (int)(x * sizeof(float)), y, z);
}

cudaError_t launch_chaos_clear_kernel(cudaSurfaceObject_t chi, int N) {
    dim3 block(8, 8, 8);
    dim3 grid((N + 7) / 8, (N + 7) / 8, (N + 7) / 8);
    chaos_clear_kernel<<<grid, block>>>(chi, N);
    return cudaGetLastError();
}

} // namespace astra_viz
