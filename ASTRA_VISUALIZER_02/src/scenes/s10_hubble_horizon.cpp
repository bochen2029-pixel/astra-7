#include "scenes/s10_hubble_horizon.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S10HubbleHorizon::base_regime() const { return astra::R_REST; }

void S10HubbleHorizon::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_REST;
    p.beta_along     = 0.0f;
    p.show_volume    = false;

    double d_m = (double)distance_Gly * 1.0e9 * astra::LIGHT_YEAR;
    d_proper_m = d_m;
    astra::Vec3 ship{0, 0, 0};
    astra::Vec3 vel{0, 0, 0};
    astra::Vec3 body{0, 0, (float)-d_m};
    astra::ObservableState obs = astra::observe(ship, vel, 1.0e10, body, 0.0, astra::R_REST);
    z_cosmo_v            = obs.z_cosmo;
    beyond_hubble_horizon = obs.beyond_hubble_horizon;

    p.show_named_bodies = true;
    p.planet_dir_xyz[0] = 0.0f;
    p.planet_dir_xyz[1] = 0.0f;
    p.planet_dir_xyz[2] = -1.0f;
    p.sun_dir_xyz[0]    = 0.3f;
    p.sun_dir_xyz[1]    = 0.2f;
    p.sun_dir_xyz[2]    = -0.95f;

    // Beyond horizon: render the body as extreme-redshift (deep red, dim). The
    // "FROZEN" property in canon means t_emit doesn't advance for further
    // recession; visually, we lock the planet tint at the horizon-crossing value.
    if (beyond_hubble_horizon) {
        p.planet_color_tint[0] = 0.4f;       // dim red
        p.planet_color_tint[1] = 0.04f;
        p.planet_color_tint[2] = 0.02f;
    } else {
        // Smoothly redshift up to the horizon.
        float t = (float)std::min(1.0, z_cosmo_v);
        p.planet_color_tint[0] = std::max(0.4f, 1.0f - 0.5f * t);
        p.planet_color_tint[1] = std::max(0.05f, 1.0f - 0.85f * t);
        p.planet_color_tint[2] = std::max(0.02f, 1.0f - 0.95f * t);
    }
    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "REST  d=%.2f Gly  %s",
                  distance_Gly,
                  beyond_hubble_horizon ? "[BEYOND HUBBLE HORIZON; frozen]" : "[within horizon]");
}

void S10HubbleHorizon::draw_parameter_panel() {
    ImGui::TextUnformatted("S10 parameters");
    ImGui::SliderFloat("distance (Gly)", &distance_Gly, 0.1f, 100.0f, "%.2f",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::TextDisabled("Hubble horizon ~ 13.8 Gly at H0=70 km/s/Mpc.");
    ImGui::TextDisabled("Push distance past that to flip beyond_hubble_horizon.");
}

void S10HubbleHorizon::draw_state_panel() {
    double horizon_Gly = (astra::C_LIGHT / astra::H0_SI) / astra::LIGHT_YEAR / 1.0e9;
    ImGui::TextUnformatted("S10  Hubble Horizon");
    ImGui::Separator();
    ImGui::Text("distance:            %.3f Gly", distance_Gly);
    ImGui::Text("d_proper:            %.3e m", d_proper_m);
    ImGui::Text("Hubble horizon (Gly): %.3f", horizon_Gly);
    ImGui::Text("z_cosmo:             %.4f", z_cosmo_v);
    ImGui::Separator();
    if (beyond_hubble_horizon) {
        ImGui::TextColored(ImVec4(1.0f, 0.3f, 0.2f, 1.0f),
                           "beyond_hubble_horizon = TRUE");
        ImGui::TextColored(ImVec4(1.0f, 0.3f, 0.2f, 1.0f),
                           "Body rendered FROZEN at horizon-crossing tint.");
    } else {
        ImGui::TextColored(ImVec4(0.5f, 1.0f, 0.5f, 1.0f),
                           "beyond_hubble_horizon = false");
    }
}

std::vector<ScalarValueAssertion> S10HubbleHorizon::value_assertions() const {
    // Deterministic anchor: 100 Gly is far beyond the horizon; 1 Gly is inside.
    astra::Vec3 ship{0, 0, 0};
    astra::Vec3 vel{0, 0, 0};
    astra::Vec3 beyond_body{0, 0, (float)(-100.0e9 * astra::LIGHT_YEAR)};
    astra::Vec3 inside_body{0, 0, (float)(-1.0e9 * astra::LIGHT_YEAR)};
    astra::ObservableState beyond = astra::observe(ship, vel, 1.0e10, beyond_body, 0.0, astra::R_REST);
    astra::ObservableState inside = astra::observe(ship, vel, 1.0e10, inside_body, 0.0, astra::R_REST);
    return {
        {"S10.beyond_hubble_horizon_true_at_100Gly",
         1.0, beyond.beyond_hubble_horizon ? 1.0 : 0.0, 1e-12},
        {"S10.beyond_hubble_horizon_false_at_1Gly",
         0.0, inside.beyond_hubble_horizon ? 1.0 : 0.0, 1e-12},
    };
}

} // namespace astra_viz
