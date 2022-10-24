"""Sphinx Configuration File."""


# =============================================================================
# Project information
# see https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# =============================================================================

project = "req2flatpak"
copyright = "2022, johannesjh"
author = "johannesjh"
release = "0.0.1"


# =============================================================================
# Path to source files
# =============================================================================

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))


# =============================================================================
# General configuration
# see https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# =============================================================================

extensions = []

# automatically generated api docs
extensions += ["sphinx.ext.autodoc"]

# automatically generated argparse commandline docs
extensions += ["sphinxarg.ext"]

templates_path = ["_templates"]
exclude_patterns = []


# =============================================================================
# Options for HTML output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# =============================================================================

# html_theme = "sphinx_rtd_theme_github_versions"
# html_static_path = ["_static"]
