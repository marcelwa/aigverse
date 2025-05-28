#ifndef AIGVERSE_ALGORITHMS_BALANCING_HPP
#define AIGVERSE_ALGORITHMS_BALANCING_HPP

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/balancing.hpp>
#include <mockturtle/algorithms/balancing/sop_balancing.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void expose_balancing_functions(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "aig_balance",
        [](Ntk& ntk, const uint32_t cut_size = 4, const uint32_t cut_limit = 8, const bool minimize_truth_table = true,
           const bool only_on_critical_path = false, const bool sop_both_phases = true,
           const bool verbose = false) -> void
        {
            mockturtle::balancing_params ps{};
            ps.cut_enumeration_ps.cut_size             = cut_size;
            ps.cut_enumeration_ps.cut_limit            = cut_limit;
            ps.cut_enumeration_ps.minimize_truth_table = minimize_truth_table;
            ps.only_on_critical_path                   = only_on_critical_path;
            ps.verbose                                 = verbose;

            mockturtle::sop_rebalancing<Ntk> rebalance_fn{};
            rebalance_fn.both_phases_ = sop_both_phases;

            ntk = mockturtle::balancing(ntk, {rebalance_fn}, ps);
        },
        "ntk"_a, "cut_size"_a = 4, "cut_limit"_a = 8, "minimize_truth_table"_a = true,
        "only_on_critical_path"_a = false, "sop_both_phases"_a = true, "verbose"_a = false);
}

}  // namespace detail

inline void balancing(pybind11::module& m)
{
    detail::expose_balancing_functions<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_ALGORITHMS_BALANCING_HPP
