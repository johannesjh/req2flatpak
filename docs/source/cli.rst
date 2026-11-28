Commandline Interface (CLI)
===========================

req2flatpak comes with a simple commandline interface
that covers basic usage
and makes it easy to get started.
For more flexibility, we recommend using the python API instead,
see :doc:`api`.
With the python API, a script can automate several of the steps below,
for example reading the platform from the runtime and generating the build module.

This page describes how to use req2flatpak for a flatpak app,
from your requirements to the build module in your manifest:

#. Resolve and pin the requirements.
#. Specify the target platform, preferably by reading it from the flatpak runtime.
#. Generate the build module.
#. Include the build module in your manifest.
#. Update when a new runtime is released.


.. _pinning-requirements:

1. Resolve and pin the requirements
-----------------------------------

req2flatpak does not resolve dependencies.
Before you run it, you need a list of requirements
in which every package, including the dependencies of your dependencies,
is pinned to its exact version, as in ``package==version``.
req2flatpak does not accept a version specification such as ``requests >= 2.0``.
Resolve the versions for the python version of the runtime that you build for,
not for your development machine.

You can use any tool that does this, for example uv, pip-tools or poetry.
As an example, the following uv command resolves ``requirements.in``,
a file with your direct and unpinned dependencies,
into a pinned ``requirements.txt`` for python 3.14.
The other tools work as well:

.. code-block:: bash

   # uv
   uv pip compile requirements.in -o requirements.txt --python-version 3.14

   # pip-tools
   pip-compile requirements.in -o requirements.txt

   # poetry (needs the poetry-plugin-export plugin)
   poetry export --without-hashes -o requirements.txt

All of these also include the dependencies of your dependencies.

We recommend to check the pinned requirements into your repository.
Then your app is built with the same package versions every time,
until you decide to update them.

req2flatpak reads the pinned requirements from a ``requirements.txt`` file,
which you specify using ``--requirements-file`` (``-r``).
Use ``-r -`` to read the file from standard input.
You can also specify individual packages using ``--requirements``,
for example ``--requirements 'requests==2.0' 'idna==3.7'``.


.. _choose-target-platform:

2. Specify the target platform
------------------------------

The target platform describes the system on which the python packages will be used:
the python version, the system architecture and the wheel tags that the system supports.
req2flatpak uses it to choose downloads that are compatible with this system.
Use the python version of the flatpak runtime that your app runs on.
There are three ways to specify a target platform.
You pass the result to req2flatpak in the next step, using the option ``--target-platforms`` (``-t``).
Create one target platform for each architecture that you build for.


.. _cli-platform-from-runtime:

From a flatpak runtime
^^^^^^^^^^^^^^^^^^^^^^

This is the most exact way, and it is what we recommend.
req2flatpak can read the python version, the wheel tags and the python packages
from an installed runtime and save them to a platform info file.
For this, run ``req2flatpak --platform-info REF``, where ``REF`` is the ref of the runtime.
The runtime must be installed already.
The ref has the form ``NAME/ARCH/BRANCH``, where an empty ``ARCH`` is the architecture of this machine.
The options ``--user``, ``--system`` and ``--installation`` choose the flatpak installation;
they are required if the runtime is installed in more than one.

As an example, the following commands install the GNOME runtime in branch ``51``
and read its platform information:

.. code-block:: bash

   flatpak install --user flathub org.gnome.Platform//51
   req2flatpak --platform-info org.gnome.Platform//51 --user -o org.gnome.Platform-51-x86_64.platforminfo.json

To read the platform for another architecture than the one of your machine,
for example aarch64 on an x86_64 machine, install the runtime for this architecture as well.
Your machine must be able to run programs of the other architecture, which needs an emulator.
Without an emulator, req2flatpak stops with an error (flatpak reports ``Exec format error``).

As an example, on Ubuntu and Debian the package ``qemu-user-binfmt`` provides such an emulator.
After installing it, you can, for example, read the platform of the aarch64 runtime, even if you are on an x86 machine:

.. code-block:: bash

   sudo apt install qemu-user-binfmt
   flatpak install --user flathub org.gnome.Platform/aarch64/51
   req2flatpak --platform-info org.gnome.Platform/aarch64/51 --user -o org.gnome.Platform-51-aarch64.platforminfo.json

If the runtime does not provide the ``packaging`` package
(neither directly nor in ``setuptools`` or ``pip``),
then the tags cannot be read from the runtime.
req2flatpak then derives the tags from the glibc version of the runtime and logs a warning.
req2flatpak only supports runtimes with CPython and glibc.

Without an argument, ``--platform-info`` describes the current platform instead,
i.e., the python interpreter and system architecture used to run the req2flatpak script.


.. _cli-platform-from-file:

From a platform info file
^^^^^^^^^^^^^^^^^^^^^^^^^

A platform info file contains the python version, the wheel tags and the python packages of a runtime,
and it describes exactly one architecture.
The previous section creates such files.
To use one, pass it as target platform, for example ``-t org.gnome.Platform-51-x86_64.platforminfo.json``.
A name is treated as a file if the file exists or if it ends with ``.json``, ``.yaml`` or ``.yml``.
YAML files can only be read if the ``pyyaml`` package is installed.

