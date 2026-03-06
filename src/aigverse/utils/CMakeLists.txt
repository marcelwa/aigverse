add_aigverse_python_binding(
  aigverse-utils
  bindings.cpp
  truth_table.cpp
  truth_table_operations.cpp
  MODULE_NAME
  utils
  INSTALL_DIR
  .)

if(SKBUILD_STATE STREQUAL "editable")
  install(
    FILES ${PROJECT_SOURCE_DIR}/python/aigverse/utils.pyi
    DESTINATION .
    COMPONENT aigverse_Python)
endif()
