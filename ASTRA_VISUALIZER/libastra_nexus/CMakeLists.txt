# libastra_nexus/CMakeLists.txt
#
# Static library containing the canonical math extracted from proto/astra_nexus.cpp,
# plus the NEW cherenkov module that closes the AUDIT 5D-F4 gap.
# Standalone test binary libastra_nexus_test exercises all assertions via doctest.

add_library(astra_nexus STATIC
    src/coord.cpp
    src/rapidity.cpp
    src/composition.cpp
    src/observe.cpp
    src/kepler.cpp
    src/cherenkov.cpp        # NEW: 5D-F4 gap closure
    src/stdio_server.cpp     # preserved (Day 2 v0.128 textverse bridge)
)

target_include_directories(astra_nexus PUBLIC include)
target_compile_features(astra_nexus PUBLIC cxx_std_17)

target_compile_options(astra_nexus PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic>
)

# ---------- Standalone test binary ----------
add_executable(libastra_nexus_test
    tests/doctest_main.cpp
    tests/test_coord.cpp
    tests/test_rapidity.cpp
    tests/test_composition.cpp
    tests/test_observe.cpp
    tests/test_kepler.cpp
    tests/test_cherenkov.cpp   # NEW: 5D-F4 gap closure tests
)

target_link_libraries(libastra_nexus_test PRIVATE astra_nexus doctest::doctest)

target_compile_options(libastra_nexus_test PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<NOT:$<CXX_COMPILER_ID:MSVC>>:-Wall -Wextra -Wpedantic>
)
