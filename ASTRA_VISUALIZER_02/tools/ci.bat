@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ci.bat - V9 CI driver. Builds the project, runs the libastra_nexus assertion
rem runner, then runs the visualizer in headless mode against the locked golden
rem PNGs. Exits non-zero on any failure - suitable to chain from any cmd-shell
rem CI harness.
rem
rem Usage (from any cmd window):
rem   tools\ci.bat
rem
rem Optional env vars:
rem   ASTRA_VIZ_OUTPUT_DIR  override results dir (default ci_results\)

cd /d "%~dp0\.."

call tools\build.bat
if errorlevel 1 (
    echo CI FAIL: build
    exit /b 10
)

echo.
echo === libastra_nexus assertion suite ===
build\src\libastra_nexus\test_libastra_nexus.exe
if errorlevel 1 (
    echo CI FAIL: libastra assertion suite
    exit /b 11
)

set "OUT_DIR=%ASTRA_VIZ_OUTPUT_DIR%"
if "%OUT_DIR%"=="" set "OUT_DIR=ci_results"
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

echo.
echo === visualizer headless --scene=all (writes %OUT_DIR%\report.json) ===
build\astra_visualizer.exe --headless --scene=all --output=%OUT_DIR%
if errorlevel 1 (
    echo CI FAIL: visualizer headless assertions
    exit /b 12
)

echo.
echo CI PASS: libastra clean + visualizer 12/12 scenes + goldens RMSE under threshold.
exit /b 0
