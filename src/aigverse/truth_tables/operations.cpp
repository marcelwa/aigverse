//
// Created by marcel on 03.09.25.
//

#include "aigverse/truth_tables/operations.hpp"

#include "aigverse/types.hpp"

#include <kitty/operations.hpp>
#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

static void bind_truth_table_operations(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "ternary_majority",
        [](const aigverse::truth_table& a, const aigverse::truth_table& b, const aigverse::truth_table& c)
        { return kitty::ternary_majority(a, b, c); }, "a"_a, "b"_a, "c"_a,
        "Compute the ternary majority of three truth tables.", pybind11::call_guard<pybind11::gil_scoped_release>());

    m.def(
        "cofactor0", [](const aigverse::truth_table& tt, const uint8_t var_index)
        { return kitty::cofactor0(tt, var_index); }, "tt"_a, "var_index"_a,
        "Returns the cofactor with respect to 0 of the variable at index `var_index` in the given truth table.",
        pybind11::call_guard<pybind11::gil_scoped_release>());

    m.def(
        "cofactor1", [](const aigverse::truth_table& tt, const uint8_t var_index)
        { return kitty::cofactor1(tt, var_index); }, "tt"_a, "var_index"_a,
        "Returns the cofactor with respect to 1 of the variable at index `var_index` in the given truth table.",
        pybind11::call_guard<pybind11::gil_scoped_release>());
}

}  // namespace detail

void bind_truth_table_operations(pybind11::module_& m)
{
    detail::bind_truth_table_operations(m);
}

}  // namespace aigverse
