/*
 * Precompiled header for the pyaigverse module.
 * Aggregates commonly used heavy system and library headers to reduce
 * compile times for each translation unit.
 */

#pragma once

// pybind11 core
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

// fmt formatting
#include <fmt/format.h>

// mockturtle frequently used minimal set
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/traits.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>

// kitty truth tables
#include <kitty/dynamic_truth_table.hpp>

// STL basics
#include <cstdint>
#include <functional>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

// lorina parsers
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
#include <lorina/verilog.hpp>

// mockturtle IO writers/readers
#include <mockturtle/io/aiger_reader.hpp>
#include <mockturtle/io/verilog_reader.hpp>
#include <mockturtle/io/write_aiger.hpp>
#include <mockturtle/io/write_dot.hpp>
#include <mockturtle/io/write_verilog.hpp>
