//
// Created by marcel on 09.09.24.
//

#ifndef AIGVERSE_RESUBSTITUTION_HPP
#define AIGVERSE_RESUBSTITUTION_HPP

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/aig_resub.hpp>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/resubstitution.hpp>
#include <pybind11/pybind11.h>

#include <cstdint>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void resubstitution(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "aig_resubstitution",
        [](Ntk& ntk, const uint32_t max_pis = 8, const uint32_t max_divisors = 150, const uint32_t max_inserts = 2,
           const uint32_t skip_fanout_limit_for_roots = 1000, const uint32_t skip_fanout_limit_for_divisors = 100,
           const bool verbose = false, const bool use_dont_cares = false, const uint32_t window_size = 12,
           const bool preserve_depth = false) -> void
        {
            mockturtle::resubstitution_params params{};
            params.max_pis                        = max_pis;
            params.max_divisors                   = max_divisors;
            params.max_inserts                    = max_inserts;
            params.skip_fanout_limit_for_roots    = skip_fanout_limit_for_roots;
            params.skip_fanout_limit_for_divisors = skip_fanout_limit_for_divisors;
            params.verbose                        = verbose;
            params.use_dont_cares                 = use_dont_cares;
            params.window_size                    = window_size;
            params.preserve_depth                 = preserve_depth;

            mockturtle::aig_resubstitution(ntk, params);

            ntk = mockturtle::cleanup_dangling(ntk);
        },
        "ntk"_a, "max_pis"_a = 8, "max_divisors"_a = 150, "max_inserts"_a = 2, "skip_fanout_limit_for_roots"_a = 1000,
        "skip_fanout_limit_for_divisors"_a = 100, "verbose"_a = false, "use_dont_cares"_a = false, "window_size"_a = 12,
        "preserve_depth"_a = false)

        ;
}

}  // namespace detail

inline void resubstitution(pybind11::module& m)
{
    detail::resubstitution<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_RESUBSTITUTION_HPP
