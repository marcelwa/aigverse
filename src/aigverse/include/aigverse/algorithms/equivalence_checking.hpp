//
// Created by marcel on 09.09.24.
//

#ifndef AIGVERSE_EQUIVALENCE_CHECKING_HPP
#define AIGVERSE_EQUIVALENCE_CHECKING_HPP

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
void equivalence_checking(pybind11::module& m)
{
    using namespace pybind11::literals;

    m.def(
        "equivalence_checking",
        [](const Spec& spec, const Impl& impl, const uint32_t conflict_limit = 0,
           const bool functional_reduction = true, const bool verbose = false) -> std::optional<bool>
        {
            const auto miter = mockturtle::miter<aigverse::aig, Spec, Impl>(spec, impl);

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
        "spec"_a, "impl"_a, "conflict_limit"_a = 0, "functional_reduction"_a = true, "verbose"_a = false)

        ;
}

}  // namespace detail

inline void equivalence_checking(pybind11::module& m)
{
    detail::equivalence_checking<aigverse::aig, aigverse::aig>(m);
}

}  // namespace aigverse

#endif  // AIGVERSE_EQUIVALENCE_CHECKING_HPP
