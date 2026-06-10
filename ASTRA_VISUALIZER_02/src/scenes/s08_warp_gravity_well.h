// s08_warp_gravity_well.h - WARP_CRUISE composed with GRAVITY_WELL (bitmask 0x28).
// State panel surfaces the canon §3.3 composite regime bitmask, §3.2 Schwarzschild
// factor, §7.1 alpha_eff = alpha_base * (1 + k*M*L^2/r^3) coupling.
// V7 shows the math + bubble + chaos overlay; full BH disc render is V8.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S08WarpGravityWell final : public IScene {
public:
    const char* id() const override    { return "S08"; }
    const char* label() const override { return "S08  Warp + GravityWell"; }
    uint32_t base_regime() const override;

    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    WarpVolumeRequest warp_volume_request() const override {
        return {true, W_now, bubble_radius_m};
    }

    // Tunables.
    float bh_mass_solar  = 1.0e6f;          // 1e6 M_sun supermassive BH
    float r_in_rs_units  = 200.0f;          // ship distance from BH in r_s units
    float L_lengthscale_m = 100.0f;         // L in alpha_eff formula
    float alpha_base     = 1.0f;
    float k_coupling     = 1.0e-3f;
    float W_now          = 1.0f;
    float bubble_radius_m = 80.0f;

    // Latched per-frame for assertions + panels.
    float grav_factor      = 1.0f;
    float alpha_eff        = 1.0f;
    float dtau_dt          = 1.0f;
};

} // namespace astra_viz
