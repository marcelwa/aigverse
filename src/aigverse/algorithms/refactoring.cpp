//
// Created by marcel on 03.09.25.
//

#include "aigverse/algorithms/refactoring.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/node_resynthesis/sop_factoring.hpp>
#include <mockturtle/algorithms/refactoring.hpp>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void refactoring(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "sop_refactoring",
        [](Ntk& ntk, const uint32_t max_pis = 6, const bool allow_zero_gain = false,
           const bool use_reconvergence_cut = false, const bool use_dont_cares = false,
           const bool verbose = false) -> void
        {
            try
            {
                mockturtle::refactoring_params params{};
                params.max_pis               = max_pis;
                params.allow_zero_gain       = allow_zero_gain;
                params.use_reconvergence_cut = use_reconvergence_cut;
                params.use_dont_cares        = use_dont_cares;
                params.verbose               = verbose;

                mockturtle::sop_factoring<Ntk> sop_resyn_engine{};

                mockturtle::refactoring(ntk, sop_resyn_engine, params);

                // create a temporary network with dangling nodes cleaned up
                auto cleaned = mockturtle::cleanup_dangling(ntk);

                ntk = std::move(cleaned);
            }
            catch (const std::exception& e)
            {
                throw std::runtime_error(fmt::format("Error in mockturtle::sop_refactoring: {}", e.what()));
            }
            catch (...)
            {
                throw std::runtime_error("Unknown error in mockturtle::sop_refactoring");
            }
        },
        "ntk"_a, "max_pis"_a = 6, "allow_zero_gain"_a = false, "use_reconvergence_cut"_a = false,
        "use_dont_cares"_a = false, "verbose"_a = false, pybind11::call_guard<pybind11::gil_scoped_release>());
}

// Explicit instantiation for AIG
template void refactoring<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_refactoring(pybind11::module_& m)
{
    detail::refactoring<aigverse::aig>(m);
}

}  // namespace aigverse
