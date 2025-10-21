//
// Created by marcel on 03.09.25.
//

#include "aigverse/algorithms/equivalence_checking.hpp"

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/equivalence_checking.hpp>
#include <mockturtle/algorithms/miter.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <cstdint>
#include <optional>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

template <typename Spec, typename Impl>
void equivalence_checking(pybind11::module_& m)
{
    using namespace pybind11::literals;

    m.def(
        "equivalence_checking",
        [](const Spec& spec, const Impl& impl, const uint32_t conflict_limit = 0,
           const bool functional_reduction = true, const bool verbose = false) -> std::optional<bool>
        {
            const auto miter = mockturtle::miter<mockturtle::aig_network, Spec, Impl>(spec, impl);

            if (!miter.has_value())
            {
                throw std::runtime_error("miter construction failed due to differing numbers of PIs or POs");
            }

            mockturtle::equivalence_checking_params params{};
            params.conflict_limit       = conflict_limit;
            params.functional_reduction = functional_reduction;
            params.verbose              = verbose;

            return mockturtle::equivalence_checking(miter.value(), params);
        },
        "spec"_a, "impl"_a, "conflict_limit"_a = 0, "functional_reduction"_a = true, "verbose"_a = false,
        pybind11::call_guard<pybind11::gil_scoped_release>());
}

// Explicit instantiation for AIG
template void equivalence_checking<aigverse::aig, aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_equivalence_checking(pybind11::module_& m)
{
    detail::equivalence_checking<aigverse::aig, aigverse::aig>(m);
}

}  // namespace aigverse
