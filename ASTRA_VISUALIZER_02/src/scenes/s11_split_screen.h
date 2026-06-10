// s11_split_screen.h - side-by-side STL_REL vs WARP_CRUISE at the same
// v_radial proves the regime-dispatched apparent_rate formula is real, not
// rendering noise. Per spec §3.11 + DESIGN_SPEC scene S11.
//
// Drives TWO SceneRenderParams (left + right) via accessors the Application
// loop calls during its split-screen path; the standard prepare_frame fills
// in the params shared between both halves (camera, starfield).
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S11SplitScreen final : public IScene {
public:
    const char* id() const override    { return "S11"; }
    const char* label() const override { return "S11  STL vs WARP split"; }
    uint32_t base_regime() const override;

    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    // The Application loop reads these to fill the per-half SceneRenderParams.
    void fill_left_half(SceneRenderParams& p) const;
    void fill_right_half(SceneRenderParams& p) const;

    bool fill_split_screen(SceneRenderParams& left,
                            SceneRenderParams& right) const override {
        fill_left_half(left);
        fill_right_half(right);
        return true;
    }

    // Tunables.
    float v_radial_c = 0.5f;
};

} // namespace astra_viz
