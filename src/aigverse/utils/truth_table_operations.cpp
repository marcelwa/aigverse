//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <kitty/operations.hpp>
#include <nanobind/nanobind.h>

#include <cstdint>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

static void bind_truth_table_operations(nanobind::module_& m)
{
    namespace nb = nanobind;

    m.def(
        "ternary_majority",
        [](const aigverse::truth_table& a, const aigverse::truth_table& b, const aigverse::truth_table& c)
        { return kitty::ternary_majority(a, b, c); }, nb::arg("a"), nb::arg("b"), nb::arg("c"),
        "Compute the ternary majority of three truth tables.",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)

    m.def(
        "cofactor0",
        [](const aigverse::truth_table& tt, const uint8_t var_index)
        {
            if (var_index >= tt.num_vars())
            {
                throw std::invalid_argument("var_index out of range");
            }
            return kitty::cofactor0(tt, var_index);
        },
        nb::arg("tt"), nb::arg("var_index"),
        "Returns the cofactor with respect to 0 of the variable at index `var_index` in the given truth table.",
        nb::call_guard<nb::gil_scoped_release>());

    m.def(
        "cofactor1",
        [](const aigverse::truth_table& tt, const uint8_t var_index)
        {
            if (var_index >= tt.num_vars())
            {
                throw std::invalid_argument("var_index out of range");
            }
            return kitty::cofactor1(tt, var_index);
        },
        nb::arg("tt"), nb::arg("var_index"),
        "Returns the cofactor with respect to 1 of the variable at index `var_index` in the given truth table.",
        nb::call_guard<nb::gil_scoped_release>());
}

}  // namespace detail

void bind_truth_table_operations(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_truth_table_operations(m);
}

}  // namespace aigverse
