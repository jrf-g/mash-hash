#!/usr/bin/env bash
set -e  # Exit on error

mkdir -p build
cd build

# Detect OS and run CMake
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
    cmake -G "MinGW Makefiles" ..
    mingw32-make
else
    cmake ..
    cmake --build .
fi
# make executeable
chmod +x build.sh
