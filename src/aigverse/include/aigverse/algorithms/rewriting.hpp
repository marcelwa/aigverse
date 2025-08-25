//
// Created by marcel on 15.09.24.
//

#ifndef AIGVERSE_REWRITING_HPP
#define AIGVERSE_REWRITING_HPP

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/cut_rewriting.hpp>
#include <mockturtle/algorithms/node_resynthesis/xag_npn.hpp>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <optional>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void rewriting(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "aig_cut_rewriting",
        [](Ntk& ntk, const uint32_t cut_size = 4, const uint32_t cut_limit = 8, const bool minimize_truth_table = true,
           const bool allow_zero_gain = false, const bool use_dont_cares = false, const uint32_t min_cand_cut_size = 3,
           const std::optional<uint32_t> min_cand_cut_size_override = std::nullopt, const bool preserve_depth = false,
           const bool verbose = false, const bool very_verbose = false) -> void
        {
            mockturtle::cut_rewriting_params params{};
            params.cut_enumeration_ps.cut_size             = cut_size;
            params.cut_enumeration_ps.cut_limit            = cut_limit;
            params.cut_enumeration_ps.minimize_truth_table = minimize_truth_table;
            params.allow_zero_gain                         = allow_zero_gain;
            params.use_dont_cares                          = use_dont_cares;
            params.min_cand_cut_size                       = min_cand_cut_size;
            params.min_cand_cut_size_override              = min_cand_cut_size_override;
            params.preserve_depth                          = preserve_depth;
            params.verbose                                 = verbose;
            params.very_verbose                            = very_verbose;

            const mockturtle::xag_npn_resynthesis<Ntk, aigverse::aig, mockturtle::xag_npn_db_kind::aig_complete>
                aig_npn_resyn_engine{};

            ntk = mockturtle::cut_rewriting(ntk, aig_npn_resyn_engine, params);
        },
        "ntk"_a, "cut_size"_a = 4, "cut_limit"_a = 8, "minimize_truth_table"_a = true, "allow_zero_gain"_a = false,
        "use_dont_cares"_a = false, "min_cand_cut_size"_a = 3, "min_cand_cut_size_override"_a = std::nullopt,
        "preserve_depth"_a = false, "verbose"_a = false, "very_verbose"_a = false)

        ;
}

}  // namespace detail

inline void rewriting(pybind11::module& m)
{
    detail::rewriting<aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_REWRITING_HPP
