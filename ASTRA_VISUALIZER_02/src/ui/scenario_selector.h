// scenario_selector.h - dropdown of registered scenes in an ImGui top-bar.
#pragma once

namespace astra_viz {

class SceneRouter;

namespace ui {

void draw_scenario_selector(SceneRouter& router);

} // namespace ui
} // namespace astra_viz
