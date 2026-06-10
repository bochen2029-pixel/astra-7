// src/renderer/starfield_renderer.h — 10K NDC point-sprite starfield with
// optional Doppler color shift applied per-fragment via uniform z_kin.

#pragma once

#include <cstdint>

namespace astra::renderer {

class StarfieldRenderer {
public:
    bool setup(int count = 10000, uint32_t seed = 0xA57DA7U);
    void teardown();

    // Renders the starfield. z_kin > 0 redshifts star colors via
    // physics::apply_kin_redshift in the FS.
    void render(float z_kin);

private:
    uint32_t program_  = 0;
    uint32_t vao_      = 0;
    uint32_t vbo_      = 0;
    int      count_    = 0;
    int      loc_z_kin_ = -1;
};

}  // namespace astra::renderer
