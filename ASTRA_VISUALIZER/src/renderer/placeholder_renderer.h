// src/renderer/placeholder_renderer.h — colored NDC quad renderer shared by
// S01 (REST) + S02/S03 (Doppler) scenes.
//
// Renders a list of `Placeholder { ndc_xy, half_extent, RGB }` items. The
// fragment shader applies a uniform kin-redshift z to each placeholder's
// color, so the same renderer drives the rest scene (z=0) and the
// relativistic recede scenes (z > 0).

#pragma once

#include <cstdint>
#include <vector>

namespace astra::renderer {

struct Placeholder {
    const char* short_name;
    float ndc_x, ndc_y;
    float half_extent;     // NDC half-extent
    float r, g, b;         // unshifted RGB
};

class PlaceholderRenderer {
public:
    bool setup();
    void teardown();

    // Render all placeholders at the current viewport, applying `z_kin`
    // per-pixel through `physics::apply_kin_redshift` in the FS.
    void render(int viewport_width,
                int viewport_height,
                const std::vector<Placeholder>& placeholders,
                float z_kin);

private:
    uint32_t program_  = 0;
    uint32_t vao_      = 0;
    uint32_t vbo_      = 0;
    int loc_scale_  = -1;
    int loc_offset_ = -1;
    int loc_color_  = -1;
    int loc_aspect_ = -1;
    int loc_z_kin_  = -1;
};

}  // namespace astra::renderer
