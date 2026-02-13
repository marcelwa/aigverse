//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_verilog.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>
#include <string>  // NOLINT(misc-include-cleaner)

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_verilog(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    using namespace pybind11::literals;

    m.def(
        "write_verilog", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_verilog(ntk, filename.string()); }, "network"_a,
        "filename"_a);  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void write_verilog<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_verilog(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::write_verilog<aigverse::aig>(m);
}

}  // namespace aigverse
