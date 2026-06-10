#include "scenes/s02_stl_recede_05c.h"

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

uint32_t S02StlRecede05c::base_regime() const { return astra::R_STL_REL; }

void S02StlRecede05c::activate() { beta_ = 0.5f; }

void S02StlRecede05c::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_STL_REL;
    p.beta_along     = beta_;
    p.show_volume    = false;
    p.show_named_bodies = true;
    // ship_velocity_xyz is the direction the ship is moving (so it RECEDES from
    // the planet at -z). Receding from the planet at -z means moving +z.
    p.ship_velocity_xyz[0] = 0.0f;
    p.ship_velocity_xyz[1] = 0.0f;
    p.ship_velocity_xyz[2] = 1.0f;

    // Planet tint: SR redshift suppresses blue. For beta=0.5 z_kin ~ 0.732.
    // tint = (1, 1-0.4*z, 1-0.85*z) clamped to [0, 1]. At beta=0.5:
    //   tint = (1.0, 0.707, 0.378)  -> planet pixel reads ~(1.0, 0.71, 0.38).
    double z = astra::compute_z_kin((double)beta_ * astra::C_LIGHT);
    float zf = (float)std::min(1.0, z);
    p.planet_color_tint[0] = 1.0f;
    p.planet_color_tint[1] = std::max(0.0f, 1.0f - 0.4f  * zf);
    p.planet_color_tint[2] = std::max(0.0f, 1.0f - 0.85f * zf);

    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "STL_REL %.3fc recede", beta_);
}

void S02StlRecede05c::draw_parameter_panel() {
    ImGui::TextUnformatted("S02 parameters");
    ImGui::SliderFloat("beta (recede)", &beta_, -0.99f, 0.99f, "%.4f");
}

void S02StlRecede05c::draw_state_panel() {
    double v_rad = (double)beta_ * astra::C_LIGHT;
    double rate  = astra::compute_apparent_rate(v_rad, astra::R_STL_REL);
    double z_kin = astra::compute_z_kin(v_rad);
    double gamma = std::cosh(std::atanh((double)beta_));

    ImGui::TextUnformatted("S02  STL_REL 0.5c");
    ImGui::Separator();
    ImGui::Text("beta:           %+.4f c", beta_);
    ImGui::Text("gamma:          %.6f", gamma);
    ImGui::Text("apparent_rate:  %+.6f  (libastra STL_REL)", rate);
    ImGui::Text("z_kin:          %+.6f", z_kin);
    ImGui::Separator();
    ImGui::TextDisabled("apparent_rate = sqrt((1-beta)/(1+beta)) per SR Doppler.");
}

std::vector<ScalarValueAssertion> S02StlRecede05c::value_assertions() const {
    double v_rad = (double)beta_ * astra::C_LIGHT;
    double rate  = astra::compute_apparent_rate(v_rad, astra::R_STL_REL);
    double rate_expected = std::sqrt((1.0 - (double)beta_) / (1.0 + (double)beta_));
    double gamma_lib = std::cosh(std::atanh((double)beta_));
    double gamma_expected = std::cosh(std::atanh(0.5));
    double rate_warp = astra::compute_apparent_rate(v_rad, astra::R_WARP_CRUISE);
    return {
        // V2 gate standard: 1e-6 absolute (6 sig figs). float slider -> double
        // promotion introduces ~1e-7 noise that's irrelevant to the physics.
        {"S02.apparent_rate_matches_SR_Doppler", rate_expected, rate, 1e-6},
        {"S02.gamma_at_beta_05_equals_cosh_atanh_05", gamma_expected, gamma_lib, 1e-6},
        // Witness for the regime dispatch (canon: STL != WARP at the same v).
        {"S02.regime_dispatch_STL_differs_from_WARP", 0.5, rate_warp, 1e-6},
    };
}

std::vector<ScalarPixelAssertion> S02StlRecede05c::pixel_assertions(int fb_w, int fb_h) const {
    int planet_px = (int)((float)fb_w * 0.275f);
    int planet_py = (int)((float)fb_h * 0.818f);
    return {
        // Planet R stays bright (>= 0.7); R is not Doppler-suppressed at this beta.
        {"S02.planet_pixel_R_high",   planet_px, planet_py, 0, 0.85f, 0.20f},
        // Planet B suppressed to ~0.38 by redshift tint (<= 0.55).
        {"S02.planet_pixel_B_below_055", planet_px, planet_py, 2, 0.30f, 0.25f},
    };
}

} // namespace astra_viz
