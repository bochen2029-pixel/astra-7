#include "app/scene_router.h"
#include "scenes/s01_rest_baseline.h"
#include "scenes/s02_stl_recede_05c.h"
#include "scenes/s03_stl_recede_09c.h"
#include "scenes/s04_warp_charge.h"
#include "scenes/s05_warp_cruise_2c.h"
#include "scenes/s06_warp_cruise_10c_cherenkov.h"
#include "scenes/s07_photon_source_history.h"
#include "scenes/s08_warp_gravity_well.h"
#include "scenes/s09_chaos_reflex.h"
#include "scenes/s10_hubble_horizon.h"
#include "scenes/s11_split_screen.h"
#include "scenes/s12_eye_ear_decoupling.h"

#include "astra_nexus/regime.h"

namespace astra_viz {

SceneRouter::SceneRouter() {
    using namespace astra;
    scenes_.emplace_back(std::make_unique<S01RestBaseline>());
    scenes_.emplace_back(std::make_unique<S02StlRecede05c>());
    scenes_.emplace_back(std::make_unique<S03StlRecede09c>());
    scenes_.emplace_back(std::make_unique<S04WarpCharge>());
    scenes_.emplace_back(std::make_unique<S05WarpCruise2c>());
    scenes_.emplace_back(std::make_unique<S06WarpCruise10cCherenkov>());
    scenes_.emplace_back(std::make_unique<S07PhotonSourceHistory>());
    scenes_.emplace_back(std::make_unique<S08WarpGravityWell>());
    scenes_.emplace_back(std::make_unique<S09ChaosReflex>());
    scenes_.emplace_back(std::make_unique<S10HubbleHorizon>());
    scenes_.emplace_back(std::make_unique<S11SplitScreen>());
    scenes_.emplace_back(std::make_unique<S12EyeEarDecoupling>());
}

void SceneRouter::set_current(int idx) {
    if (idx < 0 || idx >= (int)scenes_.size() || idx == current_) return;
    if (current_scene()) current_scene()->deactivate();
    current_ = idx;
    if (current_scene()) current_scene()->activate();
}

IScene* SceneRouter::current_scene() const {
    return (current_ >= 0 && current_ < (int)scenes_.size()) ? scenes_[current_].get() : nullptr;
}

} // namespace astra_viz
