//
// Created by marcel on 12.12.24.
//

#ifndef AIGVERSE_OPERATIONS_HPP
#define AIGVERSE_OPERATIONS_HPP

#include <pybind11/pybind11.h>

namespace aigverse
{

// Registers truth tables' free function bindings
void bind_truth_table_operations(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_OPERATIONS_HPP
