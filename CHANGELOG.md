<!-- Entries in each category are sorted by merge time, with the latest PRs appearing first. -->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on a mixture of [Keep a Changelog] and [Common Changelog].
This project adheres to [Semantic Versioning], with the exception that minor
releases may include breaking changes.

## [Unreleased]

### Added

- ✨ Add `run_many` to the `aigverse.abc` bridge, which runs one ABC script over many
  networks at once, one process per network across all cores, and with
  `return_exceptions=True` hands back each failure in its network's place instead of
  losing the batch to the first bad design ([#467]) ([**@marcelwa**])

### Changed

- ⚡️ Run `examples/abc_recipe_study.py`'s sweep as one batch per recipe rather than one
  ABC call at a time, and give it a `--jobs` flag. Its 400 runs over the default design
  set drop from 44 s to 11 s on sixteen cores, with identical measurements ([#467])
  ([**@marcelwa**])
- ⚡️ Release the GIL in the `generators` bindings, so random and structured
  network construction overlaps across threads instead of blocking every other
  worker ([#478]) ([**@marcelwa**])
- ⚡️ Release the GIL in the `io` bindings, so reading and writing networks
  overlaps across threads instead of serializing against every other worker
  ([#477]) ([**@marcelwa**])

### Fixed

- 🐛 Resolve the ABC executable once per `run_script` call instead of twice. The second
  lookup ran after ABC had already finished, purely to name the binary in an error, so a
  binary that disappeared mid-run discarded a successful result ([#467]) ([**@marcelwa**])

## [0.1.5] - 2026-08-24

### Added

- ✨ Add `simulate_sequential`, which runs a `SequentialAig` over a number of clock
  cycles from its reset state and returns the primary output values and the register
  values per cycle ([#458]) ([**@marcelwa**])
- 👷 Run `nox -s minimums` in CI across the full platform matrix, so the declared
  dependency floors are actually installed and tested instead of only claimed
  ([#453]) ([**@marcelwa**])
- ✨ Add a `--full` flag to the `tests` and `minimums` nox sessions that installs
  every optional dependency group and selects every marker, replacing the
  implicit `CI` environment check ([#453]) ([**@marcelwa**])
- ✨ Add an `examples/` directory of standalone, PEP 723 scripts that run with
  `uv run` and no setup, starting with an ABC recipe study that asks whether one
  best recipe exists ([#410]) ([**@marcelwa**])
- 👷 Smoke-run the examples in the ABC workflow, so a library change that breaks
  one is caught by CI rather than by the next person to run it ([#410])
  ([**@marcelwa**])
- ✨ Support `SequentialAig` in the `aigverse.abc` bridge, carrying registers
  through ABC along with their reset values in the classic namespace ([#406])
  ([**@marcelwa**])

### Changed

- 👷 Restructure CI into a thin `ci.yml` caller over one reusable workflow per
  concern, gated by change detection and aggregated into a single required
  `🚦 Check` ([#422]) ([**@marcelwa**])
- ⚡️ Adopt nanobind 3.0's split mode, so one `abi3` wheel per platform covers
  every supported Python from 3.10 up instead of three. Cold build time drops
  3.15x and the shipped payload 4.3x; the extensions themselves shrink 26% by no
  longer each carrying their own copy of the nanobind library, which is now the
  separate `nanobind-backend` runtime dependency. Free-threaded interpreters are
  not supported until Python 3.15 brings them a stable ABI ([#463])
  ([**@marcelwa**])
- ⚡️ Build the extension once per wheel tag in the `tests` and `minimums` nox
  sessions instead of once per interpreter, so interpreters sharing a tag reuse
  one wheel rather than each getting a purpose-built one ([#456])
  ([**@marcelwa**])

### Fixed

- 🐛 Refuse an AIGER file with latches in `read_aiger_into_aig` and
  `read_ascii_aiger_into_aig`, which used to segfault or silently drop the
  registers, and point users at the sequential reader instead ([#457])
  ([**@marcelwa**])
- 👷 Cache Windows compiles. `scikit-build-core` defaults to the Visual Studio
  generator, which ignores `CMAKE_<LANG>_COMPILER_LAUNCHER`, so the compiler
  cache was configured on Windows and then never invoked -- every job rebuilt
  every translation unit once per interpreter. Windows now builds with Ninja and
  caches with `sccache`, whose MSVC support, unlike ccache's, actually hits
  ([#456]) ([**@marcelwa**])
- 🐛 Forward `-h` and `--help` to `sphinx-build` in the `docs` nox session, which
  its own argument parser used to intercept ([#453]) ([**@marcelwa**])
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

[unreleased]: https://github.com/marcelwa/aigverse/compare/v0.1.5...HEAD
[0.1.5]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.5
[0.1.4]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.4
[0.1.3]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.3
[0.1.2]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.2
[0.1.1]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.1
[0.1.0]: https://github.com/marcelwa/aigverse/releases/tag/v0.1.0

<!-- PR links -->

[#467]: https://github.com/marcelwa/aigverse/pull/467
[#478]: https://github.com/marcelwa/aigverse/pull/478
[#477]: https://github.com/marcelwa/aigverse/pull/477
[#463]: https://github.com/marcelwa/aigverse/pull/463
[#458]: https://github.com/marcelwa/aigverse/pull/458
[#457]: https://github.com/marcelwa/aigverse/pull/457
[#456]: https://github.com/marcelwa/aigverse/pull/456
[#453]: https://github.com/marcelwa/aigverse/pull/453
[#448]: https://github.com/marcelwa/aigverse/pull/448
[#447]: https://github.com/marcelwa/aigverse/pull/447
[#445]: https://github.com/marcelwa/aigverse/pull/445
[#435]: https://github.com/marcelwa/aigverse/pull/435
[#430]: https://github.com/marcelwa/aigverse/pull/430
[#422]: https://github.com/marcelwa/aigverse/pull/422
[#421]: https://github.com/marcelwa/aigverse/pull/421
[#420]: https://github.com/marcelwa/aigverse/pull/420
[#419]: https://github.com/marcelwa/aigverse/pull/419
[#417]: https://github.com/marcelwa/aigverse/pull/417
[#410]: https://github.com/marcelwa/aigverse/pull/410
[#409]: https://github.com/marcelwa/aigverse/pull/409
[#407]: https://github.com/marcelwa/aigverse/pull/407
[#406]: https://github.com/marcelwa/aigverse/pull/406
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
