//
// Created by Jingren on 20.04.25.
//

#ifndef AIGVERSE_WRITE_VERILOG_HPP
#define AIGVERSE_WRITE_VERILOG_HPP

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
void write_verilog(pybind11::module_& m);

extern template void write_verilog<aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_write_verilog(pybind11::module_& m);

}  // namespace aigverse

#endif  // AIGVERSE_WRITE_VERILOG_HPP
