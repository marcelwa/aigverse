add_aigverse_python_binding(
  aigverse-networks
  bindings.cpp
  logic_networks.cpp
  edge_list.cpp
  index_list.cpp
  MODULE_NAME
  networks
  INSTALL_DIR
  .)

if(SKBUILD_STATE STREQUAL "editable")
  install(
    FILES ${PROJECT_SOURCE_DIR}/python/aigverse/networks.pyi
    DESTINATION .
    COMPONENT aigverse_Python)
endif()
