// src/util/screenshot.cpp

#include "util/screenshot.h"
#include "util/log.h"

#include <glad/gl.h>

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include <stb_image_write.h>

#include <cstring>
#include <vector>

namespace astra::util {

bool save_framebuffer_png(const char* path,
                          int width,
                          int height,
                          unsigned int framebuffer_name)
{
    if (width <= 0 || height <= 0 || !path) return false;

    GLint prev_read = 0;
    glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING, &prev_read);
    glBindFramebuffer(GL_READ_FRAMEBUFFER, framebuffer_name);
    glPixelStorei(GL_PACK_ALIGNMENT, 1);

    std::vector<unsigned char> pixels(static_cast<size_t>(width) * height * 4);
    glReadPixels(0, 0, width, height, GL_RGBA, GL_UNSIGNED_BYTE, pixels.data());
    glBindFramebuffer(GL_READ_FRAMEBUFFER, static_cast<GLuint>(prev_read));

    // Flip Y (GL is bottom-left origin; PNG is top-left).
    const size_t row_bytes = static_cast<size_t>(width) * 4;
    std::vector<unsigned char> flipped(pixels.size());
    for (int y = 0; y < height; y++) {
        std::memcpy(flipped.data() + static_cast<size_t>(y) * row_bytes,
                    pixels.data()  + static_cast<size_t>(height - 1 - y) * row_bytes,
                    row_bytes);
    }

    int ok = stbi_write_png(path, width, height, 4, flipped.data(),
                            static_cast<int>(row_bytes));
    if (!ok) {
        log::error("stbi_write_png failed: %s", path);
        return false;
    }
    return true;
}

}  // namespace astra::util
