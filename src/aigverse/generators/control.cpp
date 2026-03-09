#include "aigverse/types.hpp"

#include <mockturtle/generators/control.hpp>
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
void bind_control(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    using signal = mockturtle::signal<Ntk>;

    m.def(
        "multiplexer",
        [](const uint32_t bitwidth) -> Ntk
        {
            if (bitwidth == 0u)
            {
                throw std::invalid_argument("bitwidth must be greater than 0");
            }

            Ntk ntk{};

            const auto cond = ntk.create_pi();

            std::vector<signal> t{};
            std::vector<signal> e{};
            t.reserve(bitwidth);
            e.reserve(bitwidth);

            for (auto i = 0u; i < bitwidth; ++i)
            {
                t.push_back(ntk.create_pi());
                e.push_back(ntk.create_pi());
            }

            const auto outputs = mockturtle::mux(ntk, cond, t, e);
            for (const auto& s : outputs)
            {
                ntk.create_po(s);
            }

            return ntk;
        },
        nb::arg("bitwidth"),
        R"pb(Creates a complete word-level n-bit 2:1 MUX network.

Args:
    bitwidth: Number of bits in each data input word.

Returns:
    An ``Aig`` with ``1 + 2 * bitwidth`` primary inputs and ``bitwidth``
    primary outputs.

Raises:
    ValueError: If ``bitwidth`` is not greater than ``0``.
)pb");

    m.def(
        "binary_decoder",
        [](const uint32_t num_select_bits) -> Ntk
        {
            if (num_select_bits == 0u)
            {
                throw std::invalid_argument("num_select_bits must be greater than 0");
            }

            Ntk ntk{};

            std::vector<signal> xs{};
            xs.reserve(num_select_bits);
            for (auto i = 0u; i < num_select_bits; ++i)
            {
                xs.push_back(ntk.create_pi());
            }

            const auto outputs = mockturtle::binary_decoder(ntk, xs);
            for (const auto& s : outputs)
            {
                ntk.create_po(s);
            }

            return ntk;
        },
        nb::arg("num_select_bits"),
        R"pb(Creates a complete binary-decoder network.

Args:
    num_select_bits: Number of select input bits.

Returns:
    An ``Aig`` with ``num_select_bits`` primary inputs and
    ``2 ** num_select_bits`` primary outputs.

Raises:
    ValueError: If ``num_select_bits`` is not greater than ``0``.
)pb");
}

// Explicit instantiation for AIGs
template void bind_control<aigverse::aig>(nanobind::module_& m);

}  // namespace detail

void bind_control_generators(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_control<aigverse::aig>(m);
}

}  // namespace aigverse
