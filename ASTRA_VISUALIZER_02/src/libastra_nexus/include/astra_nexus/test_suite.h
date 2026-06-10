// test_suite.h — assertion runner. Mirrors canon proto/astra_nexus.cpp:404-887
// PLUS the 4 new Cherenkov assertions described in DESIGN_SPEC §4.5.
//
// Run via the standalone exe (test_libastra_nexus) or by linking + calling
// astra::test::run_all() yourself. The function prints PASS/FAIL per assertion
// to stdout and updates the counters in `astra::test::passed` / `failed`.
//
// Expected post-Cherenkov totals when run on a clean tree:
//   - canon: 66 PASS, 0 FAIL
//   - mirror: 70+ PASS, 0 FAIL  (66 canon + 4 new Cherenkov)
//
// CLAUDE.md §4 verification step demands the >=69 floor.
#pragma once

namespace astra {
namespace test {

extern int passed;
extern int failed;

void run_all();

} // namespace test
} // namespace astra
