//
// Created by marcel on 03.09.25.
//

#include "aigverse/truth_tables/truth_table.hpp"

#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <kitty/bit_operations.hpp>
#include <kitty/dynamic_truth_table.hpp>
#include <kitty/hash.hpp>
#include <kitty/print.hpp>
#include <pybind11/operators.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <sstream>
#include <stdexcept>
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

void bind_truth_table(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{

    namespace py = pybind11;
    using namespace pybind11::literals;

    py::class_<aigverse::truth_table>(m, "TruthTable")
        .def(py::init<uint32_t>(), "num_vars"_a,  // NOLINT(misc-include-cleaner)
             "Create a TruthTable with 'num_vars' variables with all bits set to 0.")

        // Operators
        .def(py::self == py::self, "other"_a)  // NOLINT(misc-redundant-expression)
        .def(py::self != py::self, "other"_a)  // NOLINT(misc-redundant-expression)
        .def(py::self < py::self, "other"_a)   // NOLINT(misc-redundant-expression)
        .def(py::self & py::self, "other"_a)   // NOLINT(misc-redundant-expression)
        .def(py::self | py::self, "other"_a)   // NOLINT(misc-redundant-expression)
        .def(py::self ^ py::self, "other"_a)   // NOLINT(misc-redundant-expression)
        .def(~py::self)

        // Python list-like convenience functions
        .def("__len__", &aigverse::truth_table::num_bits)
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
                    throw py::index_error("index out of range");  // NOLINT(misc-include-cleaner)
                }

                return kitty::get_bit(self, static_cast<uint64_t>(index));
            },
            "index"_a)
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
                return py::make_iterator(detail::truth_table_bit_iterator(self, 0),
                                         detail::truth_table_bit_iterator(self, self.num_bits()));
            },
            py::keep_alive<0, 1>())  // NOLINT(misc-include-cleaner)

        // Method bindings
        .def("num_vars", &aigverse::truth_table::num_vars, "Returns the number of variables.")
        .def("num_blocks", &aigverse::truth_table::num_blocks, "Returns the number of blocks.")
        .def("num_bits", &aigverse::truth_table::num_bits, "Returns the number of bits.")

        // operator= for assigning to other truth tables
        .def(
            "__copy__", [](const aigverse::truth_table& self) { return self; },
            "Returns a shallow copy of the truth table.")
        .def(
            "__deepcopy__",
            [](const aigverse::truth_table& self, py::dict&) { return self; },  // NOLINT(misc-include-cleaner)
            "Returns a deep copy of the truth table.")
        .def(
            "__assign__", [](aigverse::truth_table& self, const aigverse::truth_table& other) { return self = other; },
            "other"_a, "Assigns the truth table from another compatible truth table.")

        // Hashing
        .def(
            "__hash__", [](const aigverse::truth_table& self) { return kitty::hash<aigverse::truth_table>{}(self); },
            "Returns the hash of the truth table.")

        // Pickle support
        .def(py::pickle([](const aigverse::truth_table& self)
                        { return py::make_tuple(self.num_vars(), self._bits); },  // NOLINT(misc-include-cleaner)
                        [](const py::tuple& t)                                    // NOLINT(misc-include-cleaner)
                        {
                            if (t.size() != 2)
                            {
                                throw std::runtime_error("Invalid state for TruthTable unpickling.");
                            }
                            auto num_vars = t[0].cast<uint32_t>();
                            auto words    = t[1].cast<std::vector<uint64_t>>();
                            if (words.empty())
                            {
                                throw std::runtime_error("Cannot unpickle an empty TruthTable.");
                            }
                            aigverse::truth_table tt{num_vars};
                            if (tt.num_blocks() != words.size())
                            {
                                throw std::runtime_error("Mismatched block count during unpickling.");
                            }
                            kitty::create_from_words(tt, words.begin(), words.end());  // NOLINT(misc-include-cleaner)
                            return tt;
                        }))

        // Free functions added to the class for convenience
        .def(
            "set_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                kitty::set_bit(self, index);
            },
            "index"_a, "Sets the bit at the given index.")
        .def(
            "get_bit",
            [](const aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                return kitty::get_bit(self, index);
            },
            "index"_a, "Returns the bit at the given index.")
        .def(
            "clear_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                kitty::clear_bit(self, index);
            },
            "index"_a, "Clears the bit at the given index.")
        .def(
            "flip_bit",
            [](aigverse::truth_table& self, const uint64_t index)
            {
                if (index >= self.num_bits())
                {
                    throw py::index_error("index out of range");
                }
                kitty::flip_bit(self, index);
            },
            "index"_a, "Flips the bit at the given index.")
        .def(
            "get_block",
            [](const aigverse::truth_table& self, const uint64_t block_index)
            {
                if (block_index >= self.num_blocks())
                {
                    throw py::index_error("block index out of range");
                }
                return kitty::get_block(self, block_index);
            },
            "block_index"_a, "Returns a 64-bit block of bits.")
        .def(
            "create_nth_var",
            [](aigverse::truth_table& self, const uint64_t var_index, const bool complement)
            {
                if (var_index >= self.num_vars())
                {
                    throw py::index_error(
                        "Index of the variable must be smaller than the truth table's number of variables.");
                }

                kitty::create_nth_var(self, static_cast<uint8_t>(var_index),
                                      complement);  // NOLINT(misc-include-cleaner)
            },
            "var_index"_a, "complement"_a = false, "Constructs projections (single-variable functions).")
        .def(
            "create_from_binary_string",
            [](aigverse::truth_table& self, const std::string& binary)  // NOLINT(misc-include-cleaner)
            {
                if (binary.size() != self.num_bits())
                {
                    throw std::invalid_argument(
                        "Number of characters in binary string must match the number of bits in the truth table.");
                }

                kitty::create_from_binary_string(self, binary);  // NOLINT(misc-include-cleaner)
            },
            "binary"_a, "Constructs truth table from binary string.")
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

                kitty::create_from_hex_string(self, hexadecimal);  // NOLINT(misc-include-cleaner)
            },
            "hexadecimal"_a, "Constructs truth table from hexadecimal string.")
        .def(
            "create_random",
            [](aigverse::truth_table& self) { kitty::create_random(self); },  // NOLINT(misc-include-cleaner)
            "Constructs a random truth table.")
        .def(
            "create_majority",
            [](aigverse::truth_table& self) { kitty::create_majority(self); },  // NOLINT(misc-include-cleaner)
            "Constructs a MAJ truth table.")
        .def("clear", &kitty::clear<aigverse::truth_table>, "Clears all bits.")
        .def("count_ones", &kitty::count_ones<aigverse::truth_table>, "Counts ones in truth table.")
        .def("count_zeroes", &kitty::count_zeros<aigverse::truth_table>, "Counts zeroes in truth table.")
        .def(
            "is_const0",
            [](const aigverse::truth_table& self) { return kitty::is_const0(self); },  // NOLINT(misc-include-cleaner)
            "Checks if the truth table is constant 0.")
        .def(
            "is_const1", [](const aigverse::truth_table& self)
            { return kitty::is_const0(kitty::unary_not(self)); },  // NOLINT(misc-include-cleaner)
            "Checks if the truth table is constant 1.")

        // Representations
        .def(
            "__repr__",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_hex(self, stream);
                return fmt::format("TruthTable <vars={}>: {}", self.num_vars(), stream.str());
            },
            "Returns an abstract string representation of the truth table.")
        .def(
            "to_binary",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_binary(self, stream);
                return stream.str();
            },
            "Returns the truth table as a string in binary representation.")
        .def(
            "to_hex",
            [](const aigverse::truth_table& self)
            {
                std::stringstream stream{};
                kitty::print_hex(self, stream);
                return stream.str();
            },
            "Returns the truth table as a string in hexadecimal representation.");
}

}  // namespace aigverse
