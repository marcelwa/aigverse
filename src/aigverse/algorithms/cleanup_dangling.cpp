//
// Created by marcel on 06.03.26.
//

#include "aigverse/types.hpp"

#include "transform_helpers.hpp"

#include <mockturtle/algorithms/cleanup.hpp>
#include <nanobind/nanobind.h>

#include <cstdint>
#include <type_traits>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void cleanup(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    // The topo_view writes shared traversal state; retain the GIL or clone when there is no GIL to protect it.
    m.def(
        "cleanup_dangling",
        [](const Ntk& ntk, const bool remove_dangling_pis = false, const bool remove_redundant_pos = false) -> Ntk
        {
            if constexpr (std::is_same_v<typename Ntk::base_type, klut>)
            {
                const auto snapshot = snapshot_network(ntk);
                auto       result   = mockturtle::cleanup_dangling(snapshot, remove_dangling_pis, remove_redundant_pos);
                if constexpr (std::is_same_v<Ntk, named_klut>)
                {
                    if (remove_redundant_pos)
                    {
                        // Native cleanup copies output names by their old indices even when it removes outputs.
                        named_klut renamed(static_cast<const klut&>(result));
                        renamed.set_network_name(result.get_network_name());
                        result.foreach_node(
                            [&](const auto n)
                            {
                                if (result.has_name(n))
                                {
                                    renamed.set_name(n, result.get_name(n));
                                }
                            });
                        uint32_t output_index = 0;
                        snapshot.foreach_po(
                            [&](const auto f, const auto index)
                            {
                                if (!snapshot.is_pi(f) && !snapshot.is_constant(f))
                                {
                                    if (snapshot.has_output_name(index))
                                    {
                                        renamed.set_output_name(output_index, snapshot.get_output_name(index));
                                    }
                                    ++output_index;
                                }
                            });
                        return renamed;
                    }
                }
                return result;
            }
            else
            {
#ifdef NB_FREE_THREADED
                const auto snapshot = ntk.clone();
#else
                const auto& snapshot = ntk;
#endif
                return mockturtle::cleanup_dangling(snapshot, remove_dangling_pis, remove_redundant_pos);
            }
        },
        nb::arg("ntk"), nb::kw_only(), nb::arg("remove_dangling_pis") = false, nb::arg("remove_redundant_pos") = false,
        R"pb(Removes dangling logic (dead nodes) from a network.

Args:
    ntk: The input logic network.
    remove_dangling_pis: Whether to also remove primary inputs with no fanouts in the input network.
    remove_redundant_pos: Whether to remove outputs driven directly by primary inputs or constants.

Returns:
    A cleaned network with dangling structures removed.)pb");
}

template void cleanup<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_cleanup_dangling(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::cleanup<aigverse::aig>(m);
    detail::cleanup<aigverse::named_klut>(m);
    detail::cleanup<aigverse::klut>(m);
}

}  // namespace aigverse
