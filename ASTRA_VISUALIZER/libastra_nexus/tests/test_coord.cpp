// libastra_nexus/tests/test_coord.cpp
//
// AstraCoord (§1.1) — ported from proto/astra_nexus.cpp test::run_all
// "AstraCoord (§1.1)" + "AstraCoord at billion-light-year scale" sections.

#include <doctest/doctest.h>
#include "astra_nexus/coord.h"
#include "astra_nexus/constants.h"
#include <cmath>
#include <cstdint>

using namespace astra;

TEST_CASE("AstraCoord §1.1 — local + sector distance + renormalize") {
    AstraCoord a{0, 0, 0, 0, 0, 0};
    AstraCoord b{0, 0, 0, 1000.0, 0, 0};
    CHECK(std::abs(astra_distance(a, b) - 1000.0) < 1e-9);  // 1km local distance

    AstraCoord c{1, 0, 0, 0, 0, 0};
    CHECK(std::abs(astra_distance(a, c) - SECTOR_SIZE) < 1e-6);  // 1-sector distance

    AstraCoord d{0, 0, 0, 600000.0, 0, 0};  // exceeds LOCAL_MAX
    d.renormalize();
    CHECK(d.sx == 1);                                   // Renormalize rolls sx to 1
    CHECK(std::abs(d.lx - (-400000.0)) < 1e-9);        // Renormalize lx after roll

    // Round-trip
    d.lx += 1.5e6;
    d.renormalize();
    CHECK(std::abs((d.lx + d.sx * SECTOR_SIZE) - 2.1e6) < 1e-9);  // Round-trip preserves total
}

TEST_CASE("AstraCoord at billion-light-year scale") {
    // 100 Mly distance test
    double d_target = 100.0e6 * LIGHT_YEAR;
    int64_t sectors = (int64_t)(d_target / SECTOR_SIZE);
    AstraCoord ship{0, 0, 0, 0, 0, 0};
    AstraCoord far_obj{sectors, 0, 0, 0, 0, 0};
    double d = astra_distance(ship, far_obj);
    CHECK(std::abs(d - sectors * SECTOR_SIZE) < 1.0);  // Distance at 100 Mly scale, m-precision

    // Reach test: int64 sectors * 1000 km
    // 2^63 ~= 9.2e18, * 1e6 m = 9.2e24 m ~= 970 Mly
    double max_reach_ly = ((double)INT64_MAX * SECTOR_SIZE) / LIGHT_YEAR;
    CHECK(max_reach_ly > 9.0e8);  // AstraCoord reaches > 900M ly with sub-mm precision
}
