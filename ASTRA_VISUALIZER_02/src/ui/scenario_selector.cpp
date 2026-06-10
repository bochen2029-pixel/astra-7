#include "ui/scenario_selector.h"
#include "app/scene_router.h"

#include <imgui.h>

namespace astra_viz::ui {

void draw_scenario_selector(SceneRouter& router) {
    ImGui::SetNextWindowPos(ImVec2(10, 10), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(330, 0), ImGuiCond_FirstUseEver);
    if (ImGui::Begin("Scene", nullptr, ImGuiWindowFlags_AlwaysAutoResize)) {
        int idx = router.current_index();
        const char* preview = router.label(idx);
        if (ImGui::BeginCombo("##scenes", preview)) {
            for (int i = 0; i < router.scene_count(); i++) {
                bool selected = (i == idx);
                if (ImGui::Selectable(router.label(i), selected)) {
                    router.set_current(i);
                }
                if (selected) ImGui::SetItemDefaultFocus();
            }
            ImGui::EndCombo();
        }
        ImGui::TextDisabled("1-9, Shift+1-3 to switch  |  hold RMB to look");
    }
    ImGui::End();
}

} // namespace astra_viz::ui
