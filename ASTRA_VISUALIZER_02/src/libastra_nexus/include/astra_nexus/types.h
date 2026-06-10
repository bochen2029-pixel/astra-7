// types.h — shared physics value-types used across kernels, shaders, and
// assertions. Lives here so the future UE5 plugin can consume the same header.
//
// WarpFieldSample is the per-voxel summary produced by warp_field_eval.cu and
// consumed by volume_renderer.cpp + lensing.cpp + cherenkov.cpp. Per DESIGN_SPEC
// Part 2.3.
//
// Plain-old-data (no methods, no virtuals) so the same layout works on both
// host and device.
#pragma once

namespace astra {

struct WarpFieldSample {
    float metric;                 // W(x,t)
    float metric_gradient[3];     // grad W
    float metric_shift;           // gravitational + warp redshift (NOT kinematic Doppler)
    float chaos_intensity;
    float vorticity;
    float ray_deflection[3];      // alpha_lens * grad W * ds contribution per march step
    float cherenkov_angle;        // local Cherenkov cone angle (radians), -1 if inactive
};

} // namespace astra
