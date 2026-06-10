// parameter_panel.h - per-scene parameter tunables. Defers to
// IScene::draw_parameter_panel() so each scene controls its own sliders.
#pragma once

namespace astra_viz {

class SceneRouter;

namespace ui {

void draw_parameter_panel(SceneRouter& router);

} // namespace ui
} // namespace astra_viz
