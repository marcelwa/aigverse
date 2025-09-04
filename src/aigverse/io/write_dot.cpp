//
// Created by marcel on 03.09.25.
//

#include "aigverse/io/write_dot.hpp"

#include <mockturtle/io/write_dot.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>

#include <filesystem>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_dot(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "write_dot", [](const Ntk& ntk, const std::filesystem::path& filename)
        { mockturtle::write_dot(ntk, filename.string()); }, "network"_a, "filename"_a);
}

// Explicit instantiation for AIG
template void write_dot<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_dot(pybind11::module_& m)
{
    detail::write_dot<aigverse::aig>(m);
}

}  // namespace aigverse
