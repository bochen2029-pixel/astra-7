#include "scenes/s07_photon_source_history.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

namespace {

// Star sits at -z, 1 ly behind ship-start. Ship moves +z. Wide enough range
// that the observation evolves over the scene's runtime.
constexpr double STAR_INITIAL_Z_M = -1.0 * 9.4607304725808e15;     // 1 ly behind ship-start

} // anon

uint32_t S07PhotonSourceHistory::base_regime() const { return astra::R_WARP_CRUISE; }

void S07PhotonSourceHistory::activate() {
    t_cosmic_s = 0.0;
    t_emit_s   = 0.0;
    beyond_photon_history = false;
    body_t_source_start_s = (double)t_source_start_relative_yr * astra::SECONDS_PER_YEAR;
}

void S07PhotonSourceHistory::prepare_frame(SceneRenderParams& p) {
    double dt_wall = p.dt_wall_s;
    if (dt_wall <= 0.0) dt_wall = 1.0 / 60.0;
    double dt_cosmic = dt_wall * (double)sim_speedup_x;
    t_cosmic_s += dt_cosmic;

    // Re-resolve from slider in case the operator nudged it.
    body_t_source_start_s = (double)t_source_start_relative_yr * astra::SECONDS_PER_YEAR;

    double v_si = (double)v_app_c * astra::C_LIGHT;
    astra::Vec3 ship_pos{0.0, 0.0, v_si * t_cosmic_s};
    astra::Vec3 ship_vel{0.0, 0.0, v_si};
    astra::Vec3 body_pos{0.0, 0.0, STAR_INITIAL_Z_M};
    astra::ObservableState obs = astra::observe(
        ship_pos, ship_vel, t_cosmic_s, body_pos, 0.0, astra::R_WARP_CRUISE,
        body_t_source_start_s);

    t_emit_s = obs.t_emit;
    beyond_photon_history = obs.beyond_photon_history;

    p.regime         = astra::R_WARP_CRUISE;
    p.beta_along     = 0.0f;
    p.show_volume    = true;
    p.show_named_bodies = !beyond_photon_history;   // discrete disappearance
    p.planet_dir_xyz[0] = 0.0f;
    p.planet_dir_xyz[1] = 0.0f;
    p.planet_dir_xyz[2] = -1.0f;
    p.sun_dir_xyz[0]    = 0.3f;
    p.sun_dir_xyz[1]    = 0.0f;
    p.sun_dir_xyz[2]    = -1.0f;
    // Bright white star tint until the photon-history bound kicks in; then off.
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = 0.95f;
    p.planet_color_tint[2] = 0.85f;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "WARP_CRUISE %.0fc  %s", v_app_c,
                  beyond_photon_history ? "[STAR ABSENT: beyond_photon_history]"
                                         : "[star visible]");
}

void S07PhotonSourceHistory::draw_parameter_panel() {
    ImGui::TextUnformatted("S07 parameters");
    ImGui::SliderFloat("v_app (c)",                  &v_app_c, 100.0f, 50000.0f, "%.0f");
    ImGui::SliderFloat("t_source_start (yr from t0)",
                       &t_source_start_relative_yr, -1.0e10f, 0.0f, "%.2g",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("sim speed (cs/wcs)",  &sim_speedup_x, 1.0e12f, 1.0e16f, "%.1g",
                        ImGuiSliderFlags_Logarithmic);
    if (ImGui::Button("Reset clock to t=0")) {
        t_cosmic_s = 0.0;
        beyond_photon_history = false;
    }
    if (beyond_photon_history) {
        ImGui::TextColored(ImVec4(1.0f, 0.5f, 0.2f, 1.0f),
                           "beyond_photon_history = TRUE - star absent");
    }
}

void S07PhotonSourceHistory::draw_state_panel() {
    ImGui::TextUnformatted("S07  PhotonSourceHistory");
    ImGui::Separator();
    ImGui::Text("v_app:               %.0f c", v_app_c);
    ImGui::Text("t_cosmic:            %+.6e s",      t_cosmic_s);
    ImGui::Text("t_emit:              %+.6e s",      t_emit_s);
    ImGui::Text("body_t_source_start: %+.6e s  (%.2g yr)",
                body_t_source_start_s, (double)t_source_start_relative_yr);
    ImGui::Separator();
    if (beyond_photon_history) {
        ImGui::TextColored(ImVec4(1.0f, 0.4f, 0.3f, 1.0f),
                           "beyond_photon_history = TRUE");
        ImGui::TextColored(ImVec4(1.0f, 0.4f, 0.3f, 1.0f),
                           "Star OMITTED from frame (not faded).");
    } else {
        ImGui::TextColored(ImVec4(0.7f, 1.0f, 0.7f, 1.0f),
                           "beyond_photon_history = false");
    }
    ImGui::TextDisabled("Discrete transition: frame N has star; frame N+1 does not.");
}

std::vector<ScalarValueAssertion> S07PhotonSourceHistory::value_assertions() const {
    // Deterministic check that the canon flag transitions correctly. Synthesize
    // a "before" and "after" observation that bracket the canonical crossover.
    astra::Vec3 ship{0, 0, 0};
    astra::Vec3 vel{0, 0, 0};
    astra::Vec3 body{0, 0, -1.0 * astra::LIGHT_YEAR};
    double one_year_s = astra::LIGHT_YEAR / astra::C_LIGHT;

    astra::ObservableState early = astra::observe(ship, vel, 0.0, body, 0.0,
                                                   astra::R_REST, one_year_s);
    astra::ObservableState late  = astra::observe(ship, vel, 100.0 * one_year_s,
                                                   body, 0.0, astra::R_REST, one_year_s);
    return {
        // beyond_photon_history flips to TRUE when t_emit < body_t_source_start.
        // expected/measured both encode the flag as 1.0 / 0.0 so the assertion
        // tolerance can be tight (boolean comparison).
        {"S07.beyond_photon_history_true_at_observing_before_source_on",
         1.0, early.beyond_photon_history ? 1.0 : 0.0, 1e-12},
        {"S07.beyond_photon_history_false_at_observing_after_source_on",
         0.0, late.beyond_photon_history ? 1.0 : 0.0, 1e-12},
    };
}

} // namespace astra_viz
