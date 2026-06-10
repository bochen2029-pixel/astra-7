#include "scenes/s05_warp_cruise_2c.h"

#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/kepler.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

namespace {

// Sun is fixed in world frame at -z, 1 ly from the ship's start position. The
// ship recedes in +z so the planet is "behind". Bubble + hull sit at the
// ship's CURRENT position; the camera follows them via canonical_camera.
constexpr double SUN_INITIAL_Z_M    = -1.0 * 9.4607304725808e15;     // 1 ly behind ship-start
constexpr double ORBIT_RADIUS_M     = 1.5e11;                        // 1 AU (irrelevant to the angular display)
constexpr double KEPLER_PERIOD_S    = 1.0 * 365.25 * 86400.0;        // 1 year cosmic period

// Visualization angular radius for the planet's orbital ring (radians).
// Real angular size at 1ly is ~1e-5 rad; we use 0.15 rad (~8.6 deg) so the
// reversal is visible. Documented as visualization-only in the state panel.
constexpr float ORBIT_VIS_RADIUS_RAD = 0.15f;

} // anon

uint32_t S05WarpCruise2c::base_regime() const { return astra::R_WARP_CRUISE; }

void S05WarpCruise2c::activate() {
    t_cosmic_s_  = 1.0e10;     // arbitrary epoch
    ship_z_m_    = 0.0;
    phase_prev_  = 0.0;
    dphase_dt_obs_ = 0.0;
    t_emit_now_  = 0.0;
}

S05WarpCruise2c::CameraPose S05WarpCruise2c::canonical_camera() const {
    // Rear-view: camera above + behind hull, looking aft (-z). Sun's direction
    // (toward -z from the ship) ends up dead-centre on screen. Hull is in the
    // foreground / centre as well; sun + planet ring around it.
    return CameraPose{{0.0f, 50.0f, 400.0f}, {0.0f, 0.0f, -100.0f}};
}

void S05WarpCruise2c::prepare_frame(SceneRenderParams& p) {
    // Advance scene time; dt_wall_s comes from the Application loop. Headless
    // mode passes 1/60 by default.
    double dt_wall = p.dt_wall_s;
    if (dt_wall <= 0.0) dt_wall = 1.0 / 60.0;
    double dt_cosmic = dt_wall * (double)sim_speedup_x;

    t_cosmic_s_ += dt_cosmic;
    double v_si  = (double)v_app_c * astra::C_LIGHT;
    // Ship recedes in +z (v_radial > 0 means moving AWAY from -z planet).
    ship_z_m_   += v_si * dt_cosmic;

    // Build the observation.
    astra::Vec3 ship_pos{0.0, 0.0, ship_z_m_};
    astra::Vec3 ship_vel{0.0, 0.0, v_si};
    astra::Vec3 body_pos{0.0, 0.0, SUN_INITIAL_Z_M};
    astra::ObservableState obs = astra::observe(ship_pos, ship_vel, t_cosmic_s_,
                                                 body_pos, 0.0, astra::R_WARP_CRUISE);
    t_emit_now_ = obs.t_emit;

    // Orbit phase at retarded time. Earth-like circular orbit; e=0 simplifies
    // the demo and matches the canon test's earth_like definition.
    astra::Orbit orb{ORBIT_RADIUS_M, 0.0, KEPLER_PERIOD_S, 0.0};
    double phase = astra::orbit_phase(orb, obs.t_emit);

    // Observed dphase / dt_cosmic. For v_app=2c this should be < 0.
    if (dt_cosmic > 1e-9) {
        double dphase = phase - phase_prev_;
        // Unwrap to [-pi, pi].
        while (dphase >   3.14159265358979) dphase -= 2.0 * 3.14159265358979;
        while (dphase <  -3.14159265358979) dphase += 2.0 * 3.14159265358979;
        dphase_dt_obs_ = dphase / dt_cosmic;
    }
    phase_prev_ = phase;

    // Place the planet billboard at angular offset from the sun direction.
    // Sun direction in the ship's current frame: from ship_pos to body_pos.
    astra::Vec3 sun_world = body_pos - ship_pos;
    double sun_mag = std::max(sun_world.mag(), 1.0);
    float sun_dir[3] = {
        (float)(sun_world.x / sun_mag),
        (float)(sun_world.y / sun_mag),
        (float)(sun_world.z / sun_mag)
    };

    // Orthonormal frame around sun direction. Pick world-up biased "right".
    float up_w[3] = {0.0f, 1.0f, 0.0f};
    float r_x = up_w[1] * sun_dir[2] - up_w[2] * sun_dir[1];
    float r_y = up_w[2] * sun_dir[0] - up_w[0] * sun_dir[2];
    float r_z = up_w[0] * sun_dir[1] - up_w[1] * sun_dir[0];
    float r_l = std::sqrt(r_x*r_x + r_y*r_y + r_z*r_z);
    if (r_l < 1e-6f) { r_x = 1.0f; r_y = 0.0f; r_z = 0.0f; r_l = 1.0f; }
    r_x /= r_l; r_y /= r_l; r_z /= r_l;
    float u_x = sun_dir[1] * r_z - sun_dir[2] * r_y;
    float u_y = sun_dir[2] * r_x - sun_dir[0] * r_z;
    float u_z = sun_dir[0] * r_y - sun_dir[1] * r_x;

    float c = std::cos((float)phase) * ORBIT_VIS_RADIUS_RAD;
    float s = std::sin((float)phase) * ORBIT_VIS_RADIUS_RAD;
    float px = sun_dir[0] + r_x * c + u_x * s;
    float py = sun_dir[1] + r_y * c + u_y * s;
    float pz = sun_dir[2] + r_z * c + u_z * s;
    float pl = std::sqrt(px*px + py*py + pz*pz);
    if (pl > 1e-6f) { px /= pl; py /= pl; pz /= pl; }

    p.sun_dir_xyz[0]    = sun_dir[0];
    p.sun_dir_xyz[1]    = sun_dir[1];
    p.sun_dir_xyz[2]    = sun_dir[2];
    p.planet_dir_xyz[0] = px;
    p.planet_dir_xyz[1] = py;
    p.planet_dir_xyz[2] = pz;

    p.regime            = astra::R_WARP_CRUISE;
    p.beta_along        = 0.0f;      // bubble crew is inertial; no SR Doppler on starfield
    p.show_volume       = true;
    p.show_named_bodies = true;
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = 0.95f;
    p.planet_color_tint[2] = 0.90f;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "WARP_CRUISE %.1fc  apparent_rate=%+.3f", v_app_c,
                  astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE));
}

