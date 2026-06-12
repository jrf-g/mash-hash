@echo off
if not exist build mkdir build
cd build

:: Use MSVC if available, else MinGW
where cl >nul 2>nul
if %errorlevel%==0 (
    cmake -G "NMake Makefiles" ..
    nmake
) else (
    cmake -G "MinGW Makefiles" ..
    mingw32-make
)
