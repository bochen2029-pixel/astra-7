// verify_math.h - bit-for-bit table dump that mirrors proto/astra_nexus.cpp's
// demo_voyage() output exactly. Lets the operator `diff -y` against canon and
// confirm the V2 math bridge agrees to 6+ sig figs (CLAUDE.md §7 V2 gate).
#pragma once

namespace astra_viz {

// Prints the canonical voyage table to stdout. Returns 0 always.
int run_verify_math();

} // namespace astra_viz
