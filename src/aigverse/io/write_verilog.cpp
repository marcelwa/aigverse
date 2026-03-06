//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_verilog.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_verilog(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "write_verilog", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_verilog(ntk, filename.string()); }, nb::arg("ntk"), nb::arg("filename"));
}

// Explicit instantiation for AIG
template void write_verilog<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_write_verilog(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::write_verilog<aigverse::aig>(m);
}

}  // namespace aigverse
