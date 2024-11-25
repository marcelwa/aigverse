include(${PROJECT_SOURCE_DIR}/cmake/CheckSubmodules.cmake)

# Include pybind11
add_subdirectory(pybind11)

# Include mockturtle
set(MOCKTURTLE_EXAMPLES OFF CACHE BOOL "" FORCE)
set(MOCKTURTLE_EXPERIMENTS OFF CACHE BOOL "" FORCE)
set(MOCKTURTLE_TEST OFF CACHE BOOL "" FORCE)
check_if_present(mockturtle)
add_subdirectory(mockturtle)
