cmake_minimum_required(VERSION 3.27)

# CUDA arch targets must be set BEFORE project() or CMake picks compute_75 (Turing)
# and the V3+ kernels silently misbehave. Per Buddhabrot's hard-won lesson:
#   89  = RTX 40-series Ada Lovelace (baseline)
#   90  = Hopper H100/H200 (kept for completeness)
#   120 = RTX 50-series Blackwell consumer (requires CUDA 12.9+; 13.x recommended)
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 89 90 120 CACHE STRING "CUDA arch targets")
endif()

project(astra_visualizer
    VERSION 0.1.0
    DESCRIPTION "ASTRA-7 visual physics testbed: CUDA + OpenGL, 12 scenes, pixel-level assertions"
    LANGUAGES C CXX CUDA
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Static CUDA runtime so astra_visualizer.exe ships without cudart64_*.dll alongside.
set(CMAKE_CUDA_RUNTIME_LIBRARY Static)

# Static MSVC runtime so astra_visualizer.exe runs without the VS C++ Redistributable
# on the target machine. Cascades to FetchContent'd subprojects automatically.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

find_package(CUDAToolkit REQUIRED)

add_compile_definitions(_CRT_SECURE_NO_WARNINGS NOMINMAX)

# ---------- Dependencies (FetchContent; Buddhabrot pattern, proven on this host) ----------

include(FetchContent)
set(FETCHCONTENT_QUIET FALSE)

# GLFW 3.4 - windowing + input
FetchContent_Declare(glfw
    GIT_REPOSITORY https://github.com/glfw/glfw.git
    GIT_TAG 3.4
    GIT_SHALLOW TRUE
)
set(GLFW_BUILD_DOCS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(GLFW_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(GLFW_INSTALL OFF CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(glfw)

# GLAD v2.0.6 - OpenGL 4.6 core loader, generated at configure time
FetchContent_Declare(glad
    GIT_REPOSITORY https://github.com/Dav1dde/glad.git
    GIT_TAG v2.0.6
    GIT_SHALLOW TRUE
    SOURCE_SUBDIR cmake
)
FetchContent_MakeAvailable(glad)
glad_add_library(glad_gl_core_46 REPRODUCIBLE API gl:core=4.6)

# Dear ImGui v1.91.5 - immediate-mode UI overlay
FetchContent_Declare(imgui
    GIT_REPOSITORY https://github.com/ocornut/imgui.git
    GIT_TAG v1.91.5
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(imgui)

add_library(imgui STATIC
    ${imgui_SOURCE_DIR}/imgui.cpp
    ${imgui_SOURCE_DIR}/imgui_demo.cpp
    ${imgui_SOURCE_DIR}/imgui_draw.cpp
    ${imgui_SOURCE_DIR}/imgui_tables.cpp
    ${imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
    ${imgui_SOURCE_DIR}/backends/imgui_impl_opengl3.cpp
)
target_include_directories(imgui PUBLIC
    ${imgui_SOURCE_DIR}
    ${imgui_SOURCE_DIR}/backends
)
target_link_libraries(imgui PUBLIC glfw)
target_compile_options(imgui PRIVATE
    $<$<CXX_COMPILER_ID:MSVC>:/W3 /MP /utf-8>
)

# GLM 1.0.1 - math (header-only)
FetchContent_Declare(glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.1
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(glm)

# stb (image_write etc.) - public domain single-header collection
FetchContent_Declare(stb
    GIT_REPOSITORY https://github.com/nothings/stb.git
    GIT_TAG master
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(stb)
add_library(stb_headers INTERFACE)
target_include_directories(stb_headers INTERFACE ${stb_SOURCE_DIR})

# ---------- Subprojects ----------

add_subdirectory(src/libastra_nexus)

# ---------- astra_visualizer executable ----------

set(ASTRA_VIZ_SOURCES
    src/main.cpp
    src/app/application.cpp
    src/app/camera.cpp
    src/app/scene_router.cpp
    src/physics/physics_core.cpp
    src/renderer/cherenkov_cone.cpp
    src/physics/reflex_stub.cpp
    src/renderer/chaos_field.cpp
    src/renderer/gl_context.cpp
    src/renderer/graphics_program.cpp
    src/renderer/hull.cpp
    src/renderer/named_bodies.cpp
    src/renderer/starfield.cpp
    src/renderer/wake_trail.cpp
    src/renderer/warp_volume.cpp
    src/scenes/scene_base.cpp
    src/scenes/s01_rest_baseline.cpp
    src/scenes/s02_stl_recede_05c.cpp
    src/scenes/s03_stl_recede_09c.cpp
    src/scenes/s04_warp_charge.cpp
    src/scenes/s05_warp_cruise_2c.cpp
    src/scenes/s06_warp_cruise_10c_cherenkov.cpp
    src/scenes/s07_photon_source_history.cpp
    src/scenes/s08_warp_gravity_well.cpp
    src/scenes/s09_chaos_reflex.cpp
    src/scenes/s10_hubble_horizon.cpp
    src/scenes/s11_split_screen.cpp
    src/scenes/s12_eye_ear_decoupling.cpp
    src/ui/assertion_panel.cpp
    src/ui/parameter_panel.cpp
    src/ui/physics_calc_panel.cpp
    src/ui/scenario_selector.cpp
    src/ui/state_display.cpp
    src/util/log.cpp
    src/util/stb_impl.cpp
    src/util/timer.cpp
    src/util/verify_math.cpp
    src/validation/golden_diff.cpp
    src/validation/json_report.cpp
    src/validation/pixel_sampler.cpp
    src/validation/screenshot.cpp
    src/kernels/warp_field.cu
    src/kernels/chaos_pde.cu
)

add_executable(astra_visualizer ${ASTRA_VIZ_SOURCES})

target_include_directories(astra_visualizer PRIVATE
    src
    ${CUDAToolkit_INCLUDE_DIRS}
)

target_link_libraries(astra_visualizer PRIVATE
    libastra_nexus
    glfw
    glad_gl_core_46
    imgui
    glm::glm
    stb_headers
    CUDA::cudart_static
)

# Per-language compile flags. nvcc's argument parser chokes on bare MSVC flags
# ("A single input file is required ..."); wrap host flags inside -Xcompiler=
# when forwarding through nvcc. Buddhabrot's hard-won lesson, preserved here.
target_compile_options(astra_visualizer PRIVATE
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:MSVC>>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<COMPILE_LANGUAGE:CUDA>:--use_fast_math
                               -Xcompiler=/W3,/MP,/utf-8,/Zc:preprocessor>
)

set_target_properties(astra_visualizer PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
)

# Copy shaders next to the .exe at build time so the runtime can find them
# at $<TARGET_FILE_DIR:astra_visualizer>/shaders/
add_custom_command(TARGET astra_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/src/shaders
        $<TARGET_FILE_DIR:astra_visualizer>/shaders
)
