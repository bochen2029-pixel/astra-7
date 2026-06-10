// src/renderer/gl_helpers.cpp

#include "renderer/gl_helpers.h"

#include <cstdio>
#include <vector>

namespace astra::renderer {

namespace {

GLuint compile_one(GLenum kind, const char* src, std::string* error_log) {
    GLuint sh = glCreateShader(kind);
    glShaderSource(sh, 1, &src, nullptr);
    glCompileShader(sh);
    GLint ok = 0;
    glGetShaderiv(sh, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        GLint len = 0;
        glGetShaderiv(sh, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len > 0 ? len : 1);
        glGetShaderInfoLog(sh, len, nullptr, log.data());
        if (error_log) {
            *error_log = std::string(kind == GL_VERTEX_SHADER ? "[VS] " : "[FS] ") + log.data();
        }
        glDeleteShader(sh);
        return 0;
    }
    return sh;
}

}  // namespace

GLuint compile_program(const char* vertex_src,
                       const char* fragment_src,
                       std::string* error_log)
{
    GLuint vs = compile_one(GL_VERTEX_SHADER,   vertex_src,   error_log);
    if (!vs) return 0;
    GLuint fs = compile_one(GL_FRAGMENT_SHADER, fragment_src, error_log);
    if (!fs) { glDeleteShader(vs); return 0; }

    GLuint prog = glCreateProgram();
    glAttachShader(prog, vs);
    glAttachShader(prog, fs);
    glLinkProgram(prog);
    glDeleteShader(vs);
    glDeleteShader(fs);

    GLint ok = 0;
    glGetProgramiv(prog, GL_LINK_STATUS, &ok);
    if (!ok) {
        GLint len = 0;
        glGetProgramiv(prog, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len > 0 ? len : 1);
        glGetProgramInfoLog(prog, len, nullptr, log.data());
        if (error_log) *error_log = std::string("[LINK] ") + log.data();
        glDeleteProgram(prog);
        return 0;
    }
    return prog;
}

void create_unit_quad(GLuint* out_vao, GLuint* out_vbo) {
    // Two triangles covering [-1, +1] in NDC. Vertex layout: vec2.
    static const float verts[12] = {
        -1.0f, -1.0f,
         1.0f, -1.0f,
        -1.0f,  1.0f,

         1.0f, -1.0f,
         1.0f,  1.0f,
        -1.0f,  1.0f,
    };
    GLuint vao = 0, vbo = 0;
    glGenVertexArrays(1, &vao);
    glGenBuffers(1, &vbo);
    glBindVertexArray(vao);
    glBindBuffer(GL_ARRAY_BUFFER, vbo);
    glBufferData(GL_ARRAY_BUFFER, sizeof(verts), verts, GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 2 * sizeof(float), nullptr);
    glBindVertexArray(0);
    glBindBuffer(GL_ARRAY_BUFFER, 0);
    *out_vao = vao;
    *out_vbo = vbo;
}

}  // namespace astra::renderer
