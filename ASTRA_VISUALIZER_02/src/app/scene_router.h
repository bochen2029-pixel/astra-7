// scene_router.h - owns the list of registered scenes + the currently-active one.
// In V1 only S01 RestBaseline has a real implementation; S02-S12 register as
// "coming soon" stub IScenes that show a placeholder state panel.
#pragma once

#include <memory>
#include <vector>

#include "scenes/scene_base.h"

namespace astra_viz {

class SceneRouter {
public:
    SceneRouter();

    int  current_index() const { return current_; }
    void set_current(int idx);

    IScene* current_scene() const;

    int scene_count() const { return (int)scenes_.size(); }
    const char* label(int i) const { return scenes_[i]->label(); }
    const char* id(int i)    const { return scenes_[i]->id(); }

private:
    std::vector<std::unique_ptr<IScene>> scenes_;
    int current_ = 0;
};

} // namespace astra_viz
