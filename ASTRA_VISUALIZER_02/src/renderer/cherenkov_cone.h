// cherenkov_cone.h - geometric cone billboard rendered around the warp bubble
// at the half-angle returned by libastra::compute_cherenkov_angle(W, beta).
//
// V6 implementation: a procedurally-generated cone mesh with apex at the
// bubble's leading edge, axis along ship velocity, half-angle from libastra.
// Translucent cyan tint per spec §6 step 10 (Cherenkov cone aesthetic). When
// `compute_cherenkov_angle` returns -1 (n*beta <= 1 inactive), draw() is a no-op.
#pragma once

#include <cstdint>
#include "renderer/graphics_program.h"

namespace astra_viz {

class CherenkovCone {
public:
    bool init(int radial_segments = 48);
    void shutdown();

    // half_angle_rad < 0 means "Cherenkov inactive" - draw nothing.
    // axis_dir is the unit vector the cone opens around (ship velocity).
    // apex_world is the world-space position of the cone tip.
    // length_m sets how far the cone extends along the axis.
    void draw(const float* view_col_major, const float* proj_col_major,
              float half_angle_rad,
              const float axis_dir_xyz[3],
              const float apex_world_xyz[3],
              float length_m) const;

private:
    uint32_t vao_     = 0;
    uint32_t vbo_     = 0;
    uint32_t ebo_     = 0;
    int      n_indices_ = 0;
    GraphicsProgram prog_;
};

} // namespace astra_viz
