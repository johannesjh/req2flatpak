Using the Commandline Interface
===============================

req2flatpak comes with a simple commandline interface
that covers basic usage
and makes it easy to get started.


Example
-------

You can, for example, invoke req2flatpak’s commandline interface like this:

.. code:: bash

   req2flatpak --requirements-file requirements.txt --target-platforms cp314-x86_64 cp314-aarch64

When invoked like this, req2flatpak will read the requirements file,
query pypi about available downloads, choose appropriate downloads for
the specified target platforms, and generate a flatpak-builder build
module.


Documentation of Commandline Options
------------------------------------

req2flatpak's commandline interface supports the following commands and options.

.. argparse::
   :ref: req2flatpak.cli_parser
   :prog: req2flatpak
   :nodescription:



Specifying Python Package Requirements
--------------------------------------

You can specify python packages as individual commandline arguments or by providing a ``requirements.txt`` file.
As a result, req2flatpak will include these packages in the generated build module.

It is important to note that req2flatpak expects all package versions to be fully specified.
For example, req2flatpak will not accept a package version specification such as ``requests >= 2.0``.
Instead, req2flatpak expects all versions to be pinned using the ``==`` operator, such as, e.g., ``requests == 2.0``.

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
in the flatpak-builder build module that it generates.

The string format for specifying target platforms is ``<python_version>-<system-architecture>``:

- The python version is specified as, e.g., ``cp313`` for cpython 3.13 or ``cp314`` for cpython 3.14, and so on.
  Other python interpreters instead of cpython are not supported.
- The system architecture can either be ``x86_64`` or ``aarch64``.


Querying Information about the Current Platform
-----------------------------------------------

req2flatpak provides a ``platform-info`` command for querying information
about the current platform, i.e., about the python interpreter and system
architecture used to run the req2flatpak script.

You can run the ``platform-info`` command on your target platform to save
information about this platform. You can later use the information about your
target platform when generating a flatpak build module using req2flatpak's
python apis by reading the platform information from a file and by creating
a platform object from it.

Example:

.. code:: bash

   req2flatpak --platform-info


This will generate output like this:

.. code:: json

   {
       "python_version": [
   	"3",
   	"14",
   	"0"
       ],
       "python_tags": [
   	"cp314-cp314-manylinux_2_41_x86_64",
   	"cp314-cp314-manylinux_2_40_x86_64",
   	"cp314-cp314-manylinux_2_39_x86_64",
   	"..."
       ]
   }


\...note that the list of tags has been shortened in the above output
because the list of tags is about 700 lines long.


Querying Installed Python Packages
----------------------------------

req2flatpak provides a command ``installed-packages`` which allows to  query
currently installed python packages.

You can run the ``installed-packages`` command on your target platform to find
out which packages are already installed on this platform. You can later use
this information when resolving and pinning python packages in your python
application or library, e.g., when using pip, pip-compile or poetry, in order
to make sure that your package versions are compatible with your target platform.
