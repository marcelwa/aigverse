//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <kitty/bit_operations.hpp>
#include <kitty/constructors.hpp>
#include <kitty/dynamic_truth_table.hpp>
#include <kitty/hash.hpp>
#include <kitty/operations.hpp>
#include <kitty/print.hpp>
#include <nanobind/make_iterator.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/nanobind.h>
#include <nanobind/operators.h>   // NOLINT(misc-include-cleaner)
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)
#include <nanobind/stl/vector.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace aigverse
{

namespace detail
{

/**
 * An iterator helper class to iterate over the bits of a truth table.
 */
class truth_table_bit_iterator
{
  public:
    /**
     * Default constructor.
     *
     * @param table The truth table to iterate over.
     * @param i Start index of the iteration.
     */
    truth_table_bit_iterator(const aigverse::truth_table& table, const uint64_t i) : tt{&table}, index{i} {}
    /**
     * Dereference operator to obtain the current bit in the truth table.
     *
     * @return The current bit in the truth table at the current index.
     */
    bool operator*() const
    {
        return static_cast<bool>(kitty::get_bit(*tt, index));
    }
    /**
     * Pre-increment operator to move to the next bit in the truth table.
     *
     * @return Reference to the updated iterator.
     */
    truth_table_bit_iterator& operator++()
    {
        ++index;
        return *this;
    }
    /**
     * Equality operator to compare two iterators.
     *
     * @param other The other iterator to compare with.
     * @return `true` if both iterators point to the same index of the same truth table, `false` otherwise.
     */
    bool operator==(const truth_table_bit_iterator& other) const
    {
        return tt == other.tt && index == other.index;
    }
    /**
     * Inequality operator to compare two iterators.
     *
     * @param other The other iterator to compare with.
     * @return `true` if both iterators point to different indices, `false` otherwise.
     */
    bool operator!=(const truth_table_bit_iterator& other) const
    {
        return !(*this == other);
    }

  private:
    /**
     * Pointer to the truth table being iterated over.
     */
    const aigverse::truth_table* tt;
    /**
     * Current index in the truth table.
     */
    uint64_t index;
};

}  // namespace detail

void bind_truth_table(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{

    namespace nb = nanobind;

    nb::class_<aigverse::truth_table>(m, "TruthTable", R"pb(Represents a dynamic Boolean truth table.)pb")
        .def(nb::init<uint32_t>(), nb::arg("num_vars"),
             R"pb(Creates a truth table with all bits initialized to ``0``.

Args:
    num_vars: Number of Boolean variables.)pb")

        // Operators
        .def(nb::self == nb::self, nb::arg("other"),
             R"pb(Checks equality with another truth table.)pb")  // NOLINT(misc-redundant-expression)
        .def(nb::self != nb::self, nb::arg("other"),
             R"pb(Checks inequality with another truth table.)pb")  // NOLINT(misc-redundant-expression)
        .def(nb::self < nb::self, nb::arg("other"),
             R"pb(Lexicographically compares two truth tables.)pb")  // NOLINT(misc-redundant-expression)
        .def(nb::self & nb::self, nb::arg("other"),
             R"pb(Computes bitwise AND with another truth table.)pb")  // NOLINT(misc-redundant-expression)
        .def(nb::self | nb::self, nb::arg("other"),
             R"pb(Computes bitwise OR with another truth table.)pb")  // NOLINT(misc-redundant-expression)
        .def(nb::self ^ nb::self, nb::arg("other"),
             R"pb(Computes bitwise XOR with another truth table.)pb")  // NOLINT(misc-redundant-expression)
        .def(~nb::self, R"pb(Computes bitwise NOT.)pb")

        // Python list-like convenience functions
        .def("__len__", &aigverse::truth_table::num_bits, R"pb(Returns the number of bits.)pb")
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
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }

                return kitty::get_bit(self, static_cast<uint64_t>(index));
            },
            nb::arg("index"),
            R"pb(Returns one bit by index.

Args:
    index: Bit index.

Returns:
    The bit value.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "__setitem__",
            [](aigverse::truth_table& self, int64_t index, const bool value)
            {
                if (index < 0)
                {
                    index += static_cast<int64_t>(self.num_bits());
                }
                if (index < 0 || static_cast<uint64_t>(index) >= self.num_bits())
                {
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
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
            nb::arg("index"), nb::arg("value"),
            R"pb(Sets one bit by index.

Args:
    index: Bit index.
    value: New bit value.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "__iter__",
            [](const aigverse::truth_table& self)
            {
                return nb::make_iterator(nb::type<aigverse::truth_table>(), "bit_iterator",
                                         detail::truth_table_bit_iterator(self, 0),
                                         detail::truth_table_bit_iterator(self, self.num_bits()));
            },
            R"pb(Returns an iterator over all bits.)pb", nb::keep_alive<0, 1>())  // NOLINT(misc-include-cleaner)

        // Method bindings
        .def("num_vars", &aigverse::truth_table::num_vars, R"pb(Returns the number of variables.)pb")
        .def("num_blocks", &aigverse::truth_table::num_blocks, R"pb(Returns the number of storage blocks.)pb")
        .def("num_bits", &aigverse::truth_table::num_bits, R"pb(Returns the number of truth table bits.)pb")

        // operator= for assigning to other truth tables
        .def(
            "__copy__", [](const aigverse::truth_table& self) { return self; },
            R"pb(Returns a shallow copy of the truth table.)pb")
        .def(
            "__deepcopy__", [](const aigverse::truth_table& self, nb::dict&) { return self; },
            R"pb(Returns a deep copy of the truth table.)pb")
        .def(
            "__assign__", [](aigverse::truth_table& self, const aigverse::truth_table& other) { return self = other; },
            nb::arg("other"),
            R"pb(Assigns from another truth table with a compatible shape.

Args:
    other: Source truth table.

Returns:
    The updated truth table.)pb")

        // Hashing
        .def(
            "__hash__", [](const aigverse::truth_table& self) { return kitty::hash<aigverse::truth_table>{}(self); },
            R"pb(Returns a hash value for dictionary/set usage.)pb")

        // Pickle support via __getstate__ / __setstate__
        .def(
            "__getstate__",
            [](const aigverse::truth_table& self) { return nb::make_tuple(self.num_vars(), self._bits); },
            R"pb(Returns pickle state as ``(num_vars, words)``.)pb")
        .def(
            "__setstate__",
            [](aigverse::truth_table& self, const nb::tuple& t)
            {
                if (t.size() != 2)
                {
                    throw std::runtime_error("Invalid state for TruthTable unpickling.");
                }
                const auto num_vars = nb::cast<uint32_t>(t[0]);
                auto       words    = nb::cast<std::vector<uint64_t>>(t[1]);
                if (words.empty())
                {
                    throw std::runtime_error("Cannot unpickle an empty TruthTable.");
                }
                new (&self) aigverse::truth_table{num_vars};
                if (self.num_blocks() != words.size())
                {
                    throw std::runtime_error("Mismatched block count during unpickling.");
                }
                kitty::create_from_words(self, words.begin(), words.end());
            },
            nb::arg("state"),
            R"pb(Restores a truth table from pickle state.

Args:
    state: Tuple ``(num_vars, words)``.

Raises:
    RuntimeError: If the serialized state is malformed.)pb")

        // Free functions added to the class for convenience
        .def(
            "set_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }
                kitty::set_bit(self, index);
            },
            nb::arg("index"),
            R"pb(Sets one bit to ``1``.

Args:
    index: Bit index.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "get_bit",
            [](const aigverse::truth_table& self, const uint64_t index) -> bool
            {
                if (index >= self.num_bits())
                {
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }
                return static_cast<bool>(kitty::get_bit(self, index));
            },
            nb::arg("index"),
            R"pb(Returns one bit value.

Args:
    index: Bit index.

Returns:
    The bit value.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "clear_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }
                kitty::clear_bit(self, index);
            },
            nb::arg("index"),
            R"pb(Clears one bit to ``0``.

Args:
    index: Bit index.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "flip_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw nb::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }
                kitty::flip_bit(self, index);
            },
            nb::arg("index"),
            R"pb(Toggles one bit value.

