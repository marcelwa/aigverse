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

template <typename Spec, typename Impl>
void equivalence_checking(pybind11::module_& m);

extern template void equivalence_checking<aigverse::aig, aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_equivalence_checking(pybind11::module_& m);

}  // namespace aigverse
