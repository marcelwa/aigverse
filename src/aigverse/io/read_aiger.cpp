//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/aiger_reader.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <filesystem>
#include <stdexcept>
#include <string>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void read_aiger(pybind11::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

    m.def(
        fmt::format("read_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_aiger_result =
                lorina::read_aiger(filename.string(), mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_aiger_result != lorina::return_code::success)  // NOLINT(misc-include-cleaner)
            {
                throw std::runtime_error("Error reading AIGER file");
            }

            return ntk;
        },
        py::arg("filename"));

    m.def(
        fmt::format("read_ascii_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_ascii_aiger_result =
                lorina::read_ascii_aiger(filename.string(), mockturtle::aiger_reader<Ntk>(ntk), &diag);

            if (read_ascii_aiger_result != lorina::return_code::success)  // NOLINT(misc-include-cleaner)
            {
                throw std::runtime_error("Error reading ASCII AIGER file");
            }

            return ntk;
        },
        py::arg("filename"));
}

// Explicit instantiations for named AIG and sequential AIG
template void read_aiger<aigverse::named_aig>(pybind11::module_& m, const std::string& network_name);
template void read_aiger<aigverse::sequential_aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_aiger(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::read_aiger<aigverse::named_aig>(m, "aig");
    detail::read_aiger<aigverse::sequential_aig>(m, "sequential_aig");
}

}  // namespace aigverse
