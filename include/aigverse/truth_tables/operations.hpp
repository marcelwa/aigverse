//
// Created by marcel on 12.12.24.
//

#pragma once

namespace pybind11
{
class module_;
}

namespace aigverse
{

// Registers truth tables' free function bindings
void bind_truth_table_operations(pybind11::module_& m);

}  // namespace aigverse
