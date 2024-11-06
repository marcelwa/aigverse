//
// Created by marcel on 06.11.24.
//

#ifndef SIMULATION_HPP
#define SIMULATION_HPP

#include <mockturtle/algorithms/simulation.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <iostream>
#include <new>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void simulation(pybind11::module& m)
{
    namespace py = pybind11;
    using namespace py::literals;

    m.def(
        "simulate",
        [](const Ntk& ntk) -> std::vector<kitty::dynamic_truth_table>
        {
            if (ntk.num_pis() > 16)
            {
                std::cout << "[w] trying to simulate a network with more than 16 inputs; this might take while and "
                             "potentially cause memory issues\n";
            }

            try
            {
                return mockturtle::simulate<kitty::dynamic_truth_table>(
                    ntk,
                    // NOLINTNEXTLINE
                    mockturtle::default_simulator<kitty::dynamic_truth_table>{static_cast<unsigned>(ntk.num_pis())});
            }
            catch (const std::bad_alloc&)
            {
                std::cout << "[e] network has too many inputs to store its truth table; out of memory!\n";
                throw;
            }
        },
        "network"_a);
}

}  // namespace detail

inline void simulation(pybind11::module& m)
{
    detail::simulation<mockturtle::aig_network>(m);
    detail::simulation<mockturtle::depth_view<mockturtle::aig_network>>(m);
}

}  // namespace aigverse

#endif  // SIMULATION_HPP
