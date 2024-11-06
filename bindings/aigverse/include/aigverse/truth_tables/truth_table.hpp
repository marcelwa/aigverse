//
// Created by marcel on 06.11.24.
//

#ifndef AIGVERSE_TRUTH_TABLE_HPP
#define AIGVERSE_TRUTH_TABLE_HPP

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <kitty/bit_operations.hpp>
#include <kitty/dynamic_truth_table.hpp>
#include <kitty/hash.hpp>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <sstream>

namespace aigverse
{

namespace detail
{

inline void truth_tables(pybind11::module& m)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    using dyn_tt = kitty::dynamic_truth_table;

    py::class_<dyn_tt>(m, "TruthTable")
        .def(py::init<>(), "Create an empty TruthTable with 0 variables.")
        .def(py::init<uint32_t>(), "num_vars"_a,
             "Create a TruthTable with 'num_vars' variables with all bits set to 0.")

        // Operators
        .def(py::self == py::self, "other"_a)
        .def(py::self != py::self, "other"_a)
        .def(py::self < py::self, "other"_a)

        // Method bindings
        .def("num_vars", &dyn_tt::num_vars, "Returns the number of variables.")
        .def("num_blocks", &dyn_tt::num_blocks, "Returns the number of blocks.")
        .def("num_bits", &dyn_tt::num_bits, "Returns the number of bits.")

        // Operator= for assigning other truth tables
        .def(
            "__copy__", [](const dyn_tt& self) -> dyn_tt { return self; }, "Returns a shallow copy of the truth table.")
        .def(
            "__deepcopy__", [](const dyn_tt& self, [[maybe_unused]] py::dict&) -> dyn_tt { return self; },
            "Returns a deep copy of the truth table.")
        .def(
            "__assign__", [](dyn_tt& self, const dyn_tt& other) -> dyn_tt { return self = other; }, "other"_a,
            "Assigns the truth table from another compatible truth table.")

        // Hashing
        .def(
            "__hash__", [](const dyn_tt& self) { return kitty::hash<dyn_tt>{}(self); },
            "Returns the hash of the truth table.")

        // Free functions added to the class for convenience
        .def(
            "set_bit", [](dyn_tt& self, const uint64_t index) -> void { kitty::set_bit(self, index); }, "index"_a,
            "Sets the bit at the given index.")
        .def(
            "get_bit", [](const dyn_tt& self, const uint64_t index) -> bool { return kitty::get_bit(self, index); },
            "index"_a, "Returns the bit at the given index.")
        .def(
            "clear_bit", [](dyn_tt& self, const uint64_t index) -> void { kitty::clear_bit(self, index); }, "index"_a,
            "Clears the bit at the given index.")
        .def(
            "flip_bit", [](dyn_tt& self, const uint64_t index) -> void { kitty::flip_bit(self, index); }, "index"_a,
            "Flips the bit at the given index.")
        .def(
            "get_block", [](const dyn_tt& self, const uint64_t block_index) -> uint64_t
            { return kitty::get_block(self, block_index); }, "block_index"_a, "Returns a block of bits vector.")

        .def(
            "create_nth_var",
            [](dyn_tt& self, const uint8_t var_index, const bool complement = false) -> void
            {
                if (var_index >= self.num_vars())
                {
                    throw std::runtime_error("Index of the variable must be smaller than the truth table's number of "
                                             "variables.");
                }

                kitty::create_nth_var(self, var_index, complement);
            },
            "var_index"_a, "complement"_a = false,
            "Constructs projections (single-variable functions). Note that the index of the variable must be smaller "
            "than the truth table's number of variables.")
        .def(
            "create_from_binary_string",
            [](dyn_tt& self, const std::string& binary) -> void
            {
                if (binary.size() != self.num_bits())
                {
                    throw std::runtime_error(
                        "Number of characters in binary string must match the number of bits in the truth table.");
                }

                kitty::create_from_binary_string(self, binary);
            },
            "binary"_a,
            "Constructs truth table from binary string. Note that the first character in the string represents the "
            "most significant bit in the truth table. For example, the 2-input AND function is represented by the "
            "binary string '1000'. The number of characters in 'binary' must match the number of bits in the truth "
            "table.")

        .def(
            "create_from_hex_string",
            [](dyn_tt& self, const std::string& hex) -> void
            {
                if (self.num_vars() < 2)
                {
                    if (hex.size() != 1)
                    {
                        throw std::runtime_error(
                            "Number of characters in hex string must be one fourth the number of bits in "
                            "the truth table.");
                    }
                }
                else if ((hex.size() << 2u) != self.num_bits())
                {
                    throw std::runtime_error(
                        "Number of characters in hex string must be one fourth the number of bits in "
                        "the truth table.");
                }

                kitty::create_from_hex_string(self, hex);
            },
            "hex"_a,
            "Constructs truth table from hexadecimal string. Note that the first character in the string "
            "represents the four most significant bit in the truth table. For example, the 3-input majority "
            "function is represented by the binary string 'E8' or 'e8'. The number of characters in 'hex' "
            "must be one fourth the number of bits in the truth table.")
        .def(
            "create_random", [](dyn_tt& self) -> void { kitty::create_random(self); },
            "Constructs a random truth table.")

        .def("clear", &kitty::clear<dyn_tt>, "Clears all bits.")

        .def("count_ones", &kitty::count_ones<dyn_tt>, "Counts ones in truth table.")
        .def("count_zeroes", &kitty::count_zeros<dyn_tt>, "Counts zeroes in truth table.")

        .def(
            "is_const0", [](const dyn_tt& self) -> bool { return kitty::is_const0(self); },
            "Checks if the truth table is constant 0.")
        .def(
            "is_const1", [](const dyn_tt& self) -> bool { return kitty::is_const0(kitty::unary_not(self)); },
            "Checks if the truth table is constant 1.")

        // Representations
        .def(
            "__repr__",
            [](const dyn_tt& self) -> std::string { return fmt::format("TruthTable <vars={}>", self.num_vars()); },
            "Returns an abstract string representation of the truth table.")
        .def(
            "to_binary",
            [](const dyn_tt& self) -> std::string
            {
                std::stringstream stream{};
                kitty::print_binary(self, stream);

                return stream.str();
            },
            "Returns the truth table as a string in binary representation.")
        .def(
            "to_hex",
            [](const dyn_tt& self) -> std::string
            {
                std::stringstream stream{};
                kitty::print_hex(self, stream);

                return stream.str();
            },
            "Returns the truth table as a string in hexadecimal representation.")

        ;
}

}  // namespace detail

inline void truth_tables(pybind11::module& m)
{
    detail::truth_tables(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_TRUTH_TABLE_HPP
