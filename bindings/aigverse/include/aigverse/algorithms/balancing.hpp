#ifndef AIGVERSE_ALGORITHMS_BALANCING_HPP
#define AIGVERSE_ALGORITHMS_BALANCING_HPP

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/balancing.hpp>
#include <mockturtle/networks/aig.hpp>  // For aig_network
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
            // Assuming mockturtle::balancing_params exists and its default constructor is suitable.
            mockturtle::balancing_params ps{};
            // Assuming mockturtle::balancing returns a new network, which is then assigned back to ntk.
            // This matches the style in rewriting.hpp
            ntk = mockturtle::balancing(ntk, ps);
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
