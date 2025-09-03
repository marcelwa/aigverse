//
// Created by marcel on 04.09.24.
//

#ifndef AIGVERSE_LOGIC_NETWORKS_HPP
#define AIGVERSE_LOGIC_NETWORKS_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void bind_network(pybind11::module& m, const std::string& network_name);

extern template void bind_network<aigverse::aig>(pybind11::module& m, const std::string& network_name);
// extern template void network<aigverse::mig>(pybind11::module& m, const std::string& network_name);
// extern template void network<aigverse::xag>(pybind11::module& m, const std::string& network_name);

}  // namespace detail

// Registers logic network bindings
void bind_logic_networks(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_LOGIC_NETWORKS_HPP
