pybind11_add_module(pyaigverse
        # Prefer thin LTO if available
        THIN_LTO
        aigverse.cpp)
target_link_libraries(pyaigverse PRIVATE mockturtle)
target_include_directories(pyaigverse
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
set_property(TARGET pyaigverse PROPERTY POSITION_INDEPENDENT_CODE ON)

if (MSVC)
    target_compile_options(pyaigverse PRIVATE /utf-8)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_WIN32")
    add_definitions(-DUNICODE -D_UNICODE)
endif()

# Install directive for scikit-build-core
install(TARGETS pyaigverse
        DESTINATION .
        COMPONENT aigverse_Python)
