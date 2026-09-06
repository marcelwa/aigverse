function(add_aigverse_python_binding target_name)
  cmake_parse_arguments(ARG "" "MODULE_NAME;INSTALL_DIR" "" ${ARGN})
  set(SOURCES ${ARG_UNPARSED_ARGUMENTS})

  nanobind_add_module(
    # Extension name
    ${target_name}
    # Split mode: the nanobind library is resolved at import time from the
    # `nanobind-backend` wheel, so one abi3 binary covers Python 3.10 up.
    # Requires free-threaded Python 3.15 or newer (`abi3t`, PEP 803).
    BACKEND_MODULE
    nanobind_backend
    # Free-threaded support
    FREE_THREADED
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
    set(module_name ${ARG_MODULE_NAME})
  else()
    set(module_name ${target_name})
  endif()

  # Keep the embedded static libraries' symbols local. nanobind hides only the
  # module's own (`CXX_VISIBILITY_PRESET hidden`); mockturtle's and ABC's
  # archives keep default visibility, so each extension re-exported them for the
  # dynamic linker to interpose across all five. Ported from scpd.
  if(APPLE)
    target_link_options(${target_name} PRIVATE
                        "LINKER:-exported_symbol,_PyInit_${module_name}")
  elseif(UNIX)
    target_link_options(${target_name} PRIVATE "LINKER:--exclude-libs,ALL")

    # `--gc-sections` collects nothing without these. A linked build inherited
    # both from `nanobind-static`; split mode links no nanobind target.
    target_compile_options(
      ${target_name}
      PRIVATE
        "$<$<OR:$<CONFIG:Release>,$<CONFIG:MinSizeRel>,$<CONFIG:RelWithDebInfo>>:-ffunction-sections;-fdata-sections>"
    )
    target_link_options(
      ${target_name}
      PRIVATE
      "$<$<OR:$<CONFIG:Release>,$<CONFIG:MinSizeRel>,$<CONFIG:RelWithDebInfo>>:LINKER:--gc-sections>"
    )
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
