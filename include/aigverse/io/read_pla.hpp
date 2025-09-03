//
// Created by Jingren on 06.05.25.
//

#ifndef AIGVERSE_READ_PLA_HPP
#define AIGVERSE_READ_PLA_HPP

#include "aigverse/types.hpp"

#include <pybind11/pybind11.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_pla(pybind11::module& m, const std::string& network_name);

extern template void read_pla<aigverse::aig>(pybind11::module& m, const std::string& network_name);

}  // namespace detail

void read_pla(pybind11::module& m);

}  // namespace aigverse

#endif  // AIGVERSE_READ_PLA_HPP
