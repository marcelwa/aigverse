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

  # Keep the statically linked dependencies local. nanobind attaches
  # `--exclude-libs`, `-ffunction-sections`/`-fdata-sections` and
  # `--gc-sections` to the nanobind library target as PUBLIC options, and a
  # split-mode extension links no such target, so it inherits none of them.
  # Without this block every module re-exports the internals of the static
  # libraries it embeds -- five copies of mockturtle's `abc::exorcism`, mutable
  # globals included, which the dynamic linker is then free to interpose across
  # modules.
  if(APPLE)
    target_link_options(${target_name} PRIVATE
                        "LINKER:-exported_symbol,_PyInit_${module_name}")

    # Apple's x86-64 ABI compares RTTI by pointer, so nanobind's exception type
    # information has to stay exported for an exception to cross a module
    # boundary. Its arm64 ABI compares the type names instead.
    if(CMAKE_SYSTEM_PROCESSOR STREQUAL "x86_64")
      target_link_options(
        ${target_name}
        PRIVATE
        "LINKER:-exported_symbol,__ZTIN8nanobind4abi112python_errorE"
        "LINKER:-exported_symbol,__ZTSN8nanobind4abi112python_errorE"
        "LINKER:-exported_symbol,__ZTIN8nanobind4abi117builtin_exceptionE"
        "LINKER:-exported_symbol,__ZTSN8nanobind4abi117builtin_exceptionE")
    endif()
  elseif(UNIX)
    target_link_options(${target_name} PRIVATE "LINKER:--exclude-libs,ALL")

    # Section garbage collection needs the per-function and per-data sections to
    # collect; nanobind's own `-Os` does not emit them.
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
  elseif(WIN32)
    set_target_properties(${target_name} PROPERTIES WINDOWS_EXPORT_ALL_SYMBOLS
                                                    OFF)
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
