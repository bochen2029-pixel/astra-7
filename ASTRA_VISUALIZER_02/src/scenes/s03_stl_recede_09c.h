// s03_stl_recede_09c.h - STL_REL at beta=0.9. Dramatic SR Doppler + aberration.
// apparent_rate = sqrt(0.1/1.9) ~ 0.2294; gamma = cosh(atanh(0.9)) ~ 2.294.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S03StlRecede09c final : public IScene {
public:
    const char* id() const override    { return "S03"; }
    const char* label() const override { return "S03  STL Recede 0.9c"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;
    std::vector<ScalarPixelAssertion> pixel_assertions(int fb_w, int fb_h) const override;

private:
    float beta_ = 0.9f;
};

} // namespace astra_viz
