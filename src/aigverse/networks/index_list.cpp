//
// Created by marcel on 04.09.25.
//

#include "index_list.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>  // NOLINT(misc-include-cleaner)
#include <mockturtle/utils/index_list.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/tuple.h>   // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>  // NOLINT(misc-include-cleaner)

#include <cstddef>
#include <cstdint>
#include <string>
#include <tuple>
#include <type_traits>
#include <vector>

namespace aigverse
{

namespace detail
{

template <typename Ntk>
void ntk_index_list(nanobind::module_& m, const std::string& network_name)  // NOLINT(misc-use-internal-linkage)
{
    namespace nb = nanobind;

    if constexpr (std::is_same_v<Ntk, aigverse::aig>)
    {
        /**
         * Index list.
         */
        using IndexList = aigverse::aig_index_list;  // NOLINT(readability-identifier-naming)
        nb::class_<IndexList>(m, fmt::format("{}IndexList", network_name).c_str(),
                              R"pb(Represents an index-list encoding of an AIG network.)pb")
            .def(nb::init<const uint32_t>(), nb::arg("num_pis") = 0,
                 R"pb(Creates an empty index list with a given number of primary inputs.

Args:
    num_pis: Number of primary inputs to initialize.)pb")
            .def(nb::init<const std::vector<uint32_t>&>(), nb::arg("values"),
                 R"pb(Creates an index list from raw integer values.

Args:
    values: Raw index-list encoding values.)pb")

            .def("raw", &IndexList::raw,
                 R"pb(Returns the raw integer encoding.

Returns:
    A list of encoded index-list values.)pb")

            .def_prop_ro("size", &IndexList::size, R"pb(Number of raw entries in the encoding.)pb")
            .def_prop_ro("num_gates", &IndexList::num_gates, R"pb(Number of encoded gates.)pb")
            .def_prop_ro("num_pis", &IndexList::num_pis, R"pb(Number of encoded primary inputs.)pb")
            .def_prop_ro("num_pos", &IndexList::num_pos, R"pb(Number of encoded primary outputs.)pb")

            .def("add_inputs", &IndexList::add_inputs, nb::arg("n") = 1u,
                 R"pb(Appends primary inputs to the encoding.

Args:
    n: Number of inputs to append.)pb")
            .def("add_and", &IndexList::add_and, nb::arg("lit0"), nb::arg("lit1"),
                 R"pb(Appends an AND gate to the encoding.

Args:
    lit0: First fanin literal.
    lit1: Second fanin literal.)pb")
            .def("add_xor", &IndexList::add_xor, nb::arg("lit0"), nb::arg("lit1"),
                 R"pb(Appends an XOR gate to the encoding.

Args:
    lit0: First fanin literal.
    lit1: Second fanin literal.)pb")
            .def("add_output", &IndexList::add_output, nb::arg("lit"),
                 R"pb(Appends a primary output literal.

Args:
    lit: Output literal.)pb")

            .def("clear", &IndexList::clear, R"pb(Clears all encoded data.)pb")
            .def(
                "to_aig",
                [](const IndexList& il)
                {
                    Ntk ntk{};
                    mockturtle::decode(ntk, il);
                    return ntk;
                },
                R"pb(Decodes the index list into an AIG network.

Returns:
    A decoded AIG network.)pb",
                nb::rv_policy::move)

            .def(
                "gates",
                [](const IndexList& il)
                {
                    std::vector<std::tuple<uint32_t, uint32_t>> gates{};
                    gates.reserve(il.num_gates());

                    il.foreach_gate([&gates](const auto& lit0, const auto& lit1) { gates.emplace_back(lit0, lit1); });

                    return gates;
                },
                R"pb(Returns encoded gate fanins as literal pairs.

Returns:
    A list of ``(lit0, lit1)`` tuples for each gate.)pb")

            .def(
                "pos",
                [](const IndexList& il)
                {
                    std::vector<uint32_t> pos{};
                    pos.reserve(il.num_pos());

                    il.foreach_po([&pos](const auto& lit) { pos.push_back(lit); });

                    return pos;
                },
                R"pb(Returns encoded primary output literals.

Returns:
    A list of output literals.)pb")

            .def(
                "__iter__",
                [](const IndexList& il)
                {
                    const auto raw = il.raw();
                    nb::list   raw_list;
                    for (const auto& v : raw)
                    {
                        raw_list.append(v);
                    }
                    return nb::iter(raw_list);
                },
                R"pb(Returns an iterator over the raw encoding values.)pb",
                nb::sig("def __iter__(self) -> Iterator[int]"))
            .def(
                "__getitem__",
                [](const IndexList& il, const std::size_t i)
                {
                    const auto& v = il.raw();
                    if (i >= v.size())
                    {
                        throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                    }
                    return v[i];
                },
                nb::arg("index"),
                R"pb(Returns one raw encoding value by index.

Args:
    index: Position in the raw encoding.

Returns:
    The raw value at ``index``.

Raises:
    IndexError: If ``index`` is out of range.)pb")
            .def(
                "__setitem__",
                [](IndexList& il, const std::size_t i, const uint32_t value)
                {
                    auto v = il.raw();
                    if (i >= v.size())
                    {
                        throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                    }
                    v[i] = value;
                    il   = IndexList(v);  // reconstruct the index list with the new vector
                },
                nb::arg("index"), nb::arg("value"),
                R"pb(Sets one raw encoding value by index.

    Args:
        index: Position in the raw encoding.
        value: Replacement raw value.

    Raises:
        IndexError: If ``index`` is out of range.)pb")
            .def(
                "__len__", [](const IndexList& il) { return il.size(); },
                R"pb(Returns the number of raw encoding entries.)pb")
            .def(
                "__repr__", [](const IndexList& il) { return fmt::format("IndexList({})", il); },
                R"pb(Returns a developer-friendly string representation.)pb")
            .def(
                "__str__", [](const IndexList& il) { return mockturtle::to_index_list_string(il); },
                R"pb(Returns a textual index-list dump.)pb")

            ;

        nb::implicitly_convertible<nb::list, IndexList>();
    }
}
}  // namespace detail

void bind_ntk_index_list(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::ntk_index_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
