#include "scenes/s12_eye_ear_decoupling.h"

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
constexpr double SUN_INITIAL_Z_M  = -1.0 * 9.4607304725808e15;     // 1 ly behind ship-start
constexpr double KEPLER_PERIOD_S  = astra::SECONDS_PER_YEAR;
constexpr double ORBIT_RADIUS_M   = 1.5e11;
constexpr float  ORBIT_VIS_RAD    = 0.15f;
} // anon

uint32_t S12EyeEarDecoupling::base_regime() const { return astra::R_WARP_CRUISE; }

void S12EyeEarDecoupling::activate() {
    t_cosmic_s_ = 1.0e10;
    ship_z_m_   = 0.0;
    warp_engaged = true;
    t_emit_now_ = 0.0;
}

S12EyeEarDecoupling::CameraPose S12EyeEarDecoupling::canonical_camera() const {
    return CameraPose{{0.0f, 50.0f, 400.0f}, {0.0f, 0.0f, -100.0f}};
}

void S12EyeEarDecoupling::prepare_frame(SceneRenderParams& p) {
    double dt_wall = p.dt_wall_s;
    if (dt_wall <= 0.0) dt_wall = 1.0 / 60.0;
    double dt_cosmic = dt_wall * (double)sim_speedup_x;
    t_cosmic_s_ += dt_cosmic;

    double v_si = warp_engaged ? ((double)v_app_c * astra::C_LIGHT) : 0.0;
    ship_z_m_   += v_si * dt_cosmic;

    astra::Vec3 ship_pos{0.0, 0.0, ship_z_m_};
    astra::Vec3 ship_vel{0.0, 0.0, v_si};
    astra::Vec3 body_pos{0.0, 0.0, SUN_INITIAL_Z_M};
    uint32_t regime = warp_engaged ? astra::R_WARP_CRUISE : astra::R_REST;
    astra::ObservableState obs = astra::observe(ship_pos, ship_vel, t_cosmic_s_,
                                                 body_pos, 0.0, regime);
    t_emit_now_ = obs.t_emit;

    astra::Orbit orb{ORBIT_RADIUS_M, 0.0, KEPLER_PERIOD_S, 0.0};
    double phase = astra::orbit_phase(orb, obs.t_emit);

    // Place planet billboard on a ring around the sun direction.
    astra::Vec3 sun_world = body_pos - ship_pos;
    double sun_mag = std::max(sun_world.mag(), 1.0);
    float sun_dir[3] = { (float)(sun_world.x / sun_mag),
                          (float)(sun_world.y / sun_mag),
                          (float)(sun_world.z / sun_mag) };
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
    float c = std::cos((float)phase) * ORBIT_VIS_RAD;
    float s = std::sin((float)phase) * ORBIT_VIS_RAD;
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

    p.regime            = regime;
    p.beta_along        = 0.0f;
    p.show_volume       = warp_engaged;
    p.show_named_bodies = true;
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = 0.95f;
    p.planet_color_tint[2] = 0.90f;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "%s  audio=%.0fHz  t_emit=%+.3e",
                  warp_engaged ? "WARP_CRUISE" : "REST (warp shutdown)",
                  warp_engaged ? audio_freq_warp_drone : audio_freq_shutdown,
                  t_emit_now_);
}

void S12EyeEarDecoupling::draw_parameter_panel() {
    ImGui::TextUnformatted("S12 parameters - book-canon scene");
    ImGui::SliderFloat("v_app (c)",         &v_app_c,           0.0f, 10.0f, "%.3f");
    ImGui::SliderFloat("sim speed (cs/wcs)", &sim_speedup_x, 1.0e3f, 1.0e6f, "%.1g",
                        ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("audio drone (Hz)",  &audio_freq_warp_drone, 50.0f, 2000.0f, "%.0f");
    ImGui::SliderFloat("audio shutdown (Hz)", &audio_freq_shutdown, 30.0f,  500.0f, "%.0f");
    if (warp_engaged) {
        if (ImGui::Button("Disengage warp (emergency)")) {
            warp_engaged = false;
        }
    } else {
        if (ImGui::Button("Re-engage warp")) { warp_engaged = true; }
    }
    if (ImGui::Button("Reset clock to t=0")) {
        t_cosmic_s_ = 1.0e10; ship_z_m_ = 0.0; warp_engaged = true;
    }
}

void S12EyeEarDecoupling::draw_state_panel() {
    ImGui::TextUnformatted("S12  Eye-Ear Decoupling");
    ImGui::Separator();
    ImGui::Text("AUDIO (t_cosmic = NOW):");
    ImGui::TextColored(ImVec4(0.55f, 0.85f, 1.0f, 1.0f),
                       "  %.0f Hz  (%s)",
                       warp_engaged ? audio_freq_warp_drone : audio_freq_shutdown,
                       warp_engaged ? "warp drone" : "shutdown drone");
    ImGui::Spacing();
    ImGui::Text("VISUAL (t_emit, retarded):");
    ImGui::TextColored(ImVec4(1.0f, 0.65f, 0.35f, 1.0f),
                       "  t_emit = %+.6e s", t_emit_now_);
    ImGui::Text("  t_cosmic - t_emit  = %.4e s",
                t_cosmic_s_ - t_emit_now_);
    ImGui::Separator();
    if (!warp_engaged) {
        ImGui::TextColored(ImVec4(1.0f, 0.5f, 0.2f, 1.0f),
                           "WARP DISENGAGED at audio_t=NOW; visual_t lags by light-travel-time.");
    } else {
        ImGui::TextDisabled("Press Disengage warp to see audio snap + visual lag.");
    }
    ImGui::TextDisabled("This scene makes book CANON.md cycle-1 endogenous/exogenous literal.");
}

std::vector<ScalarValueAssertion> S12EyeEarDecoupling::value_assertions() const {
    // The headless test verifies the canonical observation arithmetic: at 1 ly
    // recession with WARP at v_app=2c, t_emit < t_cosmic by ~1 lookback period.
    astra::Vec3 ship{0, 0, 0};
    astra::Vec3 vel{0, 0, 2.0 * astra::C_LIGHT};
    astra::Vec3 body{0, 0, -1.0 * astra::LIGHT_YEAR};
    astra::ObservableState obs = astra::observe(ship, vel, 1.0e10, body, 0.0, astra::R_WARP_CRUISE);
    double lookback_expected = astra::LIGHT_YEAR / astra::C_LIGHT;     // ~1 yr at 1 ly
    double lookback_observed = 1.0e10 - obs.t_emit;
    return {
        {"S12.t_emit_lags_t_cosmic_by_lookback",
         lookback_expected, lookback_observed, lookback_expected * 0.01},
        {"S12.apparent_rate_reversed_during_warp_v2c",
         -1.0,
         astra::compute_apparent_rate(2.0 * astra::C_LIGHT, astra::R_WARP_CRUISE),
         1e-12},
    };
}

} // namespace astra_viz
