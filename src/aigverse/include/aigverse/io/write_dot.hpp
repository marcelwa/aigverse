//
// Created by marcel on 22.04.24.
//

#ifndef AIGVERSE_WRITE_DOT_HPP
#define AIGVERSE_WRITE_DOT_HPP

#include <mockturtle/io/write_dot.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_dot(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "write_dot", [](const Ntk& ntk, const std::string& filename) { mockturtle::write_dot(ntk, filename); },
        "network"_a, "filename"_a);
}

}  // namespace detail

inline void write_dot(pybind11::module& m)
{
    detail::write_dot<mockturtle::aig_network>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_DOT_HPP
