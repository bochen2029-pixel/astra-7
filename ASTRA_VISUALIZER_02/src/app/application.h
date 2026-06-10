// application.h - the main loop owner. Owns GL context, hull + starfield,
// camera, scene router, ImGui state. main.cpp just constructs + run()s this.
#pragma once

#include <string>

namespace astra_viz {

struct AppOptions {
    int  width  = 1920;
    int  height = 1080;
    std::string start_scene_id;     // "S01" etc.; empty = use first

    // Smoke-test path: run `bench_frames` with VSync off, print frame stats, exit.
    // 0 means normal interactive mode. Used by CI and V1 gate verification.
    int  bench_frames = 0;

    // V3 trivial CUDA-GL volume; on by default. CLI `--no-volume` turns it off
    // for diagnostic isolation (e.g. confirming a runtime issue is volume-side).
    bool enable_volume = true;

    // Headless evaluation. When non-empty, opens a hidden window, snaps the
    // camera to each scene's canonical pose, runs `headless_frames` frames
    // per scene, evaluates value + pixel assertions, dumps summary to stdout,
    // exits with 0 only if all assertions pass. "all" runs every registered
    // scene with assertions defined. Otherwise the value is a single scene ID.
    std::string headless_scene_id;
    int         headless_frames = 30;

    // Output directory for headless screenshots + JSON report. Empty means
    // skip both (V8 behaviour: stdout summary only).
    std::string output_dir;

    // V9: writes a fresh golden PNG per scene to assets/reference_renders/.
    // Loud warning printed first. CI must NEVER pass this flag without the
    // operator's explicit per-run sign-off (commit-message marker is the
    // expected sign-off mechanism per CLAUDE.md §11.2).
    bool regenerate_goldens = false;
};

class Application {
public:
    int run(const AppOptions& opts);
};

} // namespace astra_viz
