// json_report.h - emits the headless-run JSON report at the path passed via
// --output=DIR. Format per DESIGN_SPEC §6 / CLAUDE.md §11.4. No nlohmann/json
// dependency yet; the report is small enough that hand-formatted output keeps
// the link surface clean.
#pragma once

#include <string>
#include <vector>

#include "validation/assertion.h"
#include "validation/golden_diff.h"

namespace astra_viz {

struct SceneReportRow {
    std::string scene_id;
    std::string scene_label;
    std::vector<AssertionResult> results;
    GoldenDiffResult              golden;     // golden_present=false means "skipped"
    std::string                   screenshot_path;
};

struct HeadlessReport {
    std::string version          = "0.1.0";
    int         libastra_assertion_count = 0;
    int         scenes_passed    = 0;
    int         scenes_failed    = 0;
    int         total_assertions = 0;
    int         assertions_passed = 0;
    std::vector<SceneReportRow>   scenes;
};

bool write_json_report(const std::string& path, const HeadlessReport& report);

} // namespace astra_viz
