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

    // No GIL release here. `cleanup_dangling` builds a `topo_view` over the caller's network, which writes into that
    // network's storage; see `transform_helpers.hpp` for the rule. The other three view-building bindings run on a
    // clone instead and keep their guard, but this call is a single pass: a clone costs 75% of it at 10k gates and
    // 3.7x at 1k, against a threaded gain that is 2.36x at 10k and 0.87x at 1k (#482).
    m.def(
        "cleanup_dangling",
        [](const Ntk& ntk, const bool remove_dangling_pis = false, const bool remove_redundant_pos = false) -> Ntk
        { return mockturtle::cleanup_dangling(ntk, remove_dangling_pis, remove_redundant_pos); }, nb::arg("ntk"),
        nb::kw_only(), nb::arg("remove_dangling_pis") = false, nb::arg("remove_redundant_pos") = false,
        R"pb(Removes dangling logic (dead nodes) from a network.

Args:
    ntk: The input logic network.
    remove_dangling_pis: Whether to also remove dangling primary inputs.
    remove_redundant_pos: Whether to remove redundant primary outputs.

Returns:
    A cleaned network with dangling structures removed.)pb");
}

template void cleanup<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_cleanup_dangling(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::cleanup<aigverse::aig>(m);
}

}  // namespace aigverse
