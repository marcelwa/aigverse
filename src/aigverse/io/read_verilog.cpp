//
// Created by marcel on 03.09.25.
//

#include "aigverse/io/read_verilog.hpp"

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
#include <lorina/verilog.hpp>
#include <mockturtle/io/verilog_reader.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_verilog(pybind11::module& m, const std::string& network_name)
{
    using namespace pybind11::literals;

    m.def(
        fmt::format("read_verilog_into_{}", network_name).c_str(),
        [](const std::string& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_verilog_result =
                lorina::read_verilog(filename, mockturtle::verilog_reader<Ntk>(ntk), &diag);

            if (read_verilog_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading Verilog file");
            }

            return ntk;
        },
        "filename"_a);
}

// Explicit instantiation for AIG
template void read_verilog<aigverse::aig>(pybind11::module& m, const std::string& network_name);

}  // namespace detail

void read_verilog(pybind11::module& m)
{
    detail::read_verilog<aigverse::aig>(m, "aig");
}

}  // namespace aigverse
