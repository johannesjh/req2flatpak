Using the Commandline Interface
===============================

You can invoke req2flatpak’s commandline interface like this:

.. code:: bash

   ./req2flatpak.py --requirements-file requirements.txt --target-platforms 310-x86_64 310-aarch64

Target platform strings are defined as ``<pythonversion>-<architecture>`` and accept the following values:

-  Python versions are specified as ``29`` for cpython 2.9 or ``310``
   for cpython 3.10, and so on.
-  System architectures can either be ``x86_64`` or ``aarch64``.

When invoked like this, req2flatpak will read the requirements file,
query pypi about available downloads, choose appropriate downloads for
the specified target platforms, and generate a flatpak-builder build
module.

Note that req2flatpak will not resolve transitive dependencies or freeze
dependency versions. Use other tools like
`pip-compile <https://pypi.org/project/pip-tools/>`__ or
`poetry <https://pypi.org/project/poetry/>`__ for this purpose and
generate/export a fully resolved requirements.txt file using these
tools.

Run ``req2flatpak.py --help`` to learn more about available commandline
options.