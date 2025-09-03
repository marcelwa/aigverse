add_library(libaigverse INTERFACE)
add_library(aigverse::libaigverse ALIAS libaigverse)

# Collect all headers
file(GLOB_RECURSE AIGVERSE_PUBLIC_HEADERS CONFIGURE_DEPENDS
     "${PROJECT_SOURCE_DIR}/include/aigverse/*.hpp")

# Expose include directory
target_include_directories(libaigverse INTERFACE ${PROJECT_SOURCE_DIR}/include)

# Register header file set for IDE integration and installation metadata
target_sources(libaigverse
  INTERFACE
    FILE_SET HEADERS
    BASE_DIRS ${PROJECT_SOURCE_DIR}/include
    FILES ${AIGVERSE_PUBLIC_HEADERS}
)

# Enforce project-wide C++ standard feature requirement
target_compile_features(libaigverse INTERFACE cxx_std_${CMAKE_CXX_STANDARD})

# Propagate options and warnings
target_link_libraries(libaigverse INTERFACE aigverse::aigverse_options
        aigverse::aigverse_warnings)

set_target_properties(
        libaigverse
        PROPERTIES
        CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN YES)

# Install headers via file set (skipped if global install disabled)
if(NOT CMAKE_SKIP_INSTALL_RULES)
  install(TARGETS libaigverse FILE_SET HEADERS)
endif()
