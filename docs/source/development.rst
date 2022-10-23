Development
===========

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
