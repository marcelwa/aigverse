//
// Created by Jingren on 06.05.25.
//

#pragma once

#include "aigverse/types.hpp"

#include <string>

namespace pybind11
{
class module_;
}

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_pla(pybind11::module_& m, const std::string& network_name);

extern template void read_pla<aigverse::aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_pla(pybind11::module_& m);

}  // namespace aigverse
