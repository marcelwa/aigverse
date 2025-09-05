//
// Created by marcel on 03.09.25.
//

#include "aigverse/io/read_aiger.hpp"

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/aiger_reader.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>

#include <filesystem>
#include <stdexcept>
#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_aiger(pybind11::module_& m, const std::string& network_name)
{
    using namespace pybind11::literals;

    m.def(
        fmt::format("read_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_aiger_result =
                lorina::read_aiger(filename.string(), mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_aiger_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading AIGER file");
            }

            return ntk;
        },
        "filename"_a);

    m.def(
        fmt::format("read_ascii_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_ascii_aiger_result =
                lorina::read_ascii_aiger(filename.string(), mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_ascii_aiger_result != lorina::return_code::success)
            {
                throw std::runtime_error("Error reading ASCII AIGER file");
            }

            return ntk;
        },
        "filename"_a);
}

// Explicit instantiations for AIG and sequential AIG
template void read_aiger<aigverse::aig>(pybind11::module_& m, const std::string& network_name);
template void read_aiger<aigverse::sequential_aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_aiger(pybind11::module_& m)
{
    detail::read_aiger<aigverse::aig>(m, "aig");
    detail::read_aiger<aigverse::sequential_aig>(m, "sequential_aig");
}

}  // namespace aigverse
