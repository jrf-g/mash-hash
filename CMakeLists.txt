cmake_minimum_required(VERSION 3.10)
project(MashHash)

# Use C++17 for compatibility
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add the executable from notice.cpp
add_executable(MashHash notice.cpp)

# Optional: extra warnings for safety
if (MSVC)
    target_compile_options(MashHash PRIVATE /W4)
else()
    target_compile_options(MashHash PRIVATE -Wall -Wextra -pedantic)
endif()
