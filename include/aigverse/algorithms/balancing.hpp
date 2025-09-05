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
void balancing(pybind11::module_& m);

extern template void balancing<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_balancing(pybind11::module_& m);

}  // namespace aigverse
