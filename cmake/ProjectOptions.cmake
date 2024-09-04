include(cmake/SystemLink.cmake)
include(CMakeDependentOption)
include(CheckCXXCompilerFlag)
include(FetchContent)

macro(aigverse_supports_sanitizers)
  if((CMAKE_CXX_COMPILER_ID MATCHES ".*Clang.*" OR CMAKE_CXX_COMPILER_ID MATCHES
                                                   ".*GNU.*") AND NOT WIN32)
    set(SUPPORTS_UBSAN ON)
  else()
    set(SUPPORTS_UBSAN OFF)
  endif()

  if((CMAKE_CXX_COMPILER_ID MATCHES ".*Clang.*" OR CMAKE_CXX_COMPILER_ID MATCHES
                                                   ".*GNU.*") AND WIN32)
    set(SUPPORTS_ASAN OFF)
  else()
    set(SUPPORTS_ASAN ON)
  endif()
endmacro()

macro(aigverse_setup_options)
  option(AIGVERSE_ENABLE_HARDENING "Enable hardening" OFF)
  option(AIGVERSE_ENABLE_COVERAGE "Enable coverage reporting" OFF)
  cmake_dependent_option(
    AIGVERSE_ENABLE_GLOBAL_HARDENING
    "Attempt to push hardening options to built dependencies" ON
    AIGVERSE_ENABLE_HARDENING OFF)

  option(AIGVERSE_ENABLE_IPO "Enable IPO/LTO" OFF)
  option(AIGVERSE_WARNINGS_AS_ERRORS "Treat Warnings As Errors" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_ADDRESS "Enable address sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_LEAK "Enable leak sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_UNDEFINED "Enable undefined sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_THREAD "Enable thread sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_MEMORY "Enable memory sanitizer" OFF)
  option(AIGVERSE_ENABLE_UNITY_BUILD "Enable unity builds" OFF)
  option(AIGVERSE_ENABLE_PCH "Enable precompiled headers" OFF)
  option(AIGVERSE_ENABLE_CACHE "Enable ccache" ON)

  if(NOT PROJECT_IS_TOP_LEVEL)
    mark_as_advanced(
      AIGVERSE_ENABLE_IPO
      AIGVERSE_WARNINGS_AS_ERRORS
      AIGVERSE_ENABLE_SANITIZER_ADDRESS
      AIGVERSE_ENABLE_SANITIZER_LEAK
      AIGVERSE_ENABLE_SANITIZER_UNDEFINED
      AIGVERSE_ENABLE_SANITIZER_THREAD
      AIGVERSE_ENABLE_SANITIZER_MEMORY
      AIGVERSE_ENABLE_UNITY_BUILD
      AIGVERSE_ENABLE_COVERAGE
      AIGVERSE_ENABLE_PCH
      AIGVERSE_ENABLE_CACHE)
  endif()

endmacro()

macro(aigverse_global_options)
  if(AIGVERSE_ENABLE_IPO)
    include(cmake/InterproceduralOptimization.cmake)
    aigverse_enable_ipo()
  endif()

  aigverse_supports_sanitizers()

  if(AIGVERSE_ENABLE_HARDENING AND AIGVERSE_ENABLE_GLOBAL_HARDENING)
    include(cmake/Hardening.cmake)
    if(NOT SUPPORTS_UBSAN
       OR AIGVERSE_ENABLE_SANITIZER_UNDEFINED
       OR AIGVERSE_ENABLE_SANITIZER_ADDRESS
       OR AIGVERSE_ENABLE_SANITIZER_THREAD
       OR AIGVERSE_ENABLE_SANITIZER_LEAK)
      set(ENABLE_UBSAN_MINIMAL_RUNTIME FALSE)
    else()
      set(ENABLE_UBSAN_MINIMAL_RUNTIME TRUE)
    endif()
    aigverse_enable_hardening(aigverse_options ON ${ENABLE_UBSAN_MINIMAL_RUNTIME})
  endif()
endmacro()

macro(aigverse_local_options)
  if(PROJECT_IS_TOP_LEVEL)
    include(cmake/StandardProjectSettings.cmake)
  endif()

  add_library(aigverse_warnings INTERFACE)
  add_library(aigverse_options INTERFACE)

  include(cmake/CompilerWarnings.cmake)
  aigverse_set_project_warnings(aigverse_warnings ${AIGVERSE_WARNINGS_AS_ERRORS}
                               "" "" "" "")

  include(cmake/Sanitizers.cmake)
  aigverse_enable_sanitizers(
    aigverse_options ${AIGVERSE_ENABLE_SANITIZER_ADDRESS}
    ${AIGVERSE_ENABLE_SANITIZER_LEAK} ${AIGVERSE_ENABLE_SANITIZER_UNDEFINED}
    ${AIGVERSE_ENABLE_SANITIZER_THREAD} ${AIGVERSE_ENABLE_SANITIZER_MEMORY})

  set_target_properties(aigverse_options
                        PROPERTIES UNITY_BUILD ${AIGVERSE_ENABLE_UNITY_BUILD})

  if(AIGVERSE_ENABLE_PCH)
    target_precompile_headers(aigverse_options INTERFACE <vector> <string>
                              <utility>)
  endif()

  if(AIGVERSE_ENABLE_CACHE)
    include(cmake/Cache.cmake)
    aigverse_enable_cache()
  endif()

  if(AIGVERSE_ENABLE_COVERAGE)
    include(cmake/Coverage.cmake)
    aigverse_enable_coverage(aigverse_options)
  endif()

  if(AIGVERSE_WARNINGS_AS_ERRORS)
    check_cxx_compiler_flag("-Wl,--fatal-warnings" LINKER_FATAL_WARNINGS)
    if(LINKER_FATAL_WARNINGS)
      # This is not working consistently, so disabling for now
      # target_link_options(aigverse_options INTERFACE -Wl,--fatal-warnings)
    endif()
  endif()

  if(AIGVERSE_ENABLE_HARDENING AND NOT AIGVERSE_ENABLE_GLOBAL_HARDENING)
    include(cmake/Hardening.cmake)
    if(NOT SUPPORTS_UBSAN
       OR AIGVERSE_ENABLE_SANITIZER_UNDEFINED
       OR AIGVERSE_ENABLE_SANITIZER_ADDRESS
       OR AIGVERSE_ENABLE_SANITIZER_THREAD
       OR AIGVERSE_ENABLE_SANITIZER_LEAK)
      set(ENABLE_UBSAN_MINIMAL_RUNTIME FALSE)
    else()
      set(ENABLE_UBSAN_MINIMAL_RUNTIME TRUE)
    endif()
    aigverse_enable_hardening(aigverse_options OFF
                             ${ENABLE_UBSAN_MINIMAL_RUNTIME})
  endif()

endmacro()
