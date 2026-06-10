// log.h - one-line wrappers around printf so we can re-target later if we want.
// Stays single-translation-unit and dependency-free on purpose.
//
// Also hosts a single tiny helper unrelated to logging: exe_directory(). It
// returns the absolute path of the directory containing the running .exe so
// renderer code can locate `shaders/...` next to the binary regardless of cwd.
#pragma once

#include <string>

namespace astra_viz::log {

void info(const char* fmt, ...);
void warn(const char* fmt, ...);
void error(const char* fmt, ...);

} // namespace astra_viz::log

namespace astra_viz {

// Returns a trailing-slash terminated absolute path. Resolved once and cached.
const std::string& exe_directory();

} // namespace astra_viz
