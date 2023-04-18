Development
===========

If you want to work on req2flatpak, this section helps you get started.

req2flatpak is developed in an open-source, community-driven way,
as a voluntary effort in the authors’ free time.
All contributions are greatly appreciated…
pull requests are welcome, and so are bug reports and suggestions for improvement.


Obtaining the Source Code
-------------------------

req2flatpak's original source code lives in this github repository:
https://github.com/johannesjh/req2flatpak.
You can download the source code by cloning the git repository.


Installing Python
-----------------

Most systems come with python pre-installed.
You can use this python version to develop req2flatpak.

It can be useful to install a specific (older) version of python
to make sure req2flatpak stays compatible with older targeted python versions.

* Python versions targeted by req2flatpak are defined in the ``pyproject.toml`` file.
* You can use `pyenv <https://github.com/pyenv/pyenv>`__
  to install various python versions for use in a virtual environment.
  It is a good practice to install and use the oldest still supported python version
  when developing req2flatpak.


Setting up a Development Environment
------------------------------------

Simply clone/open req2flatpak in the IDE of your choice.
Features and languages that the IDE should ideally support include:

* python
* poetry for managing req2flatpak's dependencies in a virtual environment
* restructured text (``*.rst``) for writing documentation


Installing Dependencies
-----------------------

req2flatpak depends on very few other software packages, as documented in req2flatpak's ``pyproject.toml`` file.
Run ``poetry install`` to install these packages into a python virtual environment.


Running a Development Version
-----------------------------

Have a look at the commands available in req2flatpak's ``makefile``.
These commands show how to run a local req2flatpak development version,
as well as various other development-related tasks.

.. literalinclude:: ../../Makefile
   :language: Makefile
   :dedent:


Understanding the Architecture and Design Goals
------------------------------------------------

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
(other tools like pip-compile and poetry are already good at this).


Modifying and Contributing Code
-------------------------------

You are free to modify req2flatpak as you wish
(under the terms of its very permissive MIT license).
You are very welcome to contribute improvements back to the original req2flatpak.


Running Tests
-------------

Use the ``make test`` command to run automated tests.


Ensuring Code quality
---------------------

Use `pre-commit <https://pre-commit.com/>`__ to prettify and lint the code before committing changes,


.. code:: bash

   # to install pre-commit on your system,
   # follow instructions from https://pre-commit.com/, for example:
   pip install pre-commit  # install pre-commit using pip

   # to install the pre-commit git hooks in the cloned req2flatpak repo
   pre-commit install  # activates pre-commit in the current git repo

   # to prettify and lint all code
   pre-commit run --all

   # to prettify and lint only staged changes
   pre-commit run


If this doesn't work, you can skip specific checks by prepending ``SKIP=<hook-id>`` like so: ``SKIP=poetry-lock git commit``. You can disable all hooks for a commit by using ``git commit -n`` or disable pre-commit entirely for the repository with ``pre-commit uninstall``.
We welcome your contributions even if your workflow differs from what we recommend here.


Updating Dependencies
---------------------

There are three categories of dependencies that can be found in this repository:
*Github Actions*, *Poetry* and *pre-commit hooks*.
Currently there is no programmatic way to update the github actions we depend on.
One has to manually update the commit hashes used.

Poetry dependencies
```````````````````

Poetry differentiates between direct and indirect dependencies.
Direct dependencies are specified in ``pyproject.toml`` -- usually with a fixed version.
Updating these can introduce bugs through breaking changes in the API exposed by
these dependencies. That's why we'll focus on updating indirect dependencies first.
Running the following and committing the resulting changes to ``poetry.lock`` will
do the trick provided that set up *pre-commit* according to this guide.


.. code:: bash

   # 1. Update indirect dependencies (stored in poetry.lock)
   poetry update

   # 2. Stage and commit (runs pre-commit hooks)


Direct dependencies are updated by changing the version specified in ``pyproject.toml``.


.. code:: bash

   # 1. Determine latest version of a package
   pip show packaging

   # 2. Update version requirement in `pyproject.toml`
   # 3. Update `poetry.lock` (`--no-update` will prevent updating indirect dependencies)
   poetry lock --no-update

   # 4. Install newest version (adjust options to your dev env)
   poetry install --with lint --all-extras

   # 5. Stage and commit (runs pre-commit hooks)


Pre-commit hooks
````````````````

Pre-commit hooks require a bit more steps to update because they are partially
synced with the versions specified in ``poetry.lock``.


.. code:: bash

   # 1. Update pre-commit hooks
   pre-commit autoupdate --freeze

   # 2. Stage `.pre-commit-config.yaml`
   git add .pre-commit-config.yaml

   # 3. Sync with poetry
   pre-commit run

   # 4. Remove `frozen: x.x.x` comments for unfrozen dependencies
   # 5. Stage and commit (runs pre-commit hooks)


Publishing a Release
--------------------

Use the following steps to publish a release of req2flatpak:

* Enter the version number to be released in ``pyproject.toml``, e.g., ``version = "1.2.3"``. Commit and push this change to a branch and create a merge request.
* Describe the release in ``docs/source/changelog.rst``. Commit and push the modified changelog in the same branch.
* Verify that the branch builds correctly. Ideally run some manual tests. Optionally tag a release candidate by pushing a tag such as v1.2.3-rc1. If the quality looks good, merge the branch.
* Tag the main branch with the version to be released, e.g., push a tag named ``v1.2.3``.
* Github CI will build the python package and publish it on PyPI.
