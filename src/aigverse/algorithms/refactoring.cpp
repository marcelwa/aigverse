//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include "transform_helpers.hpp"

#include <fmt/format.h>
#include <mockturtle/algorithms/node_resynthesis/sop_factoring.hpp>
#include <mockturtle/algorithms/refactoring.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <exception>
#include <optional>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void refactoring(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "sop_refactoring",
        [](Ntk& ntk, const uint32_t max_pis = 6, const bool allow_zero_gain = false,
           const bool use_reconvergence_cut = false, const bool use_dont_cares = false,
           const bool use_quick_factoring = true, const bool try_both_polarities = true,
           const bool consider_inverter_cost = false, const bool verbose = false,
           const bool inplace = false) -> std::optional<Ntk>
        {
            try
            {
                mockturtle::refactoring_params params{};
                params.max_pis               = max_pis;
                params.allow_zero_gain       = allow_zero_gain;
                params.use_reconvergence_cut = use_reconvergence_cut;
                params.use_dont_cares        = use_dont_cares;
                params.verbose               = verbose;

                mockturtle::sop_factoring_params sop_params{};
                sop_params.use_quick_factoring    = use_quick_factoring;
                sop_params.try_both_polarities    = try_both_polarities;
                sop_params.consider_inverter_cost = consider_inverter_cost;
                mockturtle::sop_factoring<Ntk> sop_resyn_engine{sop_params};

                return run_transform(ntk, inplace, [&params, &sop_resyn_engine](Ntk& target)
                                     { mockturtle::refactoring(target, sop_resyn_engine, params); });
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
        nb::arg("ntk"), nb::kw_only(), nb::arg("max_pis") = 6, nb::arg("allow_zero_gain") = false,
        nb::arg("use_reconvergence_cut") = false, nb::arg("use_dont_cares") = false,
        nb::arg("use_quick_factoring") = true, nb::arg("try_both_polarities") = true,
        nb::arg("consider_inverter_cost") = false, nb::arg("verbose") = false, nb::arg("inplace") = false,
        R"pb(Performs SOP-based network refactoring.

Args:
    ntk: The input logic network.
    max_pis: Maximum number of leaves used in local windows.
    allow_zero_gain: Whether substitutions with zero gain are allowed.
    use_reconvergence_cut: Whether to use reconvergence-driven cuts.
    use_dont_cares: Whether to use don't-care information.
    use_quick_factoring: Whether to use the quick SOP factoring heuristic.
    try_both_polarities: Whether both output polarities are explored.
    consider_inverter_cost: Whether inverter cost is included in optimization.
    verbose: Whether to print verbose progress output.
    inplace: Whether to mutate ``ntk`` in place.

Returns:
    The refactored network if ``inplace`` is ``False``. Otherwise ``None``.

Raises:
    RuntimeError: If refactoring fails in the underlying synthesis engine.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void refactoring<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_refactoring(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::refactoring<aigverse::aig>(m);
}

}  // namespace aigverse
