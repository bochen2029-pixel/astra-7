// src/scenes/i_scene.h — IScene interface for renderable physics scenes.
//
// Spec: DESIGN_SPEC §6 ("The 12 visual test scenes"); each scene returns
// pixel + libastra-derived assertions, an optional golden image path, and a
// canonical timestamp at which the golden was captured.

#pragma once

#include <string>
#include <vector>

#include "validation/scalar_pixel_assertion.h"

namespace astra::scenes {

class IScene {
public:
    virtual ~IScene() = default;

    // Short scene id, e.g. "S01_RestBaseline". Stable; used in CLI + reports.
    virtual const char* name() const = 0;

    // Human-readable description. Shown in UI; not parsed.
    virtual const char* description() const { return ""; }

    // One-time setup (creates GL resources, loads scenario JSON, etc.).
    // Called on the GL thread with the visualizer's context current.
    virtual void setup() = 0;

    // Advance simulation by `dt_seconds`. Called once per frame.
    virtual void tick(float dt_seconds) = 0;

    // Render content into the currently-bound framebuffer.
    virtual void render(int viewport_width, int viewport_height) = 0;

    // ImGui parameter / state panel for the right-hand UI column.
    virtual void render_ui() {}

    // Tear down GL resources.
    virtual void teardown() = 0;

    // Pixel-level assertions evaluated by the validation layer each frame
    // (interactive) or at the canonical timestamp (headless).
    virtual std::vector<validation::ScalarPixelAssertion> assertions() const {
        return {};
    }

    // Libastra-derived numeric assertions: precomputed values from
    // libastra_nexus that the scene reports as canonical references. These
    // run in headless mode WITHOUT needing rendering to land, so they are
    // the V1.2 unit-of-account.
    virtual std::vector<validation::NumericAssertion> numeric_assertions() const {
        return {};
    }

    // Path to canonical-golden PNG (relative to assets/reference_renders/).
    // nullptr = no golden recorded yet.
    virtual const char* golden_path() const { return nullptr; }

    // The simulation timestamp at which the golden was captured / should be
    // sampled in headless mode. Default: scene-start (t=0).
    virtual float canonical_timestamp_seconds() const { return 0.0f; }

    // Total wall-clock seconds the headless runner should advance before
    // sampling assertions. Default: 0 (sample immediately at t=0).
    virtual float headless_warmup_seconds() const { return 0.0f; }
};

}  // namespace astra::scenes
