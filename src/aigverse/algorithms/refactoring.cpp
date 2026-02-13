//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/cleanup.hpp>
#include <mockturtle/algorithms/node_resynthesis/sop_factoring.hpp>
#include <mockturtle/algorithms/refactoring.hpp>
#include <pybind11/cast.h>
#include <pybind11/pybind11.h>

#include <cstdint>
#include <exception>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void refactoring(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;  // NOLINT(misc-unused-alias-decls)

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
        py::arg("ntk"), py::arg("max_pis") = 6, py::arg("allow_zero_gain") = false,
        py::arg("use_reconvergence_cut") = false, py::arg("use_dont_cares") = false, py::arg("verbose") = false,
        pybind11::call_guard<pybind11::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void refactoring<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_refactoring(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::refactoring<aigverse::aig>(m);
}

}  // namespace aigverse
