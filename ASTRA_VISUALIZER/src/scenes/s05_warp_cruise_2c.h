// src/scenes/s05_warp_cruise_2c.h — S05: Warp Cruise at v_app=2c (THE PAYOFF).
//
// Spec: DESIGN_SPEC §6 S05 ("RetardedTimeOrbitReversal — orbit reversal at 2c").
//
// V1.10 stage: adds trail rendering (ring buffer of last N planet positions
// with progressively fading alpha). Without the trail a single frame just
// shows "a planet at a position"; with the trail the operator can see the
// motion DIRECTION at one glance, and the spec-distinctive backward sweep
// becomes unmistakable in interactive sign-off.

#pragma once

#include <cstdint>
#include <vector>

#include "renderer/placeholder_renderer.h"
#include "renderer/starfield_renderer.h"
#include "scenes/i_scene.h"

namespace astra::scenes {

class S05_WarpCruise2c : public IScene {
public:
    const char* name() const override { return "S05_WarpCruise2c"; }
    const char* description() const override {
        return "Warp Cruise v_app=2c: planet orbits BACKWARD via retarded-time observation";
    }

    void setup() override;
    void tick(float dt_seconds) override;
    void render(int viewport_width, int viewport_height) override;
    void teardown() override;

    std::vector<validation::NumericAssertion>    numeric_assertions() const override;
    std::vector<validation::ScalarPixelAssertion> assertions()        const override;

    float canonical_timestamp_seconds() const override { return 15.0f; }
    float headless_warmup_seconds()  const override     { return 15.0f; }

private:
    // Scene parameters.
    static constexpr double v_app_over_c_   = 2.0;
    static constexpr double period_seconds_ = 60.0;
    static constexpr float  orbit_radius_ndc_ = 0.40f;

    // Canonical planet color (V1.10: held as named constants for both rendering
    // and assertion-expected-value derivation).
    static constexpr float kPlanetR = 0.30f;
    static constexpr float kPlanetG = 0.55f;
    static constexpr float kPlanetB = 0.90f;

    // Trail capacity + subsample. 60 entries appended once per ~0.25s of sim
    // time. With period_seconds_=60s and rate=-1, 60 entries span 15s of sim
    // = 90 degrees of orbit — clearly visible arc.
    static constexpr int    kTrailLen           = 60;
    static constexpr double kTrailAppendInterval = 0.25;  // seconds of sim per trail entry

    // Sim state. V1.10: sim_time is double to survive float-accumulation drift
    // under headless 60Hz chunked ticking (900 chunks * float drift -> ~6e-5 t_emit
    // error -> phase drift past 1e-6 tolerance).
    double sim_time_seconds_ = 0.0;
    double apparent_rate_    = -1.0;
    double t_emit_           = 0.0;
    double current_phase_    = 0.0;
    float  planet_ndc_x_     = orbit_radius_ndc_;  // initial (phase=0)
    float  planet_ndc_y_     = 0.0f;

    // Trail ring buffer.
    struct TrailPoint { float ndc_x, ndc_y; };
    std::vector<TrailPoint> trail_;
    int    trail_count_              = 0;     // valid entries in [0, kTrailLen]
    double next_trail_append_time_   = 0.0;   // sim_time at which to append next entry

    renderer::PlaceholderRenderer  placeholders_renderer_;
    renderer::StarfieldRenderer    starfield_;

    mutable int last_viewport_w_ = 0;
    mutable int last_viewport_h_ = 0;
};

}  // namespace astra::scenes
