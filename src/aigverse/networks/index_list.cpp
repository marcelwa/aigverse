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

#include <algorithm>
#include <cctype>
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
        nb::class_<IndexList>(m, fmt::format("{}IndexList", network_name).c_str())
            .def(nb::init<const uint32_t>(), nb::arg("num_pis") = 0)
            .def(nb::init<const std::vector<uint32_t>&>(), nb::arg("values"))

            .def("raw", &IndexList::raw)

            .def("size", &IndexList::size)
            .def("num_gates", &IndexList::num_gates)
            .def("num_pis", &IndexList::num_pis)
            .def("num_pos", &IndexList::num_pos)

            .def("add_inputs", &IndexList::add_inputs, nb::arg("n") = 1u)
            .def("add_and", &IndexList::add_and, nb::arg("lit0"), nb::arg("lit1"))
            .def("add_xor", &IndexList::add_xor, nb::arg("lit0"), nb::arg("lit1"))
            .def("add_output", &IndexList::add_output, nb::arg("lit"))

            .def("clear", &IndexList::clear)

            .def("gates",
                 [](const IndexList& il)
                 {
                     std::vector<std::tuple<uint32_t, uint32_t>> gates{};
                     gates.reserve(il.num_gates());

                     il.foreach_gate([&gates](const auto& lit0, const auto& lit1) { gates.emplace_back(lit0, lit1); });

                     return gates;
                 })

            .def("pos",
                 [](const IndexList& il)
                 {
                     std::vector<uint32_t> pos{};
                     pos.reserve(il.num_pos());

                     il.foreach_po([&pos](const auto& lit) { pos.push_back(lit); });

                     return pos;
                 })

            .def("__iter__",
                 [](const IndexList& il)
                 {
                     const auto raw = il.raw();
                     nb::list   raw_list;
                     for (const auto& v : raw)
                     {
                         raw_list.append(v);
                     }
                     return nb::iter(raw_list);
                 })
            .def("__getitem__",
                 [](const IndexList& il, const std::size_t i)
                 {
                     const auto& v = il.raw();
                     if (i >= v.size())
                     {
                         throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                     }
                     return v[i];
                 })
            .def("__setitem__",
                 [](IndexList& il, const std::size_t i, const uint32_t value)
                 {
                     auto v = il.raw();
                     if (i >= v.size())
                     {
                         throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                     }
                     v[i] = value;
                     il   = IndexList(v);  // reconstruct the index list with the new vector
                 })

            .def("__len__", [](const IndexList& il) { return il.size(); })

            .def("__repr__", [](const IndexList& il) { return fmt::format("IndexList({})", il); })
            .def("__str__", [](const IndexList& il) { return mockturtle::to_index_list_string(il); })

            ;

        nb::implicitly_convertible<nb::list, IndexList>();

        m.def(
            "to_index_list",
            [](const Ntk& ntk)
            {
                IndexList il{};
                mockturtle::encode(il, ntk);
                return il;
            },
            nb::arg("ntk"), nb::rv_policy::move);  // NOLINT(misc-include-cleaner)

        auto lower_case_network_name = network_name;
        std::transform(lower_case_network_name.begin(), lower_case_network_name.end(), lower_case_network_name.begin(),
                       [](const auto c) { return static_cast<char>(std::tolower(static_cast<unsigned char>(c))); });

        m.def(
            fmt::format("to_{}", lower_case_network_name).c_str(),
            [](const IndexList& il)
            {
                Ntk ntk{};
                mockturtle::decode(ntk, il);
                return ntk;
            },
            nb::arg("il"), nb::rv_policy::move);  // NOLINT(misc-include-cleaner)
    }
}
}  // namespace detail

void bind_ntk_index_list(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::ntk_index_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse
