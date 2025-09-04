//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_SIMULATION_HPP
#define AIGVERSE_SIMULATION_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void simulation(pybind11::module_& m);

extern template void simulation<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_simulation(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_SIMULATION_HPP
