# Enable cache if available
function(aigverse_enable_cache)
  set(CACHE_OPTION
      "ccache"
      CACHE STRING "Compiler cache to be used")
  set(CACHE_OPTION_VALUES "ccache" "sccache")
  set_property(CACHE CACHE_OPTION PROPERTY STRINGS ${CACHE_OPTION_VALUES})
  list(FIND CACHE_OPTION_VALUES ${CACHE_OPTION} CACHE_OPTION_INDEX)

  if(CACHE_OPTION_INDEX EQUAL -1)
    message(
      FATAL_ERROR
        "Unsupported compiler cache '${CACHE_OPTION}'. Supported entries are ${CACHE_OPTION_VALUES}"
    )
  endif()

  unset(CACHE_BINARY CACHE)
  find_program(CACHE_BINARY NAMES ${CACHE_OPTION})
  if(CACHE_BINARY)
    message(STATUS "${CACHE_BINARY} found and enabled")
    set(CMAKE_CXX_COMPILER_LAUNCHER
        ${CACHE_BINARY}
        CACHE FILEPATH "CXX compiler cache used")
    set(CMAKE_C_COMPILER_LAUNCHER
        ${CACHE_BINARY}
        CACHE FILEPATH "C compiler cache used")
  else()
    unset(CMAKE_CXX_COMPILER_LAUNCHER CACHE)
    unset(CMAKE_C_COMPILER_LAUNCHER CACHE)
    message(
      WARNING "${CACHE_OPTION} is enabled but was not found. Not using it")
  endif()
endfunction()
