Changelog
=========

..
   This changelog is written by hand.
   Newest releases are added to the top of the file.


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
