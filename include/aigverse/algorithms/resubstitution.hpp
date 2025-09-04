//
// Created by marcel on 09.09.24.
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
void resubstitution(pybind11::module_& m);

extern template void resubstitution<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_resubstitution(pybind11::module_& m);

}  // namespace aigverse
