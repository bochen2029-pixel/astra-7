// warp_field.cuh - host-callable launcher for the V5 warp-bubble field kernel.
// Replaces the V3 trivial test pattern. Writes the warp metric W(x) into a
// 128^3 GL_R32F texture; the volume fragment shader samples it to render the
// violet-blue bubble with a sharp boundary at high |grad W|.
//
// Analytical Alcubierre-inspired shape: smooth sphere SDF -> shape function
// f(r_s) per spec §6 step 4. V6+ can replace with a real CFD-baked RBF
// network without changing the host-side interface.
#pragma once

#include <cuda_runtime.h>

namespace astra_viz {

struct WarpFieldParams {
    float bubble_center[3];   // metres, world space
    float bubble_radius_m;    // distance from centre at which W = 0
    float W_amplitude;        // [0, 1]; the active scene's W slider
    float world_half_extent;  // metres; the 3D texture covers [-h, h]^3 centred at origin
};

cudaError_t launch_warp_field_kernel(cudaSurfaceObject_t surf, int N,
                                     const WarpFieldParams& params);

} // namespace astra_viz
