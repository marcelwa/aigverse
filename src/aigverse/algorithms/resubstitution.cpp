//
// Created by marcel on 03.09.25.
//

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
void resubstitution(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

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
        py::arg("ntk"), py::arg("max_pis") = 8, py::arg("max_divisors") = 150, py::arg("max_inserts") = 2,
        py::arg("skip_fanout_limit_for_roots") = 1000, py::arg("skip_fanout_limit_for_divisors") = 100,
        py::arg("verbose") = false, py::arg("use_dont_cares") = false, py::arg("window_size") = 12,
        py::arg("preserve_depth") = false, pybind11::call_guard<pybind11::gil_scoped_release>());
}

// Explicit instantiation for AIG
template void resubstitution<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_resubstitution(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::resubstitution<aigverse::aig>(m);
}

}  // namespace aigverse
