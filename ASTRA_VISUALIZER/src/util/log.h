// src/util/log.h — minimal printf-style logger.

#pragma once

#include <cstdio>

namespace astra::log {

template <typename... Args>
void info(const char* fmt, Args... args) {
    std::printf("[INFO] ");
    std::printf(fmt, args...);
    std::printf("\n");
    std::fflush(stdout);
}

template <typename... Args>
void warn(const char* fmt, Args... args) {
    std::fprintf(stderr, "[WARN] ");
    std::fprintf(stderr, fmt, args...);
    std::fprintf(stderr, "\n");
    std::fflush(stderr);
}

template <typename... Args>
void error(const char* fmt, Args... args) {
    std::fprintf(stderr, "[ERR ] ");
    std::fprintf(stderr, fmt, args...);
    std::fprintf(stderr, "\n");
    std::fflush(stderr);
}

}  // namespace astra::log
