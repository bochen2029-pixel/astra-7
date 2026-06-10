// src/scenes/s02_stl_recede_05c.cpp

#include "scenes/s02_stl_recede_05c.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/rapidity.h"
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

}  // namespace

void S02_StlRecede05c::setup() {
    z_kin_ = static_cast<float>(astra::compute_z_kin(beta() * astra::C_LIGHT));
    placeholders_ = {
        // Centered planet — rear view. Canonical ocean-blue color preserved
        // from S01 for cross-scene parity. Redshift applied per-pixel by the
        // PlaceholderRenderer's FS.
        {"planet", 0.0f, 0.0f, 0.12f, 0.30f, 0.55f, 0.90f},
    };
    starfield_.setup();
    placeholders_renderer_.setup();
}

void S02_StlRecede05c::tick(float /*dt_seconds*/) {}

void S02_StlRecede05c::render(int viewport_width, int viewport_height) {
    last_viewport_w_ = viewport_width;
    last_viewport_h_ = viewport_height;
    glClearColor(0.012f, 0.018f, 0.035f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    starfield_.render(z_kin_);
    placeholders_renderer_.render(viewport_width, viewport_height,
                                  placeholders_, z_kin_);
}

void S02_StlRecede05c::teardown() {
    placeholders_renderer_.teardown();
    starfield_.teardown();
    placeholders_.clear();
}

std::vector<validation::NumericAssertion> S02_StlRecede05c::numeric_assertions() const {
    using namespace astra;
    std::vector<validation::NumericAssertion> out;
    double b = beta();

    // gamma from libastra Rapidity vs analytic 1/sqrt(1-b^2)
    {
        validation::NumericAssertion a;
        a.name = "gamma_at_beta";
        Rapidity r{{0, 0, std::atanh(b)}};
        a.measured_value = r.gamma();
        a.expected_value = 1.0 / std::sqrt(1.0 - b * b);
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.7 v0.126 rapidity";
        a.libastra_call  = "astra::Rapidity{{0,0,atanh(beta)}}.gamma()";
        out.push_back(a);
    }

    // z_kin from libastra vs analytic sqrt((1+b)/(1-b)) - 1
    {
        validation::NumericAssertion a;
        a.name = "z_kin_at_beta";
        a.measured_value = compute_z_kin(b * C_LIGHT);
        a.expected_value = std::sqrt((1.0 + b) / (1.0 - b)) - 1.0;
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.4 SR longitudinal Doppler";
        a.libastra_call  = "astra::compute_z_kin(beta * C_LIGHT)";
        out.push_back(a);
    }

    // STL_REL apparent_rate sanity: never reverses; sqrt((1-b)/(1+b))
    {
        validation::NumericAssertion a;
        a.name = "apparent_rate_stl_rel";
        a.measured_value = compute_apparent_rate(b * C_LIGHT, R_STL_REL);
        a.expected_value = std::sqrt((1.0 - b) / (1.0 + b));
        a.tolerance      = 1e-9;
        a.spec_section   = "§3.11 STL_REL apparent rate (SR formula)";
        a.libastra_call  = "astra::compute_apparent_rate(beta*C_LIGHT, R_STL_REL)";
        out.push_back(a);
    }

    return out;
}

std::vector<validation::ScalarPixelAssertion> S02_StlRecede05c::assertions() const {
    std::vector<validation::ScalarPixelAssertion> out;
    if (last_viewport_w_ <= 0 || last_viewport_h_ <= 0) return out;
    if (placeholders_.empty()) return out;

    const auto& p = placeholders_[0];  // planet
    physics::RGB shifted = physics::apply_kin_redshift(
        physics::RGB{p.r, p.g, p.b}, z_kin_);

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
        a.spec_section   = "§3.4 SR longitudinal Doppler -> redshifted planet color";
        a.libastra_call  = "physics::apply_kin_redshift(planet_rgb, compute_z_kin(beta*C_LIGHT))";
        out.push_back(a);
    };
    add("planet_center_R_redshifted", 0, shifted.r);
    add("planet_center_G_redshifted", 1, shifted.g);
    add("planet_center_B_redshifted", 2, shifted.b);

    return out;
}

}  // namespace astra::scenes
