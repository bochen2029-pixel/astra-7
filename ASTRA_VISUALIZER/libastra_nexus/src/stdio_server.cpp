// libastra_nexus/src/stdio_server.cpp
//
// JSON-over-stdio bridge for proto/textverse (preserved from Day 2 v0.128).
// Extracted from proto/astra_nexus.cpp lines 950-1382. Semantics IDENTICAL.
//
// Wire format (unchanged):
//   request:  {"op":"<name>","args":{<json-object-of-string-or-number>}}
//   response: {"ok":true,"result":<number|string|object>}
//             {"ok":false,"error":"<message>"}

#include "astra_nexus/stdio_server.h"
#include "astra_nexus/constants.h"
#include "astra_nexus/regime.h"
#include "astra_nexus/observe.h"
#include "astra_nexus/composition.h"
#include "astra_nexus/kepler.h"

#include <cctype>
#include <cstdio>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>

namespace astra {
namespace stdio_server {

namespace {

struct JValue {
    enum Type { NUMBER, STRING, OBJECT } type = OBJECT;
    double n = 0.0;
    std::string s;
    std::map<std::string, JValue> obj;
};

void skip_ws(const std::string& src, size_t& i) {
    while (i < src.size() && std::isspace(static_cast<unsigned char>(src[i]))) i++;
}

std::string parse_string(const std::string& src, size_t& i) {
    if (i >= src.size() || src[i] != '"') throw std::runtime_error("expected string");
    i++;
    std::string out;
    while (i < src.size() && src[i] != '"') {
        if (src[i] == '\\') {
            i++;
            if (i >= src.size()) throw std::runtime_error("unterminated escape");
            char c = src[i++];
            switch (c) {
                case 'n':  out += '\n'; break;
                case 't':  out += '\t'; break;
                case 'r':  out += '\r'; break;
                case '\\': out += '\\'; break;
                case '"':  out += '"';  break;
                case '/':  out += '/';  break;
                default:   out += c;    break;
            }
        } else {
            out += src[i++];
        }
    }
    if (i >= src.size()) throw std::runtime_error("unterminated string");
    i++;  // skip closing "
    return out;
}

double parse_number(const std::string& src, size_t& i) {
    size_t start = i;
    if (i < src.size() && (src[i] == '-' || src[i] == '+')) i++;
    while (i < src.size()) {
        char c = src[i];
        bool ok = std::isdigit(static_cast<unsigned char>(c)) || c == '.'
                  || c == 'e' || c == 'E' || c == '+' || c == '-';
        if (!ok) break;
        i++;
    }
    if (i == start) throw std::runtime_error("expected number");
    return std::stod(src.substr(start, i - start));
}

JValue parse_value(const std::string& src, size_t& i);

JValue parse_object(const std::string& src, size_t& i) {
    if (i >= src.size() || src[i] != '{') throw std::runtime_error("expected object");
    i++;
    skip_ws(src, i);
    JValue out;
    out.type = JValue::OBJECT;
    if (i < src.size() && src[i] == '}') { i++; return out; }
    while (true) {
        skip_ws(src, i);
        std::string key = parse_string(src, i);
        skip_ws(src, i);
        if (i >= src.size() || src[i] != ':') throw std::runtime_error("expected ':'");
        i++;
        skip_ws(src, i);
        out.obj[key] = parse_value(src, i);
        skip_ws(src, i);
        if (i < src.size() && src[i] == ',') { i++; continue; }
        if (i < src.size() && src[i] == '}') { i++; break; }
        throw std::runtime_error("expected ',' or '}'");
    }
    return out;
}

JValue parse_value(const std::string& src, size_t& i) {
    skip_ws(src, i);
    if (i >= src.size()) throw std::runtime_error("unexpected EOF");
    if (src[i] == '"') {
        JValue v;
        v.type = JValue::STRING;
        v.s = parse_string(src, i);
        return v;
    }
    if (src[i] == '{') return parse_object(src, i);
    JValue v;
    v.type = JValue::NUMBER;
    v.n = parse_number(src, i);
    return v;
}

std::string escape_json_string(const std::string& s) {
    std::string out;
    out += '"';
    for (char c : s) {
        if      (c == '"')  out += "\\\"";
        else if (c == '\\') out += "\\\\";
        else if (c == '\n') out += "\\n";
        else if (c == '\r') out += "\\r";
        else if (c == '\t') out += "\\t";
        else                out += c;
    }
    out += '"';
    return out;
}

std::string make_ok_number(double n) {
    char buf[64];
    std::snprintf(buf, sizeof(buf), "{\"ok\":true,\"result\":%.17g}", n);
    return buf;
}

std::string make_ok_string(const std::string& s) {
    return "{\"ok\":true,\"result\":" + escape_json_string(s) + "}";
}

// All values encoded as numeric (bools encoded as 0/1) to keep the wire
// format stable and the Python NexusResponse parser simple.
std::string make_ok_object(const std::map<std::string, double>& kv) {
    std::string out = "{\"ok\":true,\"result\":{";
    bool first = true;
    for (const auto& [k, v] : kv) {
        if (!first) out += ",";
        first = false;
        char buf[64];
        std::snprintf(buf, sizeof(buf), "%.17g", v);
        out += escape_json_string(k) + ":" + buf;
    }
    out += "}}";
    return out;
}

std::string make_error(const std::string& msg) {
    return "{\"ok\":false,\"error\":" + escape_json_string(msg) + "}";
}

Vec3 parse_vec3(const JValue& v) {
    if (v.type != JValue::OBJECT) throw std::runtime_error("expected vec3 object");
    auto get_num = [&](const char* k) -> double {
        auto it = v.obj.find(k);
        if (it == v.obj.end() || it->second.type != JValue::NUMBER)
            throw std::runtime_error(std::string("vec3 missing/non-numeric '") + k + "'");
        return it->second.n;
    };
    return Vec3{get_num("x"), get_num("y"), get_num("z")};
}

double require_number(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end() || it->second.type != JValue::NUMBER)
        throw std::runtime_error(std::string("missing or non-numeric '") + key + "'");
    return it->second.n;
}

const std::string& require_string(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end() || it->second.type != JValue::STRING)
        throw std::runtime_error(std::string("missing or non-string '") + key + "'");
    return it->second.s;
}

Vec3 require_vec3(const JValue& args, const char* key) {
    auto it = args.obj.find(key);
    if (it == args.obj.end())
        throw std::runtime_error(std::string("missing vec3 '") + key + "'");
    return parse_vec3(it->second);
}

uint32_t parse_regime_string(const std::string& s) {
    if (s == "REST")          return R_REST;
    if (s == "STL_NONREL")    return R_STL_NONREL;
    if (s == "STL_REL")       return R_STL_REL;
    if (s == "WARP_CHARGE")   return R_WARP_CHARGE;
    if (s == "WARP_CRUISE")   return R_WARP_CRUISE;
    if (s == "WARP_SHUTDOWN") return R_WARP_SHUTDOWN;
    if (s == "GRAVITY_WELL")  return R_GRAVITY_WELL;
    if (s == "CRYOSLEEP")     return R_CRYOSLEEP;
    throw std::runtime_error("unknown regime: " + s);
}

std::string dispatch(const JValue& req) {
    if (req.type != JValue::OBJECT) {
        return make_error("request must be a JSON object");
    }
    auto it_op = req.obj.find("op");
    if (it_op == req.obj.end()) return make_error("missing 'op' field");
    if (it_op->second.type != JValue::STRING) return make_error("'op' must be a string");
    const std::string& op = it_op->second.s;

    JValue args;
    auto it_args = req.obj.find("args");
    if (it_args != req.obj.end()) args = it_args->second;

    if (op == "health") {
        return make_ok_string("alive");
    }

    if (op == "version") {
        return make_ok_string("astra_nexus v0.128");
    }

    if (op == "compute_apparent_rate") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        auto it_v = args.obj.find("v_radial");
        auto it_r = args.obj.find("regime");
        if (it_v == args.obj.end() || it_v->second.type != JValue::NUMBER) {
            return make_error("missing or non-numeric 'v_radial'");
        }
        if (it_r == args.obj.end() || it_r->second.type != JValue::STRING) {
            return make_error("missing or non-string 'regime'");
        }
        try {
            uint32_t regime = parse_regime_string(it_r->second.s);
            double rate = compute_apparent_rate(it_v->second.n, regime);
            return make_ok_number(rate);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "kepler_at") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            Orbit orb;
            orb.a      = require_number(args, "a");
            orb.e      = require_number(args, "e");
            orb.period = require_number(args, "period");
            orb.t0     = require_number(args, "t0");
            double t   = require_number(args, "t");
            return make_ok_number(orbit_phase(orb, t));
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "composition_rule_evaluate") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            double W_warp     = require_number(args, "W_warp");
            double grav       = require_number(args, "grav_factor");
            double gamma_kin  = require_number(args, "gamma_kin");
            double warp_flag  = require_number(args, "warp_active");
            bool warp_active  = warp_flag != 0.0;
            return make_ok_number(dtau_dt_cosmic(W_warp, grav, gamma_kin, warp_active));
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "retarded_time_solve") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            double d_proper = require_number(args, "d_proper");
            double z_cosmo  = require_number(args, "z_cosmo");
            double t_cosmic = require_number(args, "t_cosmic");
            double lookback = compute_lookback(d_proper, z_cosmo);
            return make_ok_number(t_cosmic - lookback);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "observe") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            Vec3 ship_pos       = require_vec3(args, "ship_pos");
            Vec3 ship_velocity  = require_vec3(args, "ship_velocity");
            double t_cosmic     = require_number(args, "t_cosmic");
            Vec3 body_pos       = require_vec3(args, "body_pos");
            double body_metric  = require_number(args, "body_metric_shift");
            uint32_t regime     = parse_regime_string(require_string(args, "regime"));
            double body_t_source_start = -std::numeric_limits<double>::infinity();
            auto it_tss = args.obj.find("body_t_source_start");
            if (it_tss != args.obj.end() && it_tss->second.type == JValue::NUMBER) {
                body_t_source_start = it_tss->second.n;
            }
            ObservableState obs = observe(ship_pos, ship_velocity, t_cosmic,
                                          body_pos, body_metric, regime,
                                          body_t_source_start);
            std::map<std::string, double> result;
            result["d_proper"]              = obs.d_proper;
            result["v_radial"]              = obs.v_radial;
            result["z_cosmo"]               = obs.z_cosmo;
            result["z_kin"]                 = obs.z_kin;
            result["z_metric"]              = obs.z_metric;
            result["z_total"]               = obs.z_total;
            result["t_emit"]                = obs.t_emit;
            result["apparent_rate"]         = obs.apparent_rate;
            result["time_reversed"]         = obs.time_reversed ? 1.0 : 0.0;
            result["beyond_photon_history"] = obs.beyond_photon_history ? 1.0 : 0.0;
            result["beyond_hubble_horizon"] = obs.beyond_hubble_horizon ? 1.0 : 0.0;
            return make_ok_object(result);
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "detect_regime") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        try {
            double rapidity_omega = require_number(args, "rapidity_omega");
            double warp_present_f = require_number(args, "warp_present");
            double cryo_f         = require_number(args, "cryosleep_active");
            double grav_factor    = require_number(args, "grav_factor");
            bool warp_present     = warp_present_f != 0.0;
            bool cryosleep_active = cryo_f != 0.0;

            uint32_t base = 0;
            if (warp_present) {
                const std::string& phase = require_string(args, "warp_phase");
                if      (phase == "charging") base = R_WARP_CHARGE;
                else if (phase == "cruising") base = R_WARP_CRUISE;
                else if (phase == "dropping") base = R_WARP_SHUTDOWN;
                else if (phase == "shutdown") base = R_WARP_SHUTDOWN;
                else throw std::runtime_error("unknown warp_phase: " + phase);
            } else {
                if (rapidity_omega == 0.0) {
                    base = R_REST;
                } else {
                    double beta = std::tanh(rapidity_omega);
                    base = (beta < 0.1) ? R_STL_NONREL : R_STL_REL;
                }
            }
            uint32_t composite = base;
            if (cryosleep_active)    composite |= R_CRYOSLEEP;
            if (grav_factor < 0.99)  composite |= R_GRAVITY_WELL;
            return make_ok_number(static_cast<double>(composite));
        } catch (const std::exception& e) {
            return make_error(e.what());
        }
    }

    if (op == "physics_query") {
        if (args.type != JValue::OBJECT) return make_error("'args' must be an object");
        auto it_q = args.obj.find("query");
        auto it_p = args.obj.find("params");
        if (it_q == args.obj.end() || it_q->second.type != JValue::STRING)
            return make_error("physics_query missing or non-string 'query'");
        if (it_p == args.obj.end() || it_p->second.type != JValue::OBJECT)
            return make_error("physics_query missing or non-object 'params'");
        const std::string& inner_op = it_q->second.s;
        if (inner_op == "physics_query")
            return make_error("physics_query cannot recurse into itself");
        JValue inner_req;
        inner_req.type = JValue::OBJECT;
        JValue inner_op_v;
        inner_op_v.type = JValue::STRING;
        inner_op_v.s = inner_op;
        inner_req.obj["op"]   = inner_op_v;
        inner_req.obj["args"] = it_p->second;
        return dispatch(inner_req);
    }

    return make_error("unknown op: " + op);
}

}  // namespace

int run() {
    std::ios_base::sync_with_stdio(false);
    std::string line;
    while (std::getline(std::cin, line)) {
        if (!line.empty() && line.back() == '\r') line.pop_back();
        if (line.empty()) continue;
        std::string response;
        try {
            size_t i = 0;
            JValue req = parse_value(line, i);
            response = dispatch(req);
        } catch (const std::exception& e) {
            response = make_error(std::string("parse error: ") + e.what());
        }
        std::cout << response << "\n";
        std::cout.flush();
    }
    return 0;
}

}  // namespace stdio_server
}  // namespace astra
