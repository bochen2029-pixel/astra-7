// src/app/headless_mode.h — headless CI runner.
//
// Spec: DESIGN_SPEC §2.3 "Per frame (headless mode)" + §7.4 "validation report
// (JSON output for CI)".

#pragma once

namespace astra::app {

struct CliArgs;

// Returns process exit code:
//   0 on success (all assertions PASS),
//   1 on assertion failures,
//   2+ on infrastructure errors (CUDA/GL/IO).
int run_headless(const CliArgs& args);

}  // namespace astra::app
