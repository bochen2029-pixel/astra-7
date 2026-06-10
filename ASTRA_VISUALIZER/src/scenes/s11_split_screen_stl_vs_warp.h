// src/scenes/s11_split_screen_stl_vs_warp.h — S11: Split-screen STL_REL vs
// WARP_CRUISE at the same v_radial=0.5c.
//
// Spec: DESIGN_SPEC §6 S11; §3.11 regime-dispatched apparent rate; §10
// validation row "STL_REL formula was NOT 1/gamma".
//
// At v_radial = 0.5c:
//   STL_REL apparent_rate = sqrt((1-0.5)/(1+0.5)) = sqrt(1/3) ~= 0.5774
//   WARP_CRUISE apparent_rate = 1 - 0.5                       = 0.5000
//   Ratio: 1.155 — both regimes positive but distinguishably different.
//
// V1.11 stage: side-by-side rendering. Left half = STL_REL (planet shown
// with z_kin redshift applied; receding inertially). Right half = WARP_CRUISE
// (planet shown without redshift; bubble crew is locally inertial at gamma=1
// per spec §3.3 — only the geometric retarded-time effect changes things,
// no SR Doppler color). Pixel + numeric assertions confirm both rates +
// regime distinction.

#pragma once

#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S11_SplitScreenStlVsWarp : public IScene {
public:
    const char* name() const override { return "S11_SplitScreenStlVsWarp"; }
    const char* description() const override {
        return "Split-screen STL_REL vs WARP_CRUISE at v_radial=0.5c; regime distinction";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 0.0f; }
    float headless_warmup_seconds()  const override     { return 0.0f; }

private:
    static constexpr double beta_ = 0.5;  // same v_radial for both regimes

    // Both panels render the same planet at NDC origin of their own half;
    // canonical "ocean blue" color matches S01/S02/S03/S05.
    static constexpr float kPlanetR = 0.30f;
    static constexpr float kPlanetG = 0.55f;
    static constexpr float kPlanetB = 0.90f;

    // Doppler z_kin applied to the LEFT (STL) half only.
    float z_kin_stl_ = 0.0f;

    renderer::StarfieldRenderer     starfield_;
    renderer::PlaceholderRenderer   placeholders_renderer_;
    std::vector<renderer::Placeholder> planet_;  // single-element; reused for both halves

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
