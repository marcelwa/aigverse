#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_truth_table(nanobind::module_& m);
void bind_truth_table_operations(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(utils, m)
{
    m.doc() = "Utility data structures and functions";
    aigverse::bind_truth_table(m);
    aigverse::bind_truth_table_operations(m);
}
