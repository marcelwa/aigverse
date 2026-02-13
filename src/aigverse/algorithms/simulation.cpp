//
// Created by marcel on 03.09.25.
//

#include "aigverse/algorithms/simulation.hpp"

#include "aigverse/types.hpp"

#include <kitty/dynamic_truth_table.hpp>
#include <mockturtle/algorithms/simulation.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // NOLINT(misc-include-cleaner)

#include <iostream>
#include <new>
#include <unordered_map>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void simulation(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;  // NOLINT(misc-unused-alias-decls)
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
        "network"_a);  // NOLINT(misc-include-cleaner)

    m.def(
        "simulate_nodes",
        [](const Ntk& ntk) -> std::unordered_map<uint64_t, kitty::dynamic_truth_table>  // NOLINT(misc-include-cleaner)
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

                std::unordered_map<mockturtle::node<Ntk>, kitty::dynamic_truth_table>
                    node_to_tt{};  // NOLINT(misc-include-cleaner)

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
        "network"_a, pybind11::call_guard<pybind11::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void simulation<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_simulation(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::simulation<aigverse::aig>(m);
}

}  // namespace aigverse
