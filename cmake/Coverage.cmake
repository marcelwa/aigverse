function(aigverse_enable_coverage target)
  if(NOT CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    message(FATAL_ERROR "AIGVERSE_ENABLE_COVERAGE requires GCC.")
  endif()
  # Concurrent binding calls must not race on GCC's coverage counters.
  target_compile_options(${target} INTERFACE --coverage -fprofile-update=atomic
                                             -O0 -g)
  target_link_options(${target} INTERFACE --coverage)
endfunction()
