#include "scenes/s04_warp_charge.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/regime.h"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S04WarpCharge::base_regime() const { return astra::R_WARP_CHARGE; }

void S04WarpCharge::activate() { scene_t_s_ = 0.0f; W_now = 0.0f; }

void S04WarpCharge::prepare_frame(SceneRenderParams& p) {
    // 0..charge_duration_s: WARP_CHARGE with W ramping. After: WARP_CRUISE at W=1.
    scene_t_s_ += (float)p.dt_wall_s;
    float ramp = std::clamp(scene_t_s_ / std::max(0.01f, charge_duration_s), 0.0f, 1.0f);
    W_now = ramp;

    p.regime         = (ramp < 1.0f) ? astra::R_WARP_CHARGE : astra::R_WARP_CRUISE;
    p.beta_along     = 0.0f;
    p.show_volume    = true;
    p.show_named_bodies = true;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  (ramp < 1.0f) ? "WARP_CHARGE  W=%.3f" : "WARP_CRUISE  W=%.3f", W_now);
}

void S04WarpCharge::draw_parameter_panel() {
    ImGui::TextUnformatted("S04 parameters");
    ImGui::SliderFloat("charge duration (s)", &charge_duration_s, 0.5f, 30.0f, "%.1f");
    ImGui::SliderFloat("bubble radius (m)",   &bubble_radius_m,   20.0f, 140.0f, "%.0f");
    if (ImGui::Button("Reset charge to t=0")) { scene_t_s_ = 0.0f; W_now = 0.0f; }
    ImGui::SameLine();
    ImGui::Text("scene t = %.2f s", scene_t_s_);
}

void S04WarpCharge::draw_state_panel() {
    double dtau = astra::dtau_dt_cosmic((double)W_now, 1.0, 1.0, /*warp_active=*/true);
    ImGui::TextUnformatted("S04  Warp Charge");
    ImGui::Separator();
    ImGui::Text("scene t:        %.3f s",         scene_t_s_);
    ImGui::Text("W (warp metric): %.4f",          W_now);
    ImGui::Text("dtau/dt_cosmic: %.6f",           dtau);
    ImGui::Text("regime:         WARP_%s",        (W_now < 1.0f) ? "CHARGE" : "CRUISE");
}

std::vector<ScalarValueAssertion> S04WarpCharge::value_assertions() const {
    // dtau/dt at W=1 with warp_active should reduce to f_warp(1) = 0.5 per the
    // composition rule (gamma_kin=1 for bubble crew). This anchors the scene
    // to the canon composition rule even when the operator hasn't watched the
    // ramp; we test at W=1 deterministically.
    double dtau_at_W1 = astra::dtau_dt_cosmic(1.0, 1.0, 1.0, true);
    return {
        {"S04.dtau_dt_at_W1_equals_half", 0.5, dtau_at_W1, 1e-12},
    };
}

} // namespace astra_viz
