// s05_warp_cruise_2c.h - THE PAYOFF. WARP_CRUISE at v_app=2c; a Kepler-orbiting
// planet is rendered at orbit_phase(orb, t_emit). Operator personally watches
// the orbit run BACKWARD - non-negotiable sign-off requirement per CLAUDE.md §3.2.
//
// Implementation: scene tracks its own t_cosmic_s + ship_z (advanced each frame
// at v_radial). observe() returns t_emit; orbit_phase(orb, t_emit) gives the
// planet's angular position. The planet billboard is offset from a fixed sun
// direction by a small angular orbit radius (visualization scale; the actual
// orbit is 1 AU but at 1 ly it would subtend <0.001 deg - too small to see).
#pragma once

#include "scenes/scene_base.h"

namespace astra_viz {

class S05WarpCruise2c final : public IScene {
public:
    const char* id() const override    { return "S05"; }
    const char* label() const override { return "S05  Warp Cruise 2c"; }
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

    float W_now           = 1.0f;
    float bubble_radius_m = 80.0f;

    // Tunables.
    float v_app_c        = 2.0f;        // ship recession speed in units of c
    float orbit_period_s = 30.0f;       // wallclock seconds for one orbit (compressed)
    float sim_speedup_x  = 86400.0f;    // cosmic seconds per wallclock second; 1 day/sec default

private:
    double t_cosmic_s_     = 0.0;
    double ship_z_m_       = 0.0;       // ship's current world z (negative if v_app > 0 receding from -z planet)
    double phase_prev_     = 0.0;       // last orbit phase, used by the "phase running backward" assertion
    double dphase_dt_obs_  = 0.0;       // observed dphase / dt (rad / cosmic-second)
    double t_emit_now_     = 0.0;
};

} // namespace astra_viz
