// hull.h - placeholder hull mesh. Procedurally generated as an elongated
// blended-wing-body approximating the 280m x 78m x 22m geometry from
// hull_design_v0.md. A real OBJ asset slots in here later.
#pragma once

#include <cstdint>
#include "renderer/graphics_program.h"

namespace astra_viz {

class Hull {
public:
    bool init();         // builds VAO/VBO + loads hull.vert/frag
    void shutdown();

    void draw(const float* view_col_major, const float* proj_col_major,
              float wall_time_s) const;

    uint32_t tri_count() const { return tri_count_; }

private:
    uint32_t vao_ = 0;
    uint32_t vbo_ = 0;
    uint32_t ebo_ = 0;
    uint32_t tri_count_ = 0;
    GraphicsProgram prog_;
};

} // namespace astra_viz
