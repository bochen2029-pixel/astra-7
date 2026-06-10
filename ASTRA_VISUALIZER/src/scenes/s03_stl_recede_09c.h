// src/scenes/s03_stl_recede_09c.h — S03: STL_REL recede at beta=0.9.
//
// Spec: DESIGN_SPEC §6 S03 — parameter sweep of S02 with stronger redshift.
// gamma ~= 2.294; z_kin ~= 3.359 (sqrt(19) - 1).

#pragma once

#include "scenes/s02_stl_recede_05c.h"

namespace astra::scenes {

class S03_StlRecede09c : public S02_StlRecede05c {
public:
    const char* name() const override { return "S03_StlRecede09c"; }
    const char* description() const override {
        return "STL_REL recede at beta=0.9; z_kin ~= 3.359 (sqrt(19)-1)";
    }

protected:
    double beta() const override { return 0.9; }
};

}  // namespace astra::scenes
