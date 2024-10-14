//
// Created by marcel on 05.09.24.
//

#ifndef AIGVERSE_WRITE_AIGER_HPP
#define AIGVERSE_WRITE_AIGER_HPP

#include <fmt/format.h>
#include <mockturtle/io/write_aiger.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_aiger(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "write_aiger", [](const Ntk& ntk, const std::string& filename) { mockturtle::write_aiger(ntk, filename); },
        "network"_a, "filename"_a);
}

}  // namespace detail

inline void write_aiger(pybind11::module& m)
{
    detail::write_aiger<mockturtle::aig_network>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_AIGER_HPP
