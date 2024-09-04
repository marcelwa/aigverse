//
// Created by marcel on 04.09.24.
//

#ifndef AIGVERSE_READ_AIGER_HPP
#define AIGVERSE_READ_AIGER_HPP

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <mockturtle/io/aiger_reader.hpp>
#include <mockturtle/networks/aig.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_aiger(pybind11::module& m, const std::string& network_name)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    m.def(
        fmt::format("read_aiger_into_{}", network_name).c_str(),
        [](const std::string& filename)
        {
            Ntk ntk{};

            const auto read_verilog_result = lorina::read_aiger(filename, mockturtle::aiger_reader<Ntk>(ntk));

            if (read_verilog_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading AIGER file");
            }

            return ntk;
        },
        "filename"_a);
}

}  // namespace detail

inline void read_aiger(pybind11::module& m)
{
    detail::read_aiger<mockturtle::aig_network>(m, "aig");
}

}  // namespace aigverse

#endif  // AIGVERSE_READ_AIGER_HPP
