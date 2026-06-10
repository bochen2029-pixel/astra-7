// s02_stl_recede_05c.h - STL_REL regime at beta = 0.5 receding. Demonstrates
// SR longitudinal Doppler + mild aberration. apparent_rate = sqrt(1/3) ~ 0.5774.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S02StlRecede05c final : public IScene {
public:
    const char* id() const override    { return "S02"; }
    const char* label() const override { return "S02  STL Recede 0.5c"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;
    std::vector<ScalarPixelAssertion> pixel_assertions(int fb_w, int fb_h) const override;

private:
    float beta_ = 0.5f;       // along ship's +z forward direction
};

} // namespace astra_viz
