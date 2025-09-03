# Automatically collect all .cpp sources in this directory (recursive)
file(GLOB_RECURSE AIGVERSE_PY_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

pybind11_add_module(pyaigverse
        THIN_LTO
        ${AIGVERSE_PY_SOURCES})

# Provide namespaced alias for consistent consumer usage
add_library(aigverse::pyaigverse ALIAS pyaigverse)

# Link against the public header-only target and dependencies (namespaced)
target_link_libraries(pyaigverse PRIVATE aigverse::aigverse aigverse::mockturtle)

# Precompiled header to speed up heavy pybind11/fmt/mockturtle includes
target_precompile_headers(pyaigverse PRIVATE "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/pch.hpp>")

set_property(TARGET pyaigverse PROPERTY POSITION_INDEPENDENT_CODE ON)

if (MSVC)
    target_compile_options(pyaigverse PRIVATE /utf-8)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_WIN32")
    add_definitions(-DUNICODE -D_UNICODE)
endif ()

# Install directive for scikit-build-core
install(TARGETS pyaigverse
        DESTINATION .
        COMPONENT aigverse_Python)
