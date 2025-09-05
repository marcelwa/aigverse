//
// Created by marcel on 06.11.24.
//

#pragma once

#include "aigverse/types.hpp"

namespace pybind11
{
class module_;
}

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