Args:
    index: Bit index.

Raises:
    IndexError: If ``index`` is out of range.)pb")
        .def(
            "get_block",
            [](const aigverse::truth_table& self, const uint64_t block_index)
            {
                if (block_index >= self.num_blocks())
                {
                    throw nb::index_error("block index out of range");
                }
                return kitty::get_block(self, block_index);
            },
            nb::arg("block_index"),
            R"pb(Returns one 64-bit storage block.

Args:
    block_index: Block index.

Returns:
    The block value.

Raises:
    IndexError: If ``block_index`` is out of range.)pb")
        .def(
            "create_nth_var",
            [](aigverse::truth_table& self, const uint64_t var_index, const bool complement)
            {
                if (var_index >= self.num_vars())
                {
                    throw nb::index_error(
                        "Index of the variable must be smaller than the truth table's number of variables.");
                }

                kitty::create_nth_var(self, static_cast<uint8_t>(var_index), complement);
            },
            nb::arg("var_index"), nb::arg("complement") = false,
            R"pb(Creates the projection function for one variable.

Args:
    var_index: Variable index to project.
    complement: Whether to complement the projection.

Raises:
    IndexError: If ``var_index`` is out of range.)pb")
        .def(
            "create_from_binary_string",
            [](aigverse::truth_table& self, const std::string& binary)
            {
                if (binary.size() != self.num_bits())
                {
                    throw std::invalid_argument(
                        "Number of characters in binary string must match the number of bits in the truth table.");
                }

                kitty::create_from_binary_string(self, binary);
            },
            nb::arg("binary"),
            R"pb(Loads bit values from a binary string.

Args:
    binary: Binary string of length ``num_bits``.

Raises:
    ValueError: If the string length does not match ``num_bits``.)pb")
        .def(
            "create_from_hex_string",
            [](aigverse::truth_table& self, const std::string& hexadecimal)
            {
                if (self.num_vars() < 2)
                {
                    if (hexadecimal.size() != 1)
                    {
                        throw std::invalid_argument(
                            "Number of characters in hex string must be one fourth the number of "
                            "bits in the truth table.");
                    }
                }
                else if ((hexadecimal.size() << 2u) != self.num_bits())
                {
                    throw std::invalid_argument(
                        "Number of characters in hex string must be one fourth the number of bits in the truth table.");
                }

                kitty::create_from_hex_string(self, hexadecimal);
            },
            nb::arg("hexadecimal"),
            R"pb(Loads bit values from a hexadecimal string.

Args:
    hexadecimal: Hex string matching the truth table size.

Raises:
    ValueError: If the string length does not match the expected size.)pb")
        .def(
            "create_random", [](aigverse::truth_table& self) { kitty::create_random(self); },
            R"pb(Fills the truth table with random bits.)pb")
        .def(
            "create_majority", [](aigverse::truth_table& self) { kitty::create_majority(self); },
            R"pb(Fills the truth table with the majority function.)pb")
        .def("clear", &kitty::clear<aigverse::truth_table>, R"pb(Clears all bits to ``0``.)pb")
        .def("count_ones", &kitty::count_ones<aigverse::truth_table>, R"pb(Returns the number of set bits.)pb")
        .def("count_zeroes", &kitty::count_zeros<aigverse::truth_table>, R"pb(Returns the number of cleared bits.)pb")
        .def(
            "is_const0", [](const aigverse::truth_table& self) { return kitty::is_const0(self); },
            R"pb(Returns whether all bits are ``0``.)pb")
        .def(
            "is_const1", [](const aigverse::truth_table& self) { return kitty::is_const0(kitty::unary_not(self)); },
            R"pb(Returns whether all bits are ``1``.)pb")

        // Representations
        .def(
            "__repr__",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_hex(self, stream);
                return fmt::format("TruthTable <vars={}>: {}", self.num_vars(), stream.str());
            },
            R"pb(Returns a developer-friendly string representation.)pb")
        .def(
            "to_binary",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_binary(self, stream);
                return stream.str();
            },
            R"pb(Returns the truth table as a binary string.)pb")
        .def(
            "to_hex",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_hex(self, stream);
                return stream.str();
            },
            R"pb(Returns the truth table as a hexadecimal string.)pb");
}

}  // namespace aigverse
