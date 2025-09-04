//
// Created by marcel on 15.09.24.
//

#ifndef AIGVERSE_REFACTORING_HPP
#define AIGVERSE_REFACTORING_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void refactoring(pybind11::module& m);

extern template void refactoring<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void bind_refactoring(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_REFACTORING_HPP
