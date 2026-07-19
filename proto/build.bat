@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
rem Build the source NEXT TO THIS SCRIPT (%~dp0), never a hardcoded checkout:
rem the old `cd /d C:\ASTRA-7\proto` silently compiled the MAIN checkout's
rem source when run from a git worktree (caught 2026-07-19, Track C
rem micro-turn). Worktree sessions are a working pattern now; the script
rem must build what sits beside it.
cd /d "%~dp0"
cl /std:c++17 /EHsc /O2 /nologo astra_nexus.cpp /Fe:astra_nexus.exe
