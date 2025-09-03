//
// Created by marcel on 03.09.25.
//

#include "aigverse/io/write_aiger.hpp"

#include <mockturtle/io/write_aiger.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

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

// Explicit instantiation for AIG
template void write_aiger<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void write_aiger(pybind11::module& m)
{
    detail::write_aiger<aigverse::aig>(m);
}

}  // namespace aigverse
