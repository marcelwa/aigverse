#ifndef AIGVERSE_ALGORITHMS_BALANCING_HPP
#define AIGVERSE_ALGORITHMS_BALANCING_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void balancing(pybind11::module_& m);

extern template void balancing<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_balancing(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_ALGORITHMS_BALANCING_HPP
