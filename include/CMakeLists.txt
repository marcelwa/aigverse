add_library(aigverse INTERFACE)
add_library(aigverse::aigverse ALIAS aigverse)

# Collect all project headers
file(GLOB_RECURSE AIGVERSE_PUBLIC_HEADERS CONFIGURE_DEPENDS
     "${PROJECT_SOURCE_DIR}/include/aigverse/*.hpp")

# Expose include directories (build + install interfaces)
# Avoid plain absolute paths to support relocatable packages
# Public headers live in source include dir
# install tree flattens to include/
target_include_directories(aigverse
  INTERFACE
    $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
    $<BUILD_INTERFACE:${AIGVERSE_GENERATED_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Register header file set for IDE integration and installation metadata
# Multiple BASE_DIRS so CMake knows how to layout the installed tree
#
# Using a FILE_SET ensures proper exposure in CMake package exports later
# if export() logic is added.
#
# (GLOB with CONFIGURE_DEPENDS keeps IDE view in sync when adding headers.)
target_sources(aigverse
  INTERFACE
    FILE_SET HEADERS
    BASE_DIRS
      ${PROJECT_SOURCE_DIR}/include
    FILES
      ${AIGVERSE_PUBLIC_HEADERS}
)

# Enforce project-wide C++ standard feature requirement (redundant but explicit)
target_compile_features(aigverse INTERFACE cxx_std_${CMAKE_CXX_STANDARD})

# Propagate options and warnings
target_link_libraries(aigverse INTERFACE
  $<BUILD_INTERFACE:aigverse_options>
  $<BUILD_INTERFACE:aigverse_warnings>
)

# Visibility / conformity flags for consumers.
# * GCC/Clang: hide symbols by default
# * MSVC: tighten language conformance & proper __cplusplus, modern preprocessor
# Symbol export on MSVC still requires dllexport/dllimport if building shared libs.
target_compile_options(aigverse
  INTERFACE
        $<BUILD_INTERFACE:$<$<COMPILE_LANG_AND_ID:CXX,Clang,AppleClang,GNU>:-fvisibility=hidden -fvisibility-inlines-hidden>>
        $<BUILD_INTERFACE:$<$<COMPILE_LANG_AND_ID:CXX,MSVC>:/permissive- /Zc:__cplusplus /Zc:inline /Zc:preprocessor /Zc:throwingNew /EHsc>>
)

# Install headers via file set (skipped if global install disabled)
if(NOT CMAKE_SKIP_INSTALL_RULES)
  install(TARGETS aigverse FILE_SET HEADERS)
endif()
