// wake_trail.h - warp wake (P3 per DESIGN_SPEC). Maintains a ring buffer of
// the ship's recent world-space positions and renders them as a billboard
// strip that fades with age. Cheap; no physics, just visual continuity to
// show "the ship was just there" during warp egress and inter-scene motion.
#pragma once

#include <cstdint>
#include <vector>
#include "renderer/graphics_program.h"

namespace astra_viz {

class WakeTrail {
public:
    bool init(int max_points = 256);
    void shutdown();

    // Push a new ship position; trail oldest entry drops when buffer full.
    void push_sample(const float xyz[3]);

    // Reset the buffer (e.g. on scene activate).
    void clear();

    // Renders the trail as additive line strip with vertex-age fade.
    void draw(const float* view_col_major, const float* proj_col_major) const;

    int point_count() const { return (int)points_.size(); }

private:
    int max_points_ = 0;
    std::vector<float> points_;       // xyz per point, oldest at index 0
    uint32_t vao_ = 0;
    uint32_t vbo_ = 0;
    GraphicsProgram prog_;
    mutable bool dirty_ = true;
};

} // namespace astra_viz
