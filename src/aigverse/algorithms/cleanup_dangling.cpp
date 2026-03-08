//
// Created by marcel on 06.03.26.
//

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/cleanup.hpp>
#include <nanobind/nanobind.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void cleanup(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "cleanup_dangling",
        [](const Ntk& ntk, const bool remove_dangling_pis = false, const bool remove_redundant_pos = false) -> Ntk
        { return mockturtle::cleanup_dangling(ntk, remove_dangling_pis, remove_redundant_pos); }, nb::arg("ntk"),
        nb::arg("remove_dangling_pis") = false, nb::arg("remove_redundant_pos") = false,
        R"pb(Removes dangling logic (dead nodes) from a network.

Args:
    ntk: The input logic network.
    remove_dangling_pis: Whether to also remove dangling primary inputs.
    remove_redundant_pos: Whether to remove redundant primary outputs.

Returns:
    A cleaned network with dangling structures removed.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

template void cleanup<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_cleanup_dangling(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::cleanup<aigverse::aig>(m);
}

}  // namespace aigverse
