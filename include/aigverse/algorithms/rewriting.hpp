//
// Created by marcel on 15.09.24.
//

#ifndef AIGVERSE_REWRITING_HPP
#define AIGVERSE_REWRITING_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void rewriting(pybind11::module& m);

extern template void rewriting<aigverse::aig>(pybind11::module& m);

}  // namespace detail

void bind_rewriting(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_REWRITING_HPP
