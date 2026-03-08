//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/balancing.hpp>
#include <mockturtle/algorithms/balancing/esop_balancing.hpp>
#include <mockturtle/algorithms/balancing/sop_balancing.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <stdexcept>
#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void balancing(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "balancing",
        [](Ntk& ntk, const uint32_t cut_size = 4, const uint32_t cut_limit = 8, const bool minimize_truth_table = true,
           const bool only_on_critical_path = false, const std::string& rebalance_function = "sop",
           const bool sop_both_phases = true, const bool verbose = false) -> Ntk
        {
            mockturtle::balancing_params ps{};
            ps.cut_enumeration_ps.cut_size             = cut_size;
            ps.cut_enumeration_ps.cut_limit            = cut_limit;
            ps.cut_enumeration_ps.minimize_truth_table = minimize_truth_table;
            ps.only_on_critical_path                   = only_on_critical_path;
            ps.verbose                                 = verbose;

            if (rebalance_function == "sop")
            {
                mockturtle::sop_rebalancing<Ntk> rebalance_fn{};
                rebalance_fn.both_phases_ = sop_both_phases;

                return mockturtle::balancing(ntk, {rebalance_fn}, ps);
            }
            if (rebalance_function == "esop")
            {
                mockturtle::esop_rebalancing<Ntk> rebalance_fn{};
                rebalance_fn.both_phases = sop_both_phases;

                return mockturtle::balancing(ntk, {rebalance_fn}, ps);
            }

            throw std::invalid_argument(fmt::format(
                "Unknown rebalance function: '{}'. Possible values are 'sop' and 'esop'.", rebalance_function));
        },
        nb::arg("ntk"), nb::arg("cut_size") = 4, nb::arg("cut_limit") = 8, nb::arg("minimize_truth_table") = true,
        nb::arg("only_on_critical_path") = false, nb::arg("rebalance_function") = "sop",
        nb::arg("sop_both_phases") = true, nb::arg("verbose") = false,
        R"pb(Balances a network using SOP or ESOP-based local restructuring.

Args:
    ntk: The input logic network.
    cut_size: Maximum cut size used during cut enumeration.
    cut_limit: Maximum number of cuts retained per node.
    minimize_truth_table: Whether to minimize cut truth tables during enumeration.
    only_on_critical_path: Whether to balance only nodes on the critical path.
    rebalance_function: Rebalancing engine to use. Supported values are
        ``"sop"`` and ``"esop"``.
    sop_both_phases: Whether to consider both phases in SOP/ESOP balancing.
    verbose: Whether to print verbose progress output.

Returns:
    A new balanced network.

Raises:
    ValueError: If ``rebalance_function`` is not one of the supported values.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void balancing<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_balancing(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::balancing<aigverse::aig>(m);
}

}  // namespace aigverse
