//
// Created by marcel on 09.09.24.
//

#ifndef AIGVERSE_EQUIVALENCE_CHECKING_HPP
#define AIGVERSE_EQUIVALENCE_CHECKING_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

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

#endif  // AIGVERSE_EQUIVALENCE_CHECKING_HPP
