//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/cut_rewriting.hpp>
#include <mockturtle/algorithms/node_resynthesis/xag_npn.hpp>
#include <pybind11/cast.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <optional>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void rewriting(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;  // NOLINT(misc-unused-alias-decls)

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
        py::arg("ntk"), py::arg("cut_size") = 4, py::arg("cut_limit") = 8, py::arg("minimize_truth_table") = true,
        py::arg("allow_zero_gain") = false, py::arg("use_dont_cares") = false, py::arg("min_cand_cut_size") = 3,
        py::arg("min_cand_cut_size_override") = std::nullopt, py::arg("preserve_depth") = false,
        py::arg("verbose") = false, py::arg("very_verbose") = false,
        pybind11::call_guard<pybind11::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void rewriting<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_rewriting(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::rewriting<aigverse::aig>(m);
}

}  // namespace aigverse
