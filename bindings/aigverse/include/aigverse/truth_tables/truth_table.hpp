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

/**
 * @brief An iterator for traversing the bits of a truth table.
 *
 * This class provides a standard C++ iterator interface for iterating over the individual bits of a
 * `aigverse::truth_table`. It is used to implement Python's list-like iteration protocol (`__iter__`).
 */
class truth_table_bit_iterator
{
  public:
    /**
     * @brief Constructs a bit iterator.
     *
     * @param tt The truth table to iterate over.
     * @param index The starting index of the iterator.
     */
    truth_table_bit_iterator(const aigverse::truth_table& tt, const uint64_t index) : tt{&tt}, index{index} {}

    /**
     * @brief Dereferences the iterator to get the current bit.
     *
     * @return The boolean value of the bit at the current position.
     */
    bool operator*() const
    {
        return static_cast<bool>(kitty::get_bit(*tt, index));
    }

    /**
     * @brief Increments the iterator to the next bit.
     *
     * @return A reference to the incremented iterator.
     */
    truth_table_bit_iterator& operator++()
    {
        ++index;
        return *this;
    }

    /**
     * @brief Compares two iterators for equality.
     *
     * @param other The other iterator to compare with.
     * @return `true` if both iterators point to the same bit, `false` otherwise.
     */
    bool operator==(const truth_table_bit_iterator& other) const
    {
        return index == other.index;
    }

    /**
     * @brief Compares two iterators for inequality.
     *
     * @param other The other iterator to compare with.
     * @return `true` if the iterators point to different bits, `false` otherwise.
     */
    bool operator!=(const truth_table_bit_iterator& other) const
    {
        return !(*this == other);
    }

  private:
    /**
     * @brief A pointer to the truth table being iterated over.
     */
    const aigverse::truth_table* tt;
    /**
     * @brief The current bit index.
     */
    uint64_t index;
};

