#include "aigverse/types.hpp"

#include "transform_helpers.hpp"

#include <mockturtle/algorithms/klut_to_graph.hpp>
#include <mockturtle/utils/name_utils.hpp>
#include <nanobind/nanobind.h>

namespace aigverse
{
namespace
{
template <typename Ntk, typename Result>
void bind_conversion(nanobind::module_& m)
{
    m.def(
        "convert_klut_to_aig",
        [](const Ntk& ntk) -> Result
        {
            const auto                         snapshot = detail::snapshot_network(ntk);
            const nanobind::gil_scoped_release release{};
            auto                               result = mockturtle::convert_klut_to_graph<Result>(snapshot);
            mockturtle::restore_network_name(snapshot, result);
            return result;
        },
        nanobind::arg("ntk"),
        R"pb(Resynthesizes a k-LUT network into an independent AIG.

Args:
    ntk: The input k-LUT network, which is left unchanged.

Returns:
    An Aig, or NamedAig for NamedKlut, preserving primary input/output order and names.
    Native disjoint-support and Shannon decomposition with NPN resynthesis implement the conversion.)pb");
}
}  // namespace

void bind_klut_conversion(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    bind_conversion<named_klut, named_aig>(m);
    bind_conversion<klut, aig>(m);
}
}  // namespace aigverse
