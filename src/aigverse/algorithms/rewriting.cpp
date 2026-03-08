//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/cut_rewriting.hpp>
#include <mockturtle/algorithms/node_resynthesis/xag_npn.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <optional>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void rewriting(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "aig_cut_rewriting",
        [](Ntk& ntk, const uint32_t cut_size = 4, const uint32_t cut_limit = 8, const bool minimize_truth_table = true,
           const bool allow_zero_gain = false, const bool use_dont_cares = false, const uint32_t min_cand_cut_size = 3,
           const std::optional<uint32_t> min_cand_cut_size_override = std::nullopt, const bool preserve_depth = false,
           const bool verbose = false, const bool very_verbose = false) -> Ntk
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

            return mockturtle::cut_rewriting(ntk, aig_npn_resyn_engine, params);
        },
        nb::arg("ntk"), nb::arg("cut_size") = 4, nb::arg("cut_limit") = 8, nb::arg("minimize_truth_table") = true,
        nb::arg("allow_zero_gain") = false, nb::arg("use_dont_cares") = false, nb::arg("min_cand_cut_size") = 3,
        nb::arg("min_cand_cut_size_override") = std::nullopt, nb::arg("preserve_depth") = false,
        nb::arg("verbose") = false, nb::arg("very_verbose") = false,
        R"pb(Rewrites an AIG network using cut-based NPN resynthesis.

Args:
    ntk: The input logic network.
    cut_size: Maximum cut size used during cut enumeration.
    cut_limit: Maximum number of cuts retained per node.
    minimize_truth_table: Whether to minimize cut truth tables.
    allow_zero_gain: Whether replacements with zero gain are allowed.
    use_dont_cares: Whether to use don't-care information.
    min_cand_cut_size: Minimum candidate cut size.
    min_cand_cut_size_override: Optional override for minimum candidate cut size.
    preserve_depth: Whether replacements must preserve network depth.
    verbose: Whether to print verbose progress output.
    very_verbose: Whether to print highly detailed progress output.

Returns:
    A rewritten network.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void rewriting<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_rewriting(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::rewriting<aigverse::aig>(m);
}

}  // namespace aigverse
