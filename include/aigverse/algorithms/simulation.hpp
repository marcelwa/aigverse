//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_SIMULATION_HPP
#define AIGVERSE_SIMULATION_HPP

#include "aigverse/types.hpp"

#include <kitty/dynamic_truth_table.hpp>
#include <mockturtle/algorithms/simulation.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <iostream>
#include <new>
#include <unordered_map>
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

    m.def(
        "simulate_nodes",
        [](const Ntk& ntk) -> std::unordered_map<uint64_t, kitty::dynamic_truth_table>
        {
            if (ntk.num_pis() > 16)
            {
                std::cout << "[w] trying to simulate a network with more than 16 inputs; this might take while and "
                             "potentially cause memory issues\n";
            }

            try
            {
                const auto n_map = mockturtle::simulate_nodes<kitty::dynamic_truth_table>(
                    ntk,
                    // NOLINTNEXTLINE
                    mockturtle::default_simulator<kitty::dynamic_truth_table>{static_cast<unsigned>(ntk.num_pis())});

                std::unordered_map<mockturtle::node<Ntk>, kitty::dynamic_truth_table> node_to_tt{};

                // convert vector implementation to unordered_map
                ntk.foreach_node([&n_map, &node_to_tt](const auto& n) { node_to_tt[n] = n_map[n]; });
                return node_to_tt;
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
    detail::simulation<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_SIMULATION_HPP
