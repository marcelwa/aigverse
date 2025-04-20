//
// Created by Jingren on 04.20.25.
//

#ifndef AIGVERSE_READ_PLA_HPP
#define AIGVERSE_READ_PLA_HPP

#include <fmt/format.h>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/pla_reader.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_pla(pybind11::module& m, const std::string& network_name)
{
    using namespace pybind11::literals;

    m.def(
        fmt::format("read_pla_into_{}", network_name).c_str(),
        [](const std::string& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_pla_result = lorina::read_pla(filename, mockturtle::pla_reader<Ntk>(ntk), &diag);

            if (read_pla_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading pla file");
            }

            return ntk;
        },
        "filename"_a);
}

}  // namespace detail

inline void read_pla(pybind11::module& m)
{
    detail::read_pla<aigverse::aig>(m, "aig");
}

}  // namespace aigverse

#endif  // AIGVERSE_READ_PLA_HPP
