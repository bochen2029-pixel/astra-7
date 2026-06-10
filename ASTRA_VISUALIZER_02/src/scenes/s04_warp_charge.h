// s04_warp_charge.h - warp bubble forms over a configurable charge_duration_s.
// W ramps 0 -> 1 over that window; the volume renderer makes the bubble fade in.
// Regime: WARP_CHARGE during the ramp, WARP_CRUISE after.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S04WarpCharge final : public IScene {
public:
    const char* id() const override    { return "S04"; }
    const char* label() const override { return "S04  Warp Charge"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    WarpVolumeRequest warp_volume_request() const override {
        return {true, W_now, bubble_radius_m};
    }

    float W_now              = 0.0f;
    float charge_duration_s  = 5.0f;
    float bubble_radius_m    = 80.0f;

private:
    float scene_t_s_         = 0.0f;
};

} // namespace astra_viz
