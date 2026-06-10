// s06_warp_cruise_10c_cherenkov.h - extends S05 with v_app=10c (so the orbit
// reverses at 9x speed) AND a Cherenkov cone visualized at the angle returned
// by libastra::compute_cherenkov_angle(W, beta). Closes AUDIT 5D-F4 at the
// VISUAL level (V0 closed it at the math level; this scene shows the cone).
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S06WarpCruise10cCherenkov final : public IScene {
public:
    const char* id() const override    { return "S06"; }
    const char* label() const override { return "S06  Warp Cruise 10c + Cherenkov"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    CameraPose canonical_camera() const override;

    WarpVolumeRequest warp_volume_request() const override {
        return {true, W_now, bubble_radius_m};
    }
    CherenkovOverlay  cherenkov_overlay()   const override {
        CherenkovOverlay c{};
        c.active         = cherenkov_angle_rad >= 0.0f;
        c.half_angle_rad = cherenkov_angle_rad;
        c.axis_xyz[0]    = ship_axis_xyz[0];
        c.axis_xyz[1]    = ship_axis_xyz[1];
        c.axis_xyz[2]    = ship_axis_xyz[2];
        c.apex_xyz[0]    = cone_apex_xyz[0];
        c.apex_xyz[1]    = cone_apex_xyz[1];
        c.apex_xyz[2]    = cone_apex_xyz[2];
        c.length_m       = cone_length_m;
        return c;
    }

    float W_now           = 1.0f;
    float bubble_radius_m = 80.0f;
    float cone_length_m   = 220.0f;

    // Scene tunables.
    float v_app_c         = 10.0f;
    float sim_speedup_x   = 86400.0f;

    // Latched per-frame values for the application loop and assertions.
    float cherenkov_angle_rad = -1.0f;   // < 0 = inactive
    float ship_axis_xyz[3]    = {0.0f, 0.0f, 1.0f};
    float cone_apex_xyz[3]    = {0.0f, 0.0f, 0.0f};
};

} // namespace astra_viz
