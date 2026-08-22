function(add_aigverse_python_binding target_name)
  cmake_parse_arguments(ARG "" "MODULE_NAME;INSTALL_DIR" "" ${ARGN})
  set(SOURCES ${ARG_UNPARSED_ARGUMENTS})

  # Split mode keeps the nanobind library out of the extension and resolves it
  # at import time from the `nanobind-backend` wheel. One `abi3` binary then
  # covers every Python from 3.10 up, instead of the three wheels a linked
  # stable-ABI build needs (3.10, 3.11, and abi3 from 3.12).
  #
  # Free-threaded interpreters have no such stable ABI before the `abi3t` of
  # Python 3.15, so those fall back to a linked, version-specific build.
  # `NB_FREE_THREADED` is set by nanobind's own config from the interpreter's
  # ABI tag.
  if(NB_FREE_THREADED AND Python_VERSION VERSION_LESS 3.15)
    set(AIGVERSE_NB_ABI_OPTIONS FREE_THREADED)
  else()
    set(AIGVERSE_NB_ABI_OPTIONS BACKEND_MODULE nanobind_backend FREE_THREADED)
  endif()

  nanobind_add_module(
    # Extension name
    ${target_name}
    # Stable ABI strategy, plus free-threaded support (ignored by nanobind on
    # interpreters that do not support it)
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
