#include "ui/assertion_panel.h"
#include "app/scene_router.h"
#include "scenes/scene_base.h"

#include <imgui.h>

namespace astra_viz::ui {

void draw_assertion_panel(SceneRouter& router,
                          const std::vector<AssertionResult>& last_results) {
    ImGuiViewport* vp = ImGui::GetMainViewport();
    float right = vp->WorkPos.x + vp->WorkSize.x - 360.0f;
    float top   = vp->WorkPos.y + 380.0f;
    ImGui::SetNextWindowPos(ImVec2(right, top), ImGuiCond_FirstUseEver);
    ImGui::SetNextWindowSize(ImVec2(350, 0), ImGuiCond_FirstUseEver);

    if (!ImGui::Begin("Assertions  (value layer)")) { ImGui::End(); return; }

    IScene* scene = router.current_scene();
    if (!scene) {
        ImGui::TextDisabled("(no scene active)");
        ImGui::End();
        return;
    }

    int passed = 0, failed = 0;
    for (const auto& r : last_results) {
        if (r.passed) passed++; else failed++;
    }
    ImVec4 hdr = (failed == 0) ? ImVec4(0.5f, 1.0f, 0.5f, 1.0f)
                                : ImVec4(1.0f, 0.4f, 0.4f, 1.0f);
    ImGui::TextColored(hdr, "%d PASS / %d FAIL  (value assertions)", passed, failed);
    ImGui::TextDisabled("(pixel assertions evaluate in --headless mode only)");
    ImGui::Separator();

    for (const auto& r : last_results) {
        ImVec4 c = r.passed ? ImVec4(0.7f, 1.0f, 0.7f, 1.0f)
                            : ImVec4(1.0f, 0.5f, 0.5f, 1.0f);
        ImGui::TextColored(c, "[%s] %s", r.passed ? "PASS" : "FAIL", r.name.c_str());
        if (!r.passed) {
            ImGui::SameLine();
            ImGui::TextDisabled("(got %.6g, exp %.6g, diff %.3g)",
                                r.measured, r.expected, r.diff);
        }
    }

    ImGui::End();
}

} // namespace astra_viz::ui
