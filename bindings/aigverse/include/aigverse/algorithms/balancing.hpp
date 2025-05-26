#ifndef AIGVERSE_ALGORITHMS_BALANCING_HPP
#define AIGVERSE_ALGORITHMS_BALANCING_HPP

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/balancing.hpp>
#include <mockturtle/algorithms/balancing/sop_balancing.hpp>  // Added
#include <mockturtle/networks/aig.hpp>                        // For aig_network
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
        [](Ntk& ntk) -> void { // Return void, modify ntk by reference (reassignment)
            mockturtle::balancing_params ps{};
            mockturtle::sop_rebalancing<Ntk> rebalance_fn; // Added
            // Corrected call based on mockturtle example: pass {rebalance_fn}
            ntk = mockturtle::balancing(static_cast<Ntk const&>(ntk), {rebalance_fn}, ps);
        },
        "ntk"_a,
        "Balances an AIG network. The network is updated with the balanced version."
    );
}

}  // namespace detail

void balancing(pybind11::module& m)
{
    detail::expose_balancing_functions<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_ALGORITHMS_BALANCING_HPP
