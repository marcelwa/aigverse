//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_TRUTH_TABLE_HPP
#define AIGVERSE_TRUTH_TABLE_HPP

#include <pybind11/pybind11.h>

namespace aigverse
{

// Registers truth table bindings
void bind_truth_table(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_TRUTH_TABLE_HPP
