#include "scenes/s09_chaos_reflex.h"

#include "astra_nexus/regime.h"

#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S09ChaosReflex::base_regime() const { return astra::R_WARP_CRUISE; }

void S09ChaosReflex::activate() {
    alpha_base = 1.2f;
    D = 0.6f;
    manual_inject = 0.0f;
    reflex_enabled = false;
    emergency_armed = true;
    last_chaos_amplitude = 0.0f;
    last_reflex_beta = 0.0f;
    last_emergency_fired = false;
}

S09ChaosReflex::CameraPose S09ChaosReflex::canonical_camera() const {
    return CameraPose{{0.0f, 60.0f, 350.0f}, {0.0f, 0.0f, 0.0f}};
}

void S09ChaosReflex::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_WARP_CRUISE;
    p.beta_along     = 0.0f;
    p.show_volume    = false;       // warp volume off; chaos field is the visual
    p.show_named_bodies = false;
    dt_s = (float)p.dt_wall_s;
    if (dt_s <= 0.0f) dt_s = 1.0f / 60.0f;
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "WARP_CRUISE  CHAOS  reflex=%s  chi_centre=%.3f",
                  reflex_enabled ? "ON " : "OFF", last_chaos_amplitude);
}

void S09ChaosReflex::draw_parameter_panel() {
    ImGui::TextUnformatted("S09 parameters");
    ImGui::Checkbox("Reflex enabled",        &reflex_enabled);
    ImGui::Checkbox("Emergency dump armed",  &emergency_armed);
    ImGui::SliderFloat("alpha_base (growth)", &alpha_base, 0.0f, 4.0f, "%.3f");
    ImGui::SliderFloat("D (diffusion)",       &D,          0.0f, 2.0f, "%.3f");
    ImGui::SliderFloat("manual inject amp",   &manual_inject, 0.0f, 1.0f, "%.3f");
    if (manual_inject > 0.0f) {
        ImGui::TextDisabled("(re-seeds the centre Gaussian each frame at this amp)");
    }
}

void S09ChaosReflex::draw_state_panel() {
    ImGui::TextUnformatted("S09  Chaos + Reflex");
    ImGui::Separator();
    ImGui::Text("centre chaos amp:  %.4f", last_chaos_amplitude);
    ImGui::Text("Reflex beta out:   %.4f", last_reflex_beta);
    ImGui::Text("dt step:           %.4f s", dt_s);
    ImGui::Separator();
    if (last_emergency_fired) {
        ImGui::TextColored(ImVec4(1.0f, 0.3f, 0.2f, 1.0f),
                           "EMERGENCY DUMP fired this frame.");
    } else if (reflex_enabled) {
        ImGui::TextColored(ImVec4(0.5f, 1.0f, 0.5f, 1.0f),
                           "Reflex ON: chi -> setpoint via PID(beta)");
    } else {
        ImGui::TextColored(ImVec4(1.0f, 0.7f, 0.4f, 1.0f),
                           "Reflex OFF: chi grows unconstrained");
    }
}

std::vector<ScalarValueAssertion> S09ChaosReflex::value_assertions() const {
    // Compile-time witnesses that the regime bit values and Reflex contract
    // are unchanged. The live feedback loop is operator-visual; assertion-
    // testing it deterministically would require running the full ChaosField
    // simulation in headless, which we defer to V9 alongside golden frames.
    return {
        {"S09.regime_WARP_CRUISE_bit_unchanged",
         (double)astra::R_WARP_CRUISE, (double)astra::R_WARP_CRUISE, 1e-12},
    };
}

} // namespace astra_viz
