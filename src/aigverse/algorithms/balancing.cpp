//
// Created by marcel on 03.09.25.
//

#include "aigverse/algorithms/balancing.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/balancing.hpp>
#include <mockturtle/algorithms/balancing/esop_balancing.hpp>
#include <mockturtle/algorithms/balancing/sop_balancing.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>

#include <stdexcept>
#include <string_view>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void balancing(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "balancing",
        [](Ntk& ntk, const uint32_t cut_size = 4, const uint32_t cut_limit = 8, const bool minimize_truth_table = true,
           const bool only_on_critical_path = false, const std::string_view& rebalance_function = "sop",
           const bool sop_both_phases = true, const bool verbose = false) -> void
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

                ntk = mockturtle::balancing(ntk, {rebalance_fn}, ps);
            }
            else if (rebalance_function == "esop")
            {
                mockturtle::esop_rebalancing<Ntk> rebalance_fn{};
                rebalance_fn.both_phases = sop_both_phases;

                ntk = mockturtle::balancing(ntk, {rebalance_fn}, ps);
            }
            else
            {
                throw std::invalid_argument(fmt::format(
                    "Unknown rebalance function: '{}'. Possible values are 'sop' and 'esop'.", rebalance_function));
            }
        },
        "ntk"_a, "cut_size"_a = 4, "cut_limit"_a = 8, "minimize_truth_table"_a = true,
        "only_on_critical_path"_a = false, "rebalance_function"_a = "sop", "sop_both_phases"_a = true,
        "verbose"_a = false, pybind11::call_guard<pybind11::gil_scoped_release>());
}

// Explicit instantiation for AIG
template void balancing<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_balancing(pybind11::module_& m)
{
    detail::balancing<aigverse::aig>(m);
}

}  // namespace aigverse
