#include "scenes/s11_split_screen.h"

#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S11SplitScreen::base_regime() const {
    return astra::R_STL_REL | astra::R_WARP_CRUISE;     // composite for state-panel display
}

void S11SplitScreen::prepare_frame(SceneRenderParams& p) {
    // The "global" params are unused; Application's split-screen path reads
    // fill_left_half / fill_right_half instead. We set sensible defaults so
    // any code path that misses the split fork doesn't render garbage.
    p.regime         = base_regime();
    p.beta_along     = 0.0f;
    p.show_volume    = false;
    p.show_named_bodies = false;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "STL_REL vs WARP_CRUISE  v_radial=%.3f c", v_radial_c);
}

void S11SplitScreen::fill_left_half(SceneRenderParams& p) const {
    p = SceneRenderParams{};
    p.regime         = astra::R_STL_REL;
    p.beta_along     = v_radial_c;
    p.show_volume    = false;       // STL ship: no warp bubble
    p.show_named_bodies = true;
    p.ship_velocity_xyz[0] = 0.0f;
    p.ship_velocity_xyz[1] = 0.0f;
    p.ship_velocity_xyz[2] = 1.0f;
    // Mild redshift tint approximating z_kin at this beta.
    double z = astra::compute_z_kin((double)v_radial_c * astra::C_LIGHT);
    float zf = (float)std::min(1.0, z);
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = std::max(0.0f, 1.0f - 0.4f  * zf);
    p.planet_color_tint[2] = std::max(0.0f, 1.0f - 0.85f * zf);
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "LEFT: STL_REL beta=%.3f  rate=%.4f",
                  v_radial_c,
                  astra::compute_apparent_rate((double)v_radial_c * astra::C_LIGHT, astra::R_STL_REL));
}

void S11SplitScreen::fill_right_half(SceneRenderParams& p) const {
    p = SceneRenderParams{};
    p.regime         = astra::R_WARP_CRUISE;
    p.beta_along     = 0.0f;        // bubble crew inertial; no SR Doppler on starfield
    p.show_volume    = true;
    p.show_named_bodies = true;
    p.ship_velocity_xyz[0] = 0.0f;
    p.ship_velocity_xyz[1] = 0.0f;
    p.ship_velocity_xyz[2] = 1.0f;
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = 0.95f;
    p.planet_color_tint[2] = 0.90f;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "RIGHT: WARP_CRUISE v_app=%.3fc  rate=%.4f",
                  v_radial_c,
                  astra::compute_apparent_rate((double)v_radial_c * astra::C_LIGHT, astra::R_WARP_CRUISE));
}

void S11SplitScreen::draw_parameter_panel() {
    ImGui::TextUnformatted("S11 parameters");
    ImGui::SliderFloat("v_radial (c)", &v_radial_c, -0.99f, 5.0f, "%.3f");
}

void S11SplitScreen::draw_state_panel() {
    double v_si  = (double)v_radial_c * astra::C_LIGHT;
    double r_stl = astra::compute_apparent_rate(v_si, astra::R_STL_REL);
    double r_wp  = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);
    ImGui::TextUnformatted("S11  STL vs WARP split-screen");
    ImGui::Separator();
    ImGui::Text("v_radial:        %+.4f c", v_radial_c);
    ImGui::Text("LEFT  STL_REL  rate: %+.6f", r_stl);
    ImGui::Text("RIGHT WARP     rate: %+.6f", r_wp);
    ImGui::Text("|delta|:        %+.6f", std::abs(r_stl - r_wp));
    ImGui::Separator();
    ImGui::TextDisabled("At v=0.5c: STL = sqrt(1/3) ~ 0.5774, WARP = 0.5 (canon).");
    ImGui::TextDisabled("Visual gap proves regime dispatch is real, not artifact.");
}

std::vector<ScalarValueAssertion> S11SplitScreen::value_assertions() const {
    // Anchor to canonical v=0.5c regardless of slider.
    double v_si  = 0.5 * astra::C_LIGHT;
    double r_stl = astra::compute_apparent_rate(v_si, astra::R_STL_REL);
    double r_wp  = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);
    return {
        {"S11.STL_REL_apparent_rate_at_05c_equals_sqrt_one_third",
         std::sqrt(1.0 / 3.0), r_stl, 1e-9},
        {"S11.WARP_CRUISE_apparent_rate_at_05c_equals_half",
         0.5, r_wp, 1e-12},
        {"S11.regime_dispatch_difference_at_05c_above_005",
         1.0,
         (std::abs(r_stl - r_wp) > 0.05) ? 1.0 : 0.0,
         1e-12},
    };
}

} // namespace astra_viz
