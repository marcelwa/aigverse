//
// Created by marcel on 15.09.24.
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
void refactoring(pybind11::module_& m);

extern template void refactoring<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_refactoring(pybind11::module_& m);

}  // namespace aigverse
