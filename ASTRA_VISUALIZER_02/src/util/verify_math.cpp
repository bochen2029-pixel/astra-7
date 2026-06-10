#include "util/verify_math.h"

#include "astra_nexus/constants.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/vec3.h"

#include <cmath>
#include <cstdio>

namespace astra_viz {

namespace {

// Mirrors proto/astra_nexus.cpp:894-910 print_obs_row format byte-for-byte
// so the output diffs cleanly against the canon binary's demo_voyage().
void print_obs_row(const char* label, const astra::ObservableState& o) {
    std::printf("  %-32s d=%6.2f ly | v_rad=%+8.2fc | rate=%+10.4f",
                label,
                o.d_proper / astra::LIGHT_YEAR,
                o.v_radial / astra::C_LIGHT,
                o.apparent_rate);
    if (o.time_reversed) {
        std::printf("  TIME REVERSED at %.2fx", std::fabs(o.apparent_rate));
    } else if (o.apparent_rate > 1.5) {
        std::printf("  fast-forward %.2fx", o.apparent_rate);
    } else if (o.apparent_rate < 0.5) {
        std::printf("  slow-mo %.4fx", o.apparent_rate);
    } else {
        std::printf("  ~real-time");
    }
    std::printf("\n");
}

} // anon

int run_verify_math() {
    std::printf("\n========================= VOYAGE DEMO =========================\n");
    std::printf("Ship starts at rest near a planet 1 ly away (in +z direction).\n");
    std::printf("Accelerates, then enters WARP, observing the planet behind.\n\n");

    using astra::C_LIGHT;
    using astra::LIGHT_YEAR;
    astra::Vec3 planet{0, 0, -1.0 * LIGHT_YEAR};
    double t = 1.0e10;

    struct Phase {
        const char* label;
        astra::Vec3 ship_pos;
        astra::Vec3 ship_vel;
        uint32_t regime;
    };

    Phase phases[] = {
        {"REST near origin",                  {0,0,0}, {0, 0, 0},                       astra::R_REST},
        {"STL_NONREL 0.05c +z",               {0,0,0}, {0, 0, 0.05 * C_LIGHT},          astra::R_STL_NONREL},
        {"STL_REL 0.5c +z (recede)",          {0,0,0}, {0, 0, 0.5 * C_LIGHT},           astra::R_STL_REL},
        {"STL_REL 0.9c +z (recede)",          {0,0,0}, {0, 0, 0.9 * C_LIGHT},           astra::R_STL_REL},
        {"STL_REL 0.99c +z (recede)",         {0,0,0}, {0, 0, 0.99 * C_LIGHT},          astra::R_STL_REL},
        {"WARP_CRUISE 1c (recede)",           {0,0,0}, {0, 0, 1.0 * C_LIGHT},           astra::R_WARP_CRUISE},
        {"WARP_CRUISE 2c (recede)",           {0,0,0}, {0, 0, 2.0 * C_LIGHT},           astra::R_WARP_CRUISE},
        {"WARP_CRUISE 10c (recede)",          {0,0,0}, {0, 0, 10.0 * C_LIGHT},          astra::R_WARP_CRUISE},
        {"WARP_CRUISE 100c (recede)",         {0,0,0}, {0, 0, 100.0 * C_LIGHT},         astra::R_WARP_CRUISE},
        {"WARP_CRUISE 8000c (recede)",        {0,0,0}, {0, 0, 8000.0 * C_LIGHT},        astra::R_WARP_CRUISE},
        {"WARP_CRUISE 2c APPROACH (-z)",      {0,0,0}, {0, 0, -2.0 * C_LIGHT},          astra::R_WARP_CRUISE},
    };

    for (const auto& p : phases) {
        astra::ObservableState o = astra::observe(p.ship_pos, p.ship_vel, t, planet, 0.0, p.regime);
        print_obs_row(p.label, o);
    }
    std::printf("\nNote: STL_REL formulas (SR longitudinal Doppler) and WARP formulas\n");
    std::printf("(classical retarded-time, bubble gamma=1) differ. The spec must lock\n");
    std::printf("regime-dispatched apparent-rate to render this correctly.\n");
    return 0;
}

} // namespace astra_viz
