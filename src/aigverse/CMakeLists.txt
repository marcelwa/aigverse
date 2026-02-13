# Automatically collect all .cpp sources in this directory (recursive)
file(GLOB_RECURSE AIGVERSE_PY_SOURCES CONFIGURE_DEPENDS
     "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

pybind11_add_module(pyaigverse THIN_LTO ${AIGVERSE_PY_SOURCES})

# Provide namespaced alias for consistent consumer usage
add_library(aigverse::pyaigverse ALIAS pyaigverse)

# Link against dependencies (namespaced)
target_link_libraries(
  pyaigverse PRIVATE aigverse::mockturtle aigverse::aigverse_options
                     aigverse::aigverse_warnings)

# Include types.hpp and pch.hpp
target_include_directories(pyaigverse PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}/..")

# Precompiled header to speed up heavy pybind11/fmt/mockturtle includes
target_precompile_headers(
  pyaigverse PRIVATE "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/pch.hpp>")

set_property(TARGET pyaigverse PROPERTY POSITION_INDEPENDENT_CODE ON)

if(MSVC)
  target_compile_options(pyaigverse PRIVATE /utf-8)
  target_compile_definitions(pyaigverse PRIVATE UNICODE _UNICODE)
endif()

# Install directive for scikit-build-core
install(
  TARGETS pyaigverse
  DESTINATION .
  COMPONENT aigverse_Python)
