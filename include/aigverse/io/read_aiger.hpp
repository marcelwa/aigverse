//
// Created by marcel on 04.09.24.
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
void read_aiger(pybind11::module_& m, const std::string& network_name);

extern template void read_aiger<aigverse::named_aig>(pybind11::module_& m, const std::string& network_name);
extern template void read_aiger<aigverse::sequential_aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_aiger(pybind11::module_& m);

}  // namespace aigverse
