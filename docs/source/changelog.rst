Changelog
=========

..
   This changelog is written by hand.
   Newest releases are added to the top of the file.

v0.4.0 (2026-11-16)
-------------------

Highlight: req2flatpak requires Python 3.11 or newer.


Breaking changes:

- Python 3.8, 3.9 and 3.10 are no longer supported. 
  That's because Python 3.10 reached end-of-life on 2026-10-01 and we upgraded dependencies.
  This applies to the Python that runs req2flatpak. Target platforms can still use other Python versions.
- Refactored assertions to raise a ``ValueError`` instead of an ``AssertionError``.
  As a benefit, the assertions now also work when python runs with ``-O``.
- ``FlatpakGenerator.pip_install_template`` is renamed to ``FlatpakGenerator.default_pip_install_template``.

Fixes:

- The ``--cache`` option now fills the persistent cache. An empty cache file was replaced by an in-memory dict before, so nothing was ever stored.
- The ``--outfile`` is only created once the output is ready. A failing run no longer leaves an empty file behind.

Documentation improvements:

- New page "Recipes" with tested examples for the Python API.
- Removed the "standalone script" installation option from the installation instructions (#85).
  Install req2flatpak as a python package instead, so that its dependencies are installed too.
- Fixed the customization example in the API guide. 

Improvements for Development:

- ruff now performs additional linting checks, replacing bandit and pydocstyle.
- Type checking is done using ty.
- Updated all dependencies. The pre-commit hooks and CI use the same pinned Poetry version (Poetry 2).
- Updated CI. It now uses actions that run on Node.js 24 and runs on ubuntu-24.04. The devcontainer uses Python 3.11.
- Got rid of the unmaintained documentation dependency ``sphinx-rtd-theme-github-versions``.

Full Changelog: https://github.com/johannesjh/req2flatpak/compare/v0.3.2...v0.4.0


v0.3.2 (2026-11-15)
-------------------

Improvements:

- Relaxed the version constraint for the ``packaging`` dependency from ``^21.3`` to ``>=21.3``, see #92


Fixes:

- Close output stream which was causing empty outfile files on Python 3.14, see #91


Full Changelog: https://github.com/johannesjh/req2flatpak/compare/v0.3.1...v0.3.2


v0.3.1 (2025-03-30) "Python 3.12"
---------------------------------

Highlight: Compatibility with Python 3.12


Improvements for Development:

- Improved CI #73 #79 #82
- Added devcontainers configuration #65
- Now using ruff for linting #87


Fixes:

- Fixed an error when no urls are found in a pypi release in #71


Maintenance and dependency updates:

- Updated dependencies in #62 #74
- Improved docs in #77 #81 #86 
- Now using `packaging` instead of the deprecated `pkg_resources` package #76


Full Changelog: https://github.com/johannesjh/req2flatpak/compare/v0.2...v0.3


v0.2 (2023-06-04) "Yaml"
------------------------

Highlight: req2flatpak can now generate yaml output.

Features:

- Adds yaml output.
  It is now possible to generate yaml output by specifying a ``.yaml`` file extension
  or by specifying the ``--yaml`` commandline option.

Bugfixes:

- Fixes sorting when architecture is None - `#34 <https://github.com/johannesjh/req2flatpak/pull/34>`_
- Fixes exception handling with invalid platforms - `#39 <https://github.com/johannesjh/req2flatpak/pull/39>`_


v0.1 (2022-12-23) "Initial Release"
-----------------------------------

Highlight: This is the initial release of req2flatpak.

Features:

- Generates a flatpak-builder build module for given python package requirements; the module will install the required packages as part of a flatpak build.
- This initial release already comes with documentation, a clean code style, and automated tests that are run using continuous integration.
