// src/app/cli.h — CLI argument parser.
//
// Spec: see DESIGN_SPEC §8 "CLI design".
//
// Forms:
//   astra_visualizer.exe
//   astra_visualizer.exe --scene=S05_WarpCruise2c
//   astra_visualizer.exe --scene=5                      (numeric shorthand)
//   astra_visualizer.exe --headless --scene=all --output=ci_results/
//   astra_visualizer.exe --regenerate-goldens --scene=all
//   astra_visualizer.exe --record-png-sequence --scene=S05 --duration=30 --output=seq/
//   astra_visualizer.exe --version
//   astra_visualizer.exe --help

#pragma once

#include <string>

namespace astra::app {

struct CliArgs {
    // Mode selection (mutually exclusive within {headless, regenerate_goldens, record_sequence}).
    bool interactive          = true;
    bool headless             = false;
    bool regenerate_goldens   = false;
    bool record_sequence      = false;

    // Information flags.
    bool show_version = false;
    bool show_help    = false;

    // Per-mode parameters.
    std::string scene;          // "S05_WarpCruise2c", "S05", "5", or "all"
    std::string output;         // output directory
    double      duration = 0.0; // seconds (for --record-png-sequence)

    // Interactive-only window hints.
    int width  = 1280;
    int height = 720;

    // Parse error message (empty when ok).
    std::string parse_error;

    bool valid() const { return parse_error.empty(); }
};

CliArgs parse(int argc, char** argv);

void print_help();
void print_version();

}  // namespace astra::app
