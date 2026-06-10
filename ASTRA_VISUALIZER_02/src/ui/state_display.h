// state_display.h - right-side panel; defers to the active scene's draw_state_panel.
#pragma once

namespace astra_viz {

class SceneRouter;
class FrameTimer;
class Camera;

namespace ui {

void draw_state_display(SceneRouter& router, const FrameTimer& timer, const Camera& cam);

} // namespace ui
} // namespace astra_viz
