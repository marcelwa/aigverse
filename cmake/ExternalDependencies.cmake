# Declare all external dependencies and make sure that they are available.

include(FetchContent)
include(CMakeDependentOption)

if(NOT SKBUILD)
  # Need Development.Module so that python_add_library/python3_add_library are defined
  find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
  # Manually detect the installed pybind11 package and import it into CMake.
  execute_process(
    COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE pybind11_DIR)
  list(APPEND CMAKE_PREFIX_PATH "${pybind11_DIR}")
endif()

message(STATUS "Python executable: ${Python_EXECUTABLE}")

# add pybind11 library
find_package(pybind11 2.13.6 CONFIG REQUIRED)
