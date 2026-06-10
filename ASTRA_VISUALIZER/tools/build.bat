@echo off
REM tools/build.bat — Windows convenience wrapper.
REM Activates VS2022 x64 environment, then configures + builds via Ninja.
REM
REM Usage:
REM   tools\build.bat                 (defaults to Release)
REM   tools\build.bat Debug
REM   tools\build.bat Release libastra_nexus_test     (specific target)

setlocal

set CONFIG=%1
if "%CONFIG%"=="" set CONFIG=Release

set TARGET=%2

set VCVARSALL="C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
set CMAKE="C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"
set NINJA_DIR=C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja

REM Force MSVC 14.43 toolset (per CLAUDE.md cold-start preference).
set VCToolsVersion=14.43.34808

call %VCVARSALL% x64 -vcvars_ver=14.43
if errorlevel 1 (
    echo [build.bat] ERROR: vcvarsall.bat failed
    exit /b 1
)

REM Add bundled Ninja to PATH.
set PATH=%NINJA_DIR%;%PATH%

pushd "%~dp0.."

if not exist build mkdir build

%CMAKE% -S . -B build -G "Ninja" -DCMAKE_BUILD_TYPE=%CONFIG% -DCMAKE_C_COMPILER=cl -DCMAKE_CXX_COMPILER=cl
if errorlevel 1 (
    echo [build.bat] ERROR: cmake configure failed
    popd
    exit /b 1
)

if "%TARGET%"=="" (
    %CMAKE% --build build --config %CONFIG%
) else (
    %CMAKE% --build build --config %CONFIG% --target %TARGET%
)
if errorlevel 1 (
    echo [build.bat] ERROR: cmake build failed
    popd
    exit /b 1
)

popd
echo [build.bat] DONE: %CONFIG%
endlocal
