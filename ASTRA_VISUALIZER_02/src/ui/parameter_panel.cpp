#include "ui/parameter_panel.h"
#include "app/scene_router.h"
#include "scenes/scene_base.h"

#include <imgui.h>

namespace astra_viz::ui {

void draw_parameter_panel(SceneRouter& router) {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(ImVec2(10.0f, 110.0f), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(330, 0), ImGuiCond_FirstUseEver);
    (void)vp;

    if (!ImGui::Begin("Scene parameters")) { ImGui::End(); return; }
    IScene* s = router.current_scene();
    if (!s) {
        ImGui::TextDisabled("(no scene active)");
    } else {
        s->draw_parameter_panel();
    }
    ImGui::End();
}

} // namespace astra_viz::ui
