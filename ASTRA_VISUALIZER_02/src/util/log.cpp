#include "util/log.h"

#include <cstdarg>
#include <cstdio>
#include <string>

#ifdef _WIN32
#  define WIN32_LEAN_AND_MEAN
#  include <windows.h>
#endif

namespace astra_viz::log {

static void vprint(const char* tag, const char* fmt, std::va_list args) {
    std::fprintf(stderr, "[%s] ", tag);
    std::vfprintf(stderr, fmt, args);
    std::fprintf(stderr, "\n");
}

void info(const char* fmt, ...) {
    std::va_list args; va_start(args, fmt); vprint("info", fmt, args); va_end(args);
}
void warn(const char* fmt, ...) {
    std::va_list args; va_start(args, fmt); vprint("warn", fmt, args); va_end(args);
}
void error(const char* fmt, ...) {
    std::va_list args; va_start(args, fmt); vprint("err ", fmt, args); va_end(args);
}

} // namespace astra_viz::log

namespace astra_viz {

const std::string& exe_directory() {
    static std::string cached;
    if (!cached.empty()) return cached;
#ifdef _WIN32
    char buf[1024];
    DWORD n = GetModuleFileNameA(nullptr, buf, sizeof(buf));
    if (n > 0 && n < sizeof(buf)) {
        std::string p(buf, n);
        size_t slash = p.find_last_of("\\/");
        if (slash != std::string::npos) cached = p.substr(0, slash + 1);
    }
#endif
    if (cached.empty()) cached = "./";
    return cached;
}

} // namespace astra_viz
