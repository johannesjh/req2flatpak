Installation
============

Installing req2flatpak is easy.
Multiple installation methods are available.


Installing the Python Package
-----------------------------

You can install req2flatpak as a python package.
This is the default and recommended installation method.

For example:

.. code-block:: bash

   pip install req2flatpak
   req2flatpak --help


The first command will install the latest release of req2flatpak.
The second command will display req2flatpak's help,
allowing you to verify that req2flatpak was installed successfully.


.. _running-without-installing:

Running without Installing
--------------------------

You can also run req2flatpak without installing it first.
Tools like `uv <https://docs.astral.sh/uv/>`_ and `pipx <https://pipx.pypa.io/>`_
download req2flatpak into a temporary environment and run it there.
Use the same arguments as you would use for ``req2flatpak``.

For example:

.. code-block:: bash

   uvx req2flatpak --help
   pipx run req2flatpak --help

If you use req2flatpak's python API in a script,
you can declare req2flatpak as a dependency in a header at the top of the script
(see `inline script metadata <https://packaging.python.org/en/latest/specifications/inline-script-metadata/>`_).
When you run the script with ``uv run``, uv installs the declared dependencies first
and then runs the script, so you do not need to install req2flatpak yourself.
For example, this script declares req2flatpak as a dependency, and it generates a build module:

.. literalinclude:: ../../tests/test_getting_started.py
   :start-after: example_getting_started_start
   :end-before: example_getting_started_end
   :language: python
   :dedent:

Save it as ``build_module.py`` and run it:

.. code-block:: bash

   uv run build_module.py

See :doc:`api` for an explanation of this script.


Installing from Git
-------------------

It is possible to install req2flatpak from a git repository.
This installation method is useful if you want to install and test
a new, experimental version of req2flatpak that has not yet been officially released.

To install req2flatpak from a git repository, run this command:

.. code-block:: bash

   pip install git+https://github.com/johannesjh/req2flatpak


The above command will install req2flatpak from the git repository's main branch.

You can, of course, specify other git repositories,
for example in order to install from a forked repository of req2flatpak.
And it is possible to specify specific branches, commits and tags,
see `pip's documentation on VCS support <https://pip.pypa.io/en/stable/topics/vcs-support/>`_.
