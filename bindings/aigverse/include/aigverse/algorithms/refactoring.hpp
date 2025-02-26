//
// Created by marcel on 15.09.24.
//

#ifndef AIGVERSE_REFACTORING_HPP
#define AIGVERSE_REFACTORING_HPP

#include "aigverse/types.hpp"

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
void refactoring(pybind11::module& m)
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

                // copy the cleaned network back to the original network
                ntk = std::move(cleaned);
            }
            catch (const std::exception& e)
            {
                throw std::runtime_error(std::string("Error in sop_refactoring: ") + e.what());
            }
            catch (...)
            {
                throw std::runtime_error("Unknown error in sop_refactoring");
            }
        },
        "ntk"_a, "max_pis"_a = 6, "allow_zero_gain"_a = false, "use_reconvergence_cut"_a = false,
        "use_dont_cares"_a = false, "verbose"_a = false)

        ;
}

}  // namespace detail

inline void refactoring(pybind11::module& m)
{
    detail::refactoring<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_REFACTORING_HPP
