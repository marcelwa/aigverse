add_aigverse_python_binding(
  aigverse-io
  bindings.cpp
  read_aiger.cpp
  write_aiger.cpp
  read_pla.cpp
  read_verilog.cpp
  write_verilog.cpp
  write_dot.cpp
  MODULE_NAME
  io
  INSTALL_DIR
  .)

if(SKBUILD_STATE STREQUAL "editable")
  install(
    FILES ${PROJECT_SOURCE_DIR}/python/aigverse/io.pyi
    DESTINATION .
    COMPONENT aigverse_Python)
endif()
