pybind11_add_module(aigverse
        # Prefer thin LTO if available
        THIN_LTO
        aigverse.cpp)
target_link_libraries(aigverse PRIVATE mockturtle)
target_include_directories(aigverse
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
set_property(TARGET aigverse PROPERTY POSITION_INDEPENDENT_CODE ON)

if (MSVC)
    target_compile_options(aigverse PRIVATE /utf-8)
endif()

# Install directive for scikit-build-core
install(TARGETS aigverse
        DESTINATION .
        COMPONENT aigverse_Python)
