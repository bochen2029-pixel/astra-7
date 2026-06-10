// libastra_nexus/include/astra_nexus/stdio_server.h
//
// JSON-over-stdio bridge for proto/textverse (preserved from Day 2 v0.128).
// Wire format unchanged from proto/astra_nexus.cpp lines 950-1382.

#pragma once

namespace astra {
namespace stdio_server {

// Read JSON request lines from stdin, write JSON response lines to stdout,
// until EOF. Returns process exit code (always 0 on clean EOF).
int run();

}  // namespace stdio_server
}  // namespace astra
