# BUILD.md — ASTRA-7 Visualizer 02

Build instructions for Windows 11 + RTX 40-series + Visual Studio 2022. Linux x86_64 is the permitted second platform per the parent project's Platform Discipline; instructions below cover Windows.

---

## Requirements

| Tool | Version | Where to get |
|---|---|---|
| Windows | 11 | required |
| Visual Studio | 2022 Community 17.8+ | https://visualstudio.microsoft.com/vs/community/ — install the **Desktop development with C++** workload |
| MSVC toolset | 14.40+ | bundled with VS2022 (14.43 verified) |
| CUDA Toolkit | 12.x or 13.x | https://developer.nvidia.com/cuda-downloads (CUDA 13.1 verified) |
| NVIDIA driver | recent (591+ verified) | bundled with CUDA installer or https://www.nvidia.com/Download/index.aspx |
| GPU | RTX 40-series (compute_89) minimum; RTX 50 (compute_120) supported | required for CUDA + OpenGL 4.6 |
| CMake | 3.27+ | VS-bundled (Common7/IDE/CommonExtensions/Microsoft/CMake) works; or https://cmake.org |
| Ninja | recent | VS-bundled or https://ninja-build.org |
| git | recent | required for FetchContent dependency clone |

System CMake / Ninja on PATH are NOT required: the bundled VS copies work and the helper script `tools\build.bat` invokes them by absolute path.

Internet connectivity is required on the **first** configure (to clone GLFW, GLAD, Dear ImGui, GLM, stb via FetchContent). Subsequent builds are offline.

---

## Build via helper (recommended)

From any cmd or PowerShell window:

```bat
cd C:\ASTRA-7\ASTRA_VISUALIZER_02
tools\build.bat
```

`tools\build.bat` does three things:

1. Sets up the VS2022 environment via `vcvarsall.bat x64`.
2. On first run: configures CMake with Ninja generator at `build/`.
3. Builds the `astra_visualizer.exe` target (and the `test_libastra_nexus.exe` math runner) into `build/`.

First build takes ~30-60 seconds (FetchContent + 60+ TUs). Incremental builds take 1-5 seconds depending on changed file.

---

## Build manually (no helper)

From a **x64 Native Tools Command Prompt for VS 2022** (Start menu shortcut):

```bat
cd C:\ASTRA-7\ASTRA_VISUALIZER_02
cmake -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release
```

Output:

- `build\astra_visualizer.exe` — the interactive visualizer + headless runner
- `build\src\libastra_nexus\test_libastra_nexus.exe` — the canonical-math assertion suite
- `build\shaders\` — runtime-loaded GLSL files (copied by CMake POST_BUILD)
- `build\src\libastra_nexus\libastra_nexus.lib` — static library (header-only consumers can link directly)

---

## Run

### Interactive

```bat
build\astra_visualizer.exe                         # opens window; defaults to S01
build\astra_visualizer.exe --scene=S05             # jumps to a specific scene
build\astra_visualizer.exe --width=2560 --height=1440
```

Controls + scene list: see `README.md`.

### Headless (CI / scripts)

```bat
build\astra_visualizer.exe --headless --scene=all                          # all 12 scenes; exit 0 iff all PASS
build\astra_visualizer.exe --headless --scene=S05                          # one scene
build\astra_visualizer.exe --headless --scene=all --output=results         # also writes results\report.json + 12 PNGs
build\astra_visualizer.exe --headless --scene=all --output=results --regenerate-goldens
```

The full CI flow lives in `tools\ci.bat`:

```bat
tools\ci.bat
```

This builds, runs the libastra assertion suite (75 / 0), then runs the visualizer headless. Exits 0 on success; non-zero on any failure with an explanatory code:

- 10 — build failed
- 11 — libastra assertion suite regressed
- 12 — visualizer assertion gate failed

### Smoke benchmark (FPS measurement, V-Sync off)

```bat
build\astra_visualizer.exe --bench=600 --scene=S05 --width=1920 --height=1080
```

Runs 600 frames at the given scene + resolution and reports `avg ms / FPS / min / max` to stdout. Useful for regression detection.

### Verify canon math vs visualizer bridge

```bat
build\astra_visualizer.exe --verify-math
```

Prints the canonical voyage table (mirrors `proto/astra_nexus.cpp::demo_voyage` byte-for-byte). Diff against the parent project's canon binary to confirm the math bridge is identity. Used during V2 spec gate; preserved for future drift checks.

---

## Common build issues

| Symptom | Cause | Fix |
|---|---|---|
| `vcvarsall failed` from `tools\build.bat` | `vswhere.exe` not on PATH | The script prepends `Program Files (x86)\Microsoft Visual Studio\Installer` automatically; verify VS2022 install path matches |
| `Cannot open include file: 'cstdint'` from MSVC | MSVC env vars missing (running `cmake --build` without vcvarsall) | Use `tools\build.bat`, or invoke from "x64 Native Tools Command Prompt" |
| `nvcc fatal: A single input file is required` | Bare MSVC flags reaching nvcc | Already handled in `CMakeLists.txt` via `-Xcompiler=`; if you've edited it, ensure CUDA TUs use the wrapped flags |
| `cudart64_*.dll not found` at runtime | Dynamic CUDA runtime; should be static | `set(CMAKE_CUDA_RUNTIME_LIBRARY Static)` is in CMakeLists.txt; if regressed, restore |
| `MSVCP140.dll not found` at runtime on a clean machine | Dynamic MSVC runtime | `set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")` in CMakeLists.txt fixes |
| GL 4.6 context fails | Old driver / non-NVIDIA GPU / iGPU active | Update NVIDIA driver; force discrete GPU in NVIDIA Control Panel for `astra_visualizer.exe` |
| Hull mesh black or invisible | Shaders not next to exe | `cmake --build` triggers a POST_BUILD copy of `src/shaders/ -> build/shaders/`; if you edited a shader after the last link, manually `cp -r src/shaders/* build/shaders/` or trigger a relink (e.g. `touch src/main.cpp`) |

---

## Distribution

The result is a single-file launchable:

```
astra_visualizer.exe        (~1.7 MB statically linked CUDA + MSVC runtime)
shaders/                    (GLSL files; copied next to exe by build)
assets/reference_renders/   (12 golden PNGs for headless CI; ~1.9 MB total)
```

Required at runtime: NVIDIA driver + Windows OS DLLs (KERNEL32, USER32, GDI32, SHELL32, IMM32, etc.). NO CUDA toolkit needed. NO VS C++ Redistributable needed.

---

**Operator:** Bo Chen
**Substrate:** Windows 11 + RTX 40-series + CUDA 13.x + OpenGL 4.6
