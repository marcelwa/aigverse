//
// Created by marcel on 06.11.24.
//

#pragma once

namespace pybind11
{
class module_;
}

namespace aigverse
{

// Registers truth table bindings
void bind_truth_table(pybind11::module_& m);

}  // namespace aigverse
