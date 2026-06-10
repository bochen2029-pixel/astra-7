#include "ui/physics_calc_panel.h"
#include "physics/physics_core.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"

#include <imgui.h>

#include <cmath>

namespace astra_viz::ui {

namespace {

struct RegimeChoice {
    const char* label;
    uint32_t    bits;
    bool        warp_active;
};
const RegimeChoice kRegimes[] = {
    {"REST",           astra::R_REST,                                   false},
    {"STL_NONREL",     astra::R_STL_NONREL,                             false},
    {"STL_REL",        astra::R_STL_REL,                                false},
    {"WARP_CHARGE",    astra::R_WARP_CHARGE,                            true },
    {"WARP_CRUISE",    astra::R_WARP_CRUISE,                            true },
    {"WARP_SHUTDOWN",  astra::R_WARP_SHUTDOWN,                          true },
    {"WARP+GRAV_WELL", astra::R_WARP_CRUISE | astra::R_GRAVITY_WELL,    true },
};

struct Preset {
    const char* label;
    int  regime_choice;
    float beta_radial;        // multiples of c; negative = approaching
    float W;
    float d_to_body_ly;       // light-years
    bool  warp_override;      // if true, warp_active comes from regime, not the bool
};
const Preset kPresets[] = {
    {"REST near 1 ly body",            0, 0.0f,  0.0f,    1.0f, true},
    {"STL_REL recede 0.5c",            2, 0.5f,  0.0f,    1.0f, true},
    {"STL_REL recede 0.9c",            2, 0.9f,  0.0f,    1.0f, true},
    {"STL_REL approach 0.5c",          2, -0.5f, 0.0f,    1.0f, true},
    {"WARP_CRUISE 2c recede (S05)",    4, 2.0f,  1.0f,    1.0f, true},
    {"WARP_CRUISE 10c recede (S06)",   4, 10.0f, 1.0f,    1.0f, true},
    {"WARP_CRUISE 100c recede",        4, 100.0f, 1.0f,   1.0f, true},
    {"WARP_CRUISE 8000c (S07)",        4, 8000.0f, 1.0f,  1.0f, true},
    {"WARP_CRUISE -10c approach",      4, -10.0f, 1.0f,   1.0f, true},
};

} // anon

PhysicsCalcPanel::PhysicsCalcPanel() {
    // Default to REST baseline (preset 0).
    const Preset& p = kPresets[0];
    regime_choice_ = p.regime_choice;
    input_.regime              = kRegimes[regime_choice_].bits;
    input_.warp_active         = kRegimes[regime_choice_].warp_active;
    input_.v_radial_si         = (double)p.beta_radial * astra::C_LIGHT;
    input_.W_warp              = (double)p.W;
    input_.d_to_body_si        = (double)p.d_to_body_ly * astra::LIGHT_YEAR;
    input_.t_cosmic_s          = 0.0;
    input_.body_metric_shift   = 0.0;
    input_.grav_factor         = 1.0;
    input_.body_t_source_start = -1.0e300;
    output_ = physics_calc(input_);
}

void PhysicsCalcPanel::draw() {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    float bottom = vp->WorkPos.y + vp->WorkSize.y - 360.0f;
    ImGui::SetNextWindowPos(ImVec2(10.0f, bottom), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(420, 350), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("PhysicsCalc  (libastra_nexus bridge)")) { ImGui::End(); return; }

    // Preset row.
    {
        const char* preview = kPresets[preset_choice_].label;
        if (ImGui::BeginCombo("preset", preview)) {
            for (int i = 0; i < (int)(sizeof(kPresets) / sizeof(kPresets[0])); i++) {
                bool selected = (i == preset_choice_);
                if (ImGui::Selectable(kPresets[i].label, selected)) {
                    preset_choice_ = i;
                    const Preset& p = kPresets[i];
                    regime_choice_     = p.regime_choice;
                    input_.regime      = kRegimes[regime_choice_].bits;
                    input_.warp_active = kRegimes[regime_choice_].warp_active;
                    input_.v_radial_si = (double)p.beta_radial * astra::C_LIGHT;
                    input_.W_warp      = (double)p.W;
                    input_.d_to_body_si = (double)p.d_to_body_ly * astra::LIGHT_YEAR;
                }
                if (selected) ImGui::SetItemDefaultFocus();
            }
            ImGui::EndCombo();
        }
    }
    ImGui::Separator();

    // Regime selector.
    if (ImGui::BeginCombo("regime", kRegimes[regime_choice_].label)) {
        for (int i = 0; i < (int)(sizeof(kRegimes) / sizeof(kRegimes[0])); i++) {
            bool selected = (i == regime_choice_);
            if (ImGui::Selectable(kRegimes[i].label, selected)) {
                regime_choice_ = i;
                input_.regime      = kRegimes[i].bits;
                input_.warp_active = kRegimes[i].warp_active;
            }
            if (selected) ImGui::SetItemDefaultFocus();
        }
        ImGui::EndCombo();
    }

    // Sliders. v_radial works in units of c so the operator's mental model
    // doesn't have to juggle scientific notation. Range -10c .. +10000c gives
    // S05 (2c), S06 (10c), and S07 (8000c) configurations in one slider.
    float beta_c = (float)(input_.v_radial_si / astra::C_LIGHT);
    if (ImGui::SliderFloat("v_radial (c)", &beta_c, -10.0f, 10000.0f, "%.4f",
                            ImGuiSliderFlags_Logarithmic)) {
        input_.v_radial_si = (double)beta_c * astra::C_LIGHT;
    }

    float W = (float)input_.W_warp;
    if (ImGui::SliderFloat("W (warp metric)", &W, 0.0f, 1.0f, "%.3f")) {
        input_.W_warp = (double)W;
    }

    float d_ly = (float)(input_.d_to_body_si / astra::LIGHT_YEAR);
    if (ImGui::SliderFloat("body distance (ly)", &d_ly, 0.001f, 1.0e10f, "%.4g",
                            ImGuiSliderFlags_Logarithmic)) {
        input_.d_to_body_si = (double)d_ly * astra::LIGHT_YEAR;
    }

    float grav = (float)input_.grav_factor;
    if (ImGui::SliderFloat("grav_factor", &grav, 0.1f, 1.0f, "%.4f")) {
        input_.grav_factor = (double)grav;
    }

    // Compute fresh every frame; ~nanoseconds in scalar libastra calls.
    output_ = physics_calc(input_);
    const auto& o = output_;

    ImGui::Separator();
    ImGui::Text("Rapidity:   omega=%.6f  gamma=%.6f  beta=%.6f", o.omega, o.gamma, o.beta);
    ImGui::Text("Composition: f_warp=%.6f  dtau/dt=%.6f", o.f_warp, o.dtau_dt_cosmic);
    ImGui::Separator();
    ImGui::TextUnformatted("ObservableState (libastra_nexus::observe)");
    ImGui::Text("  d_proper     = %.6e m  (%.4f ly)",
                o.obs.d_proper, o.obs.d_proper / astra::LIGHT_YEAR);
    ImGui::Text("  v_radial     = %+10.4f c", o.obs.v_radial / astra::C_LIGHT);
    ImGui::Text("  z_cosmo      = %+12.6e", o.obs.z_cosmo);
    ImGui::Text("  z_kin        = %+12.6f", o.obs.z_kin);
    ImGui::Text("  z_metric     = %+12.6f", o.obs.z_metric);
    ImGui::Text("  z_total      = %+12.6e", o.obs.z_total);
    ImGui::Text("  t_emit       = %+12.6e s", o.obs.t_emit);
    ImGui::Text("  apparent_rate (raw) = %+12.6f", o.apparent_rate_raw);
    ImGui::Text("  apparent_rate /1+z  = %+12.6f", o.obs.apparent_rate);
    if (o.obs.time_reversed)        ImGui::TextColored(ImVec4(1,0.5f,0,1),  "  TIME REVERSED");
    if (o.obs.beyond_photon_history) ImGui::TextColored(ImVec4(1,0.3f,0,1),  "  beyond_photon_history");
    if (o.obs.beyond_hubble_horizon) ImGui::TextColored(ImVec4(1,0.3f,0,1),  "  beyond_hubble_horizon");

    ImGui::End();
}

} // namespace astra_viz::ui
