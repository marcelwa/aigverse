//
// Created by Jingren on 20.04.25.
//

#ifndef AIGVERSE_WRITE_VERILOG_HPP
#define AIGVERSE_WRITE_VERILOG_HPP

#include <mockturtle/io/write_verilog.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

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

}  // namespace detail

inline void write_verilog(pybind11::module& m)
{
    detail::write_verilog<mockturtle::aig_network>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_VERILOG_HPP
