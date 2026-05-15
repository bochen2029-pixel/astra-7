@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d C:\ASTRA-7\proto
cl /std:c++17 /EHsc /O2 /nologo astra_nexus.cpp /Fe:astra_nexus.exe
