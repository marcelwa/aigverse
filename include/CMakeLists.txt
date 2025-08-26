add_library(libaigverse INTERFACE)

target_include_directories(libaigverse INTERFACE ${PROJECT_SOURCE_DIR}/include)

target_compile_features(libaigverse INTERFACE cxx_std_${CMAKE_CXX_STANDARD})

target_link_libraries(libaigverse INTERFACE aigverse::aigverse_options
        aigverse::aigverse_warnings)

set_target_properties(
        libaigverse
        PROPERTIES
        CXX_VISIBILITY_PRESET hidden
        VISIBILITY_INLINES_HIDDEN YES)
