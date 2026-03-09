#include "aigverse/types.hpp"

#include <mockturtle/generators/arithmetic.hpp>
#include <mockturtle/traits.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <stdexcept>
#include <vector>

namespace aigverse
{

namespace detail
{

namespace nb = nanobind;

template <typename Ntk>
void bind_arithmetic(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    using signal = mockturtle::signal<Ntk>;

    m.def(
        "ripple_carry_adder",
        [](const uint32_t bitwidth) -> Ntk
        {
            if (bitwidth == 0u)
            {
                throw std::invalid_argument("bitwidth must be greater than 0");
            }

            Ntk ntk{};

            std::vector<signal> a{};
            std::vector<signal> b{};
            a.reserve(bitwidth);
            b.reserve(bitwidth);

            for (auto i = 0u; i < bitwidth; ++i)
            {
                a.push_back(ntk.create_pi());
                b.push_back(ntk.create_pi());
            }

            auto carry = ntk.get_constant(false);
            mockturtle::carry_ripple_adder_inplace(ntk, a, b, carry);
            for (const auto& bit : a)
            {
                ntk.create_po(bit);
            }
            ntk.create_po(carry);
            return ntk;
        },
        nb::arg("bitwidth"),
        R"pb(Creates a complete ripple-carry adder benchmark network.

Args:
    bitwidth: Number of bits per operand.

Returns:
    An ``Aig`` with ``2 * bitwidth`` primary inputs and
    ``bitwidth + 1`` primary outputs (sum plus carry-out).

Raises:
    ValueError: If ``bitwidth`` is not greater than ``0``.
)pb");

    m.def(
        "carry_lookahead_adder",
        [](const uint32_t bitwidth) -> Ntk
        {
            if (bitwidth == 0u)
            {
                throw std::invalid_argument("bitwidth must be greater than 0");
            }

            Ntk ntk{};

            std::vector<signal> a{};
            std::vector<signal> b{};
            a.reserve(bitwidth);
            b.reserve(bitwidth);

            for (auto i = 0u; i < bitwidth; ++i)
            {
                a.push_back(ntk.create_pi());
                b.push_back(ntk.create_pi());
            }

            auto carry = ntk.get_constant(false);
            mockturtle::carry_lookahead_adder_inplace(ntk, a, b, carry);
            for (const auto& bit : a)
            {
                ntk.create_po(bit);
            }
            ntk.create_po(carry);
            return ntk;
        },
        nb::arg("bitwidth"),
        R"pb(Creates a complete carry-lookahead adder benchmark network.

Args:
    bitwidth: Number of bits per operand.

Returns:
    An ``Aig`` with ``2 * bitwidth`` primary inputs and
    ``bitwidth + 1`` primary outputs (sum plus carry-out).

Raises:
    ValueError: If ``bitwidth`` is not greater than ``0``.
)pb");

    m.def(
        "ripple_carry_multiplier",
        [](const uint32_t bitwidth) -> Ntk
        {
            if (bitwidth == 0u)
            {
                throw std::invalid_argument("bitwidth must be greater than 0");
            }

            Ntk ntk{};

            std::vector<signal> a{};
            std::vector<signal> b{};
            a.reserve(bitwidth);
            b.reserve(bitwidth);

            for (auto i = 0u; i < bitwidth; ++i)
            {
                a.push_back(ntk.create_pi());
                b.push_back(ntk.create_pi());
            }

            const auto product = mockturtle::carry_ripple_multiplier(ntk, a, b);
            for (const auto& bit : product)
            {
                ntk.create_po(bit);
            }
            return ntk;
        },
        nb::arg("bitwidth"),
        R"pb(Creates a complete ripple-carry multiplier benchmark network.

Args:
    bitwidth: Number of bits per operand.

Returns:
    An ``Aig`` with ``2 * bitwidth`` primary inputs and
    ``2 * bitwidth`` primary outputs representing the product bits.

Raises:
    ValueError: If ``bitwidth`` is not greater than ``0``.
)pb");

    m.def(
        "sideways_sum_adder",
        [](const uint32_t bitwidth) -> Ntk
        {
            if (bitwidth == 0u)
            {
                throw std::invalid_argument("bitwidth must be greater than 0");
            }

            Ntk ntk{};

            std::vector<signal> a{};
            a.reserve(bitwidth);

            for (auto i = 0u; i < bitwidth; ++i)
            {
                a.push_back(ntk.create_pi());
            }

            const auto sum = mockturtle::sideways_sum_adder(ntk, a);
            for (const auto& bit : sum)
            {
                ntk.create_po(bit);
            }
            return ntk;
        },
        nb::arg("bitwidth"),
        R"pb(Creates a complete sideways sum adder benchmark network.

Args:
    bitwidth: Number of input bits.

Returns:
    An ``Aig`` with ``bitwidth`` primary inputs and output bits encoding
    the population count of the input word.

Raises:
    ValueError: If ``bitwidth`` is not greater than ``0``.
)pb");
}

// Explicit instantiation for AIGs
template void bind_arithmetic<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_arithmetic_generators(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_arithmetic<aigverse::aig>(m);
}

}  // namespace aigverse
