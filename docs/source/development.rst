Development
===========

If you want to work on req2flatpak, this section helps you get started.

req2flatpak is developed in an open-source, community-driven way,
as a voluntary effort in the authors’ free time.
All contributions are greatly appreciated…
pull requests are welcome, and so are bug reports and suggestions for improvement.


Obtaining the Source Code
-------------------------

req2flatpak's source code lives in this github repository:
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
CI and the pre-commit hooks pin a Poetry version (see ``.github/actions/setup`` and ``.pre-commit-config.yaml``),
so it is best to use the same version. A different Poetry version may rewrite the lock file.

Run ``poetry install --with lint --with docs --all-extras``.
This will install all the python packages you need into a python virtual environment.

Run ``pre-commit install``.
This will initialize pre-commit in your local development repository.


Running a Development Version
-----------------------------

Have a look at the commands available in req2flatpak's ``Makefile``.
These commands show how to run a local req2flatpak development version,
as well as various other development-related tasks.

.. literalinclude:: ../../Makefile
   :language: Makefile
   :dedent:


Understanding the Architecture and Design Goals
------------------------------------------------

req2flatpak's architecture implements the following design goals and design choices.

req2flatpak consists of just a single python file.
The probe that reads the platform from a flatpak runtime is therefore a function inside this file:
only the source code of this function is sent to the runtime, and it runs there
with the python of the runtime, using nothing but the standard library.

req2flatpak is packaged as a python package.
This allows req2flatpak to be installed using pip, poetry, and other similar tools.
Note, single-file python packages are not unusual:
other popular python packages like `six <https://pypi.python.org/pypi/six>`__
also consist of a single file only,
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
Most tests run without flatpak installed.
Only the tests in the directory ``tests_flatpak`` need flatpak and the GNOME 51 runtime;
they are skipped if these are missing.
Use ``make test-no-flatpak`` to run all other tests, without these.
CI runs ``make test-no-flatpak``.


Recording Reference Data
------------------------

The file ``tests/org.gnome.Platform-51-x86_64.platforminfo.json`` is an example of a platform info file
that was read from a real flatpak runtime. It is used by tests and in the documentation.
Record it once by hand, with the runtime installed, and check it in.
The recorded file lists more than a thousand wheel tags.
To keep the example small, shorten the list of tags by hand to a few representative ones,
for example the ``cp314`` tags for ``manylinux_2_44`` and ``manylinux_2_17``, and ``py3-none-any``.

.. code:: bash

   flatpak install --user flathub org.gnome.Platform//51
   req2flatpak --platform-info org.gnome.Platform//51 --user -o tests/org.gnome.Platform-51-x86_64.platforminfo.json

Recording the same data for aarch64 on an x86_64 machine
needs the aarch64 runtime and an emulation of the architecture, e.g., the package ``qemu-user-binfmt``
(on Ubuntu or Debian). Without it, flatpak fails with ``Exec format error``.

.. code:: bash

   flatpak install --user flathub org.gnome.Platform/aarch64/51
   req2flatpak --platform-info org.gnome.Platform/aarch64/51 --user -o tests/org.gnome.Platform-51-aarch64.platforminfo.json

Name the files ``<runtime>-<version>-<architecture>.platforminfo.json``.
The file names of the regression test of the platform tags start with ``cp3`` or ``py3``
(for example ``cp310-x86_64.platforminfo.json``), so do not start the name of a recorded file like this.


Ensuring Code quality
---------------------

Use `pre-commit <https://pre-commit.com/>`__ to prettify and lint the code before committing changes:


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


The hooks run ruff (linting and formatting, including rules for docstrings, import order,
python syntax upgrades and security issues) and ty (type checking) on the python files,
and prettier, rstcheck and Poetry checks on the other files.

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
CI installs a pinned Poetry version (see ``.github/actions/setup``),
update it together with the Poetry hooks in ``.pre-commit-config.yaml``.

The devcontainer configuration file also contains versions,
these are also manually kept up-to-date.
See the ``.devcontainer`` folder.


Poetry and pre-commit dependencies
``````````````````````````````````

The constraints in the ``pyproject.toml`` file follow a strategy that is explained in comments there:
runtime dependencies keep their lower bounds as low as the code allows and the lock file resolves to the newest releases,
whereas development tools (ruff and ty) are pinned tightly and bumped deliberately.
ty is a beta tool, so check every ty update for new findings.
Sphinx is limited to the newest major version that still supports our lowest supported python version.

First, update the poetry dependencies:

#. Manually bump the version constraints in the ``pyproject.toml`` file.
#. Run ``poetry update --with docs`` to update installed packages (including the optional docs group) and write the lock file.
#. Stage changes by running ``git add pyproject.toml poetry.lock``.


Then, update the pre-commit dependencies:

#. Run ``pre-commit install`` just to be sure that pre-commit is properly initialized.
#. Run ``pre-commit autoupdate --freeze`` to update pre-commit's packages.
#. Stage changes by running ``git add .pre-commit-config.yaml``.
#. Run ``pre-commit run`` to sync package versions from poetry to pre-commit. Note that this is a one-way-sync, i.e., `sync_with_poetry <https://github.com/floatingpurr/sync_with_poetry>`_ will copy package versions from the poetry lock file into the pre-commit yaml file.
#. Stage changes by running ``git add .pre-commit-config.yaml``.
#. run ``pre-commit run`` to verify that pre-commit now happily leaves all files unchanged.
#. Stage and commit all changes.


Publishing the Documentation
----------------------------

CI builds the documentation on every push and publishes it to the ``gh-pages`` branch (GitHub Pages)
for the ``main`` branch, for tags, and for branches whose name starts with ``doc``.
Each ref is published in its own directory, e.g., ``main``, ``v0.3.2``, or the branch name.
Directories that are already on ``gh-pages`` are kept.

The version switcher in the documentation is a template, ``docs/source/_templates/layout.html``.
It reads ``versions.txt`` from the root of ``gh-pages``,
which ``.github/scripts/write_versions.py`` regenerates at every publish:
all directories on ``gh-pages``, ``main`` first, then the tags with the newest first, then the rest.
To remove a preview of a branch, delete its directory from ``gh-pages``.


Publishing a Release
--------------------

Use the following steps to publish a release of req2flatpak:

* Enter the version number to be released in ``pyproject.toml``, e.g., ``version = "1.2.3"``. Commit and push this change to a branch and create a merge request.

* Describe the release in ``docs/source/changelog.rst``. Commit and push the modified changelog in the same branch.

* Verify that the branch builds correctly. Ideally run some manual tests. If the quality looks good, merge the branch.

* Before tagging, check on GitHub (tab Actions) that the CI workflow is enabled.
  GitHub automatically disables workflows in repositories without activity for some time (the workflow state is ``disabled_inactivity``).
  A disabled workflow ignores pushes and tags, so nothing would be built or published.
  Enable the workflow again if needed, and run it manually on the main branch to check that it passes.

* Tag the main branch with the version to be released, e.g., push a tag named ``v1.2.3``.
  Do not push tags for release candidates or for testing:
  CI builds and publishes every tag that starts with ``v`` to PyPI, using the version from ``pyproject.toml``,
  and a version that has been uploaded to PyPI can never be uploaded again.

* Github CI will build the python package and publish it on PyPI.
