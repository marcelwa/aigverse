# Enable cache if available
function(aigverse_enable_cache)
  # Check for available cache programs, preferring sccache.
  find_program(SCCACHE_BINARY sccache)
  find_program(CCACHE_BINARY ccache)

  if(SCCACHE_BINARY)
    set(CACHE_OPTION "sccache")
    set(CACHE_BINARY ${SCCACHE_BINARY})
    message(STATUS "Compiler cache 'sccache' found and enabled")
  elseif(CCACHE_BINARY)
    set(CACHE_OPTION "ccache")
    set(CACHE_BINARY ${CCACHE_BINARY})
    message(STATUS "Compiler cache 'ccache' found and enabled")
  else()
    set(CACHE_OPTION_VALUES "ccache" "sccache")
    message(NOTICE
            "No compiler cache found. Checked for: ${CACHE_OPTION_VALUES}")
    return()
  endif()

  set(CMAKE_C_COMPILER_LAUNCHER
      ${CACHE_BINARY}
      PARENT_SCOPE)
  set(CMAKE_CXX_COMPILER_LAUNCHER
      ${CACHE_BINARY}
      PARENT_SCOPE)
endfunction()
