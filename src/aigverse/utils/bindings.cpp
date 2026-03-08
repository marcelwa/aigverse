#include <nanobind/nanobind.h>

namespace aigverse
{
void bind_truth_table(nanobind::module_& m);
void bind_truth_table_operations(nanobind::module_& m);
}  // namespace aigverse

NB_MODULE(utils, m)
{
    m.doc() = R"pb(Provides utility data structures and functions.)pb";
    aigverse::bind_truth_table(m);
    aigverse::bind_truth_table_operations(m);
}
