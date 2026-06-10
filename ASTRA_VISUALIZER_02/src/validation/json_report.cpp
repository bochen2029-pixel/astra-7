#include "validation/json_report.h"
#include "util/log.h"

#include <cstdio>
#include <fstream>

namespace astra_viz {

namespace {

void write_escaped(std::ostream& os, const std::string& s) {
    os << '"';
    for (char c : s) {
        switch (c) {
            case '"':  os << "\\\""; break;
            case '\\': os << "\\\\"; break;
            case '\n': os << "\\n"; break;
            case '\r': os << "\\r"; break;
            case '\t': os << "\\t"; break;
            default:   os << c;
        }
    }
    os << '"';
}

} // anon

bool write_json_report(const std::string& path, const HeadlessReport& r) {
    std::ofstream f(path);
    if (!f) {
        astra_viz::log::error("could not open %s for write", path.c_str());
        return false;
    }
    f << "{\n";
    f << "  \"version\": "; write_escaped(f, r.version); f << ",\n";
    f << "  \"libastra_assertion_count\": " << r.libastra_assertion_count << ",\n";
    f << "  \"summary\": {\n";
    f << "    \"scenes_passed\":    " << r.scenes_passed    << ",\n";
    f << "    \"scenes_failed\":    " << r.scenes_failed    << ",\n";
    f << "    \"total_assertions\": " << r.total_assertions << ",\n";
    f << "    \"assertions_passed\": " << r.assertions_passed << "\n";
    f << "  },\n";
    f << "  \"scenes\": [\n";
    for (size_t i = 0; i < r.scenes.size(); i++) {
        const auto& s = r.scenes[i];
        f << "    {\n";
        f << "      \"id\": ";           write_escaped(f, s.scene_id);    f << ",\n";
        f << "      \"label\": ";        write_escaped(f, s.scene_label); f << ",\n";
        f << "      \"screenshot\": ";   write_escaped(f, s.screenshot_path); f << ",\n";
        f << "      \"golden\": {\n";
        f << "        \"present\": " << (s.golden.golden_present ? "true" : "false") << ",\n";
        f << "        \"mean_diff\": "  << s.golden.mean_rgb_diff << ",\n";
        f << "        \"max_diff\": "   << s.golden.max_rgb_diff  << ",\n";
        f << "        \"passed\": "     << (s.golden.passed ? "true" : "false") << ",\n";
        f << "        \"note\": ";      write_escaped(f, s.golden.note); f << "\n";
        f << "      },\n";
        f << "      \"assertions\": [\n";
        for (size_t k = 0; k < s.results.size(); k++) {
            const auto& a = s.results[k];
            f << "        {";
            f << "\"name\": ";     write_escaped(f, a.name);
            f << ", \"passed\": "  << (a.passed ? "true" : "false");
            f << ", \"expected\": " << a.expected;
            f << ", \"measured\": " << a.measured;
            f << ", \"diff\": "     << a.diff;
            f << "}";
            if (k + 1 < s.results.size()) f << ",";
            f << "\n";
        }
        f << "      ]\n";
        f << "    }";
        if (i + 1 < r.scenes.size()) f << ",";
        f << "\n";
    }
    f << "  ]\n";
    f << "}\n";
    return true;
}

} // namespace astra_viz
