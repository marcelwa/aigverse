add_aigverse_python_binding(
  aigverse-algorithms
  bindings.cpp
  balancing.cpp
  equivalence_checking.cpp
  refactoring.cpp
  resubstitution.cpp
  rewriting.cpp
  simulation.cpp
  MODULE_NAME
  algorithms
  INSTALL_DIR
  .)

if(SKBUILD_STATE STREQUAL "editable")
  install(
    FILES ${PROJECT_SOURCE_DIR}/python/aigverse/algorithms.pyi
    DESTINATION .
    COMPONENT aigverse_Python)
endif()
