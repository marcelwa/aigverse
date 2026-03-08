//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_dot.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_dot(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "write_dot", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_dot(ntk, filename.string()); }, nb::arg("ntk"), nb::arg("filename"),
        R"pb(Writes a logic network to a Graphviz DOT file for visualization.

    Args:
        ntk: The network to serialize.
        filename: Destination path for the DOT file.)pb");
}

// Explicit instantiation for AIG
template void write_dot<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_write_dot(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::write_dot<aigverse::aig>(m);
}

}  // namespace aigverse
