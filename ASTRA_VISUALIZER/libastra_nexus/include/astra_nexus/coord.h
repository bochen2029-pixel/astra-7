// libastra_nexus/include/astra_nexus/coord.h
//
// AstraCoord (§1.1) — 128-bit hierarchical floating origin.
// Extracted from proto/astra_nexus.cpp lines 88-115 (READ-ONLY source).
// Semantics IDENTICAL.

#pragma once

#include "constants.h"

namespace astra {

struct AstraCoord {
    int64_t sx, sy, sz;
    double  lx, ly, lz;

    void renormalize();
};

// Distance between two AstraCoords, accounting for sector offsets.
double astra_distance(const AstraCoord& a, const AstraCoord& b);

}  // namespace astra
