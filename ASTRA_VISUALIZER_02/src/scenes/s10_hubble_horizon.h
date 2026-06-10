// s10_hubble_horizon.h - body beyond the Hubble horizon (d > c/H_0) rendered
// FROZEN at the horizon-crossing instant; brightness fades over scenario time.
// Mirrors the canonical §3.12 test in libastra_nexus (assertion already
// passing); this scene gives the operator the visual.
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S10HubbleHorizon final : public IScene {
public:
    const char* id() const override    { return "S10"; }
    const char* label() const override { return "S10  Hubble Horizon"; }
    uint32_t base_regime() const override;

    void prepare_frame(SceneRenderParams& params) override;
    void draw_parameter_panel() override;
    void draw_state_panel() override;

    std::vector<ScalarValueAssertion> value_assertions() const override;

    // Tunables.
    float distance_Gly  = 15.0f;       // body distance in giga-light-years (~Hubble horizon ~13.8 Gly @ H0=70)
    float H0_kmps_per_Mpc = 70.0f;

    // Latched values for state panel.
    double d_proper_m            = 0.0;
    double z_cosmo_v             = 0.0;
    bool   beyond_hubble_horizon = false;
};

} // namespace astra_viz
