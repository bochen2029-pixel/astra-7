// screenshot.h - PNG dump + load helpers built on stb_image_write / stb_image.
// All buffers are tightly packed 8-bit RGBA (4 bytes per pixel, row-major,
// origin TOP-LEFT after the y-flip GL_PACK_INVERT_Y is applied during readback).
#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace astra_viz {

// Reads the default framebuffer at (0, 0, w, h), 4-byte RGBA per pixel, flipped
// so output[0] is the TOP-LEFT pixel (matches PNG row order).
void read_framebuffer_rgba8(int x, int y, int w, int h, std::vector<uint8_t>& out);

// Writes RGBA8 data to a PNG. Returns true on success.
bool save_png_rgba8(const std::string& path, int w, int h, const uint8_t* data);

// Loads a PNG into RGBA8 pixels. Returns true on success; sets w, h, out.
bool load_png_rgba8(const std::string& path, int& w, int& h, std::vector<uint8_t>& out);

} // namespace astra_viz
