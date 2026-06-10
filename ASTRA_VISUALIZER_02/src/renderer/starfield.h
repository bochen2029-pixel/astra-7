// starfield.h - 10K-star backdrop. Procedurally generated at init; rendered as
// point sprites with per-star colour from blackbody. Stays VERY simple in V1:
// no Doppler (V2-V4 will add that via libastra_nexus call).
#pragma once

#include <cstdint>
#include "renderer/graphics_program.h"

namespace astra_viz {

class Starfield {
public:
    // Default seed reads "A57A4007" in hex (mnemonic: ASTRA-7); arbitrary but
    // locked so the golden PNGs reproduce bit-for-bit across runs.
    bool init(int n_stars = 10000, uint32_t seed = 0xA57A4007u);
    void shutdown();

    // ship_vel_dir is a unit vector in world space; beta in [-0.9999, 0.9999].
    // beta == 0 short-circuits to the V1 baseline (no aberration, no Doppler tint).
    void draw(const float* view_col_major, const float* proj_col_major,
              const float ship_vel_dir_xyz[3], float beta) const;

    int star_count() const { return n_stars_; }

private:
    uint32_t vao_ = 0;
    uint32_t vbo_ = 0;
    int n_stars_ = 0;
    GraphicsProgram prog_;
};

} // namespace astra_viz
