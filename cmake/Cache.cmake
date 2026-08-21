# Enable cache if available
function(aigverse_enable_cache)
  # ccache's MSVC support is nominal: half the invocations come back
  # "Uncacheable" and the rest never hit, so it costs a process launch per
  # translation unit and returns nothing. sccache is what MSVC builds actually
  # cache with, so make it the default there.
  if(MSVC)
    set(CACHE_OPTION_DEFAULT "sccache")
  else()
    set(CACHE_OPTION_DEFAULT "ccache")
  endif()

  set(CACHE_OPTION
      ${CACHE_OPTION_DEFAULT}
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
    # The Visual Studio generator ignores CMAKE_<LANG>_COMPILER_LAUNCHER
    # outright. Configuring one there looks like it works and caches nothing,
    # which is exactly how this went unnoticed until Windows CI was timed
    # against the other platforms.
    if(CMAKE_GENERATOR MATCHES "Visual Studio")
      message(
        WARNING
          "${CACHE_OPTION} was found, but the '${CMAKE_GENERATOR}' generator ignores "
          "compiler launchers, so nothing will be cached. Configure with -G Ninja "
          "(or set CMAKE_GENERATOR=Ninja) to make the cache effective.")
    endif()
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
