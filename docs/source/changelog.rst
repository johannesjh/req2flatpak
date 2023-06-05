Changelog
=========

..
   This changelog is written by hand.
   Newest releases are added to the top of the file.


v0.2 (2023-06-05) "Yaml"
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
