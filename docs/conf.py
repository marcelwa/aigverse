# Copyright (c) 2025 Chair for Design Automation, TUM
# All rights reserved.
#
# SPDX-License-Identifier: MIT
#
# Licensed under the MIT License

"""Sphinx configuration file."""

from __future__ import annotations

import os
import subprocess
import warnings
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()


try:
    from aigverse import __version__ as version
except ModuleNotFoundError:
    try:
        version = metadata.version("aigverse")
    except ModuleNotFoundError:
        msg = (
            "Package should be installed to produce documentation! "
            "Assuming a modern git archive was used for version discovery."
        )
        warnings.warn(msg, stacklevel=1)

        from setuptools_scm import get_version

        version = get_version(root=str(ROOT), fallback_root=ROOT)

# Filter git details from version
release = version.split("+")[0]

project = "aigverse"
author = "Marcel Walter, Technical University of Munich"
language = "en"
project_copyright = "2025, Marcel Walter, Technical University of Munich"

master_doc = "index"

templates_path = ["_templates"]
html_css_files = ["custom.css"]

extensions = [
    "myst_nb",
    "autoapi.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinxext.opengraph",
    "sphinx.ext.viewcode",
    "sphinxcontrib.inkscapeconverter",
    "breathe",
]

source_suffix = [".rst", ".md"]

exclude_patterns = [
    "_build",
    "**.ipynb_checkpoints",
    "**.jupyter_cache",
    "**jupyter_execute",
    "Thumbs.db",
    ".DS_Store",
    ".env",
    ".venv",
]

pygments_style = "colorful"

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "networkx": ("https://networkx.org/documentation/stable/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
}

myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "substitution",
    "deflist",
    "dollarmath",
]
myst_substitutions = {
    "version": version,
}
myst_heading_anchors = 3
nitpicky = True

# -- Options for {MyST}NB ----------------------------------------------------

nb_execution_mode = "cache"
nb_mime_priority_overrides = [
    # builder name, mime type, priority
    ("latex", "image/svg+xml", 15),
]

copybutton_prompt_text = r"(?:\(\.?venv\) )?(?:\[.*\] )?\$ "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"

modindex_common_prefix = ["aigverse."]

autoapi_dirs = ["../bindings/aigverse"]
autoapi_python_use_implicit_namespaces = True
autoapi_root = "api"
autoapi_add_toctree_entry = False
autoapi_ignore = [
    "*/**/_version.py",
    "*/**/test/*",
]
autoapi_options = [
    "members",
    "imported-members",
    "show-inheritance",
    "special-members",
    "undoc-members",
]
autoapi_keep_files = True
add_module_names = False
toc_object_entries_show_parents = "hide"
python_use_unqualified_type_names = True
napoleon_google_docstring = True
napoleon_numpy_docstring = False


breathe_projects = {"aigverse": "_build/doxygen/xml"}
breathe_default_project = "aigverse"

read_the_docs_build = os.environ.get("READTHEDOCS", None) == "True"
if read_the_docs_build:
    subprocess.call("doxygen", shell=True)  # noqa: S602, S607
    subprocess.call("mkdir api/cpp & breathe-apidoc -o api/cpp -m -f -T _build/doxygen/xml/", shell=True)  # noqa: S602, S607

# -- Options for HTML output -------------------------------------------------
html_theme = "furo"
html_static_path = ["_static"]
html_theme_options = {
    "light_logo": "aigverse_logo_light_mode.svg",
    "dark_logo": "aigverse_logo_dark_mode.svg",
    "source_repository": "https://github.com/marcelwa/aigverse/",
    "source_branch": "main",
    "source_directory": "docs/",
    "navigation_with_keys": True,
}

# -- Options for LaTeX output ------------------------------------------------

numfig = True
numfig_secnum_depth = 0

sd_fontawesome_latex = True
image_converter_args = ["-density", "300"]
latex_engine = "pdflatex"
latex_documents = [
    (
        master_doc,
        "aigverse.tex",
        r"\texttt{aigverse}\\{\Large A Python library for working with logic networks, synthesis, and optimization}",
        r"Marcel Walter\\Technical University of Munich",
        "howto",
        False,
    ),
]
latex_logo = "_static/aigverse_logo_light_mode.svg"
latex_elements = {
    "papersize": "a4paper",
    "releasename": "Version",
    "printindex": r"\footnotesize\raggedright\printindex",
    "tableofcontents": "",
    "sphinxsetup": "iconpackage=fontawesome",
    "extrapackages": r"\usepackage{qrcode,graphicx,calc,amsthm,etoolbox,flushend,mathtools}",
    "preamble": r"""
\patchcmd{\thebibliography}{\addcontentsline{toc}{section}{\refname}}{}{}{}
\DeclarePairedDelimiter\abs{\lvert}{\rvert}
\DeclarePairedDelimiter\mket{\lvert}{\rangle}
\DeclarePairedDelimiter\mbra{\langle}{\rvert}
\DeclareUnicodeCharacter{03C0}{$\pi$}

\newcommand*{\ket}[1]{\ensuremath{\mket{\mkern1mu#1}}}
\newcommand*{\bra}[1]{\ensuremath{\mbra{\mkern1mu#1}}}
\newtheorem{example}{Example}
\clubpenalty=10000
\widowpenalty=10000
\interlinepenalty 10000
\def\subparagraph{} % because IEEE classes don't define this, but titlesec assumes it's present
""",
    "extraclassoptions": r"journal, onecolumn",
    "fvset": r"\fvset{fontsize=\small}",
    "figure_align": "htb",
}
latex_domain_indices = False
latex_docclass = {
    "howto": "IEEEtran",
}
