// graphics_program.h - a minimal GL shader-program wrapper. Loads vert+frag
// from disk (paths relative to the shader root), compiles, links, and exposes
// uniform setters. No reload-on-change; that's a v1.x improvement if we want it.
#pragma once

#include <cstdint>
#include <string>

namespace astra_viz {

class GraphicsProgram {
public:
    GraphicsProgram() = default;
    ~GraphicsProgram();

    GraphicsProgram(const GraphicsProgram&) = delete;
    GraphicsProgram& operator=(const GraphicsProgram&) = delete;

    // Returns false on any compile/link failure (already logged).
    bool load_from_files(const std::string& vert_path,
                         const std::string& frag_path);

    void use() const;

    // Convenience uniform setters. Cache location internally via glGetUniformLocation
    // each call - we're not in a hot enough loop to need a cache map.
    void set_int(const char* name, int v) const;
    void set_float(const char* name, float v) const;
    void set_vec3(const char* name, float x, float y, float z) const;
    void set_vec4(const char* name, float x, float y, float z, float w) const;
    void set_mat4(const char* name, const float* m_column_major) const;

    uint32_t id() const { return program_; }

private:
    uint32_t program_ = 0;
};

} // namespace astra_viz
