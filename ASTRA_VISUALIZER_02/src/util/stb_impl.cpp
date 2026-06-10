// stb_impl.cpp - centralised single-header STB implementations. Other TUs
// include "stb_image.h" / "stb_image_write.h" with no _IMPLEMENTATION macro;
// the actual code lives here so linker doesn't see duplicate symbols.
#define STB_IMAGE_IMPLEMENTATION
#include <stb_image.h>

#define STB_IMAGE_WRITE_IMPLEMENTATION
#include <stb_image_write.h>
