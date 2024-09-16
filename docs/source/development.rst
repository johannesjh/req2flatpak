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

Clone the req2flatpak git repository in the IDE of your choice.
Features and languages that the IDE should ideally support include:

* python,
* poetry (for managing req2flatpak's dependencies in a virtual environment),
* devcontainers (optionally, for working inside a docker image instead of your local system), as well as
* restructured text (optionally, for writing documentation).


Install poetry and pre-commit using the python installer of your choice, 
e.g., by running ``pipx install poetry`` and ``pipx install pre-commit``.

Run ``poetry install --with lint --with docs --all-extras``.
This will install all the python packages you need into a python virtual environment.

Run ``pre-commit install``.
This will initialize pre-commit in your local development repository.


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
   pipx install pre-commit

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

There are multiple categories of dependencies that can be found in this repository:
CI, Poetry and pre-commit hooks.

CI dependencies
```````````````

Github actions and workflows contain hardcoded versions of container images and packages.
See the ``.github`` folder.
Currently there is no programmatic way to update the github actions we depend on.
One has to manually update the versions and/or commit hashes.

The devcontainer configuration file also contains versions,
these are also manually kept up-to-date.
See the ``.devcontainer`` folder.


Poetry and pre-commit dependencies
``````````````````````````````````

First update poetry dependencies, 

#. Manually bump the version constraints in the ``pyproject.toml`` file.
#. Run ``poetry update --with lint`` to update installed packages and write the lock file.
#. Stage changes by running ``git add pyproject.toml poetry.lock``.


Then update pre-commit dependencies,

#. Run ``pre-commit install`` just to be sure that pre-commit is properly initialized.
#. Run ``pre-commit autoupdate --freeze`` to update pre-commit's packages.
#. Stage changes by running ``git add .pre-commit-config.yaml``.
#. Run ``pre-commit run`` to sync package versions from poetry to pre-commit. Note that this is a one-way-sync, i.e., `sync_with_poetry <https://github.com/floatingpurr/sync_with_poetry>`_ will copy package versions from the poetry lock file into the pre-commit yaml file.
#. Stage changes by running ``git add .pre-commit-config.yaml``.
#. run ``pre-commit run`` to verify that pre-commit now happily leaves all files unchanged.
#. Stage and commit all changes.


Publishing a Release
--------------------

Use the following steps to publish a release of req2flatpak:

* Enter the version number to be released in ``pyproject.toml``, e.g., ``version = "1.2.3"``. Commit and push this change to a branch and create a merge request.

* Describe the release in ``docs/source/changelog.rst``. Commit and push the modified changelog in the same branch.

* Verify that the branch builds correctly. Ideally run some manual tests. Optionally tag a release candidate by pushing a tag such as v1.2.3-rc1. If the quality looks good, merge the branch.

* Tag the main branch with the version to be released, e.g., push a tag named ``v1.2.3``.

* Github CI will build the python package and publish it on PyPI.
