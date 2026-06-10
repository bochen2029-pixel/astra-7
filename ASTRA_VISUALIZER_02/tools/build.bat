@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem build.bat - configure + build the ASTRA-7 visualizer testbed.
rem Mirrors C:\Buddhabrot_CUDA\tools\build.bat which is proven on this machine.
rem Run from anywhere; this script cd's into the project root via %~dp0\..

rem vcvarsall.bat needs vswhere.exe on PATH or it errors before doing anything.
set "VSWHERE_DIR=C:\Program Files (x86)\Microsoft Visual Studio\Installer"
set "PATH=%VSWHERE_DIR%;%PATH%"

call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" x64
if errorlevel 1 (
    echo vcvarsall failed
    exit /b 1
)

set "CMAKE_EXE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set "NINJA_EXE=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"

cd /d "%~dp0\.."

if not exist build\CMakeCache.txt (
    "%CMAKE_EXE%" -S . -B build -G Ninja ^
        -DCMAKE_BUILD_TYPE=Release ^
        -DCMAKE_MAKE_PROGRAM="%NINJA_EXE%" ^
        -DCMAKE_C_COMPILER=cl.exe ^
        -DCMAKE_CXX_COMPILER=cl.exe
    if errorlevel 1 exit /b %errorlevel%
)

"%CMAKE_EXE%" --build build --config Release
exit /b %errorlevel%
