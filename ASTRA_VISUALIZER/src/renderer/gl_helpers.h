// src/renderer/gl_helpers.h — minimal GL utilities (shader compile + link;
// fullscreen-quad VAO). Used by scenes to render placeholder content without
// each scene re-implementing GL boilerplate.

#pragma once

#include <cstdint>
#include <string>

#include <glad/gl.h>

namespace astra::renderer {

// Compile vertex + fragment GLSL into a linked program. Returns 0 + writes
// `*error_log` on failure. Caller owns the GLuint and must `glDeleteProgram`.
GLuint compile_program(const char* vertex_src,
                       const char* fragment_src,
                       std::string* error_log);

// Create a VAO + VBO for a single unit quad (-1..+1 in clip-space NDC).
// `out_vao` + `out_vbo` are filled. Caller deletes via `glDeleteVertexArrays`
// + `glDeleteBuffers`. Vertex layout: location 0 = vec2 ndc_position.
void create_unit_quad(GLuint* out_vao, GLuint* out_vbo);

// Render the unit quad bound via `vao`, using the currently-bound program.
inline void draw_unit_quad(GLuint vao) {
    glBindVertexArray(vao);
    glDrawArrays(GL_TRIANGLES, 0, 6);
    glBindVertexArray(0);
}

}  // namespace astra::renderer
