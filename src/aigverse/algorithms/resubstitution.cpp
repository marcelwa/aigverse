//
// Created by marcel on 03.09.25.
//

#include "aigverse/algorithms/transform_helpers.hpp"
#include "aigverse/types.hpp"

#include <mockturtle/algorithms/aig_resub.hpp>
#include <mockturtle/algorithms/resubstitution.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <optional>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void resubstitution(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "aig_resubstitution",
        [](Ntk& ntk, const uint32_t max_pis = 8, const uint32_t max_divisors = 150, const uint32_t max_inserts = 2,
           const uint32_t skip_fanout_limit_for_roots = 1000, const uint32_t skip_fanout_limit_for_divisors = 100,
           const bool verbose = false, const bool use_dont_cares = false, const uint32_t window_size = 12,
           const bool preserve_depth = false, const bool inplace = false) -> std::optional<Ntk>
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

            return run_transform(ntk, inplace,
                                 [params](Ntk& target) { mockturtle::aig_resubstitution(target, params); });
        },
        nb::arg("ntk"), nb::kw_only(), nb::arg("max_pis") = 8, nb::arg("max_divisors") = 150,
        nb::arg("max_inserts") = 2, nb::arg("skip_fanout_limit_for_roots") = 1000,
        nb::arg("skip_fanout_limit_for_divisors") = 100, nb::arg("verbose") = false, nb::arg("use_dont_cares") = false,
        nb::arg("window_size") = 12, nb::arg("preserve_depth") = false, nb::arg("inplace") = false,
        R"pb(Performs AIG resubstitution-based optimization.

Args:
    ntk: The input logic network.
    max_pis: Maximum number of leaves in a local window.
    max_divisors: Maximum number of candidate divisors.
    max_inserts: Maximum number of inserted nodes per replacement.
    skip_fanout_limit_for_roots: Fanout threshold to skip root candidates.
    skip_fanout_limit_for_divisors: Fanout threshold to skip divisor candidates.
    verbose: Whether to print verbose progress output.
    use_dont_cares: Whether to use don't-care information.
    window_size: Window size used for don't-care computation.
    preserve_depth: Whether replacements must preserve depth.
    inplace: Whether to mutate ``ntk`` in place.

Returns:
    The optimized network if ``inplace`` is ``False``. Otherwise ``None``.)pb",
        nb::call_guard<nb::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void resubstitution<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_resubstitution(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::resubstitution<aigverse::aig>(m);
}

}  // namespace aigverse
