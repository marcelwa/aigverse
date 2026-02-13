//
// Created by marcel on 03.09.25.
//

#include "aigverse/types.hpp"

#include <mockturtle/algorithms/equivalence_checking.hpp>
#include <mockturtle/algorithms/miter.hpp>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>  // NOLINT(misc-include-cleaner)

#include <cstdint>
#include <optional>
#include <stdexcept>

namespace aigverse
{

namespace detail
{

template <typename Spec, typename Impl>
void equivalence_checking(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    namespace py = pybind11;

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
        py::arg("spec"), py::arg("impl"), py::arg("conflict_limit") = 0, py::arg("functional_reduction") = true,
        py::arg("verbose") = false,
        pybind11::call_guard<pybind11::gil_scoped_release>());  // NOLINT(misc-include-cleaner)
}

// Explicit instantiation for AIG
template void equivalence_checking<aigverse::aig, aigverse::aig>(pybind11::module_& m);

}  // namespace detail

void bind_equivalence_checking(pybind11::module_& m)  // NOLINT(misc-use-internal-linkage)
{
    detail::equivalence_checking<aigverse::aig, aigverse::aig>(m);
}

}  // namespace aigverse
