//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include "transform_helpers.hpp"

#include <mockturtle/algorithms/equivalence_checking.hpp>
#include <mockturtle/algorithms/miter.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/optional.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <optional>
#include <stdexcept>
#include <type_traits>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
static void check_cnf_fanins(const Ntk& ntk)
{
    if constexpr (std::is_same_v<typename Ntk::base_type, klut>)
    {
        ntk.foreach_gate(
            [&](const auto n)
            {
                // kitty's CNF cubes need a 32-bit slot for the gate's output literal as well.
                if (ntk.fanin_size(n) >= 32)
                {
                    throw nanobind::value_error("SAT equivalence requires LUT gates with fewer than 32 fanins");
                }
            });
    }
}

template <typename Spec, typename Impl>
void equivalence_checking(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "equivalence_checking",
        [](const Spec& spec, const Impl& impl, const uint32_t conflict_limit = 0,
           const bool functional_reduction = true, const bool verbose = false) -> std::optional<bool>
        {
            constexpr bool uses_klut =
                std::is_same_v<typename Spec::base_type, klut> || std::is_same_v<typename Impl::base_type, klut>;
            if constexpr (uses_klut)
            {
                require_combinational(spec);
                require_combinational(impl);
                check_cnf_fanins(spec);
                check_cnf_fanins(impl);
            }
            // `miter` runs `cleanup_dangling` over both networks, which builds a `topo_view` over each and writes into
            // its storage; run it on clones instead. The clones cost 2.1% of the call at 1k gates. See
            // `transform_helpers.hpp` for the rule.
            const auto                   spec_snapshot = spec.clone();
            const auto                   impl_snapshot = impl.clone();
            const nb::gil_scoped_release release{};

            using miter_ntk  = std::conditional_t<uses_klut, klut, aig>;
            const auto miter = mockturtle::miter<miter_ntk, Spec, Impl>(spec_snapshot, impl_snapshot);

            if (!miter.has_value())
            {
                throw std::runtime_error("miter construction failed due to differing numbers of PIs or POs");
            }

            mockturtle::equivalence_checking_params params{};
            params.conflict_limit = conflict_limit;
            // Random simulation in functional reduction requires at least one primary input.
            params.functional_reduction = functional_reduction && miter->num_pis() > 0;
            params.verbose              = verbose;

            return mockturtle::equivalence_checking(miter.value(), params);
        },
        nb::arg("spec"), nb::arg("impl"), nb::kw_only(), nb::arg("conflict_limit") = 0,
        nb::arg("functional_reduction") = true, nb::arg("verbose") = false,
        R"pb(Checks functional equivalence between a specification and implementation network using SAT solving.

LUT fanin checks include dangling gates. The fewer-than-32-fanin bound is a representation limit,
not a practical resource limit: LUT truth tables and ISOP/CNF construction can require exponential space and time.

Args:
    spec: The specification network.
    impl: The implementation network.
    conflict_limit: SAT conflict limit. A value of ``0`` means no limit.
    functional_reduction: Whether to perform functional reduction of an AIG/AIG miter before checking.
        Native functional reduction is not applied when either input is a Klut.
    verbose: Whether to print verbose progress output.

Returns:
    ``True`` if equivalent, ``False`` if not equivalent, or ``None`` if the
    procedure did not finish before the configured limit.

Raises:
    ValueError: For Aig/Klut or Klut/Klut comparisons, if an input is sequential or any LUT has 32 or more fanins.
    RuntimeError: If miter construction fails due to incompatible interfaces (PI/PO count mismatch).)pb");
}

// Explicit instantiation for AIG
template void equivalence_checking<aigverse::aig, aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_equivalence_checking(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::equivalence_checking<aigverse::aig, aigverse::aig>(m);
    detail::equivalence_checking<aigverse::aig, aigverse::klut>(m);
    detail::equivalence_checking<aigverse::klut, aigverse::aig>(m);
    detail::equivalence_checking<aigverse::klut, aigverse::klut>(m);
}

}  // namespace aigverse
