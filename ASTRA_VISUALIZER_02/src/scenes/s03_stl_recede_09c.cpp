#include "scenes/s03_stl_recede_09c.h"

#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/rapidity.h"
#include "astra_nexus/regime.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S03StlRecede09c::base_regime() const { return astra::R_STL_REL; }

void S03StlRecede09c::activate() { beta_ = 0.9f; }

void S03StlRecede09c::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_STL_REL;
    p.beta_along     = beta_;
    p.show_volume    = false;
    p.show_named_bodies = true;
    p.ship_velocity_xyz[0] = 0.0f;
    p.ship_velocity_xyz[1] = 0.0f;
    p.ship_velocity_xyz[2] = 1.0f;

    double z = astra::compute_z_kin((double)beta_ * astra::C_LIGHT);
    // At beta=0.9 z_kin ~ 3.36; clamp z*0.3 at 1 so the channel suppression
    // saturates cleanly. tint = (1.0, 0.15, 0.02) -> planet pixel reads deep red.
    float shift = (float)std::min(1.0, z * 0.3);
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = std::max(0.0f, 1.0f - 0.85f * shift);
    p.planet_color_tint[2] = std::max(0.0f, 1.0f - 0.98f * shift);

    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "STL_REL %.3fc recede", beta_);
}

void S03StlRecede09c::draw_parameter_panel() {
    ImGui::TextUnformatted("S03 parameters");
    ImGui::SliderFloat("beta (recede)", &beta_, -0.99f, 0.999f, "%.4f");
}

void S03StlRecede09c::draw_state_panel() {
    double v_rad = (double)beta_ * astra::C_LIGHT;
    double rate  = astra::compute_apparent_rate(v_rad, astra::R_STL_REL);
    double z_kin = astra::compute_z_kin(v_rad);
    double gamma = std::cosh(std::atanh((double)beta_));

    ImGui::TextUnformatted("S03  STL_REL 0.9c");
    ImGui::Separator();
    ImGui::Text("beta:           %+.4f c", beta_);
    ImGui::Text("gamma:          %.6f", gamma);
    ImGui::Text("apparent_rate:  %+.6f", rate);
    ImGui::Text("z_kin:          %+.6f", z_kin);
    ImGui::Separator();
    ImGui::TextDisabled("Dramatic regime: apparent_rate < 0.25, planet deep-red.");
}

std::vector<ScalarValueAssertion> S03StlRecede09c::value_assertions() const {
    double v_rad = (double)beta_ * astra::C_LIGHT;
    double rate  = astra::compute_apparent_rate(v_rad, astra::R_STL_REL);
    double rate_expected = std::sqrt((1.0 - (double)beta_) / (1.0 + (double)beta_));
    double gamma_lib = std::cosh(std::atanh((double)beta_));
    double gamma_expected = std::cosh(std::atanh(0.9));
    return {
        {"S03.apparent_rate_matches_SR_Doppler_at_09", rate_expected, rate, 1e-6},
        {"S03.gamma_at_beta_09_equals_cosh_atanh_09", gamma_expected, gamma_lib, 1e-6},
    };
}

std::vector<ScalarPixelAssertion> S03StlRecede09c::pixel_assertions(int fb_w, int fb_h) const {
    int planet_px = (int)((float)fb_w * 0.275f);
    int planet_py = (int)((float)fb_h * 0.818f);
    return {
        // R still bright (>= 0.7) at extreme recede; nothing redshifts away the red.
        {"S03.planet_pixel_R_high",          planet_px, planet_py, 0, 0.85f, 0.20f},
        // B nearly zero from heavy z_kin suppression.
        {"S03.planet_pixel_B_near_zero",     planet_px, planet_py, 2, 0.08f, 0.15f},
    };
}

} // namespace astra_viz
