// named_bodies.h - distinguished bodies rendered as fixed billboards in the
// scene. V4 needs a Sun (yellow, fixed colour) and a Planet (colour driven by
// the active scene's redshift tint) at known sky positions so per-scene pixel
// assertions can target them.
//
// Both are screen-projected billboards drawn as 2D quads in clip space; sized
// in degrees so they don't shrink to nothing at any framebuffer resolution.
#pragma once

#include <cstdint>
#include "renderer/graphics_program.h"

namespace astra_viz {

class NamedBodies {
public:
    bool init();
    void shutdown();

    // Pass world-space direction (does NOT need to be unit; we normalise).
    // Body screen-position is `direction projected through view+proj`.
    // tint multiplies the body's base colour (sun=warm yellow, planet=white).
    void draw(const float* view_col_major, const float* proj_col_major,
              const float sun_dir_xyz[3],
              const float planet_dir_xyz[3], const float planet_tint_rgb[3]) const;

private:
    uint32_t vao_ = 0;
    GraphicsProgram prog_;
};

} // namespace astra_viz
