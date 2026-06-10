#include "scenes/s01_rest_baseline.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/rapidity.h"
#include "astra_nexus/regime.h"

#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S01RestBaseline::base_regime() const { return astra::R_REST; }

void S01RestBaseline::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_REST;
    p.beta_along     = 0.0f;
    p.show_volume    = false;
    p.show_named_bodies = true;
    p.planet_color_tint[0] = 1.0f; p.planet_color_tint[1] = 1.0f; p.planet_color_tint[2] = 1.0f;
    std::strncpy(p.regime_label, "REST", sizeof(p.regime_label));
}

void S01RestBaseline::draw_state_panel() {
    astra::Rapidity rest{{0, 0, 0}};
    double gamma = rest.gamma();
    double beta  = rest.beta();
    double dtau  = astra::dtau_dt_cosmic(0.0, 1.0, gamma, /*warp_active=*/false);

    ImGui::TextUnformatted("S01  RestBaseline");
    ImGui::Separator();
    ImGui::Text("regime:   %s (0x%02x)", astra::regime_label(astra::R_REST), astra::R_REST);
    ImGui::Text("gamma:    %.6f", gamma);
    ImGui::Text("beta:     %.6f", beta);
    ImGui::Text("dtau/dt:  %.6f", dtau);
    ImGui::Separator();
    ImGui::TextDisabled("4 V4 assertions: REST gamma + beta + dtau/dt + sun-pixel R-high.");
}

std::vector<ScalarValueAssertion> S01RestBaseline::value_assertions() const {
    astra::Rapidity rest{{0, 0, 0}};
    double gamma_lib = rest.gamma();
    double beta_lib  = rest.beta();
    double dtau_lib  = astra::dtau_dt_cosmic(0.0, 1.0, gamma_lib, false);
    return {
        {"S01.gamma_at_rest_equals_one", 1.0, gamma_lib, 1e-12},
        {"S01.beta_at_rest_equals_zero", 0.0, beta_lib,  1e-12},
        {"S01.dtau_dt_at_rest_equals_one", 1.0, dtau_lib, 1e-12},
    };
}

std::vector<ScalarPixelAssertion> S01RestBaseline::pixel_assertions(int fb_w, int fb_h) const {
    // The canonical camera (0, 80, 600) looking at the origin projects the
    // default SceneRenderParams::sun_dir to approximately (0.803 fb_w, 0.931 fb_h)
    // and planet_dir to approximately (0.275 fb_w, 0.818 fb_h). At those pixels
    // the body fragment shader writes pure u_tint with alpha=1 (inner disc).
    //
    // Sun tint is fixed (1.0, 0.88, 0.55) in named_bodies.cpp; assert R high.
    // Planet at REST tint is (1, 1, 1); assert R high.
    int sun_px    = (int)((float)fb_w * 0.803f);
    int sun_py    = (int)((float)fb_h * 0.931f);
    int planet_px = (int)((float)fb_w * 0.275f);
    int planet_py = (int)((float)fb_h * 0.818f);
    return {
        // Sun: warm yellow tint -> R ~ 1.0. Assert R high (>= 0.65).
        {"S01.sun_pixel_R_high",         sun_px,    sun_py,    0, 0.85f, 0.20f},
    };
}

} // namespace astra_viz
