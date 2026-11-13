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
    // Enforce one complete flat model and normalize whitespace before native validation.
    // ASCII identifiers avoid Lorina's locale-sensitive trimming of UTF-8 name bytes.
    blif_source                                  source;
    std::unordered_map<std::string, std::string> identifiers;
    bool                                         ended = false;
    std::string                                  continued;

    const auto identifier = [&](const std::string& name)
    { return identifiers.try_emplace(name, fmt::format("s{}", identifiers.size())).first->second; };

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
            for (const auto& token : tokens)
            {
                for (const char c : token)
                {
                    if (static_cast<unsigned char>(c) >= 0x80)
                    {
                        throw std::runtime_error("BLIF covers require ASCII tokens");
                    }
                }
                source.text += token + ' ';
            }
            source.text.back() = '\n';
            continue;
        }

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
            source.text += directive;
            for (std::size_t i = 1; i < tokens.size(); ++i)
            {
                const auto& name = tokens.at(i);
                if (directive == ".inputs")
                {
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
            source.text += ".names";
            for (std::size_t i = 1; i < tokens.size(); ++i)
            {
                source.text += ' ' + identifier(tokens.at(i));
            }
            source.text += '\n';
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
    return source;
}

named_klut read_blif(const std::filesystem::path& filename)
{
    std::ifstream input(filename);
    if (!input)
    {
        throw std::runtime_error("Error opening BLIF file");
    }
    const auto                source = validate_blif(input);
    std::istringstream        normalized(source.text);
    lorina::text_diagnostics  consumer;
    lorina::diagnostic_engine diag{&consumer};
    named_klut                ntk;
    const auto result = lorina::read_blif_model(normalized, mockturtle::blif_reader<named_klut>(ntk), &diag);
    if (result != lorina::return_code::success)
    {
        throw std::runtime_error("Error reading BLIF file");
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
    // topo_view writes shared traversal state, so free-threaded writers need private node storage.
#ifdef NB_FREE_THREADED
    named_klut output(static_cast<const klut&>(ntk).clone());
#else
    named_klut output(static_cast<const klut&>(ntk));
#endif
    // Only interface names are serialized; generated internal names avoid all interface collisions.
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
    // Normal builds retain the GIL to protect topo_view's shared traversal flags.
    m.def("write_blif", &write_blif<Ntk>, nb::arg("ntk"), nb::arg("filename"),
          R"pb(Writes a combinational k-LUT network as BLIF.

Cover generation and output size can grow exponentially with LUT fanin count.
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
    m.def("read_blif", &read_blif, nb::arg("filename"),
          R"pb(Reads a flat combinational BLIF model into a NamedKlut.

Nonempty covers expand to dense truth tables whose memory grows exponentially with fanin count.

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
