// s07_photon_source_history.h - star with explicit `t_source_start` (epoch at
// which the body began emitting). Ship pulls away at high v_app; at some
// cosmic time the retarded t_emit < t_source_start, observe() flips
// beyond_photon_history to true, and the star DISAPPEARS from the frame.
// Per spec §3.11 + AUDIT R4 (provisional schema for t_source_start).
//
// Discrete disappearance (not a fade) is the demonstrable effect: frame N
// shows the star, frame N+1 omits it.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S07PhotonSourceHistory final : public IScene {
public:
    const char* id() const override    { return "S07"; }
    const char* label() const override { return "S07  PhotonSourceHistory"; }
    uint32_t base_regime() const override;

    void activate() override;
    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    // Scene tunables.
    float v_app_c                 = 8000.0f;
    float t_source_start_relative_yr = -1.0e9f;    // body started emitting 1 Gy before scenario t=0
    float sim_speedup_x           = 1.0e15f;       // very fast: covers Gyr in seconds wall-time

    // Latched values for the state panel + assertions.
    bool   beyond_photon_history = false;
    double t_cosmic_s            = 0.0;
    double t_emit_s              = 0.0;
    double body_t_source_start_s = -1.0e16;
};

} // namespace astra_viz
