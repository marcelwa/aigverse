//
// Created by marcel on 22.04.24.
//

#ifndef AIGVERSE_WRITE_DOT_HPP
#define AIGVERSE_WRITE_DOT_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void write_dot(pybind11::module& m);

extern template void write_dot<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void write_dot(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_DOT_HPP
