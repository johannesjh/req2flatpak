Changelog
=========

..
   This changelog is written by hand.
   Newest releases are added to the top of the file.

v0.5.0 (unreleased)
-------------------

Highlight: req2flatpak can read the target platform from an installed flatpak runtime.

Features:

- ``req2flatpak --platform-info REF`` reads the python version, glibc version, architecture,
  wheel tags and installed python packages from a flatpak runtime, e.g., ``org.gnome.Platform//51``.
  The options ``--user``, ``--system`` and ``--installation`` choose the flatpak installation.
  The runtime can be for another architecture if the system can run it (qemu-user emulation).
  The python API provides ``PlatformFactory.from_flatpak_runtime`` (#99).
- ``--target-platforms`` accepts platform info files in addition to short strings like ``314-x86_64``.
  The python API provides ``PlatformFactory.from_file``.
- The platform info format has the new optional fields ``arch``, ``glibc_version``, ``runtime`` and ``installed_packages``.
  Existing files keep working.
- The new methods ``FlatpakGenerator.write_build_module_as_json`` and ``FlatpakGenerator.write_build_module_as_yaml``
  save a build module to a file or a stream. The commandline interface uses them.
- ``Platform.without_installed(requirements)`` leaves out the requirements that are installed already in the same version.
- The page about the commandline interface now describes the whole workflow, from pinning requirements to including the build module in a manifest.
- The recipes page is dissolved: the commandline interface page (``cli``) and the python API page (``api``) each contain their own how-tos,
  and the new FAQ page answers common questions and links to them.

Fixes:

- Wheel tags for glibc versions newer than 2.35 can be generated, using the new ``manylinux_max`` argument of
  ``PlatformFactory.from_python_version_and_arch`` (#63). The default is unchanged.
- Duplicate platform tags no longer result in ``None`` entries.
- A target platform that cannot be parsed is now an error (exit code 2) instead of being skipped silently.

Improvements for Development:

- CI runs on ubuntu-26.04, the current Ubuntu LTS release.
- Tests that need flatpak (and qemu for aarch64) are skipped if these are not available, e.g., in CI.



v0.4.0 (2026-11-28)
-------------------

Highlight: req2flatpak requires Python 3.11 or newer.


Breaking changes:

- Python 3.8, 3.9 and 3.10 are no longer supported. 
  That's because Python 3.10 reached end-of-life on 2026-10-01 and we upgraded dependencies.
  This applies to the Python that runs req2flatpak. Target platforms can still use other Python versions.
- Refactored assertions to raise a ``ValueError`` instead of an ``AssertionError``.
  As a benefit, the assertions now also work when python runs with ``-O`` optimizations.
- ``FlatpakGenerator.pip_install_template`` is renamed to ``FlatpakGenerator.default_pip_install_template``.
- Made req2flatpak's output compliant to the ``.editorconfig`` settings with two spaces for indentation.
  Specifically, the JSON output is now indented with 2 spaces instead of 4. The YAML output keeps its 2 spaces.
  To change the indentation, use the new ``indent`` argument of ``FlatpakGenerator.build_module_as_str``
  and ``FlatpakGenerator.build_module_as_yaml_str``, or the new ``--indent`` commandline option.
  The ``--indent`` option applies to JSON and YAML, and also to the output of ``--platform-info``.

Fixes:

- A requirement that has neither a matching wheel nor an sdist (for example, only a Windows wheel)
  no longer ends in an obscure ``TypeError`` (#70).
  The commandline interface now stops with a ``ValueError`` that names the package, its version and the platform.
  ``FlatpakGenerator.build_module`` raises a ``ValueError`` if it receives a missing download (``None``).
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



v0.3.2 (2026-11-15)
-------------------

Improvements:

- Relaxed the version constraint for the ``packaging`` dependency from ``^21.3`` to ``>=21.3``, see #92


Fixes:

- Close output stream which was causing empty outfile files on Python 3.14, see #91




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




v0.2 (2023-06-04) "Yaml"
------------------------

Highlight: req2flatpak can now generate yaml output.

Features:

- Adds yaml output.
  It is now possible to generate yaml output by specifying a ``.yaml`` file extension
  or by specifying the ``--yaml`` commandline option.

Bugfixes:

- Fixes sorting when architecture is None - #34
- Fixes exception handling with invalid platforms - #39


v0.1 (2022-12-23) "Initial Release"
-----------------------------------

Highlight: This is the initial release of req2flatpak.

Features:

- Generates a flatpak-builder build module for given python package requirements; the module will install the required packages as part of a flatpak build.
- This initial release already comes with documentation, a clean code style, and automated tests that are run using continuous integration.
