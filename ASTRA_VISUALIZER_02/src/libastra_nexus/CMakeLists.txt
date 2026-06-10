# libastra_nexus - local mirror of proto/astra_nexus.cpp canon math.
# Static library; C++17/20 compatible (host-side only, no CUDA dependencies).
# Built by the parent project's top-level CMakeLists.txt via add_subdirectory().

add_library(libastra_nexus STATIC
    src/regime.cpp
    src/coord.cpp
    src/rapidity.cpp
    src/composition.cpp
    src/apparent_rate.cpp
    src/observe.cpp
    src/kepler.cpp
    src/cherenkov.cpp
    src/test_suite.cpp
)

target_include_directories(libastra_nexus PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

target_compile_features(libastra_nexus PUBLIC cxx_std_17)

target_compile_options(libastra_nexus PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /MP /utf-8 /Zc:preprocessor>
)

# Standalone test runner exe. Builds the canon mirror + Cherenkov assertions
# and prints PASS/FAIL per assertion; exits 0 iff astra::test::failed == 0.
add_executable(test_libastra_nexus
    src/test_main.cpp
)

target_link_libraries(test_libastra_nexus PRIVATE
    libastra_nexus
)

target_compile_options(test_libastra_nexus PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /MP /utf-8 /Zc:preprocessor>
)
