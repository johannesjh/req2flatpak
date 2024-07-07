"""Sphinx Configuration File."""

# pylint: disable=invalid-name

# =============================================================================
# Project information
# see https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# =============================================================================

project = "req2flatpak"
copyright = "2022-2024, johannesjh"  # pylint: disable=redefined-builtin
author = "johannesjh"
release = "0.2.0"  # TODO: must be kept in-sync with pyproject.toml

# =============================================================================
# General configuration
# see https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# =============================================================================

extensions = []

# automatically generated api docs
extensions += ["sphinx.ext.autodoc"]
extensions += ["sphinx_rtd_theme"]

# automatically generated argparse commandline docs
extensions += ["sphinxarg.ext"]

templates_path = ["_templates"]
exclude_patterns = []  # type: ignore

# =============================================================================
# Options for HTML output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
# =============================================================================

html_theme = "sphinx_rtd_theme_github_versions"
