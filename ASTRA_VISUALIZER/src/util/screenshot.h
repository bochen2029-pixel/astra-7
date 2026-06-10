// src/util/screenshot.h — write the contents of a GL framebuffer to a PNG.
//
// Uses stb_image_write. Reads RGBA8 from the bound framebuffer (default 0,
// or the supplied FBO name), flips vertically (GL is bottom-left; PNG is
// top-left), writes the file.

#pragma once

#include <cstdint>

namespace astra::util {

// Returns true on success. Pass framebuffer_name == 0 for the default backbuffer.
bool save_framebuffer_png(const char* path,
                          int width,
                          int height,
                          unsigned int framebuffer_name);

}  // namespace astra::util
