//
// Created by marcel on 04.09.24.
//

#ifndef AIGVERSE_READ_AIGER_HPP
#define AIGVERSE_READ_AIGER_HPP

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
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
    using namespace pybind11::literals;

    m.def(
        fmt::format("read_aiger_into_{}", network_name).c_str(),
        [](const std::string& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_aiger_result = lorina::read_aiger(filename, mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_aiger_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading AIGER file");
            }

            return ntk;
        },
        "filename"_a);

    m.def(
        fmt::format("read_ascii_aiger_into_{}", network_name).c_str(),
        [](const std::string& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_ascii_aiger_result =
                lorina::read_ascii_aiger(filename, mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_ascii_aiger_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading ASCII AIGER file");
            }

            return ntk;
        },
        "filename"_a);
}

}  // namespace detail

inline void read_aiger(pybind11::module& m)
{
    detail::read_aiger<aigverse::aig>(m, "aig");
    detail::read_aiger<aigverse::sequential_aig>(m, "sequential_aig");
}

}  // namespace aigverse

#endif  // AIGVERSE_READ_AIGER_HPP
