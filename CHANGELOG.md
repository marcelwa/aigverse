<!-- Entries in each category are sorted by merge time, with the latest PRs appearing first. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on a mixture of [Keep a Changelog] and [Common Changelog].
This project adheres to [Semantic Versioning], with the exception that minor
releases may include breaking changes.

## [Unreleased]

### Added

- 👷 Run `nox -s minimums` in CI, so the declared dependency floors are actually
  installed and tested instead of only claimed ([#453]) ([**@marcelwa**])

### Fixed

- 🐛 Gate the `numpy` and `torch` floors by Python version. Both predate every
  interpreter in the matrix except 3.10, so resolving them as the lowest direct
  versions fell back to a NumPy source build that fails and to a PyTorch release
  with no installable distribution ([#453]) ([**@marcelwa**])

## [0.1.4] - 2026-08-19

### Added

- 📝 Add a changelog and an upgrade guide to the documentation ([#448])
  ([**@marcelwa**])
- ✨ Add the `aigverse.abc` module, a bridge that runs the optimization scripts
  and commands of an externally installed ABC ([#405]) ([**@marcelwa**])

### Changed

- 🔧 Raise the CMake policy upper bound to 4.4, so the project no longer runs
  under three-release-old policy defaults on CMake 4.2-4.4 ([#447])
  ([**@marcelwa**])
- 🔧 Add `Developers`, `Information Technology`, and
  `Software Development :: Libraries :: Python Modules` trove classifiers, so
  `aigverse` surfaces on PyPI for its non-research audience too ([#447])
  ([**@marcelwa**])
- 🔧 Derive the version from `vcs-versioning` instead of `setuptools-scm`,
  dropping the transitive `setuptools` dependency from every wheel build
  ([#447]) ([**@marcelwa**])
- 🔧 Drop the no-op submodule checkout steps from `.readthedocs.yaml` and
  `docs/DevelopmentGuide.md`; the project has no submodules ([#447])
  ([**@marcelwa**])
- ⬆️ Update `nanobind` to version 2.15.0 ([#430], [#445])

### Fixed

- 🏷️ Fix the one-hot encoding annotations in the NetworkX adapter, which pinned
  `int8` regardless of the `dtype` the caller passed ([#435]) ([**@marcelwa**])

## [0.1.3] - 2026-08-04

### Added

- ✨ Add a benchmark loader that fetches and caches the EPFL suite on demand
  ([#409]) ([**@marcelwa**])
- ✨ Emit `llms.txt` and `llms-full.txt` from the documentation build, so agents
  read the docs as markdown instead of scraping HTML ([#417]) ([**@marcelwa**])
- 📝 Add a visualization page to the documentation ([#419]) ([**@marcelwa**])

### Changed

- 👷 Track the pinned `mockturtle` revision with a Renovate custom manager
  ([#404]) ([**@marcelwa**])

### Fixed

- 🐛 Raise `IndexError` instead of segfaulting on an out-of-range node ID
  ([#420]) ([**@marcelwa**])
- 🐛 Fix the named AIG example in the AIG documentation ([#407])
  ([**@marcelwa**])
- 👷 Drop the `cp313t-*` `cibuildwheel` skip selector, which matched a group the
  project never enables and made every wheel job warn ([#421]) ([**@marcelwa**])

## [0.1.2] - 2026-07-24

### Added

- ✨ Add cut enumeration over AIGs ([#368]) ([**@wjrforcyber**])
- ✨ Add `to_graph_tensors`, which exports an AIG as DLPack sparse tensors for
  zero-copy interop with PyTorch, JAX, and TensorFlow ([#308]) ([**@marcelwa**])
- 👷 Add a Zizmor workflow that scans the GitHub Actions workflows and uploads
  its findings to code scanning ([#392]) ([**@marcelwa**])
- 📝 Add `AGENTS.md` and `WORKFLOW.md` to steer agentic coding tools ([#382])
  ([**@marcelwa**])
- 📝 Document edge lists in the AIG guide ([#389]) ([**@marcelwa**])
- 📝 Document the gitmoji convention for commit messages and pull request titles
  ([#390]) ([**@marcelwa**])

### Changed

- ⬆️ Update `mockturtle` to the latest `mnt` revision ([#388]) ([**@marcelwa**])
- ⬆️ Update `nanobind` to version 2.13.0 ([#369])

### Fixed

- 🐛 Fix ASCII AIGER parsing for constant outputs ([#394]) ([**@marcelwa**])
- 📝 Fix role rendering and broken links in the documentation, and the PyTorch
  sparse tensor warning it raised ([#395]) ([**@marcelwa**])

## [0.1.1] - 2026-05-18

### Fixed

- 🐛 Stop `to_edge_list` from collapsing duplicate primary outputs ([#358])
  ([**@marcelwa**])

## [0.1.0] - 2026-05-09

_If you are upgrading: please see [`UPGRADING.md`](UPGRADING.md#010)._

### Added

- ✨ Expose the network generators through the new `aigverse.generators` module
  ([#305]) ([**@marcelwa**])
- 📝 Add docstrings to every module and symbol ([#303]) ([**@marcelwa**])

### Changed

- 💥 Split the monolithic package into the `networks`, `algorithms`, `io`, and
  `utils` extension modules ([#285]) ([**@marcelwa**])
- 💥 Rework the API to be Pythonic: the optimization passes return a new cleaned
  `Aig` by default and take `inplace`, and `cleanup_dangling` moves to
  `aigverse.algorithms` ([#298]) ([**@marcelwa**])
- 💥 Make every optimization parameter except the input network keyword-only
  ([#306]) ([**@marcelwa**])
- ♻️ Migrate the bindings from `pybind11` to `nanobind` ([#297])
  ([**@marcelwa**])
- 🔧 Modernize the tooling and adopt the Scientific Python repo review ([#314],
  [#335]) ([**@marcelwa**])
- ✅ Restructure the test suite around markers and shared fixtures ([#313])
  ([**@marcelwa**])
- 📝 Streamline the README and the documentation ([#334]) ([**@marcelwa**])

### Fixed

- 🐛 Fix the `stubgen` pattern file so the generated stubs come out as intended
  ([#336]) ([**@marcelwa**])

<!-- Version links -->

[unreleased]: https://github.com/marcelwa/aigverse/compare/v0.1.4...HEAD
[0.1.4]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.4
[0.1.3]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.3
[0.1.2]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.2
[0.1.1]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.1
[0.1.0]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.0

<!-- PR links -->

[#453]: https://github.com/marcelwa/aigverse/pull/453
[#448]: https://github.com/marcelwa/aigverse/pull/448
[#447]: https://github.com/marcelwa/aigverse/pull/447
[#445]: https://github.com/marcelwa/aigverse/pull/445
[#435]: https://github.com/marcelwa/aigverse/pull/435
[#430]: https://github.com/marcelwa/aigverse/pull/430
[#421]: https://github.com/marcelwa/aigverse/pull/421
[#420]: https://github.com/marcelwa/aigverse/pull/420
[#419]: https://github.com/marcelwa/aigverse/pull/419
[#417]: https://github.com/marcelwa/aigverse/pull/417
[#409]: https://github.com/marcelwa/aigverse/pull/409
[#407]: https://github.com/marcelwa/aigverse/pull/407
[#405]: https://github.com/marcelwa/aigverse/pull/405
[#404]: https://github.com/marcelwa/aigverse/pull/404
[#395]: https://github.com/marcelwa/aigverse/pull/395
[#394]: https://github.com/marcelwa/aigverse/pull/394
[#392]: https://github.com/marcelwa/aigverse/pull/392
[#390]: https://github.com/marcelwa/aigverse/pull/390
[#389]: https://github.com/marcelwa/aigverse/pull/389
[#388]: https://github.com/marcelwa/aigverse/pull/388
[#382]: https://github.com/marcelwa/aigverse/pull/382
[#369]: https://github.com/marcelwa/aigverse/pull/369
[#368]: https://github.com/marcelwa/aigverse/pull/368
[#358]: https://github.com/marcelwa/aigverse/pull/358
[#336]: https://github.com/marcelwa/aigverse/pull/336
[#335]: https://github.com/marcelwa/aigverse/pull/335
[#334]: https://github.com/marcelwa/aigverse/pull/334
[#314]: https://github.com/marcelwa/aigverse/pull/314
[#313]: https://github.com/marcelwa/aigverse/pull/313
[#308]: https://github.com/marcelwa/aigverse/pull/308
[#306]: https://github.com/marcelwa/aigverse/pull/306
[#305]: https://github.com/marcelwa/aigverse/pull/305
[#303]: https://github.com/marcelwa/aigverse/pull/303
[#298]: https://github.com/marcelwa/aigverse/pull/298
[#297]: https://github.com/marcelwa/aigverse/pull/297
[#285]: https://github.com/marcelwa/aigverse/pull/285

<!-- Contributor -->

[**@marcelwa**]: https://github.com/marcelwa
[**@wjrforcyber**]: https://github.com/wjrforcyber

<!-- General links -->

[Keep a Changelog]: https://keepachangelog.com/en/1.1.0/
[Common Changelog]: https://common-changelog.org
[Semantic Versioning]: https://semver.org/spec/v2.0.0.html
