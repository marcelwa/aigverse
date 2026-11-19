#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <lorina/blif.hpp>
#include <lorina/common.hpp>
#include <lorina/diagnostics.hpp>
#include <mockturtle/io/blif_reader.hpp>
#include <mockturtle/io/write_blif.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/filesystem.h>  // NOLINT(misc-include-cleaner)

#include <algorithm>
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

#include <pyerrors.h>

namespace aigverse
{
namespace
{
namespace nb = nanobind;

bool valid_name(const std::string& name)
{
    return !name.empty() && std::none_of(name.begin(), name.end(),
                                         [](const char c)
                                         {
                                             const auto byte = static_cast<unsigned char>(c);
                                             return byte <= 0x20 || byte == 0x7f || c == '#' || c == '\\';
                                         });
}

void check_name_encoding(const std::vector<const std::string*>& names)
{
    if (names.empty())
    {
        return;
    }
    const nb::gil_scoped_acquire acquire;
    for (const auto* name : names)
    {
        try
        {
            static_cast<void>(nb::str(name->data(), name->size()));
        }
        catch (const nb::python_error& error)
        {
            if (!error.matches(PyExc_UnicodeDecodeError))
            {
                throw;
            }
            throw std::runtime_error("Invalid UTF-8 in BLIF name");
        }
    }
}

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
    std::string                                  input_line = ".inputs";
    std::vector<const std::string*>              unicode_names;

    const auto check_input_name = [&](const std::string& name)
    {
        if (!valid_name(name))
        {
            throw std::runtime_error("Invalid BLIF name");
        }
        if (std::any_of(name.begin(), name.end(), [](const char c) { return static_cast<unsigned char>(c) >= 0x80; }))
        {
            unicode_names.push_back(&name);
        }
    };
    const auto identifier = [&](const std::string& name) -> const std::string&
    {
        const auto [it, inserted] = identifiers.try_emplace(name);
        if (inserted)
        {
            // Rehashing does not invalidate references to keys.
            check_input_name(it->first);
            it->second = fmt::format("s{}", identifiers.size());
        }
        return it->second;
    };

    std::string line;
    while (std::getline(input, line))
    {
        const auto comment = line.find('#');
        if (comment != std::string::npos)
        {
            line.erase(comment);
        }
        const auto last = line.find_last_not_of(" \t\r\f\v");
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
        if (directive == ".model")
        {
            if (!source.model.empty() || tokens.size() != 2)
            {
                throw std::runtime_error("BLIF requires one .model name");
            }
            source.model = tokens.at(1);
            check_input_name(source.model);
            continue;
        }
        if (source.model.empty())
        {
            throw std::runtime_error("BLIF must start with .model");
        }
        if (directive == ".names")
        {
            if (tokens.size() < 2 || tokens.size() - 2 > klut::max_fanin_size)
            {
                throw std::runtime_error("BLIF .names requires one output and at most 32 fanins");
            }
        }
        else if (directive == ".end" && tokens.size() == 1)
        {
            ended = true;
        }
        else if (directive == ".latch")
        {
            throw std::runtime_error("Unsupported BLIF directive: " + directive +
                                     "; only flat combinational .names models are supported");
        }

        if (directive == ".inputs")
        {
            for (auto it = tokens.begin() + 1; it != tokens.end(); ++it)
            {
                source.inputs.push_back(*it);
                input_line += ' ';
                input_line += identifier(*it);
            }
            // Keep a cover boundary here, but declare the inputs before Lorina sees any gates.
            source.text += ".inputs\n";
            continue;
        }
        if (directive == ".outputs")
        {
            source.outputs.insert(source.outputs.end(), tokens.begin() + 1, tokens.end());
        }
        const bool has_identifiers = directive == ".outputs" || directive == ".names";
        source.text += directive;
        for (auto it = tokens.begin() + 1; it != tokens.end(); ++it)
        {
            source.text += ' ';
            source.text += has_identifiers ? identifier(*it) : *it;
        }
        source.text += '\n';
    }
    if (input.bad() || !continued.empty() || !ended)
    {
        throw std::runtime_error("Incomplete BLIF file");
    }
    check_name_encoding(unicode_names);
    source.text.insert(0, ".model top\n" + input_line + '\n');
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
    klut                      network;
    const auto result = lorina::read_blif_model(normalized, mockturtle::blif_reader<klut>(network), &diag);
    if (result != lorina::return_code::success)
    {
        throw std::runtime_error("Error reading BLIF file");
    }
    named_klut ntk(network, source.model);
    ntk.foreach_pi([&](const auto n, const auto index) { ntk.set_name(n, source.inputs.at(index)); });
    ntk.foreach_po([&](const auto, const auto index) { ntk.set_output_name(index, source.outputs.at(index)); });
    return ntk;
}

template <typename Ntk>
auto blif_output(const Ntk& ntk)
{
    // topo_view writes shared traversal state, so free-threaded writers need private node storage.
#ifdef NB_FREE_THREADED
    const auto network = static_cast<const klut&>(ntk).clone();
#else
    const auto& network = static_cast<const klut&>(ntk);
#endif
    if constexpr (std::is_same_v<Ntk, named_klut>)
    {
        named_klut                                output(network);
        std::unordered_map<std::string, uint64_t> drivers{{"new_n0", 0}, {"new_n1", 1}};
        const auto                                define = [&](const std::string& name, const uint64_t signal)
        {
            if (!valid_name(name))
            {
                throw nb::value_error("Invalid BLIF interface name");
            }
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
        // Native default names are distinct. Only override names that collide with an explicit name.
        const auto avoid_collision = [&](std::string name, const auto& set_name)
        {
            if (drivers.count(name) != 0)
            {
                name += '_';
                while (drivers.count(name) != 0)
                {
                    name += '_';
                }
                set_name(name);
            }
        };
        ntk.foreach_pi(
            [&](const auto n)
            {
                if (!output.has_name(n))
                {
                    avoid_collision(fmt::format("pi{}", n), [&](const auto& name) { output.set_name(n, name); });
                }
            });
        ntk.foreach_po(
            [&](const auto, const auto index)
            {
                if (!output.has_output_name(index))
                {
                    avoid_collision(fmt::format("po{}", index),
                                    [&](const auto& name) { output.set_output_name(index, name); });
                }
            });
        ntk.foreach_gate(
            [&](const auto n)
            { avoid_collision(fmt::format("new_n{}", n), [&](const auto& name) { output.set_name(n, name); }); });
        return output;
    }
    else
    {
        return network;
    }
}

template <typename Ntk>
void write_blif(const Ntk& ntk, const std::filesystem::path& filename)
{
    const auto    output = blif_output(ntk);
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
