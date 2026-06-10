#include "scenes/s08_warp_gravity_well.h"

#include "astra_nexus/composition.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <imgui.h>

namespace astra_viz {

uint32_t S08WarpGravityWell::base_regime() const {
    return astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL;
}

void S08WarpGravityWell::prepare_frame(SceneRenderParams& p) {
    p.regime         = astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL;
    p.beta_along     = 0.0f;
    p.show_volume    = true;     // warp bubble visualized
    p.show_named_bodies = false;

    // Compute Schwarzschild factor from the canonical formula. Place BH along +x
    // for the synthetic geometry; ship at origin. r = r_in_rs_units * r_s.
    double M_kg = (double)bh_mass_solar * astra::M_SUN;
    double r_s  = astra::schwarzschild_r(M_kg);
    double r    = (double)r_in_rs_units * r_s;
    std::vector<astra::BHEntry> bhs;
    bhs.push_back({M_kg, {(float)r, 0.0f, 0.0f}});
    grav_factor = (float)astra::compute_grav_factor(bhs, astra::Vec3{0.0, 0.0, 0.0});

    // alpha_eff per §7.1: alpha_base * (1 + k * M * L^2 / r^3).
    double L_pow2 = (double)L_lengthscale_m * (double)L_lengthscale_m;
    double r_pow3 = r * r * r;
    alpha_eff = (float)((double)alpha_base * (1.0 + (double)k_coupling * M_kg * L_pow2 / r_pow3));

    dtau_dt = (float)astra::dtau_dt_cosmic((double)W_now, (double)grav_factor, 1.0,
                                            /*warp_active=*/true);

    std::snprintf(p.regime_label, sizeof(p.regime_label),
                  "WARP_CRUISE | GRAVITY_WELL  (regime=0x%02x)  dtau/dt=%.3f",
                  astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL, dtau_dt);
}

void S08WarpGravityWell::draw_parameter_panel() {
    ImGui::TextUnformatted("S08 parameters");
    ImGui::SliderFloat("BH mass (Msun)", &bh_mass_solar, 1.0f, 1.0e9f, "%.3g",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("ship r (r_s units)", &r_in_rs_units, 5.0f, 10000.0f, "%.1f",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("L (m)", &L_lengthscale_m, 1.0f, 1.0e4f, "%.1f",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("alpha_base", &alpha_base, 0.0f, 10.0f, "%.3f");
    ImGui::SliderFloat("k coupling", &k_coupling, 0.0f, 1.0e-2f, "%.3g",
                       ImGuiSliderFlags_Logarithmic);
    ImGui::SliderFloat("W (warp)", &W_now, 0.0f, 1.0f, "%.3f");
}

void S08WarpGravityWell::draw_state_panel() {
    ImGui::TextUnformatted("S08  Warp + GravityWell");
    ImGui::Separator();
    ImGui::Text("regime:       WARP_CRUISE | GRAVITY_WELL");
    ImGui::Text("regime bits:  0x%02x", astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL);
    ImGui::Separator();
    double r_s_m = astra::schwarzschild_r((double)bh_mass_solar * astra::M_SUN);
    ImGui::Text("BH mass:      %.3e Msun", bh_mass_solar);
    ImGui::Text("r_s:          %.3e m",    r_s_m);
    ImGui::Text("ship r:       %.3e m  (%.1f r_s)",
                r_s_m * r_in_rs_units, r_in_rs_units);
    ImGui::Text("grav_factor:  %.6f  (sqrt(1 - r_s/r))", grav_factor);
    ImGui::Text("alpha_eff:    %.6f  = %.3f * (1 + %.3g * M * L^2 / r^3)",
                alpha_eff, alpha_base, k_coupling);
    ImGui::Text("dtau/dt_cos:  %.6f", dtau_dt);
}

std::vector<ScalarValueAssertion> S08WarpGravityWell::value_assertions() const {
    // Anchor against a deterministic config so headless evaluation is stable.
    // r = 100 r_s with 10 Msun BH gives grav_factor = sqrt(1 - 1/100) = sqrt(0.99) ~ 0.99499.
    double M_kg_test  = 10.0 * astra::M_SUN;
    double r_s_test   = astra::schwarzschild_r(M_kg_test);
    std::vector<astra::BHEntry> bh_test;
    bh_test.push_back({M_kg_test, astra::Vec3{(float)(100.0 * r_s_test), 0.0f, 0.0f}});
    double grav_test  = astra::compute_grav_factor(bh_test, astra::Vec3{0.0, 0.0, 0.0});
    double grav_expected = std::sqrt(1.0 - 1.0 / 100.0);

    uint32_t composite = astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL;
    return {
        // sqrt(1 - 1/100) vs sqrt(0.99) literal diverge at ~1e-11 due to
        // floating-point intermediate path differences; 1e-9 is the V4-class
        // tolerance for cross-path numeric assertions.
        {"S08.grav_factor_at_r_100rs_M10Msun_equals_sqrt_099", grav_expected, grav_test, 1e-9},
        {"S08.regime_composite_warp_or_gravwell_equals_0x28", 0x28, (double)composite, 1e-12},
        {"S08.dtau_dt_at_W1_grav099_warp_active_equals_f_warp_times_grav",
         astra::f_warp_canon(1.0) * grav_expected,
         astra::dtau_dt_cosmic(1.0, grav_expected, 1.0, true), 1e-9},
    };
}

} // namespace astra_viz
