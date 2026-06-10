// s01_rest_baseline.h - sanity render at REST regime. Hull + starfield + sun +
// planet visible with no Doppler / no aberration / no warp. Assertions cover
// the libastra REST identity (gamma=1, dtau/dt=1).
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S01RestBaseline final : public IScene {
public:
    const char* id() const override    { return "S01"; }
    const char* label() const override { return "S01  RestBaseline"; }
    uint32_t base_regime() const override;

    void prepare_frame(SceneRenderParams& params) override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;
    std::vector<ScalarPixelAssertion> pixel_assertions(int fb_w, int fb_h) const override;
};

} // namespace astra_viz
