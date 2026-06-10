// assertion_panel.h - ImGui panel showing each value-assertion's PASS / FAIL
// status for the currently-active scene. Pixel assertions don't render here
// because they require the canonical camera pose (interactive camera moves
// would make them flap). Headless mode dumps pixel assertion results to stdout.
#pragma once

#include <vector>
#include "validation/assertion.h"

namespace astra_viz {

class SceneRouter;

namespace ui {

void draw_assertion_panel(SceneRouter& router,
                          const std::vector<AssertionResult>& last_results);

} // namespace ui
} // namespace astra_viz
