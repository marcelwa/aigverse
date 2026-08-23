//
// Created by marcel on 21.08.26.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/simulation_sequential.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <stdexcept>
#include <utility>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void sequential_simulation(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    using result_t = mockturtle::simulate_sequential_result<bool>;

    nb::class_<result_t>(m, "SequentialSimulationResult",
                         R"pb(Represents the outcome of simulating a sequential network over several clock cycles.

Both traces are indexed by clock cycle first: ``outputs[cycle][index]`` is the value primary
output ``index`` took in that cycle, and ``states[cycle][index]`` the value register ``index``
held while that cycle was evaluated.

``states`` is one entry longer than ``outputs``, because simulating ``n`` cycles crosses
``n + 1`` state boundaries. The first is the reset state the run started from and the last is
the state it ended in.)pb")
        .def_ro("outputs", &result_t::outputs, R"pb(Primary output values, one list per clock cycle.)pb")
        .def_ro("states", &result_t::states, R"pb(Register values, one list per state boundary.)pb")
        .def_prop_ro(
            "num_cycles", [](const result_t& self) { return self.num_cycles(); },
            R"pb(Number of clock cycles simulated.)pb")
        .def_prop_ro(
            "reset_state", [](const result_t& self) { return self.reset_state(); },
            R"pb(The state the registers were reset to.)pb")
        .def_prop_ro(
            "final_state", [](const result_t& self) { return self.final_state(); },
            R"pb(The state the registers held after the last cycle.)pb")
        .def("__len__", [](const result_t& self) { return self.outputs.size(); })
        .def("__repr__",
             [](const result_t& self)
             {
                 return fmt::format("SequentialSimulationResult(num_cycles={}, num_pos={}, num_registers={})",
                                    self.num_cycles(), self.outputs.empty() ? 0UL : self.outputs.front().size(),
                                    self.states.empty() ? 0UL : self.states.front().size());
             });

    m.def(
        "simulate_sequential",
        [](const Ntk& ntk, const uint32_t num_cycles, std::vector<std::vector<bool>> stimulus,
           const bool undefined_reset_value) -> result_t
        {
            uint32_t cycle = 0;
            for (const auto& assignment : stimulus)
            {
                if (assignment.size() != ntk.num_pis())
                {
                    throw std::invalid_argument(fmt::format(
                        "stimulus for cycle {} assigns {} value(s), but the network has {} primary input(s)", cycle,
                        assignment.size(), ntk.num_pis()));
                }
                ++cycle;
            }

            // `stimulus_simulator` needs at least one assignment and repeats its last one for
            // the rest of the run, so holding every primary input low is a single all-false
            // assignment rather than a special case.
            if (stimulus.empty())
            {
                stimulus.emplace_back(ntk.num_pis(), false);
            }

            mockturtle::simulate_sequential_params ps{};
            ps.undefined_reset_value = undefined_reset_value;

            return mockturtle::simulate_sequential<bool>(ntk, num_cycles,
                                                         mockturtle::stimulus_simulator{std::move(stimulus)}, ps);
        },
        nb::arg("ntk"), nb::arg("num_cycles"), nb::arg("stimulus") = std::vector<std::vector<bool>>{},
        nb::arg("undefined_reset_value") = false,
        R"pb(Simulates a sequential network over a number of clock cycles.

Every register starts at its reset value, the combinational logic is evaluated once per
cycle, the primary outputs are recorded, and the register inputs are latched into the
register outputs for the next cycle.

This is what distinguishes it from :func:`~aigverse.algorithms.simulate`, which evaluates
the combinational logic exactly once and has no notion of a register.

Args:
    ntk: The sequential network to simulate.
    num_cycles: Number of clock cycles to run.
    stimulus: Primary input assignments, one list of ``ntk.num_pis`` values per clock cycle.
        Cycles past the end of the stimulus repeat its last assignment, so a single
        assignment holds for the whole run. Defaults to holding every primary input at
        ``False``, which is all a design without primary inputs needs.
    undefined_reset_value: Value a register starts at when its reset value is undefined,
        which is what a register defaults to and what an AIGER latch with a
        nondeterministic reset reads back as.

Returns:
    The primary output values and the register values, per clock cycle.

Raises:
    ValueError: If an assignment in ``stimulus`` does not have one value per primary input.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for the sequential AIG
template void sequential_simulation<aigverse::sequential_aig>(nanobind::module_& m);

}  // namespace detail

void bind_sequential_simulation(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::sequential_simulation<aigverse::sequential_aig>(m);
}

}  // namespace aigverse