inline void truth_tables(pybind11::module& m)
{
    namespace py = pybind11;
    using namespace pybind11::literals;

    py::class_<aigverse::truth_table>(m, "TruthTable")
        .def(py::init<>(), "Create an empty TruthTable with 0 variables.")
        .def(py::init<uint32_t>(), "num_vars"_a,
             "Create a TruthTable with 'num_vars' variables with all bits set to 0.")

        // Operators
        .def(py::self == py::self, "other"_a)
        .def(py::self != py::self, "other"_a)
        .def(py::self < py::self, "other"_a)
        .def(py::self & py::self, "other"_a)
        .def(py::self | py::self, "other"_a)
        .def(py::self ^ py::self, "other"_a)
        .def(~py::self)

        // Python list-like convenience functions
        .def("__len__",
             [](const aigverse::truth_table& self) -> uint64_t
             {
                 if (self._bits.empty())
                 {
                     return 0;
                 }

                 return self.num_bits();
             })
        .def(
            "__getitem__",
            [](const aigverse::truth_table& self, int64_t index) -> bool
            {
                if (index < 0)
                {
                    index += static_cast<int64_t>(self.num_bits());
                }
                if (index < 0 || static_cast<uint64_t>(index) >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                return kitty::get_bit(self, static_cast<uint64_t>(index));
            },
            "index"_a)
        .def(
            "__setitem__",
            [](aigverse::truth_table& self, int64_t index, bool value)
            {
                if (index < 0)
                {
                    index += static_cast<int64_t>(self.num_bits());
                }
                if (index < 0 || static_cast<uint64_t>(index) >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                if (value)
                {
                    kitty::set_bit(self, static_cast<uint64_t>(index));
                }
                else
                {
                    kitty::clear_bit(self, static_cast<uint64_t>(index));
                }
            },
            "index"_a, "value"_a)
        .def(
            "__iter__",
            [](const aigverse::truth_table& self)
            {
                return py::make_iterator(truth_table_bit_iterator(self, 0),
                                         truth_table_bit_iterator(self, self.num_bits()));
            },
            py::keep_alive<0, 1>())

        // Method bindings
        .def("num_vars", &aigverse::truth_table::num_vars, "Returns the number of variables.")
        .def("num_blocks", &aigverse::truth_table::num_blocks, "Returns the number of blocks.")
        .def("num_bits", &aigverse::truth_table::num_bits, "Returns the number of bits.")

        // Operator= for assigning other truth tables
        .def(
            "__copy__", [](const aigverse::truth_table& self) -> aigverse::truth_table { return self; },
            "Returns a shallow copy of the truth table.")
        .def(
            "__deepcopy__", [](const aigverse::truth_table& self, [[maybe_unused]] py::dict&) -> aigverse::truth_table
            { return self; }, "Returns a deep copy of the truth table.")
        .def(
            "__assign__", [](aigverse::truth_table& self, const aigverse::truth_table& other) -> aigverse::truth_table
            { return self = other; }, "other"_a, "Assigns the truth table from another compatible truth table.")

        // Hashing
        .def(
            "__hash__", [](const aigverse::truth_table& self) { return kitty::hash<aigverse::truth_table>{}(self); },
            "Returns the hash of the truth table.")

        // Free functions added to the class for convenience
        .def(
            "set_bit", [](aigverse::truth_table& self, const uint64_t index) -> void { kitty::set_bit(self, index); },
            "index"_a, "Sets the bit at the given index.")
        .def(
            "get_bit", [](const aigverse::truth_table& self, const uint64_t index) -> bool
            { return kitty::get_bit(self, index); }, "index"_a, "Returns the bit at the given index.")
        .def(
            "clear_bit", [](aigverse::truth_table& self, const uint64_t index) -> void
            { kitty::clear_bit(self, index); }, "index"_a, "Clears the bit at the given index.")
        .def(
            "flip_bit", [](aigverse::truth_table& self, const uint64_t index) -> void { kitty::flip_bit(self, index); },
            "index"_a, "Flips the bit at the given index.")
        .def(
            "get_block", [](const aigverse::truth_table& self, const uint64_t block_index) -> uint64_t
            { return kitty::get_block(self, block_index); }, "block_index"_a, "Returns a block of bits vector.")

        .def(
            "create_nth_var",
            [](aigverse::truth_table& self, const uint8_t var_index, const bool complement = false) -> void
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
            [](aigverse::truth_table& self, const std::string& binary) -> void
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
            [](aigverse::truth_table& self, const std::string& hexadecimal) -> void
            {
                if (self.num_vars() < 2)
                {
                    if (hexadecimal.size() != 1)
                    {
                        throw std::runtime_error(
                            "Number of characters in hex string must be one fourth the number of bits in "
                            "the truth table.");
                    }
                }
                else if ((hexadecimal.size() << 2u) != self.num_bits())
                {
                    throw std::runtime_error(
                        "Number of characters in hex string must be one fourth the number of bits in "
                        "the truth table.");
                }

                kitty::create_from_hex_string(self, hexadecimal);
            },
            "hexadecimal"_a,
            "Constructs truth table from hexadecimal string. Note that the first character in the string "
            "represents the four most significant bit in the truth table. For example, the 3-input majority "
            "function is represented by the binary string 'E8' or 'e8'. The number of characters in 'hex' "
            "must be one fourth the number of bits in the truth table.")
        .def(
            "create_random", [](aigverse::truth_table& self) -> void { kitty::create_random(self); },
            "Constructs a random truth table.")
        .def(
            "create_majority", [](aigverse::truth_table& self) -> void { kitty::create_majority(self); },
            "Constructs a MAJ truth table.")

        .def("clear", &kitty::clear<aigverse::truth_table>, "Clears all bits.")

        .def("count_ones", &kitty::count_ones<aigverse::truth_table>, "Counts ones in truth table.")
        .def("count_zeroes", &kitty::count_zeros<aigverse::truth_table>, "Counts zeroes in truth table.")

        .def(
            "is_const0", [](const aigverse::truth_table& self) -> bool { return kitty::is_const0(self); },
            "Checks if the truth table is constant 0.")
        .def(
            "is_const1", [](const aigverse::truth_table& self) -> bool
            { return kitty::is_const0(kitty::unary_not(self)); }, "Checks if the truth table is constant 1.")

        // Representations
        .def(
            "__repr__", [](const aigverse::truth_table& self) -> std::string
            { return fmt::format("TruthTable <vars={}>", self.num_vars()); },
            "Returns an abstract string representation of the truth table.")
        .def(
            "to_binary",
            [](const aigverse::truth_table& self) -> std::string
            {
                std::stringstream stream{};
                kitty::print_binary(self, stream);

                return stream.str();
            },
            "Returns the truth table as a string in binary representation.")
        .def(
            "to_hex",
            [](const aigverse::truth_table& self) -> std::string
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
