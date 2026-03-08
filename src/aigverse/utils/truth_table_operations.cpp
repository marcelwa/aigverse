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
        R"pb(Computes the ternary majority of three truth tables.

Args:
    a: First truth table.
    b: Second truth table.
    c: Third truth table.

Returns:
    The bitwise majority truth table.)pb",
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
        R"pb(Computes the cofactor with respect to assigning one variable to ``0``.

Args:
    tt: Input truth table.
    var_index: Index of the variable to cofactor.

Returns:
    The cofactored truth table with ``var_index`` fixed to ``0``.

Raises:
    ValueError: If ``var_index`` is out of range.)pb",
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
        R"pb(Computes the cofactor with respect to assigning one variable to ``1``.

Args:
    tt: Input truth table.
    var_index: Index of the variable to cofactor.

Returns:
    The cofactored truth table with ``var_index`` fixed to ``1``.

Raises:
    ValueError: If ``var_index`` is out of range.)pb",
        nb::call_guard<nb::gil_scoped_release>());
}

}  // namespace detail

void bind_truth_table_operations(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_truth_table_operations(m);
}

}  // namespace aigverse
