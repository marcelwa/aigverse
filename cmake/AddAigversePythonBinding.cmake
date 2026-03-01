function(add_aigverse_python_binding target_name)
  cmake_parse_arguments(ARG "" "MODULE_NAME;INSTALL_DIR" "" ${ARGN})
  set(SOURCES ${ARG_UNPARSED_ARGUMENTS})

  pybind11_add_module(${target_name} THIN_LTO ${SOURCES})

  if(ARG_MODULE_NAME)
    set_target_properties(${target_name} PROPERTIES OUTPUT_NAME
                                                    ${ARG_MODULE_NAME})
  endif()

  target_link_libraries(
    ${target_name} PRIVATE aigverse::mockturtle aigverse::aigverse_options
                           aigverse::aigverse_warnings)

  target_include_directories(${target_name} PRIVATE "${PROJECT_SOURCE_DIR}/src")

  target_compile_definitions(${target_name}
                             PRIVATE PYBIND11_DETAILED_ERROR_MESSAGES)

  target_precompile_headers(
    ${target_name} PRIVATE
    "$<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/src/aigverse/pch.hpp>")

  if(MSVC)
    target_compile_options(${target_name} PRIVATE /utf-8)
    target_compile_definitions(${target_name} PRIVATE UNICODE _UNICODE)
  endif()

  if(NOT ARG_INSTALL_DIR)
    set(ARG_INSTALL_DIR ".")
  endif()

  if(AIGVERSE_ENABLE_IMPORT_DIAGNOSTICS)
    get_target_property(_aigverse_binding_type ${target_name} TYPE)
    get_target_property(_aigverse_binding_output_name ${target_name}
                        OUTPUT_NAME)
    get_target_property(_aigverse_binding_prefix ${target_name} PREFIX)
    get_target_property(_aigverse_binding_suffix ${target_name} SUFFIX)
    get_target_property(_aigverse_binding_pic ${target_name}
                        POSITION_INDEPENDENT_CODE)
    get_target_property(_aigverse_binding_defs ${target_name}
                        COMPILE_DEFINITIONS)
    get_target_property(_aigverse_binding_opts ${target_name} COMPILE_OPTIONS)
    get_target_property(_aigverse_binding_link_opts ${target_name} LINK_OPTIONS)
    get_target_property(_aigverse_binding_link_libraries ${target_name}
                        LINK_LIBRARIES)

    message(STATUS "[aigverse-diagnostics] target=${target_name}")
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.TYPE=${_aigverse_binding_type}")
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.OUTPUT_NAME=${_aigverse_binding_output_name}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.PREFIX=${_aigverse_binding_prefix}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.SUFFIX=${_aigverse_binding_suffix}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.POSITION_INDEPENDENT_CODE=${_aigverse_binding_pic}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.COMPILE_DEFINITIONS=${_aigverse_binding_defs}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.COMPILE_OPTIONS=${_aigverse_binding_opts}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.LINK_OPTIONS=${_aigverse_binding_link_opts}"
    )
    message(
      STATUS
        "[aigverse-diagnostics] ${target_name}.LINK_LIBRARIES=${_aigverse_binding_link_libraries}"
    )
  endif()

  install(
    TARGETS ${target_name}
    DESTINATION ${ARG_INSTALL_DIR}
    COMPONENT aigverse_Python)
endfunction()
