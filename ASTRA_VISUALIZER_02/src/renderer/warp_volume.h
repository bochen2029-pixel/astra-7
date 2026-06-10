// warp_volume.h - host-side owner of the V5 warp-bubble volume renderer.
// Re-uses the V3 GL-3D-texture + cudaGraphicsGLRegisterImage interop pattern
// (proven in test_volume); kernel now writes the warp metric W(x) instead of
// the trivial sphere-wave pattern.
#pragma once

#include <cstdint>
#include "kernels/warp_field.cuh"
#include "renderer/graphics_program.h"

struct cudaGraphicsResource;

namespace astra_viz {

class WarpVolume {
public:
    bool init(int resolution = 128, float world_half_extent = 150.0f);
    void shutdown();

    // Updates the warp metric texture by launching warp_field_kernel.
    void update(const WarpFieldParams& params);

    // Renders the volume via fullscreen-quad ray-march.
    void draw(const float* view_col_major, const float* proj_col_major,
              const float* camera_pos_xyz) const;

    int   resolution() const       { return resolution_; }
    float world_half_extent() const { return world_half_extent_; }

private:
    int   resolution_       = 0;
    float world_half_extent_ = 0.0f;

    uint32_t gl_tex_  = 0;
    uint32_t vao_     = 0;
    GraphicsProgram raymarch_prog_;

    cudaGraphicsResource* cuda_res_ = nullptr;
};

} // namespace astra_viz
