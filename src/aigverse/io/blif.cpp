#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <lorina/blif.hpp>
#include <lorina/common.hpp>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/blif_reader.hpp>
#include <mockturtle/io/write_blif.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <istream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <type_traits>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace aigverse
{
namespace
{
namespace nb = nanobind;

struct blif_source
{
    std::string              text;
    std::string              model;
    std::vector<std::string> inputs;
    std::vector<std::string> outputs;
};

blif_source validate_blif(std::istream& input)
{
    // Validate flat combinational BLIF before invoking the pinned readers, which assume
    // well-formed covers and continuations. Normalized identifiers contain only safe ASCII
    // so Lorina's unanchored directive regexes cannot match user signal names; interface
    // names are retained separately for restoration after native parsing.
    blif_source                                  source;
    std::unordered_map<std::string, std::string> identifiers;
    std::unordered_set<std::string>              drivers;
    bool                                         ended    = false;
    bool                                         in_cover = false;
    std::size_t                                  fanins   = 0;
    char                                         phase    = '\0';
    std::string                                  continued;

    const auto identifier = [&](const std::string& name)
    {
        // Lorina's unanchored directive regexes can also match inside user signal names.
        return identifiers.try_emplace(name, fmt::format("s{}", identifiers.size())).first->second;
    };
    const auto finish_cover = [&]
    {
        if (in_cover && phase == '\0')
        {
            // mockturtle requires a row for nonconstant nodes, including empty (constant-0) covers.
            source.text += fanins == 0 ? "0\n" : std::string(fanins, '-') + " 0\n";
        }
        in_cover = false;
    };

    std::string line;
    while (std::getline(input, line))
    {
        const auto comment = line.find('#');
        if (comment != std::string::npos)
        {
            line.erase(comment);
        }
        const auto last = line.find_last_not_of(" \t\r");
        if (last == std::string::npos)
        {
            line.clear();
            if (continued.empty())
            {
                continue;
            }
        }
        else
        {
            line.erase(last + 1);
            if (line.back() == '\\')
            {
                line.pop_back();
                continued += line + ' ';
                continue;
            }
        }
        line.insert(0, continued);
        continued.clear();
        std::istringstream       words(line);
        std::vector<std::string> tokens;
        for (std::string word; words >> word;)
        {
            tokens.push_back(word);
        }
        if (tokens.empty())
        {
            continue;
        }
        if (ended)
        {
            throw std::runtime_error("BLIF must contain a single model ending at .end");
        }

        const auto& directive = tokens.front();
        if (directive.front() != '.')
        {
            const auto& value = tokens.back();
            const bool  valid_grammar =
                in_cover && tokens.size() == (fanins == 0 ? 1U : 2U) && (value == "0" || value == "1");
            const bool valid_phase   = phase == '\0' || (valid_grammar && fanins != 0 && phase == value.front());
            const bool valid_pattern = fanins == 0 || (tokens.front().size() == fanins &&
                                                       tokens.front().find_first_not_of("01-") == std::string::npos);
            if (!valid_grammar || !valid_phase || !valid_pattern)
            {
                throw std::runtime_error("Invalid BLIF truth-table cover");
            }
            phase = value.front();
            source.text += fanins == 0 ? value + '\n' : tokens.front() + ' ' + value + '\n';
            continue;
        }

        finish_cover();
        if (directive == ".model")
        {
            if (!source.model.empty() || tokens.size() != 2)
            {
                throw std::runtime_error("BLIF requires one .model name");
            }
            source.model = tokens.at(1);
            source.text += ".model top\n";
        }
        else if (source.model.empty())
        {
            throw std::runtime_error("BLIF must start with .model");
        }
        else if (directive == ".inputs" || directive == ".outputs")
        {
            if (tokens.size() == 1)
            {
                continue;
            }
            source.text += directive;
            for (std::size_t i = 1; i < tokens.size(); ++i)
            {
                const auto& name = tokens.at(i);
                if (directive == ".inputs")
                {
                    if (!drivers.insert(name).second)
                    {
                        throw std::runtime_error("Duplicate BLIF signal driver");
                    }
                    source.inputs.push_back(name);
                }
                else
                {
                    source.outputs.push_back(name);
                }
                source.text += ' ' + identifier(name);
            }
            source.text += '\n';
        }
        else if (directive == ".names")
        {
            if (tokens.size() < 2 || tokens.size() - 2 > klut::max_fanin_size)
            {
                throw std::runtime_error("BLIF .names requires one output and at most 32 fanins");
            }
            if (!drivers.insert(tokens.back()).second)
            {
                throw std::runtime_error("Duplicate BLIF signal driver");
            }
            source.text += ".names";
            for (std::size_t i = 1; i < tokens.size(); ++i)
            {
                source.text += ' ' + identifier(tokens.at(i));
            }
            source.text += '\n';
            in_cover = true;
            fanins   = tokens.size() - 2;
            phase    = '\0';
        }
        else if (directive == ".end" && tokens.size() == 1)
        {
            ended = true;
            source.text += ".end\n";
        }
        else
        {
            throw std::runtime_error("Unsupported BLIF directive: " + directive +
                                     "; only flat combinational .names models are supported");
        }
    }
    if (input.bad() || !continued.empty() || !ended)
    {
        throw std::runtime_error("Incomplete BLIF file");
    }
    for (const auto& name : source.outputs)
    {
        if (drivers.count(name) == 0)
        {
            throw std::runtime_error("BLIF output has no driver: " + name);
        }
    }
    return source;
}

named_klut read_blif(const std::filesystem::path& filename)
{
    std::ifstream input(filename);
    if (!input)
    {
        throw std::runtime_error("Error opening BLIF file");
    }
    // Normalized text has no blank lines/backslashes and ends with a newline, as pinned Lorina requires.
    const auto                source = validate_blif(input);
    std::istringstream        normalized(source.text);
    lorina::text_diagnostics  consumer;
    lorina::diagnostic_engine diag{&consumer};
    named_klut                ntk;
    const auto                result = lorina::read_blif(normalized, mockturtle::blif_reader<named_klut>(ntk), &diag);
    if (result != lorina::return_code::success)
    {
        throw std::runtime_error("Error reading BLIF file: missing drivers or cyclic logic");
    }
    ntk.set_network_name(source.model);
    ntk.foreach_pi([&](const auto n, const auto index) { ntk.set_name(n, source.inputs.at(index)); });
    ntk.foreach_po([&](const auto, const auto index) { ntk.set_output_name(index, source.outputs.at(index)); });
    return ntk;
}

void check_name(const std::string& name)
{
    if (name.empty() || name.find_first_of("#\\") != std::string::npos)
    {
        throw nb::value_error("BLIF interface names must be nonempty tokens without # or backslash");
    }
    for (const char c : name)
    {
        const auto value = static_cast<unsigned char>(c);
        if (value <= 0x20 || value == 0x7f)
        {
            throw nb::value_error("BLIF interface names cannot contain whitespace or control characters");
        }
    }
}

template <typename Ntk>
void write_blif(const Ntk& ntk, const std::filesystem::path& filename)
{
    // Only interface names are serialized; generated internal names avoid all interface collisions.
    named_klut                                output(static_cast<const klut&>(ntk));
    std::unordered_map<std::string, uint64_t> drivers{{"new_n0", 0}, {"new_n1", 1}};
    if constexpr (std::is_same_v<Ntk, named_klut>)
    {
        const auto define = [&](const std::string& name, const uint64_t signal)
        {
            check_name(name);
            const auto [it, inserted] = drivers.emplace(name, signal);
            if (!inserted && it->second != signal)
            {
                const auto message = fmt::format("BLIF interface name '{}' has conflicting drivers", name);
                throw nb::value_error(message.c_str());
            }
        };
        ntk.foreach_pi(
            [&](const auto n)
            {
                if (ntk.has_name(n))
                {
                    const auto name = ntk.get_name(n);
                    define(name, n);
                    output.set_name(n, name);
                }
            });
        ntk.foreach_po(
            [&](const auto f, const auto index)
            {
                if (ntk.has_output_name(index))
                {
                    const auto name = ntk.get_output_name(index);
                    define(name, f);
                    output.set_output_name(index, name);
                }
            });
    }
    const auto fresh_name = [&](std::string name, const uint64_t signal)
    {
        while (drivers.count(name) != 0)
        {
            name += '_';
        }
        drivers.emplace(name, signal);
        return name;
    };
    ntk.foreach_pi(
        [&](const auto n)
        {
            if (!output.has_name(n))
            {
                output.set_name(n, fresh_name(fmt::format("pi{}", n), n));
            }
        });
    ntk.foreach_po(
        [&](const auto f, const auto index)
        {
            if (!output.has_output_name(index))
            {
                output.set_output_name(index, fresh_name(fmt::format("po{}", index), f));
            }
        });
    ntk.foreach_gate([&](const auto n) { output.set_name(n, fresh_name(fmt::format("new_n{}", n), n)); });
    std::ofstream stream(filename);
    if (!stream)
    {
        throw std::runtime_error("Error opening BLIF output file");
    }
    mockturtle::write_blif(output, stream);
    stream.close();
    if (!stream)
    {
        throw std::runtime_error("Error writing BLIF file");
    }
}

template <typename Ntk>
void bind_write_blif(nb::module_& m)
{
    // topo_view mutates shared traversal flags, so writers retain the GIL.
    m.def("write_blif", &write_blif<Ntk>, nb::arg("ntk"), nb::arg("filename"),
          R"pb(Writes a combinational k-LUT network as BLIF.

Very deep chains can overflow the native stack and terminate the process.
The limit depends on the platform and thread stack.

Args:
    ntk: Network to serialize. NamedKlut preserves PI/PO names and order; internal names are regenerated.
    filename: Destination path.

Raises:
    ValueError: If interface names are invalid or assign one name to different drivers.
    RuntimeError: If the destination cannot be opened or written.)pb");
}
}  // namespace

void bind_blif(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    m.def("read_blif_into_klut", &read_blif, nb::arg("filename"),
          R"pb(Reads a flat combinational BLIF model into a NamedKlut.

Args:
    filename: Source path. Only .model, .inputs, .outputs, .names, and .end are supported.

Returns:
    The parsed network with primary-input and primary-output names and order preserved.

Raises:
    RuntimeError: If the file is malformed, has missing drivers, or uses unsupported
        directives such as latches or hierarchy.)pb",
          nb::call_guard<nb::gil_scoped_release>());
    // Named networks must precede the base overload or nanobind discards their interface names.
    bind_write_blif<named_klut>(m);
    bind_write_blif<klut>(m);
}
}  // namespace aigverse
