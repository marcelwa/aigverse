//
// Created by Jingren on 21.04.25.
//

#ifndef AIGVERSE_READ_VERILOG_HPP
#define AIGVERSE_READ_VERILOG_HPP

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
void read_verilog(pybind11::module_& m, const std::string& network_name);

extern template void read_verilog<aigverse::aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_verilog(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_READ_VERILOG_HPP
