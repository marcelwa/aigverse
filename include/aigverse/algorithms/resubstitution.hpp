//
// Created by marcel on 09.09.24.
//

#ifndef AIGVERSE_RESUBSTITUTION_HPP
#define AIGVERSE_RESUBSTITUTION_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

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

#endif  // AIGVERSE_RESUBSTITUTION_HPP
