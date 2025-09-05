//
// Created by marcel on 22.04.24.
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
void write_dot(pybind11::module_& m);

extern template void write_dot<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_dot(pybind11::module_& m);

}  // namespace aigverse
