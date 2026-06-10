#include "validation/screenshot.h"
#include "util/log.h"

#include <glad/gl.h>
#include <stb_image.h>
#include <stb_image_write.h>

namespace astra_viz {

void read_framebuffer_rgba8(int x, int y, int w, int h, std::vector<uint8_t>& out) {
    out.resize((size_t)w * h * 4);
    glFinish();
    glPixelStorei(GL_PACK_ALIGNMENT, 1);
    glReadPixels(x, y, w, h, GL_RGBA, GL_UNSIGNED_BYTE, out.data());
    // glReadPixels returns rows from bottom to top; flip to TOP-LEFT origin for PNG output.
    std::vector<uint8_t> row((size_t)w * 4);
    for (int yy = 0; yy < h / 2; yy++) {
        uint8_t* a = out.data() + (size_t)yy * w * 4;
        uint8_t* b = out.data() + (size_t)(h - 1 - yy) * w * 4;
        std::copy(a, a + w * 4, row.begin());
        std::copy(b, b + w * 4, a);
        std::copy(row.begin(), row.end(), b);
    }
}

bool save_png_rgba8(const std::string& path, int w, int h, const uint8_t* data) {
    int rc = stbi_write_png(path.c_str(), w, h, 4, data, w * 4);
    if (!rc) {
        astra_viz::log::error("stbi_write_png failed: %s", path.c_str());
        return false;
    }
    return true;
}

bool load_png_rgba8(const std::string& path, int& w, int& h, std::vector<uint8_t>& out) {
    int ww = 0, hh = 0, ch = 0;
    uint8_t* pixels = stbi_load(path.c_str(), &ww, &hh, &ch, 4);
    if (!pixels) {
        return false;
    }
    w = ww; h = hh;
    out.assign(pixels, pixels + (size_t)ww * hh * 4);
    stbi_image_free(pixels);
    return true;
}

} // namespace astra_viz
