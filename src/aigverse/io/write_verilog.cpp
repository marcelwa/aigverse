//
// Created by marcel on 03.09.25.
//

#include "aigverse/io/write_verilog.hpp"

#include <mockturtle/io/write_verilog.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_verilog(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "write_verilog", [](const Ntk& ntk, const std::string& filename) { mockturtle::write_verilog(ntk, filename); },
        "network"_a, "filename"_a);
}

// Explicit instantiation for AIG
template void write_verilog<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void write_verilog(pybind11::module& m)
{
    detail::write_verilog<aigverse::aig>(m);
}

}  // namespace aigverse
