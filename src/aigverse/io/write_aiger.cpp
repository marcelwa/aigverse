//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/io/write_aiger.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>

#include <filesystem>
#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_aiger(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "write_aiger", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_aiger(ntk, filename.string()); }, "network"_a, "filename"_a);
}

// Explicit instantiation for AIG
template void write_aiger<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_aiger(pybind11::module_& m)
{
    detail::write_aiger<aigverse::aig>(m);
}

}  // namespace aigverse
