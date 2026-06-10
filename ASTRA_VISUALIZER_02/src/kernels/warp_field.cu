// warp_field.cu - V5 analytical warp-bubble kernel.
//
// Computes W(x) for each voxel from an Alcubierre-inspired shape function.
// Per spec §6 step 4 the canon shape is `f(r_s) = max(0, 1 - r^2 / R^2)` with
// smooth-min blending; V5 ships the simple polynomial form. V6+ replaces this
// kernel body with a CFD-RBF sum (host-side interface unchanged).
//
// Coordinates: voxel (i, j, k) in [0, N) maps to world position
//   p = (i - N/2 + 0.5, j - N/2 + 0.5, k - N/2 + 0.5) * (2 * world_half_extent / N)
// so the 3D texture covers the cube [-h, h]^3 in world space.
#include "kernels/warp_field.cuh"

#include <cuda_runtime.h>

namespace astra_viz {

__global__ void warp_field_kernel(cudaSurfaceObject_t surf, int N,
                                  float cx, float cy, float cz,
                                  float radius, float W_amp,
                                  float half_extent) {
    int x = blockIdx.x * blockDim.x + threadIdx.x;
    int y = blockIdx.y * blockDim.y + threadIdx.y;
    int z = blockIdx.z * blockDim.z + threadIdx.z;
    if (x >= N || y >= N || z >= N) return;

    float scale = 2.0f * half_extent / (float)N;
    float wx = ((float)x - (float)N * 0.5f + 0.5f) * scale - cx;
    float wy = ((float)y - (float)N * 0.5f + 0.5f) * scale - cy;
    float wz = ((float)z - (float)N * 0.5f + 0.5f) * scale - cz;

    float r2 = wx*wx + wy*wy + wz*wz;
    float R2 = radius * radius;

    // f(r) = max(0, 1 - r^2/R^2)^2 - smoothed shape; W ramps from amplitude at
    // centre to 0 at r = R. Squared so the boundary falloff is C^1, matching
    // the canon's smooth-min preference.
    float t = 1.0f - r2 / R2;
    if (t < 0.0f) t = 0.0f;
    float f = t * t;

    float W = W_amp * f;
    surf3Dwrite(W, surf, (int)(x * sizeof(float)), y, z);
}

cudaError_t launch_warp_field_kernel(cudaSurfaceObject_t surf, int N,
                                     const WarpFieldParams& p) {
    dim3 block(8, 8, 8);
    dim3 grid((N + 7) / 8, (N + 7) / 8, (N + 7) / 8);
    warp_field_kernel<<<grid, block>>>(surf, N,
                                       p.bubble_center[0], p.bubble_center[1], p.bubble_center[2],
                                       p.bubble_radius_m, p.W_amplitude,
                                       p.world_half_extent);
    return cudaGetLastError();
}

} // namespace astra_viz
