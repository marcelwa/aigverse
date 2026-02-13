//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/pla_reader.hpp>
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
void read_pla(pybind11::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

    m.def(
        fmt::format("read_pla_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_pla_result = lorina::read_pla(filename.string(), mockturtle::pla_reader<Ntk>(ntk), &diag);

            if (read_pla_result != lorina::return_code::success)  // NOLINT(misc-include-cleaner)
            {
                throw std::runtime_error("Error reading PLA file");
            }

            return ntk;
        },
        py::arg("filename"));  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void read_pla<aigverse::aig>(pybind11::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_pla(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::read_pla<aigverse::aig>(m, "aig");
}

}  // namespace aigverse
