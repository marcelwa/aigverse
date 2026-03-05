# Declare all external dependencies and make sure that they are available.

include(FetchContent)
include(CMakeDependentOption)

set(Python_FIND_VIRTUALENV
    FIRST
    CACHE STRING "Give precedence to virtualenvs when searching for Python")
set(Python_FIND_FRAMEWORK
    LAST
    CACHE STRING "Prefer Brew/Conda to Apple framework Python")
set(Python_ARTIFACTS_INTERACTIVE
    ON
    CACHE BOOL
          "Prevent multiple searches for Python and instead cache the results.")

find_package(Python REQUIRED COMPONENTS Interpreter Development.Module
                                        ${SKBUILD_SABI_COMPONENT})

if(Python_EXECUTABLE)
  message(STATUS "Python executable: ${Python_EXECUTABLE}")
else()
  message(FATAL_ERROR "Python executable not found")
endif()

# Detect the installed nanobind package and import it into CMake
execute_process(
  COMMAND "${Python_EXECUTABLE}" -m nanobind --cmake_dir
  OUTPUT_STRIP_TRAILING_WHITESPACE
  OUTPUT_VARIABLE nanobind_ROOT)
find_package(nanobind CONFIG REQUIRED)

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
