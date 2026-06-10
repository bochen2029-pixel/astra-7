#include "scenes/s06_warp_cruise_10c_cherenkov.h"

#include "astra_nexus/apparent_rate.h"
#include "astra_nexus/cherenkov.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S06WarpCruise10cCherenkov::base_regime() const { return astra::R_WARP_CRUISE; }

void S06WarpCruise10cCherenkov::activate() {
    cherenkov_angle_rad = -1.0f;
    ship_axis_xyz[0] = 0.0f; ship_axis_xyz[1] = 0.0f; ship_axis_xyz[2] = 1.0f;
    cone_apex_xyz[0] = 0.0f; cone_apex_xyz[1] = 0.0f; cone_apex_xyz[2] = 0.0f;
}

S06WarpCruise10cCherenkov::CameraPose S06WarpCruise10cCherenkov::canonical_camera() const {
    // Side view so the operator sees the cone opening along the ship's velocity axis.
    return CameraPose{{500.0f, 60.0f, 0.0f}, {0.0f, 0.0f, 0.0f}};
}

void S06WarpCruise10cCherenkov::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_WARP_CRUISE;
    p.beta_along     = 0.0f;
    p.show_volume    = true;
    p.show_named_bodies = false;     // S06 focuses on the cone, not orbital bodies
    p.ship_velocity_xyz[0] = 0.0f;
    p.ship_velocity_xyz[1] = 0.0f;
    p.ship_velocity_xyz[2] = 1.0f;

    double v_si = (double)v_app_c * astra::C_LIGHT;
    double rate = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);

    // Cherenkov angle uses |beta| since the formula is symmetric (n*|beta| > 1
    // matters; sign just flips cone direction, which we handle via axis sign).
    double beta_abs = std::fabs((double)v_app_c);
    // Clamp slider beta into the range where the analytic n=1+W model gives
    // sensible angles; the spec is about superluminal physics so 0..50 is plenty.
    if (beta_abs > 50.0) beta_abs = 50.0;
    double angle = astra::compute_cherenkov_angle((double)W_now, beta_abs);
    cherenkov_angle_rad = (angle < 0.0) ? -1.0f : (float)angle;

    // Cone opens in the ship's motion direction. apex at the bubble's leading edge
    // (a small offset along the ship axis from origin).
    float lead_offset_m = bubble_radius_m * 0.85f;
    ship_axis_xyz[0] = 0.0f;
    ship_axis_xyz[1] = 0.0f;
    ship_axis_xyz[2] = (v_app_c >= 0.0f) ? 1.0f : -1.0f;
    cone_apex_xyz[0] = 0.0f;
    cone_apex_xyz[1] = 0.0f;
    cone_apex_xyz[2] = ship_axis_xyz[2] * lead_offset_m;

    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "WARP_CRUISE %.1fc  rate=%+.2f  theta_c=%.2f deg",
                  v_app_c, rate,
                  (cherenkov_angle_rad >= 0.0f) ? cherenkov_angle_rad * 57.2957795f : 0.0f);
}

void S06WarpCruise10cCherenkov::draw_parameter_panel() {
    ImGui::TextUnformatted("S06 parameters");
    ImGui::SliderFloat("v_app (c)",         &v_app_c,        -50.0f, 50.0f, "%.2f");
    ImGui::SliderFloat("W (bubble)",        &W_now,           0.0f,  1.0f, "%.3f");
    ImGui::SliderFloat("bubble radius (m)", &bubble_radius_m, 20.0f, 140.0f, "%.0f");
    ImGui::SliderFloat("cone length (m)",   &cone_length_m,   50.0f, 600.0f, "%.0f");
    if (cherenkov_angle_rad < 0.0f) {
        ImGui::TextColored(ImVec4(0.9f, 0.6f, 0.3f, 1.0f),
                           "Cherenkov inactive: n*|beta| <= 1");
    }
}

void S06WarpCruise10cCherenkov::draw_state_panel() {
    double v_si = (double)v_app_c * astra::C_LIGHT;
    double rate = astra::compute_apparent_rate(v_si, astra::R_WARP_CRUISE);
    double n_W  = astra::n_refractive_default((double)W_now);
    double nb   = n_W * (double)v_app_c;
    ImGui::TextUnformatted("S06  Warp Cruise 10c + Cherenkov");
    ImGui::Separator();
    ImGui::Text("v_app:           %+.3f c", v_app_c);
    ImGui::Text("apparent_rate:   %+.4f",   rate);
    ImGui::Text("W:               %.4f",    W_now);
    ImGui::Text("n_refractive(W): %.4f",    n_W);
    ImGui::Text("n*|beta|:        %.4f",    std::fabs(nb));
    if (cherenkov_angle_rad >= 0.0f) {
        ImGui::Text("theta_cherenkov: %.4f rad  (%.2f deg)",
                    cherenkov_angle_rad, cherenkov_angle_rad * 57.2957795f);
    } else {
        ImGui::Text("theta_cherenkov: inactive (n*|beta| <= 1)");
    }
    ImGui::TextDisabled("Cone half-angle = acos(1 / (n*|beta|))  per spec §6 step 10");
}

std::vector<ScalarValueAssertion> S06WarpCruise10cCherenkov::value_assertions() const {
    // Anchor against canonical config (v=10c, W=1) so the test is deterministic
    // regardless of the slider state.
    double rate_at_10c = astra::compute_apparent_rate(10.0 * astra::C_LIGHT, astra::R_WARP_CRUISE);
    double angle_at_canon = astra::compute_cherenkov_angle(1.0, 10.0);
    // n=1+W=2 at W=1; n*beta = 20; acos(1/20) = acos(0.05) ~ 1.5208 rad ~ 87.13 deg.
    double angle_expected = std::acos(1.0 / 20.0);
    return {
        {"S06.apparent_rate_at_v10c_equals_minus_nine", -9.0, rate_at_10c, 1e-12},
        {"S06.cherenkov_angle_canon_matches_acos_inv_nbeta", angle_expected, angle_at_canon, 1e-12},
        // Inactive case (n*|beta| <= 1) returns the -1 sentinel.
        {"S06.cherenkov_inactive_at_low_beta_returns_minus_one",
         -1.0, astra::compute_cherenkov_angle(0.5, 0.1), 1e-12},
    };
}

} // namespace astra_viz
