// src/app/scene_router.cpp

#include "app/scene_router.h"
#include "scenes/i_scene.h"

// Scene includes — add as scenes land.
#include "scenes/s01_rest_baseline.h"
#include "scenes/s02_stl_recede_05c.h"
#include "scenes/s03_stl_recede_09c.h"
#include "scenes/s04_warp_charge.h"
#include "scenes/s05_warp_cruise_2c.h"
#include "scenes/s06_warp_cruise_10c_cherenkov.h"
#include "scenes/s07_warp_8000c_history_bound.h"
#include "scenes/s08_warp_gravity_well.h"
#include "scenes/s10_hubble_horizon.h"
#include "scenes/s11_split_screen_stl_vs_warp.h"
#include "scenes/s09_chaos_reflex.h"
#include "scenes/s12_eye_ear_decoupling.h"

#include <algorithm>
#include <cctype>

namespace astra::app {

namespace {

std::string to_upper(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return std::toupper(c); });
    return s;
}

bool is_numeric(const std::string& s) {
    if (s.empty()) return false;
    for (char c : s) if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    return true;
}

}  // namespace

SceneRouter::SceneRouter() {
    register_builtin();
}

void SceneRouter::add(const char* short_id, const char* full_id, const char* desc, Factory f) {
    entries_.push_back({short_id, full_id, desc, std::move(f)});
}

void SceneRouter::register_builtin() {
    add("S01", "S01_RestBaseline", "REST sanity check",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S01_RestBaseline>();
        });
    add("S02", "S02_StlRecede05c", "STL_REL recede at beta=0.5 (z_kin ~= 0.732)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S02_StlRecede05c>();
        });
    add("S03", "S03_StlRecede09c", "STL_REL recede at beta=0.9 (z_kin ~= 3.359)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S03_StlRecede09c>();
        });
    add("S04", "S04_WarpCharge", "Warp charge ramp 0..5s -> WARP_CRUISE",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S04_WarpCharge>();
        });
    add("S05", "S05_WarpCruise2c", "Warp Cruise 2c: planet orbits backward (retarded-time)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S05_WarpCruise2c>();
        });
    add("S06", "S06_WarpCruise10cCherenkov", "Warp Cruise 10c + Cherenkov cone (closes 5D-F4)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S06_WarpCruise10cCherenkov>();
        });
    add("S07", "S07_Warp8000cHistoryBound", "Warp 8000c photon-history bound (planet GONE not faded)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S07_Warp8000cHistoryBound>();
        });
    add("S08", "S08_WarpGravityWell", "Warp 0.8W + 10 M_sun BH; composite WARP_CRUISE | GRAVITY_WELL",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S08_WarpGravityWell>();
        });
    add("S09", "S09_ChaosReflex", "Fisher-KPP chaos PDE + Reflex damping (V1.13 CPU)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S09_ChaosReflex>();
        });
    add("S10", "S10_HubbleHorizon", "Body beyond Hubble horizon; frozen + redshifted",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S10_HubbleHorizon>();
        });
    add("S11", "S11_SplitScreenStlVsWarp", "Split-screen STL_REL vs WARP at v=0.5c; regime distinction",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S11_SplitScreenStlVsWarp>();
        });
    add("S12", "S12_EyeEarDecoupling", "Warp-egress eye-ear decoupling (visual lags audio mid-shutdown)",
        []() -> std::unique_ptr<scenes::IScene> {
            return std::make_unique<scenes::S12_EyeEarDecoupling>();
        });
    // V2+ scenes register here. S09 (chaos PDE + Reflex) is the only one left,
    // and requires CUDA compute work beyond the V0 sanity kernel.
}

std::unique_ptr<scenes::IScene> SceneRouter::create(const std::string& id_in) const {
    std::string id = to_upper(id_in);

    // numeric form ("5" -> "S05")
    if (is_numeric(id_in)) {
        int n = std::stoi(id_in);
        char buf[8];
        std::snprintf(buf, sizeof(buf), "S%02d", n);
        id = buf;
    }

    for (const auto& e : entries_) {
        if (to_upper(e.short_id) == id || to_upper(e.full_id) == id) {
            return e.factory();
        }
    }
    return nullptr;
}

std::vector<std::unique_ptr<scenes::IScene>> SceneRouter::create_all() const {
    std::vector<std::unique_ptr<scenes::IScene>> out;
    out.reserve(entries_.size());
    for (const auto& e : entries_) {
        out.emplace_back(e.factory());
    }
    return out;
}

}  // namespace astra::app
