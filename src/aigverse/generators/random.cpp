#include "aigverse/types.hpp"

#include <fmt/format.h>
#include <mockturtle/generators/random_network.hpp>
#include <nanobind/nanobind.h>
#include <nanobind/stl/string.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <stdexcept>
#include <string>

namespace aigverse
{

namespace detail
{

namespace nb = nanobind;

namespace
{

void validate_positive(const uint32_t value, const char* name)
{
    if (value == 0u)
    {
        throw std::invalid_argument(fmt::format("{} must be greater than 0", name));
    }
}

aig random_aig_impl(const uint32_t num_pis, const uint32_t num_gates, const uint64_t seed)
{
    validate_positive(num_pis, "num_pis");
    validate_positive(num_gates, "num_gates");

    mockturtle::random_network_generator_params_size ps{};
    ps.num_pis                        = num_pis;
    ps.num_gates                      = num_gates;
    ps.seed                           = seed;
    ps.num_networks_per_configuration = 1;
    ps.num_pis_increment              = 0;
    ps.num_gates_increment            = 0;

    auto generator = mockturtle::random_aig_generator(ps);
    return generator.generate();
}

}  // namespace

void bind_random(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    m.def("random_aig", &random_aig_impl, nb::kw_only(), nb::arg("num_pis"), nb::arg("num_gates"),
          nb::arg("seed") = static_cast<uint64_t>(0xcafeaffe),
          R"pb(Generates a single random AIG with a fixed size.

Args:
    num_pis: Number of primary inputs.
    num_gates: Number of logic gates.
    seed: Seed controlling random choices.

Returns:
    A randomly generated AIG.

Raises:
    ValueError: If ``num_pis`` or ``num_gates`` is not greater than ``0``.
)pb");
}

}  // namespace detail

void bind_random_generators(nanobind::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::bind_random(m);
}

}  // namespace aigverse
