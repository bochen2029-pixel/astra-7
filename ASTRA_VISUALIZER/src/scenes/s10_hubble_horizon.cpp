// src/scenes/s10_hubble_horizon.cpp

#include "scenes/s10_hubble_horizon.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "physics/redshift.h"

#include <glad/gl.h>

#include <cmath>
#include <cstdio>

namespace astra::scenes {

namespace {

constexpr float kPixelTol = 0.02f;

int ndc_y_to_topleft(float ndc_y, int h) {
    float t = 0.5f * (1.0f - ndc_y);
    int   y = static_cast<int>(t * (h - 1) + 0.5f);
    if (y < 0) y = 0;
    if (y >= h) y = h - 1;
    return y;
}
int ndc_x_to_topleft(float ndc_x, int w) {
    float t = 0.5f * (1.0f + ndc_x);
    int   x = static_cast<int>(t * (w - 1) + 0.5f);
    if (x < 0) x = 0;
    if (x >= w) x = w - 1;
    return x;
}

astra::ObservableState query_observe(double d_proper) {
    astra::Vec3 ship_pos{0.0, 0.0, 0.0};
    astra::Vec3 ship_vel{0.0, 0.0, 0.0};
    astra::Vec3 body_pos{0.0, 0.0, -d_proper};
    return astra::observe(ship_pos, ship_vel, 1.0e10,
                          body_pos, 0.0, astra::R_REST,
                          -std::numeric_limits<double>::infinity());
}

}  // namespace

void S10_HubbleHorizon::setup() {
    double d_proper = d_multiplier_ * astra::D_HUBBLE_SI;
    z_cosmo_ = static_cast<float>(astra::compute_z_cosmo(d_proper));

    // Body at center, faded-orange color. The placeholder renderer applies
    // kin_redshift with `z = z_cosmo_` — visually similar to cosmological
    // shift, deferred proper blackbody-temp model to v0.130 (KNOWN_ISSUES).
    placeholders_ = {
        {"body", 0.0f, 0.0f, 0.08f, 0.80f, 0.50f, 0.30f},
    };

    starfield_.setup();
    placeholders_renderer_.setup();
}

void S10_HubbleHorizon::tick(float /*dt_seconds*/) {}

void S10_HubbleHorizon::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    starfield_.render(/*z_kin=*/0.0f);
    placeholders_renderer_.render(viewport_width, viewport_height,
                                  placeholders_, z_cosmo_);  // visual proxy
}

void S10_HubbleHorizon::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
    placeholders_.clear();
}

std::vector<validation::NumericAssertion> S10_HubbleHorizon::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;
    double d_proper = d_multiplier_ * D_HUBBLE_SI;
    auto obs = query_observe(d_proper);

    // 1) beyond_hubble_horizon flag is true.
    {
        validation::NumericAssertion a;
        a.name           = "beyond_hubble_horizon_at_12_d_hubble";
        a.measured_value = obs.beyond_hubble_horizon ? 1.0 : 0.0;
        a.expected_value = 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.12 Hubble horizon flag (audit D1)";
        a.libastra_call  = "astra::observe(d=1.2*D_HUBBLE_SI).beyond_hubble_horizon";
        out.push_back(a);
    }

    // 2) z_cosmo == H0 * d / c = 1.2 (linear weak-field). Compare libastra to closed form.
    {
        validation::NumericAssertion a;
        a.name           = "z_cosmo_at_12_d_hubble";
        a.measured_value = compute_z_cosmo(d_proper);
        a.expected_value = H0_SI * d_proper / C_LIGHT;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.12 cosmological redshift (linear weak-field)";
        a.libastra_call  = "astra::compute_z_cosmo(1.2 * D_HUBBLE_SI)";
        out.push_back(a);
    }

    // 3) z_cosmo == 1.2 exactly (since the multiplier IS d/D_HUBBLE = z by linear formula).
    {
        validation::NumericAssertion a;
        a.name           = "z_cosmo_equals_multiplier";
        a.measured_value = obs.z_cosmo;
        a.expected_value = d_multiplier_;
        a.tolerance      = 1e-12;
        a.spec_section   = "§3.12 linear-z weak-field invariant";
        a.libastra_call  = "astra::observe(d=1.2*D_HUBBLE_SI).z_cosmo == 1.2";
        out.push_back(a);
    }

    // 4) d_proper equals 1.2 * D_HUBBLE_SI within float precision.
    {
        validation::NumericAssertion a;
        a.name           = "d_proper_at_setup";
        a.measured_value = obs.d_proper;
        a.expected_value = d_multiplier_ * D_HUBBLE_SI;
        a.tolerance      = 1.0;  // 1 meter tolerance on ~10^26 m scale = trivially exact
        a.spec_section   = "§1.1 distance integrity at Hubble scale";
        a.libastra_call  = "astra::observe(...).d_proper";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S10_HubbleHorizon::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;
    if (placeholders_.empty()) return out;

    // Body center pixel = apply_kin_redshift(unshifted_color, z_cosmo).
    const auto& p = placeholders_[0];
    physics::RGB shifted = physics::apply_kin_redshift(
        physics::RGB{p.r, p.g, p.b}, z_cosmo_);

    int cx = ndc_x_to_topleft(p.ndc_x, last_viewport_w_);
    int cy = ndc_y_to_topleft(p.ndc_y, last_viewport_h_);

    auto add = [&](const char* nm, int ch, float expected) {
        validation::ScalarPixelAssertion a;
        a.name           = nm;
        a.framebuffer_x  = cx;
        a.framebuffer_y  = cy;
        a.channel        = ch;
        a.expected_value = expected;
        a.tolerance      = kPixelTol;
        a.spec_section   = "§3.12 cosmologically-redshifted body color (visual proxy)";
        a.libastra_call  = "physics::apply_kin_redshift(body_rgb, z_cosmo)";
        out.push_back(a);
    };
    add("body_redshifted_R", 0, shifted.r);
    add("body_redshifted_G", 1, shifted.g);
    add("body_redshifted_B", 2, shifted.b);

    return out;
}

}  // namespace astra::scenes
