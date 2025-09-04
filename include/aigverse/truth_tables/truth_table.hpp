//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_TRUTH_TABLE_HPP
#define AIGVERSE_TRUTH_TABLE_HPP

namespace pybind11
{
class module_;
}

namespace aigverse
{

// Registers truth table bindings
void bind_truth_table(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_TRUTH_TABLE_HPP
