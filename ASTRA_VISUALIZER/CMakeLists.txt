# C:/ASTRA-7/ASTRA_VISUALIZER/CMakeLists.txt
#
# Top-level CMake configuration for the ASTRA-7 Visual Physics Testbed.
# Pattern lifted from C:/Buddhabrot_CUDA/CMakeLists.txt (proven on this machine).

cmake_minimum_required(VERSION 3.27)

# RTX 40-series (Ada) = compute_89; Hopper = compute_90; RTX 50-series Blackwell = compute_120.
# Set BEFORE project() so CMake's CUDA detection uses these.
if(NOT DEFINED CMAKE_CUDA_ARCHITECTURES)
    set(CMAKE_CUDA_ARCHITECTURES 89 90 120 CACHE STRING "")
endif()

project(astra_visualizer
    VERSION 0.1.0
    DESCRIPTION "ASTRA-7 Visual Physics Testbed"
    LANGUAGES C CXX CUDA
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_CUDA_STANDARD 17)
set(CMAKE_CUDA_STANDARD_REQUIRED ON)

# Static CUDA runtime so the .exe doesn't need cudart64_*.dll alongside.
set(CMAKE_CUDA_RUNTIME_LIBRARY Static)

# Static MSVC runtime so the .exe doesn't need the VS C++ redistributable.
# Cascades to FetchContent'd subprojects (glfw, glad, imgui, libastra_nexus).
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

find_package(CUDAToolkit REQUIRED)

add_compile_definitions(_CRT_SECURE_NO_WARNINGS NOMINMAX)

include(FetchContent)
set(FETCHCONTENT_QUIET FALSE)

# ---------- doctest (single-header test framework) ----------
FetchContent_Declare(doctest
    GIT_REPOSITORY https://github.com/doctest/doctest.git
    GIT_TAG v2.4.11
    GIT_SHALLOW TRUE
)
set(DOCTEST_WITH_TESTS OFF CACHE BOOL "" FORCE)
set(DOCTEST_WITH_MAIN_IN_STATIC_LIB OFF CACHE BOOL "" FORCE)
set(DOCTEST_NO_INSTALL ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(doctest)

# ---------- GLFW ----------
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

# ---------- GLAD (OpenGL 4.6 core, generated) ----------
FetchContent_Declare(glad
    GIT_REPOSITORY https://github.com/Dav1dde/glad.git
    GIT_TAG v2.0.6
    GIT_SHALLOW TRUE
    SOURCE_SUBDIR cmake
)
FetchContent_MakeAvailable(glad)
glad_add_library(glad_gl_core_46 REPRODUCIBLE API gl:core=4.6)

# ---------- Dear ImGui ----------
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

# ---------- GLM (header-only math) ----------
FetchContent_Declare(glm
    GIT_REPOSITORY https://github.com/g-truc/glm.git
    GIT_TAG 1.0.1
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(glm)

# ---------- stb_image_write (single-header PNG writer) ----------
FetchContent_Declare(stb
    GIT_REPOSITORY https://github.com/nothings/stb.git
    GIT_TAG master
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(stb)
add_library(stb_image_write INTERFACE)
target_include_directories(stb_image_write INTERFACE ${stb_SOURCE_DIR})

# ---------- nlohmann/json ----------
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
    GIT_SHALLOW TRUE
)
set(JSON_BuildTests OFF CACHE INTERNAL "")
FetchContent_MakeAvailable(json)

# ---------- libastra_nexus (the math library) ----------
add_subdirectory(libastra_nexus)

# ---------- visualizer executable ----------
file(GLOB_RECURSE VIS_SOURCES_CPP CONFIGURE_DEPENDS src/*.cpp)
file(GLOB_RECURSE VIS_SOURCES_CU  CONFIGURE_DEPENDS kernels/*.cu)

add_executable(astra_visualizer ${VIS_SOURCES_CPP} ${VIS_SOURCES_CU})

target_include_directories(astra_visualizer PRIVATE
    src
    kernels
    ${CUDAToolkit_INCLUDE_DIRS}
)

target_link_libraries(astra_visualizer PRIVATE
    astra_nexus
    glfw
    glad_gl_core_46
    imgui
    glm::glm
    stb_image_write
    nlohmann_json::nlohmann_json
    CUDA::cudart_static
)

# Per-language compile flags. CUDA uses -Xcompiler= to forward host flags
# through nvcc; bare MSVC flags would trip nvcc's parser
# ("A single input file is required ...").
target_compile_options(astra_visualizer PRIVATE
    $<$<AND:$<COMPILE_LANGUAGE:CXX>,$<CXX_COMPILER_ID:MSVC>>:/W3 /MP /utf-8 /Zc:preprocessor>
    $<$<COMPILE_LANGUAGE:CUDA>:--use_fast_math
                               -Xcompiler=/W3,/MP,/utf-8,/Zc:preprocessor>
)

set_target_properties(astra_visualizer PROPERTIES
    CUDA_SEPARABLE_COMPILATION ON
)

# Build-time version stamp consumed by --version.
target_compile_definitions(astra_visualizer PRIVATE
    ASTRA_VIS_VERSION="${PROJECT_VERSION}"
)

# Copy shaders next to the .exe at build time (currently empty; future-proofing).
add_custom_command(TARGET astra_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory $<TARGET_FILE_DIR:astra_visualizer>/shaders
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/shaders
        $<TARGET_FILE_DIR:astra_visualizer>/shaders
)

# Copy assets next to the .exe at build time (currently empty; future-proofing).
add_custom_command(TARGET astra_visualizer POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E make_directory $<TARGET_FILE_DIR:astra_visualizer>/assets
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/assets
        $<TARGET_FILE_DIR:astra_visualizer>/assets
)
