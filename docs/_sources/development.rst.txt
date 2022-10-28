Development
===========

If you want to work on req2flatpak, this section helps you get started.

req2flatpak is developed in an open-source, community-driven way,
as a voluntary effort in the authors’ free time.
All contributions are greatly appreciated…
pull requests are welcome, and so are bug reports and suggestions for improvement.


Architecture and Design Goals
-----------------------------

req2flatpak's architecture implements the following design goals and design choices.

req2flatpak consists of just a single python file.
This allows req2flatpak to be installed by copy-pasting this file.

req2flatpak is packaged as a python package.
This allows req2flatpak to be installed using pip, poetry, and other similar tools.
Note, single-file python packages are not unusual:
other popular python packages like `six <https://pypi.python.org/pypi/six>`__
also consist of a a single file only,
as explained in this `stackoverflow answer <https://softwareengineering.stackexchange.com/a/243045>`__.

req2flatpak requires minimal dependencies.
The benefit is that req2flatpak runs on a variety of systems.
Optional dependencies are declared in req2flatpak's ``pyproject.toml`` file.

req2flatpak aims to do one thing well.
Its focus is on generating flatpak-builder build modules
for installing required python packages in a flatpak package.
Other functionality is intentionally not included in req2flatpak,
particularly if it would increase the code size or require additional dependencies.
For example, req2flatpak does not resolve dependencies, nor does it freeze dependency versions
(other tools like pip, pip-compile and poetry can be used for this).


Obtaining the Source Code
-------------------------

req2flatpak's original source code lives in this github repository:
https://github.com/johannesjh/req2flatpak

You can download the source code by cloning the git repository.


Setting up a Development Environment
------------------------------------

Simply clone/open req2flatpak in the IDE of your choice.

Features and languages that the IDE should ideally support:
* python
* poetry for managing req2flatpak's dependencies in a virtual environment
* restructured text (``*.rst``) for writing documentation


Dependencies
------------

req2flatpak depends on very few other software packages,
as documented in req2flatpak's ``pyproject.toml`` file.


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
