// s12_eye_ear_decoupling.h - book-canon scene: at warp egress, AUDIO frequency
// (rendered as UI numeric, no playback) snaps to the shutdown drone immediately
// while the VISUAL planet position continues at the retarded t_emit until
// light catches up. The endogenous-vs-exogenous gap made literal.
//
// Per spec §6.3 + §8.3; book CANON.md cycle 1.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S12EyeEarDecoupling final : public IScene {
public:
    const char* id() const override    { return "S12"; }
    const char* label() const override { return "S12  Eye-Ear Decoupling"; }
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

    // Volume.
    float W_now = 1.0f;
    float bubble_radius_m = 80.0f;

    // Scene controls.
    float v_app_c          = 2.0f;
    float sim_speedup_x    = 86400.0f;
    bool  warp_engaged     = true;     // toggled by "Disengage warp" button
    float audio_freq_warp_drone = 247.0f;       // Hz; "operating" sound
    float audio_freq_shutdown   = 65.0f;        // Hz; immediate-snap target on disengage

private:
    double t_cosmic_s_ = 0.0;
    double ship_z_m_   = 0.0;
    double t_emit_now_ = 0.0;
};

} // namespace astra_viz
