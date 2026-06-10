// main.cpp - tiny CLI parser + hand-off to Application::run.
// CLI surface (V1):
//   astra_visualizer.exe                       -> interactive, first registered scene
//   astra_visualizer.exe --scene=S05           -> interactive, jump to S05
//   astra_visualizer.exe --width=2560 --height=1440
//   astra_visualizer.exe --help
// Headless mode (--headless --scene=all) lands in V9.
#include "app/application.h"
#include "util/verify_math.h"

#include <cstdio>
#include <cstring>
#include <string>

namespace {

void print_help() {
    std::printf(
        "ASTRA-7 visualizer (V1)\n"
        "  astra_visualizer.exe                  open interactive window\n"
        "  --scene=ID                            jump to scene (S01..S12)\n"
        "  --width=N --height=N                  window size (default 1920x1080)\n"
        "  --bench=N                             run N frames, VSync off, print stats, exit\n"
        "  --no-volume                           disable V3 CUDA-GL volume render (diagnostic)\n"
        "  --headless [--scene=ID|all]           hidden window; evaluate scene assertion(s); exit 0 if all PASS\n"
        "  --headless-frames=N                   warm-up frames per scene before sampling (default 30)\n"
        "  --output=DIR                          write per-scene PNG + report.json into DIR (headless)\n"
        "  --regenerate-goldens                  overwrite assets/reference_renders/*.png (operator-sign-off)\n"
        "  --verify-math                         dump the canonical voyage table; exits\n"
        "                                        (diffs byte-for-byte vs proto/astra_nexus demo_voyage)\n"
        "  --help                                this message\n"
        "\n"
        "Controls (interactive):\n"
        "  W/A/S/D/Q/E or Space/Ctrl  fly camera\n"
        "  Shift                       boost (10x speed)\n"
        "  RMB drag                    look around\n"
        "  1..9, Shift+1..3            switch scene\n"
        "  P                           pause sim\n"
        "  Esc                         quit\n"
    );
}

bool starts_with(const char* s, const char* prefix) {
    return std::strncmp(s, prefix, std::strlen(prefix)) == 0;
}

} // anon

int main(int argc, char** argv) {
    astra_viz::AppOptions opts;
    for (int i = 1; i < argc; i++) {
        const char* a = argv[i];
        if (!std::strcmp(a, "--help") || !std::strcmp(a, "-h")) {
            print_help(); return 0;
        }
        if (!std::strcmp(a, "--verify-math")) {
            return astra_viz::run_verify_math();
        }
        if (!std::strcmp(a, "--headless")) {
            if (opts.headless_scene_id.empty()) opts.headless_scene_id = "all";
        } else if (starts_with(a, "--headless-frames=")) {
            opts.headless_frames = std::atoi(a + std::strlen("--headless-frames="));
        } else if (starts_with(a, "--scene=")) {
            opts.start_scene_id = a + std::strlen("--scene=");
        } else if (starts_with(a, "--width=")) {
            opts.width = std::atoi(a + std::strlen("--width="));
        } else if (starts_with(a, "--height=")) {
            opts.height = std::atoi(a + std::strlen("--height="));
        } else if (starts_with(a, "--bench=")) {
            opts.bench_frames = std::atoi(a + std::strlen("--bench="));
        } else if (!std::strcmp(a, "--no-volume")) {
            opts.enable_volume = false;
        } else if (starts_with(a, "--output=")) {
            opts.output_dir = a + std::strlen("--output=");
        } else if (!std::strcmp(a, "--regenerate-goldens")) {
            opts.regenerate_goldens = true;
        } else {
            std::fprintf(stderr, "unknown arg: %s\n", a);
            print_help();
            return 64;
        }
    }
    // Resolve --headless --scene=ID into a single-scene headless run regardless
    // of arg order. "all" survives only if no --scene was given.
    if (!opts.headless_scene_id.empty() && !opts.start_scene_id.empty()) {
        opts.headless_scene_id = opts.start_scene_id;
    }
    return astra_viz::Application{}.run(opts);
}
