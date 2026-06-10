// physics_calc_panel.h - global ImGui calculator panel. Sliders for regime,
// v_radial, W, distance; live readout of the full PhysicsCalcOutput. Lets the
// operator sweep canonical configurations and watch libastra_nexus numbers
// change without touching code.
#pragma once

#include "physics/physics_core.h"

namespace astra_viz::ui {

class PhysicsCalcPanel {
public:
    PhysicsCalcPanel();
    void draw();

    const PhysicsCalcInput&  input()  const { return input_; }
    const PhysicsCalcOutput& output() const { return output_; }

private:
    PhysicsCalcInput  input_;
    PhysicsCalcOutput output_;
    int regime_choice_ = 0;
    int preset_choice_ = 0;
};

} // namespace astra_viz::ui
