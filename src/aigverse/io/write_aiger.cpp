//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_aiger.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_aiger(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "write_aiger", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_aiger(ntk, filename.string()); }, nb::arg("ntk"), nb::arg("filename"),
        R"pb(Writes a logic network to a binary AIGER file.

    Args:
        ntk: The network to serialize.
        filename: Destination path for the AIGER file.)pb");
}

// Explicit instantiation for AIG
template void write_aiger<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_write_aiger(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::write_aiger<aigverse::aig>(m);
}

}  // namespace aigverse