A platform info file looks like this:

.. code:: json

   {
     "python_version": ["3", "14", "9"],
     "python_tags": [
       "cp314-cp314-manylinux_2_44_x86_64",
       "cp314-cp314-manylinux_2_43_x86_64",
       "..."
     ],
     "arch": "x86_64",
     "glibc_version": "2.44",
     "runtime": "org.gnome.Platform//51",
     "installed_packages": {"jinja2": "3.1.6", "packaging": "26.3"}
   }

\...note that the list of tags has been shortened in the above output
because the list of tags is more than a thousand lines long.
The fields ``arch``, ``glibc_version``, ``runtime`` and ``installed_packages``
are only present if they are known.
Python packages that the runtime provides are listed with their normalized names.

We recommend to check the platform info files into your repository.
Then the platform information does not need to be re-generated every time that you run req2flatpak,
and your build does not need the runtime to be installed.


.. _cli-platform-from-string:

As a string
^^^^^^^^^^^

The quickest way for specifying the target platform is a simple string format, ``<python_version>-<architecture>``:

- The python version is specified as, e.g., ``cp313`` for cpython 3.13 or ``cp314`` for cpython 3.14, and so on.
  The prefix ``cp`` is optional, so ``314-x86_64`` works as well.
  Only cpython is supported.
- The system architecture can either be ``x86_64`` or ``aarch64``.

To specify several platforms, list them after ``-t``, separated by spaces, 
as in, for example, ``-t 314-x86_64 314-aarch64``.

Note that such a platform is an approximation:
req2flatpak will approximatly estimate the platform tags that the target platform likely supports.


.. _cli-generate-build-module:

3. Generate the build module
----------------------------

Run req2flatpak with your requirements and your target platforms.
req2flatpak queries PyPI about available downloads,
chooses suitable downloads for each of the target platforms,
and generates a flatpak-builder build module.
The option ``-o`` writes the build module to a file.

As an example, the following command uses the two platform info files from the previous step
and writes the build module to ``python3-packages.json``:

.. code-block:: bash

   req2flatpak -r requirements.txt \
     -t org.gnome.Platform-51-x86_64.platforminfo.json org.gnome.Platform-51-aarch64.platforminfo.json \
     -o python3-packages.json

Note that the commandline interface installs all packages of your requirements file,
including packages that the runtime provides already.
It does not filter them out automatically.
To leave them out, see :ref:`cli-skip-packages`.

We recommend to check the generated build module into your repository.
Then the flatpak build of your app does not need to run req2flatpak
(and does not need to query PyPI), which speeds up the builds.
It is also required if you publish your app on Flathub,
because Flathub requires static flatpak build manifests.



4. Include the build module in your manifest
--------------------------------------------

Add the generated ``python3-packages.json`` to the ``modules`` of your flatpak-builder manifest.
For example, in a YAML manifest:

.. code-block:: yaml

   modules:
     - python3-packages.json
     - name: my-app
       buildsystem: simple
       # ...


5. Update when a new runtime is released
----------------------------------------

When your app moves to a new runtime version,
repeat steps 1 to 4 for the new runtime:
resolve and pin the requirements for the python version of the new runtime,
specify the target platform for the new runtime (read its platform info),
generate the build module again, and update the manifest if necessary.
Check the updated files into your repository.

For example, if your app moves from the GNOME runtime 51 to a newer branch,
install the new runtime and run ``req2flatpak --platform-info`` for its ref.
Replace the old platform info files in your repository with the new ones.


.. _cli-tips:

Tips
----

.. _cli-skip-packages:

Skipping packages
^^^^^^^^^^^^^^^^^

There are several reasons why you may not want req2flatpak to install a package.
For example, the flatpak runtime or the base app already provides it,
you install it in another way, or you do not need it in your flatpak.
(Check the runtime that your app runs on, not the SDK that it is built in, because the SDK contains more packages.)

req2flatpak installs exactly the packages that are in your requirements.
Remove the packages from the requirements file before you run req2flatpak.
For example, to skip ``jinja2`` and ``markupsafe``:

.. code-block:: bash

   grep -v -i -E '^(jinja2|markupsafe)==' requirements.txt > requirements-flatpak.txt
   req2flatpak -r requirements-flatpak.txt -t org.gnome.Platform-51-x86_64.platforminfo.json

A fully pinned ``requirements.txt`` also lists the dependencies of your packages.
If you skip a package, then check whether you also want to skip its dependencies.


.. _cli-pip-options:

Passing additional options to pip
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The generated build module runs ``pip3 install`` with a fixed set of options.
Sometimes you need more options.
A typical example is ``--ignore-installed``,
which makes pip install a package even if a package of the same name is already installed.
The commandline interface has no option for this,
but you can post-process the generated build module, for example with ``sed``:

.. code-block:: bash

   req2flatpak -r requirements.txt -t org.gnome.Platform-51-x86_64.platforminfo.json \
     | sed 's/pip3 install/pip3 install --ignore-installed/' > python3-packages.json


Documentation of Commandline Options
------------------------------------

req2flatpak's commandline interface supports the following options.

.. argparse::
   :ref: req2flatpak.cli_parser
   :prog: req2flatpak
   :nodescription:
