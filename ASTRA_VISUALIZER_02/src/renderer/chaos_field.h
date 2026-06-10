// chaos_field.h - Fisher-KPP scalar field renderer. Owns 2 GL 3D textures
// + CUDA-GL ping-pong so the kernel reads from one and writes to the other
// each step. Display path samples the most-recently-written texture.
//
// The "centre amplitude" readback gives the Reflex PID stub a cheap proxy
// for max(chi) without a full GPU reduction. Good enough for V7's feedback
// demo; V8+ can swap in a real reduction if precision matters.
#pragma once

#include <cstdint>
#include "renderer/graphics_program.h"
#include "kernels/chaos_pde.cuh"

struct cudaGraphicsResource;

namespace astra_viz {

class ChaosField {
public:
    bool init(int resolution = 128, float world_half_extent = 150.0f);
    void shutdown();

    // Re-seeds the CURRENT (front) texture with a centred Gaussian (amp peak,
    // sigma in voxels). Other texture left as-is; will be overwritten by next step.
    void seed(float amp = 0.6f, float sigma_voxels = 8.0f);

    // Forward-Euler step (kernel reads front, writes back, swaps). All
    // parameters per ChaosPDEParams.
    void step(const ChaosPDEParams& p);

    // Clears BOTH textures to zero. Used by emergency-dump in S09.
    void clear();

    // Cheap proxy for max(chi): reads the centre voxel via cudaMemcpy3D.
    // Returns the value in [0, 1]; -1.0 if read fails. ~10 microseconds.
    float read_centre_amplitude();

    // Ray-marches the front texture; heat colormap (deep purple -> red -> yellow).
    void draw(const float* view_col_major, const float* proj_col_major,
              const float* camera_pos_xyz) const;

    int resolution() const { return resolution_; }

private:
    int   resolution_       = 0;
    float world_half_extent_ = 0.0f;

    uint32_t gl_tex_[2]      = {0, 0};
    cudaGraphicsResource* cuda_res_[2] = {nullptr, nullptr};
    int current_             = 0;        // index of the texture holding the most-recent state

    uint32_t vao_ = 0;
    GraphicsProgram raymarch_prog_;

    bool create_texture(int idx);
};

} // namespace astra_viz
