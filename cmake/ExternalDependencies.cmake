# Declare all external dependencies and make sure that they are available.

include(FetchContent)
include(CMakeDependentOption)

cmake_dependent_option(
  AIGVERSE_VENDOR_PYBIND11 "Fetch pybind11 automatically if not found" ON
  "NOT SKBUILD" OFF)
set(AIGVERSE_PYBIND11_VERSION
    2.13.6
    CACHE STRING "Desired pybind11 version")

if(NOT SKBUILD)
  # Need Development.Module so that python_add_library/python3_add_library are
  # defined
  find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)
  # Try to discover a pybind11 installation provided by Python package (pip)
  execute_process(
    COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    OUTPUT_VARIABLE pybind11_DIR
    RESULT_VARIABLE pybind11_exec_res
    ERROR_VARIABLE pybind11_exec_err)
  if(pybind11_exec_res EQUAL 0 AND pybind11_DIR)
    list(PREPEND CMAKE_PREFIX_PATH "${pybind11_DIR}")
  else()
    message(
      DEBUG
      "pybind11 --cmakedir query failed (code=${pybind11_exec_res}). stderr: ${pybind11_exec_err}"
    )
  endif()
endif()

if(Python_EXECUTABLE)
  message(STATUS "Python executable: ${Python_EXECUTABLE}")
else()
  message(FATAL_ERROR "Python executable not found")
endif()

# First attempt to find an existing pybind11 (quiet; we'll vendor if missing)
find_package(pybind11 ${AIGVERSE_PYBIND11_VERSION} CONFIG QUIET)

if(NOT pybind11_FOUND)
  if(AIGVERSE_VENDOR_PYBIND11)
    message(
      STATUS
        "pybind11 not found; fetching v${AIGVERSE_PYBIND11_VERSION} via FetchContent"
    )
    FetchContent_Declare(
      pybind11
      GIT_REPOSITORY https://github.com/pybind/pybind11.git
      GIT_TAG v${AIGVERSE_PYBIND11_VERSION}
      GIT_SHALLOW TRUE
      FIND_PACKAGE_ARGS ${AIGVERSE_PYBIND11_VERSION} CONFIG)
    # Prevent polluting parent projects if this is used as a subtree
    set(FETCHCONTENT_QUIET OFF)
    FetchContent_MakeAvailable(pybind11)
    # After vendoring, targets like pybind11::pybind11 should exist
    if(TARGET pybind11::pybind11)
      message(STATUS "Vendored pybind11 v${AIGVERSE_PYBIND11_VERSION} ready")
      set(pybind11_FOUND TRUE)
    endif()
  else()
    message(
      FATAL_ERROR
        "pybind11 (>=${AIGVERSE_PYBIND11_VERSION}) not found and AIGVERSE_VENDOR_PYBIND11=OFF. Set pybind11_DIR or enable vendorization."
    )
  endif()
endif()

if(NOT pybind11_FOUND)
  message(FATAL_ERROR "pybind11 still not available after attempted fetch.")
endif()

# Fetch mockturtle library
set(MOCKTURTLE_REV
    "1a91a7495560ae2e510316a32ca15651756dfebc"
    CACHE STRING "mockturtle identifier (tag, branch or commit hash)")
set(MOCKTURTLE_REPO_OWNER
    "marcelwa"
    CACHE STRING "mockturtle repository owner (change when using a fork)")

# Configure mockturtle options before fetching
set(MOCKTURTLE_EXAMPLES
    OFF
    CACHE BOOL "" FORCE)
set(MOCKTURTLE_EXPERIMENTS
    OFF
    CACHE BOOL "" FORCE)
set(MOCKTURTLE_TEST
    OFF
    CACHE BOOL "" FORCE)
# Ensure all static libraries built by mockturtle are position-independent This
# is required for linking into Python extension modules (shared libraries)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

message(
  STATUS
    "Fetching mockturtle from https://github.com/${MOCKTURTLE_REPO_OWNER}/mockturtle.git@${MOCKTURTLE_REV}"
)

FetchContent_Declare(
  mockturtle
  GIT_REPOSITORY https://github.com/${MOCKTURTLE_REPO_OWNER}/mockturtle.git
  GIT_TAG ${MOCKTURTLE_REV}
  GIT_SUBMODULES_RECURSE TRUE)

FetchContent_MakeAvailable(mockturtle)

# Create alias for mockturtle
add_library(aigverse::mockturtle ALIAS mockturtle)
