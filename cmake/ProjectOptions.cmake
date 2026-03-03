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
  option(AIGVERSE_ENABLE_COVERAGE "Enable coverage reporting" OFF)
  option(AIGVERSE_WARNINGS_AS_ERRORS "Treat Warnings As Errors" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_ADDRESS "Enable address sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_LEAK "Enable leak sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_UNDEFINED "Enable undefined sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_THREAD "Enable thread sanitizer" OFF)
  option(AIGVERSE_ENABLE_SANITIZER_MEMORY "Enable memory sanitizer" OFF)
  option(AIGVERSE_ENABLE_PCH "Enable precompiled headers" OFF)
  option(AIGVERSE_ENABLE_CACHE "Enable ccache" ON)
endmacro()

macro(aigverse_apply_options)
  include(cmake/StandardProjectSettings.cmake)

  add_library(aigverse_warnings INTERFACE)
  add_library(aigverse_options INTERFACE)

  include(cmake/CompilerWarnings.cmake)
  aigverse_set_project_warnings(aigverse_warnings
                                ${AIGVERSE_WARNINGS_AS_ERRORS} "" "" "" "")

  include(cmake/Sanitizers.cmake)
  aigverse_supports_sanitizers()
  aigverse_enable_sanitizers(
    aigverse_options ${AIGVERSE_ENABLE_SANITIZER_ADDRESS}
    ${AIGVERSE_ENABLE_SANITIZER_LEAK} ${AIGVERSE_ENABLE_SANITIZER_UNDEFINED}
    ${AIGVERSE_ENABLE_SANITIZER_THREAD} ${AIGVERSE_ENABLE_SANITIZER_MEMORY})

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

endmacro()
