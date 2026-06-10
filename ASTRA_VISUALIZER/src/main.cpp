// src/main.cpp — ASTRA-7 Visualizer entry.
//
// Parses CLI, dispatches to interactive Application or headless runner.

#include "app/application.h"
#include "app/cli.h"
#include "app/headless_mode.h"
#include "util/log.h"

#include <cstdio>

int main(int argc, char** argv) {
    using namespace astra::app;

    CliArgs args = parse(argc, argv);

    if (args.show_help) {
        print_help();
        return 0;
    }
    if (args.show_version) {
        print_version();
        return 0;
    }
    if (!args.valid()) {
        std::fprintf(stderr, "[CLI] %s\n", args.parse_error.c_str());
        std::fprintf(stderr, "[CLI] use --help for usage.\n");
        return 64;  // EX_USAGE
    }

    if (args.headless) {
        return run_headless(args);
    }
    if (args.regenerate_goldens) {
        // V1: not yet implemented. Will be hooked once scene infrastructure lands.
        astra::log::error("--regenerate-goldens not yet implemented (V1 stub)");
        return 70;  // EX_SOFTWARE
    }
    if (args.record_sequence) {
        astra::log::error("--record-png-sequence not yet implemented (V1 stub)");
        return 70;
    }

    // Default: interactive.
    Application app;
    if (!app.init(args)) {
        astra::log::error("Application::init failed");
        return 70;
    }
    int rc = app.run();
    app.shutdown();
    return rc;
}
