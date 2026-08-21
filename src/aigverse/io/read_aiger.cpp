//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <lorina/aiger.hpp>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/aiger_reader.hpp>
#include <mockturtle/traits.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <filesystem>
#include <stdexcept>
#include <string>

namespace aigverse
{

namespace detail
{

/**
 * A reader that refuses a latched AIGER file when `Ntk` cannot hold registers.
 *
 * mockturtle flattens such a file into extra primary inputs and outputs, one pair
 * per latch. That is lossless, but it hands back a network whose registers have
 * become free primary inputs -- a different circuit than the file describes, and
 * one that will not equivalence-check against it. A caller who reached for
 * `read_aiger_into_aig` on a sequential design almost certainly wanted the
 * sequential reader, so say so instead of silently reshaping the network.
 *
 * The check runs in `on_header`, before any node is created, so a refused file
 * leaves the network untouched.
 */
template <typename Ntk>
class refuse_latches : public mockturtle::aiger_reader<Ntk>  // NOLINT(misc-use-internal-linkage)
{
  public:
    using mockturtle::aiger_reader<Ntk>::aiger_reader;

    refuse_latches(const refuse_latches&)            = delete;
    refuse_latches(refuse_latches&&)                 = delete;
    refuse_latches& operator=(const refuse_latches&) = delete;
    refuse_latches& operator=(refuse_latches&&)      = delete;

    /**
     * `lorina::aiger_reader` is a polymorphic base with a public non-virtual
     * destructor, and mockturtle's reader inherits that. This one is only ever
     * created as a stack temporary and handed to lorina by const reference, so it
     * is never deleted through a base pointer -- but it does override a virtual
     * function, so declare the destructor virtual rather than leave a polymorphic
     * type without one.
     */
    virtual ~refuse_latches() = default;

    void on_header(uint64_t m, uint64_t i, uint64_t l, uint64_t o, uint64_t a) const override
    {
        if constexpr (!mockturtle::has_create_ro_v<Ntk>)
        {
            if (l > 0)
            {
                throw std::runtime_error(
                    fmt::format("the AIGER file describes a sequential network with {} latch(es), which this "
                                "reader would flatten into {} extra primary input/output pairs; read it with "
                                "read_aiger_into_sequential_aig or read_ascii_aiger_into_sequential_aig "
                                "instead, which preserve the registers",
                                l, l));
            }
        }

        mockturtle::aiger_reader<Ntk>::on_header(m, i, l, o, a);
    }
};

template <typename Ntk>
void read_aiger(nanobind::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;  // NOLINT(misc-unused-alias-decls)

    // Only a network that cannot hold registers refuses a latched file, so only its
    // readers document that. nanobind copies the docstring, so a temporary is safe.
    const std::string latch_clause =
        mockturtle::has_create_ro_v<Ntk> ?
            "." :
            ", or if the file has latches, which this\n        network type cannot represent. Read a "
            "sequential design with `read_aiger_into_sequential_aig`\n        or "
            "`read_ascii_aiger_into_sequential_aig` instead.";

    m.def(
        fmt::format("read_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_aiger_result = lorina::read_aiger(filename.string(), refuse_latches<Ntk>(ntk), &diag);

            if (read_aiger_result != lorina::return_code::success)  // NOLINT(misc-include-cleaner)
            {
                throw std::runtime_error("Error reading AIGER file");
            }

            return ntk;
        },
        nb::arg("filename"),
        fmt::format(R"pb(Reads a binary AIGER file into a logic network.

Args:
    filename: Path to the AIGER file.

Returns:
    The parsed network instance.

Raises:
    RuntimeError: If parsing the AIGER file fails{})pb",
                    latch_clause)
            .c_str());

    m.def(
        fmt::format("read_ascii_aiger_into_{}", network_name).c_str(),
        [](const std::filesystem::path& filename)
        {
            Ntk ntk{};

            lorina::text_diagnostics  consumer{};
            lorina::diagnostic_engine diag{&consumer};

            const auto read_ascii_aiger_result =
                lorina::read_ascii_aiger(filename.string(), refuse_latches<Ntk>(ntk), &diag);

            if (read_ascii_aiger_result != lorina::return_code::success)  // NOLINT(misc-include-cleaner)
            {
                throw std::runtime_error("Error reading ASCII AIGER file");
            }

            return ntk;
        },
        nb::arg("filename"),
        fmt::format(R"pb(Reads an ASCII AIGER file into a logic network.

Args:
    filename: Path to the ASCII AIGER file.

Returns:
    The parsed network instance.

Raises:
    RuntimeError: If parsing the ASCII AIGER file fails{})pb",
                    latch_clause)
            .c_str());
}

// Explicit instantiations for named AIG and sequential AIG
template void read_aiger<aigverse::named_aig>(nanobind::module_& m, const std::string& network_name);
template void read_aiger<aigverse::sequential_aig>(nanobind::module_& m, const std::string& network_name);

}  // namespace detail

void bind_read_aiger(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::read_aiger<aigverse::named_aig>(m, "aig");
    detail::read_aiger<aigverse::sequential_aig>(m, "sequential_aig");
}

}  // namespace aigverse
