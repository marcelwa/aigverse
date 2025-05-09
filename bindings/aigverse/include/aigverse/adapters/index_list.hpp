//
// Created by marcel on 02.05.25.
//

#ifndef AIGVERSE_INDEX_LIST_HPP
#define AIGVERSE_INDEX_LIST_HPP

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <fmt/ranges.h>
#include <mockturtle/utils/index_list.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

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
void ntk_index_list(pybind11::module& m, const std::string& network_name)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    if constexpr (std::is_same_v<Ntk, aigverse::aig>)
    {
        /**
         * Index list.
         */
        using IndexList = mockturtle::xag_index_list<true>;
        py::class_<IndexList>(m, fmt::format("{}IndexList", network_name).c_str())
            .def(py::init<const uint32_t>(), "num_pis"_a = 0)
            .def(py::init<const std::vector<uint32_t>&>(), "values"_a)

            .def("raw", &IndexList::raw)

            .def("size", &IndexList::size)
            .def("num_gates", &IndexList::num_gates)
            .def("num_pis", &IndexList::num_pis)
            .def("num_pos", &IndexList::num_pos)

            .def("add_inputs", &IndexList::add_inputs, "n"_a = 1u)
            .def("add_and", &IndexList::add_and, "lit0"_a, "lit1"_a)
            .def("add_xor", &IndexList::add_xor, "lit0"_a, "lit1"_a)
            .def("add_output", &IndexList::add_output, "lit"_a)

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
                     const auto     raw      = il.raw();
                     const py::list raw_list = py::cast(raw);
                     return py::iter(raw_list);
                 })
            .def("__getitem__",
                 [](const IndexList& il, const std::size_t i)
                 {
                     const auto& v = il.raw();
                     if (i >= v.size())
                     {
                         throw py::index_error();
                     }
                     return v[i];
                 })
            .def("__setitem__",
                 [](IndexList& il, const std::size_t i, const uint32_t value)
                 {
                     auto v = il.raw();
                     if (i >= v.size())
                     {
                         throw py::index_error();
                     }
                     v[i] = value;
                     il   = IndexList(v);  // reconstruct the index list with the new vector
                 })

            .def("__len__", [](const IndexList& il) { return il.size(); })

            .def("__repr__", [](const IndexList& il) { return fmt::format("IndexList({})", il); })
            .def("__str__", [](const IndexList& il) { return mockturtle::to_index_list_string(il); })

            ;

        py::implicitly_convertible<py::list, IndexList>();

        m.def(
            "to_index_list",
            [](const Ntk& ntk)
            {
                IndexList il{};
                mockturtle::encode(il, ntk);
                return il;
            },
            "ntk"_a);

        auto lower_case_network_name = network_name;
        std::transform(lower_case_network_name.begin(), lower_case_network_name.end(), lower_case_network_name.begin(),
                       [](const auto c) { return std::tolower(c); });

        m.def(
            fmt::format("to_{}", lower_case_network_name).c_str(),
            [](const IndexList& il)
            {
                Ntk ntk{};
                mockturtle::decode(ntk, il);
                return ntk;
            },
            "il"_a);
    }
}

}  // namespace detail

inline void to_index_list(pybind11::module& m)
{
    detail::ntk_index_list<aigverse::aig>(m, "Aig");
}

}  // namespace aigverse

namespace fmt
{

// make index_list compatible with fmt::format
template <>
struct formatter<mockturtle::xag_index_list<true>>
{
    template <typename ParseContext>
    constexpr auto parse(ParseContext& ctx)
    {
        return ctx.begin();
    }

    template <typename FormatContext>
    auto format(const mockturtle::xag_index_list<true>& il, FormatContext& ctx) const
    {
        std::vector<std::tuple<uint32_t, uint32_t>> gates{};
        gates.reserve(il.num_gates());

        il.foreach_gate([&gates](const auto& lit0, const auto& lit1) { gates.emplace_back(lit0, lit1); });

        std::vector<uint32_t> outputs{};
        outputs.reserve(il.num_pos());

        il.foreach_po([&outputs](const auto& lit) { outputs.push_back(lit); });

        return format_to(ctx.out(), "#PIs: {}, #POs: {}, #Gates: {}, Gates: {}, POs: {}", il.num_pis(), il.num_pos(),
                         il.num_gates(), gates, outputs);
    }
};

}  // namespace fmt

#endif  // AIGVERSE_INDEX_LIST_HPP
