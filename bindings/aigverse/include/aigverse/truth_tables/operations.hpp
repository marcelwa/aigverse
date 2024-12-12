//
// Created by marcel on 12.12.24.
//

#ifndef AIGVERSE_OPERATIONS_HPP
#define AIGVERSE_OPERATIONS_HPP

#include "aigverse/types.hpp"

#include <kitty/dynamic_truth_table.hpp>
#include <kitty/operations.hpp>
#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

inline void truth_table_operations(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "ternary_majority",
        [](const aigverse::truth_table& a, const aigverse::truth_table& b,
           const aigverse::truth_table& c) -> aigverse::truth_table { return kitty::ternary_majority(a, b, c); },
        "a"_a, "b"_a, "c"_a, "Compute the ternary majority of three truth tables.");

    m.def(
        "cofactor0", [](const aigverse::truth_table& tt, const uint8_t var_index) -> aigverse::truth_table
        { return kitty::cofactor0(tt, var_index); },
        "Returns the cofactor with respect to 0 of the variable at index `var_index` in the given truth table.");
    m.def(
        "cofactor1", [](const aigverse::truth_table& tt, const uint8_t var_index) -> aigverse::truth_table
        { return kitty::cofactor1(tt, var_index); },
        "Returns the cofactor with respect to 1 of the variable at index `var_index` in the given truth table.");
}

}  // namespace detail

inline void truth_table_operations(pybind11::module& m)
{
    detail::truth_table_operations(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_OPERATIONS_HPP
