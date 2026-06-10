#include "ui/state_display.h"
#include "app/camera.h"
#include "app/scene_router.h"
#include "scenes/scene_base.h"
#include "util/timer.h"

#include <imgui.h>

namespace astra_viz::ui {

void draw_state_display(SceneRouter& router, const FrameTimer& timer, const Camera& cam) {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    float right = vp->WorkPos.x + vp->WorkSize.x - 360.0f;
    ImGui::SetNextWindowPos(ImVec2(right, 10.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(350, 0), ImGuiCond_FirstUseEver);

    if (ImGui::Begin("State", nullptr, ImGuiWindowFlags_AlwaysAutoResize)) {
        ImGui::Text("frame: %.2f ms  (%.0f FPS avg)",
                    timer.avg_dt_s() * 1000.0, timer.avg_fps());
        auto p = cam.position();
        ImGui::Text("cam:   (%.1f, %.1f, %.1f) m", p.x, p.y, p.z);
        ImGui::Separator();

        IScene* s = router.current_scene();
        if (s) {
            s->draw_state_panel();
        } else {
            ImGui::TextDisabled("(no scene active)");
        }
    }
    ImGui::End();
}

} // namespace astra_viz::ui
