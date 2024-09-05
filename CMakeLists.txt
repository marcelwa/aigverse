# Large parts of this build system are based on Jason Turner's C++ Starter
# Project (https://github.com/lefticus/cpp_starter_project) and CMake Template
# (https://github.com/cpp-best-practices/cmake_template)

cmake_minimum_required(VERSION 3.21)

# Only set the CMAKE_CXX_STANDARD if it is not set by someone else
if(NOT DEFINED CMAKE_CXX_STANDARD)
  # Set C++ standard; at least C++17 is required
  set(CMAKE_CXX_STANDARD 17)
endif()

# strongly encouraged to enable this globally to avoid conflicts between
# -Wpedantic being enabled and -std=c++20 and -std=gnu++20 for example when
# compiling with PCH enabled
set(CMAKE_CXX_EXTENSIONS OFF)

# Set the project name and version
project(
  aigverse
  VERSION 0.0.2
  DESCRIPTION
    "A Python library for working with logic networks, synthesis, and optimization."
  HOMEPAGE_URL "https://github.com/marcelwa/aigverse"
  LANGUAGES CXX C)

include(cmake/PreventInSourceBuilds.cmake)
include(cmake/ProjectOptions.cmake)
include(cmake/Utilities.cmake)

aigverse_setup_options()
aigverse_global_options()
aigverse_local_options()

# don't know if this should be set globally from here or not...
set(CMAKE_CXX_VISIBILITY_PRESET hidden)

set(GIT_SHA
    "Unknown"
    CACHE STRING "SHA this build was generated from")
string(SUBSTRING "${GIT_SHA}" 0 8 GIT_SHORT_SHA)

target_compile_features(aigverse_options INTERFACE cxx_std_${CMAKE_CXX_STANDARD})

# Alias for the options target
add_library(aigverse::aigverse_options ALIAS aigverse_options)
# Alias for the warnings target
add_library(aigverse::aigverse_warnings ALIAS aigverse_warnings)

# Include libraries
add_subdirectory(libs)

# Python bindings
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/bindings/)

# If MSVC is being used, and ASAN is enabled, we need to set the debugger
# environment so that it behaves well with MSVC's debugger, and we can run the
# target from visual studio
if(MSVC)
  get_all_installable_targets(all_targets)
  message("all_targets=${all_targets}")
  set_target_properties(
    ${all_targets} PROPERTIES VS_DEBUGGER_ENVIRONMENT
                              "PATH=$(VC_ExecutablePath_x64);%PATH%")
endif()

# set the startup project for the "play" button in MSVC
set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT intro)

if(CMAKE_SKIP_INSTALL_RULES)
  return()
endif()
