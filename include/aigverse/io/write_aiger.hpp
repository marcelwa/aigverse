//
// Created by marcel on 05.09.24.
//

#ifndef AIGVERSE_WRITE_AIGER_HPP
#define AIGVERSE_WRITE_AIGER_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_aiger(pybind11::module& m);

extern template void write_aiger<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void write_aiger(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_AIGER_HPP
