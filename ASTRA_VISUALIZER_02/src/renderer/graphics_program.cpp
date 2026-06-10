#include "renderer/graphics_program.h"
#include "util/log.h"

#include <glad/gl.h>

#include <fstream>
#include <sstream>
#include <vector>

namespace astra_viz {

static std::string read_file(const std::string& path) {
    std::ifstream f(path, std::ios::binary);
    if (!f) {
        astra_viz::log::error("could not open shader file: %s", path.c_str());
        return {};
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

static uint32_t compile_stage(uint32_t kind, const std::string& src, const char* label) {
    uint32_t s = glCreateShader(kind);
    const char* p = src.c_str();
    glShaderSource(s, 1, &p, nullptr);
    glCompileShader(s);
    int ok = 0;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        int len = 0;
        glGetShaderiv(s, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len + 1, '\0');
        glGetShaderInfoLog(s, len, nullptr, log.data());
        astra_viz::log::error("shader compile (%s) failed:\n%s", label, log.data());
        glDeleteShader(s);
        return 0;
    }
    return s;
}

GraphicsProgram::~GraphicsProgram() {
    if (program_) glDeleteProgram(program_);
}

bool GraphicsProgram::load_from_files(const std::string& vert_path,
                                     const std::string& frag_path) {
    std::string vsrc = read_file(vert_path);
    std::string fsrc = read_file(frag_path);
    if (vsrc.empty() || fsrc.empty()) return false;

    uint32_t vs = compile_stage(GL_VERTEX_SHADER,   vsrc, vert_path.c_str());
    uint32_t fs = compile_stage(GL_FRAGMENT_SHADER, fsrc, frag_path.c_str());
    if (!vs || !fs) {
        if (vs) glDeleteShader(vs);
        if (fs) glDeleteShader(fs);
        return false;
    }

    uint32_t p = glCreateProgram();
    glAttachShader(p, vs);
    glAttachShader(p, fs);
    glLinkProgram(p);

    int ok = 0;
    glGetProgramiv(p, GL_LINK_STATUS, &ok);
    if (!ok) {
        int len = 0;
        glGetProgramiv(p, GL_INFO_LOG_LENGTH, &len);
        std::vector<char> log(len + 1, '\0');
        glGetProgramInfoLog(p, len, nullptr, log.data());
        astra_viz::log::error("program link failed (%s + %s):\n%s",
                              vert_path.c_str(), frag_path.c_str(), log.data());
        glDeleteShader(vs);
        glDeleteShader(fs);
        glDeleteProgram(p);
        return false;
    }
    glDetachShader(p, vs);
    glDetachShader(p, fs);
    glDeleteShader(vs);
    glDeleteShader(fs);

    if (program_) glDeleteProgram(program_);
    program_ = p;
    return true;
}

void GraphicsProgram::use() const { if (program_) glUseProgram(program_); }

void GraphicsProgram::set_int(const char* name, int v) const {
    glUniform1i(glGetUniformLocation(program_, name), v);
}
void GraphicsProgram::set_float(const char* name, float v) const {
    glUniform1f(glGetUniformLocation(program_, name), v);
}
void GraphicsProgram::set_vec3(const char* name, float x, float y, float z) const {
    glUniform3f(glGetUniformLocation(program_, name), x, y, z);
}
void GraphicsProgram::set_vec4(const char* name, float x, float y, float z, float w) const {
    glUniform4f(glGetUniformLocation(program_, name), x, y, z, w);
}
void GraphicsProgram::set_mat4(const char* name, const float* m_column_major) const {
    glUniformMatrix4fv(glGetUniformLocation(program_, name), 1, GL_FALSE, m_column_major);
}

} // namespace astra_viz
