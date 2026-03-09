add_aigverse_python_binding(
  aigverse-generators
  bindings.cpp
  random.cpp
  arithmetic.cpp
  control.cpp
  MODULE_NAME
  generators
  INSTALL_DIR
  .)

if(SKBUILD_STATE STREQUAL "editable")
  install(
    FILES ${PROJECT_SOURCE_DIR}/python/aigverse/generators.pyi
    DESTINATION .
    COMPONENT aigverse_Python)
endif()
