//
// Created by marcel on 04.09.24.
//

#ifndef AIGVERSE_READ_AIGER_HPP
#define AIGVERSE_READ_AIGER_HPP

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

extern template void read_aiger<aigverse::aig>(pybind11::module_& m, const std::string& network_name);
extern template void read_aiger<aigverse::sequential_aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_aiger(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_READ_AIGER_HPP
