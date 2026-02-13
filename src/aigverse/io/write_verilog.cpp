//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_verilog.hpp>
#include <pybind11/cast.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_verilog(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;  // NOLINT(misc-unused-alias-decls)

    m.def(
        "write_verilog", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_verilog(ntk, filename.string()); }, py::arg("ntk"), py::arg("filename"));
}

// Explicit instantiation for AIG
template void write_verilog<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_verilog(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::write_verilog<aigverse::aig>(m);
}

}  // namespace aigverse
