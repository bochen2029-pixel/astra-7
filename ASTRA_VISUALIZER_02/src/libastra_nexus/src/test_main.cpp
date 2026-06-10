// test_main.cpp - standalone runner for the libastra_nexus assertion suite.
// Returns 0 iff every assertion passes; non-zero exit means a regression
// somewhere in the canon mirror or in the new Cherenkov closure.
//
// CLAUDE.md §4 verification floor: passed >= 69 (66 canon + 3+ Cherenkov)
// AND failed == 0. We currently ship 4 new Cherenkov assertions, so the
// expected post-build report is ~71 canon + 4 Cherenkov = ~75 PASS, 0 FAIL.
#include "astra_nexus/test_suite.h"

#include <cstdio>

int main() {
    astra::test::run_all();

    std::printf("\nlibastra_nexus assertion-runner exit: passed=%d, failed=%d\n",
                astra::test::passed, astra::test::failed);

    if (astra::test::failed != 0) {
        std::printf("FAIL: %d assertion(s) regressed against canon.\n", astra::test::failed);
        return 1;
    }
    if (astra::test::passed < 69) {
        std::printf("FAIL: assertion count %d below CLAUDE.md §4 floor of 69.\n",
                    astra::test::passed);
        return 2;
    }
    std::printf("OK: %d assertions passed, none failed.\n", astra::test::passed);
    return 0;
}