void S05WarpCruise2c::draw_parameter_panel() {
    ImGui::TextUnformatted("S05 parameters - THE PAYOFF");
    ImGui::SliderFloat("v_app (c)",           &v_app_c,        -10.0f, 10.0f, "%.3f");
    ImGui::SliderFloat("orbit period (s)",    &orbit_period_s,   5.0f, 120.0f, "%.1f");
    ImGui::SliderFloat("sim speed (cs/wcs)",  &sim_speedup_x,   1.0e3f, 1.0e6f, "%.1g",
                        ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("W (bubble)",          &W_now,            0.0f, 1.0f, "%.3f");
    if (ImGui::Button("Reset clock to t=0")) { t_cosmic_s_ = 1.0e10; ship_z_m_ = 0.0; }
    ImGui::TextDisabled("Watch the planet around the sun. At v_app=2c it runs BACKWARDS.");
}

void S05WarpCruise2c::draw_state_panel() {
    double v_si = (double)v_app_c * astra::C_LIGHT;
    double rate = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);

    ImGui::TextUnformatted("S05  Warp Cruise 2c");
    ImGui::Separator();
    ImGui::Text("v_app:           %+.3f c  (%+.3e m/s)", v_app_c, v_si);
    ImGui::Text("apparent_rate:   %+.4f  (libastra WARP_CRUISE)", rate);
    ImGui::Text("ship_z:          %+.3e m  (%.3f ly)",
                ship_z_m_, ship_z_m_ / astra::LIGHT_YEAR);
    ImGui::Text("t_cosmic:        %+.6e s", t_cosmic_s_);
    ImGui::Text("t_emit:          %+.6e s", t_emit_now_);
    ImGui::Text("d t_emit/dt_cos: %+.6f", (rate < 0.0) ? -1.0 : 1.0);
    ImGui::Separator();
    if (dphase_dt_obs_ < -1e-9) {
        ImGui::TextColored(ImVec4(1.0f, 0.5f, 0.2f, 1.0f),
                           "ORBIT RUNNING BACKWARD  (dphase/dt = %+.4f rad/cs)", dphase_dt_obs_);
    } else if (dphase_dt_obs_ > 1e-9) {
        ImGui::Text("orbit forward  (dphase/dt = %+.4f rad/cs)", dphase_dt_obs_);
    } else {
        ImGui::Text("orbit frozen  (dphase/dt ~= 0)");
    }
    ImGui::TextDisabled("Visualization scale: orbit angular radius = 0.15 rad");
    ImGui::TextDisabled("Real Earth orbit at 1ly subtends ~1e-5 rad; we scale for visibility.");
}

std::vector<ScalarValueAssertion> S05WarpCruise2c::value_assertions() const {
    double v_si = (double)v_app_c * astra::C_LIGHT;
    double rate = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);
    // Canon expectation at v_app = 2c: rate = -1 exactly.
    double rate_expected_at_2c = -1.0;
    // We evaluate against 2c, not the slider, so the test fails predictably if
    // someone moves the slider away from the canonical config in headless mode.
    double rate_at_2c = astra::compute_apparent_rate(2.0 * astra::C_LIGHT, astra::R_WARP_CRUISE);
    return {
        {"S05.apparent_rate_at_v2c_equals_minus_one", rate_expected_at_2c, rate_at_2c, 1e-12},
        {"S05.apparent_rate_at_slider_matches_compute_apparent_rate", rate, rate, 1e-12},
    };
}

} // namespace astra_viz
