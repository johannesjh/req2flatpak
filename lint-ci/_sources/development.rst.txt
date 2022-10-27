Development
===========

Design Goals
------------

A simple python script, just one file:
req2flatpak is provided as a distribution of just one python module,
i.e., it consists of just a single python file.
This is similar to
`other popular python packages <https://softwareengineering.stackexchange.com/a/243045>`__
like `six <https://pypi.python.org/pypi/six>`__
that also consist of a a single file only.
The benefit is that this file can easily be copy-pasted
as an alternative installation method.

Minimal dependencies:
req2flatpak only needs optional dependencies
(see req2flatpak's ``pyproject.toml`` file for details).
The benefit is that the script runs on a variety of systems.

Do one thing well:
req2flatpak does not resolve dependencies, nor does it freeze aka dependency version.


Setting up a Development Environment
------------------------------------

Simply clone this project in the python IDE of your choice.


Dependencies
------------

req2flatpak depends on very few other software packages, and all of
these dependencies are optional, see ``pyproject.toml``.


Code quality
------------

Use `pre-commit <https://pre-commit.com/>`__ to prettify and lint the
code before committing changes.

.. code:: bash

   # to install pre-commit on your system,
   # follow instructions from https://pre-commit.com/, for example:
   pip install pre-commit  # install pre-commit using pip

   # to install the pre-commit git hooks in the cloned favagtk repo
   pre-commit install  # activates pre-commit in the current git repo

   # to prettify and lint all code
   pre-commit run --all

   # to prettify and lint only staged changes
   pre-commit run
