/*
 * Precompiled header for the pyaigverse module.
 * Aggregates commonly used heavy system and library headers to reduce
 * compile times for each translation unit.
 */

#pragma once

// pybind11 core
// NOLINTBEGIN(misc-include-cleaner)
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

// fmt formatting
#include <fmt/format.h>

// mockturtle frequently used minimal set
#include <mockturtle/networks/aig.hpp>
#include <mockturtle/networks/sequential.hpp>
#include <mockturtle/traits.hpp>
#include <mockturtle/views/depth_view.hpp>
#include <mockturtle/views/fanout_view.hpp>

// kitty truth tables
#include <kitty/dynamic_truth_table.hpp>

// STL basics
#include <array>
#include <cstdint>
#include <functional>
#include <iostream>
#include <map>
#include <optional>
#include <set>
#include <stdexcept>
#include <string>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

// aigverse types
#include "types.hpp"
// NOLINTEND(misc-include-cleaner)
