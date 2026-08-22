function(add_aigverse_python_binding target_name)
  cmake_parse_arguments(ARG "" "MODULE_NAME;INSTALL_DIR" "" ${ARGN})
  set(SOURCES ${ARG_UNPARSED_ARGUMENTS})

  # Split mode resolves the nanobind library at import time from the
  # `nanobind-backend` wheel, so one abi3 binary covers Python 3.10 up.
  # Free-threading has no stable ABI before the `abi3t` of 3.15, so it links the
  # library in and builds one wheel per version instead.
  if(NB_FREE_THREADED AND Python_VERSION VERSION_LESS 3.15)
    set(AIGVERSE_NB_ABI_OPTIONS FREE_THREADED)
  else()
    set(AIGVERSE_NB_ABI_OPTIONS BACKEND_MODULE nanobind_backend FREE_THREADED)
  endif()

  nanobind_add_module(
    # Extension name
    ${target_name}
    # Stable ABI strategy, plus free-threaded support
    ${AIGVERSE_NB_ABI_OPTIONS}
    # Link-time optimization
    LTO
    # Suppress compiler warnings in the nanobind project
    NB_SUPPRESS_WARNINGS
    # Source files
    ${SOURCES})

  # Set C++ standard
  target_compile_features(${target_name} PRIVATE cxx_std_17)

  # Disable global IPO on extension modules: cross-module LTO can cause heap
  # corruption on Windows when shared_ptr-based types are passed between
  # separate extension modules.
  set_target_properties(${target_name} PROPERTIES INTERPROCEDURAL_OPTIMIZATION
                                                  OFF)

  if(ARG_MODULE_NAME)
    set_target_properties(${target_name} PROPERTIES OUTPUT_NAME
                                                    ${ARG_MODULE_NAME})
  endif()

  target_link_libraries(
    ${target_name} PRIVATE aigverse::mockturtle aigverse::aigverse_options
                           aigverse::aigverse_warnings)

  target_include_directories(${target_name} PRIVATE "${PROJECT_SOURCE_DIR}/src")

  if(MSVC)
    target_compile_options(${target_name} PRIVATE /utf-8)
    target_compile_definitions(${target_name} PRIVATE UNICODE _UNICODE)
  endif()

  if(NOT ARG_INSTALL_DIR)
    set(ARG_INSTALL_DIR ".")
  endif()

  install(
    TARGETS ${target_name}
    DESTINATION ${ARG_INSTALL_DIR}
    COMPONENT aigverse_Python)
endfunction()
