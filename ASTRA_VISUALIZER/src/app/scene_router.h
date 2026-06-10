// src/app/scene_router.h — registry of scene factories.
//
// Scenes register themselves via factory closures. Resolution accepts
// short ids ("S05"), full ids ("S05_WarpCruise2c"), numeric strings ("5"),
// and the special name "all" (returns the full registered list).

#pragma once

#include <functional>
#include <memory>
#include <string>
#include <vector>

namespace astra::scenes { class IScene; }

namespace astra::app {

class SceneRouter {
public:
    using Factory = std::function<std::unique_ptr<scenes::IScene>()>;

    struct Entry {
        std::string short_id;   // "S01"
        std::string full_id;    // "S01_RestBaseline"
        std::string description;
        Factory factory;
    };

    SceneRouter();

    // Construct one scene by id (short / full / numeric). Returns nullptr if no match.
    std::unique_ptr<scenes::IScene> create(const std::string& id) const;

    // Construct all scenes (used by --scene=all in headless mode).
    std::vector<std::unique_ptr<scenes::IScene>> create_all() const;

    // Read-only list of registered entries (for --help, etc.).
    const std::vector<Entry>& entries() const { return entries_; }

private:
    void register_builtin();
    void add(const char* short_id, const char* full_id, const char* desc, Factory f);

    std::vector<Entry> entries_;
};

}  // namespace astra::app
