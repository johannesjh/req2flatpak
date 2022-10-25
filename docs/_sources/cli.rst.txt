Using the Commandline Interface
===============================

req2flatpak comes with a simple commandline interface
that covers basic usage
and makes it easy to get started.


Example
-------

You can, for example, invoke req2flatpak’s commandline interface like this:

.. code:: bash

   ./req2flatpak.py --requirements-file requirements.txt --target-platforms cp310-x86_64 cp310-aarch64

When invoked like this, req2flatpak will read the requirements file,
query pypi about available downloads, choose appropriate downloads for
the specified target platforms, and generate a flatpak-builder build
module.


Specifying Python Package Requirements
--------------------------------------

You can specify python packages as individual commandline arguments or by providing a ``requirements.txt`` file.
As a result, req2flatpak will include these packages in the generated build manifest.

It is important to note that req2flatpak expects all package versions to be fully specified.
For example, req2flatpak will not accept a package version specification such as ``requests >= 2.0``.
Instead, req2flatpak expects all versions to be pinned using the ``==`` operator, such as, e.g., s``requests == 2.0``.

The reason for this is that req2flatpak, by design, does not resolve or freeze dependencies.
You can use other tools like
`pip-compile <https://pypi.org/project/pip-tools/>`__ or
`poetry export <https://pypi.org/project/poetry/>`__
to resolve and freeze dependencies and to export them into a requirements.txt file.


Specifying Target Platforms
---------------------------

One or more target platforms can be specified in a simple string format
that includes the python version and system architecture.

As a result, req2flatpak will include suitable package downloads
for each of the specified target platforms
in the flatpak builder manifest that it generates.

The string format for specifying target platforms is ``<python_version>-<system-architecture>``:

- The python version is specified as, e.g., ``cp39`` for cpython 3.9 or ``cp310`` for cpython 3.10, and so on.
  Other python interpreters instead of cpython are not supported.
- The system architecture can either be ``x86_64`` or ``aarch64``.


Commandline Options
-------------------

.. argparse::
   :ref: req2flatpak.cli_parser
   :prog: req2flatpak
   :nodescription:
