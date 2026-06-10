// src/app/cli.cpp — CLI argument parser implementation.

#include "app/cli.h"

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <string_view>

#ifndef ASTRA_VIS_VERSION
#define ASTRA_VIS_VERSION "0.0.0-dev"
#endif

namespace astra::app {

namespace {

// `--key=value` -> {key, value, true}; `--flag` -> {flag, "", false}.
struct KV {
    std::string key;
    std::string value;
    bool has_value;
};

KV split_kv(std::string_view arg) {
    if (arg.size() < 2 || arg.substr(0, 2) != "--") {
        return KV{std::string(arg), "", false};
    }
    auto rest = arg.substr(2);
    auto eq = rest.find('=');
    if (eq == std::string_view::npos) {
        return KV{std::string(rest), "", false};
    }
    return KV{std::string(rest.substr(0, eq)),
              std::string(rest.substr(eq + 1)),
              true};
}

}  // namespace

CliArgs parse(int argc, char** argv) {
    CliArgs out;
    for (int i = 1; i < argc; i++) {
        KV kv = split_kv(argv[i]);
        const std::string& k = kv.key;

        if (k == "help" || k == "-h" || k == "h") {
            out.show_help = true;
            continue;
        }
        if (k == "version" || k == "-v" || k == "v") {
            out.show_version = true;
            continue;
        }
        if (k == "headless") {
            out.headless = true;
            out.interactive = false;
            continue;
        }
        if (k == "regenerate-goldens") {
            out.regenerate_goldens = true;
            out.interactive = false;
            continue;
        }
        if (k == "record-png-sequence") {
            out.record_sequence = true;
            out.interactive = false;
            continue;
        }
        if (k == "scene") {
            if (!kv.has_value) { out.parse_error = "--scene requires =value"; return out; }
            out.scene = kv.value;
            continue;
        }
        if (k == "output") {
            if (!kv.has_value) { out.parse_error = "--output requires =value"; return out; }
            out.output = kv.value;
            continue;
        }
        if (k == "duration") {
            if (!kv.has_value) { out.parse_error = "--duration requires =value"; return out; }
            out.duration = std::atof(kv.value.c_str());
            continue;
        }
        if (k == "width") {
            if (!kv.has_value) { out.parse_error = "--width requires =value"; return out; }
            out.width = std::atoi(kv.value.c_str());
            continue;
        }
        if (k == "height") {
            if (!kv.has_value) { out.parse_error = "--height requires =value"; return out; }
            out.height = std::atoi(kv.value.c_str());
            continue;
        }
        out.parse_error = std::string("unknown argument: ") + argv[i];
        return out;
    }

    // Cross-mode validation.
    if (out.headless && out.output.empty() && !out.show_help && !out.show_version) {
        out.parse_error = "--headless requires --output=PATH";
        return out;
    }
    if (out.regenerate_goldens && out.scene.empty()) {
        out.parse_error = "--regenerate-goldens requires --scene=NAME (or --scene=all)";
        return out;
    }
    if (out.record_sequence && (out.scene.empty() || out.output.empty() || out.duration <= 0.0)) {
        out.parse_error = "--record-png-sequence requires --scene, --output, --duration > 0";
        return out;
    }
    return out;
}

void print_help() {
    std::printf(
        "astra_visualizer v" ASTRA_VIS_VERSION " — ASTRA-7 Visual Physics Testbed\n"
        "\n"
        "Modes:\n"
        "  astra_visualizer                                          interactive, scene chooser\n"
        "  astra_visualizer --scene=S05_WarpCruise2c                 interactive, jump to scene\n"
        "  astra_visualizer --headless --scene=all --output=ci/      batch render + JSON report\n"
        "  astra_visualizer --headless --scene=S05 --output=smoke/   single-scene smoke\n"
        "  astra_visualizer --regenerate-goldens --scene=all         (operator-sign-off action)\n"
        "  astra_visualizer --record-png-sequence --scene=S05 \\\n"
        "                   --duration=30 --output=seq/              N-second PNG sequence\n"
        "  astra_visualizer --version                                version info\n"
        "  astra_visualizer --help                                   this message\n"
        "\n"
        "Flags:\n"
        "  --scene=NAME            scene id (\"S01_RestBaseline\", \"S05\", \"5\", or \"all\")\n"
        "  --output=PATH           output directory (required for --headless / record / regenerate)\n"
        "  --headless              no window; render + dump PNGs + JSON report; exit\n"
        "  --regenerate-goldens    overwrite assets/reference_renders/*.png (sign-off required)\n"
        "  --record-png-sequence   record N seconds of PNGs (--duration=N)\n"
        "  --width=W --height=H    interactive window size (default 1280x720)\n"
        "  --duration=N            seconds, for --record-png-sequence\n"
        "  --version / -v          print version + linked-lib info\n"
        "  --help    / -h          this message\n"
        "\n"
        "Scenes (see DESIGN_SPEC §6 for full descriptions):\n"
        "  S01_RestBaseline           REST sanity check\n"
        "  S02_StlRecede05c           STL_REL beta=0.5 recede\n"
        "  S03_StlRecede09c           STL_REL beta=0.9 recede\n"
        "  S04_WarpCharge             Warp charge sequence\n"
        "  S05_WarpCruise2c           Warp cruise 2c (THE PAYOFF: orbit reversal)\n"
        "  S06_WarpCruise10cCherenkov Warp + Cherenkov cone (5D-F4 gap closure)\n"
        "  S07_Warp8000cHistoryBound  Photon-source-history bound\n"
        "  S08_WarpGravityWell        Warp + gravity well composition\n"
        "  S09_ChaosReflex            Chaos instability + Reflex stabilizer\n"
        "  S10_HubbleHorizon          Hubble-horizon body\n"
        "  S11_SplitScreenStlVsWarp   Split-screen STL vs WARP at same v_radial\n"
        "  S12_EyeEarDecoupling       Eye-ear decoupling at warp egress\n"
    );
}

void print_version() {
    std::printf(
        "astra_visualizer v" ASTRA_VIS_VERSION "\n"
        "linked: libastra_nexus (with cherenkov.h — closes AUDIT 5D-F4 gap)\n"
        "toolchain: MSVC + CUDA + OpenGL 4.6 + GLFW + GLAD2 + Dear ImGui\n"
    );
}

}  // namespace astra::app
