Recipes
=======

This documentation page provides recipes for common questions (FAQs).
In other words, it shows how you can use and adapt req2flatpak for specific common needs.
For example, you may prefer source packages over wheels, for all or just some packages.
Or you may need to pass additional options to the pip install command.



Should I use the CLI or the Python API?
---------------------------------------

req2flatpak can be invoked using two ways, 
either through its commandline interface (CLI)
or through its python programming interface (API).

- The commandline interface (CLI, see :doc:`cli`) of req2flatpak is deliberately simple.
  It covers the basic use case and has only a few options.
  This simplicity is on purpose.
  It allows to get started quickly, and for many users that's all they need.

- The python programming interface (API, see :doc:`api`) is powerful and flexible without being complicated.
  It allows to modify data and behavior in a flexible way.

Overall, we recommend using the API because of its higher flexibility.


How do I get started using the CLI?
-----------------------------------

Invoking req2flatpak's CLI is a simple one-liner that you can run in a terminal or in a Makefile.
To get started, your typical workflow has three steps:

#. List the python packages that your application needs in a file ``requirements.in``.
   Use abstract requirements here, such as ``requests>=2.0``.
#. Resolve and pin the requirements, i.e., create a ``requirements.txt`` file
   in which all packages, including their dependencies, have exact versions.
   Use the python version of the flatpak runtime that you build for.
#. Run req2flatpak to generate a build module for flatpak-builder.
   Specify the target platforms, i.e., the python version and the architectures that you build for.

.. code-block:: bash

   # first resolve and pin your requirements, here using uv (other tools work as well, see below):
   uv pip compile requirements.in -o requirements.txt --python-version 3.14

   # then generate a build module for flatpak-builder:
   uvx req2flatpak --requirements-file requirements.txt --target-platforms 314-x86_64 314-aarch64 -o python3-packages.json

The above example code will write ``python3-packages.json``.
This is a json file with instructions for installing all the python packages from your requirements.txt file.
To use this build module in your app, you include it in your app's flatpak build manifest.

For further information about using req2flatpak and its commandline interface, see :doc:`cli`.


How do I get started using the Python API?
------------------------------------------

Using req2flatpak's python API takes a few lines of python code in your build script.
The overall workflow is the same as in the CLI example above:

#. List the python packages that your application needs in a file ``requirements.in``.
   Use abstract requirements here, such as ``requests>=2.0``.
#. Resolve and pin the requirements, i.e., create a ``requirements.txt`` file
   in which all packages, including their dependencies, have exact versions.
   Use the python version of the flatpak runtime that you build for.
#. Run req2flatpak to generate a build module for flatpak-builder.
   Specify the target platforms, i.e., the python version and the architectures that you build for.

The following script generates a build module in five simple steps:
it defines the target platforms,
reads the requirements,
queries PyPI about available downloads,
chooses downloads that are compatible with the target platforms,
and generates the build module.
The script starts with the imports from req2flatpak. The other examples on this page use the same imports, and do not repeat them.

.. literalinclude:: ../../tests/test_getting_started.py
   :start-after: example_getting_started_start
   :end-before: example_getting_started_end
   :language: python
   :dedent:

The python API gives a lot of flexibility because you can change the behavior and modify the data between each step.
The recipes below provide further examples for that.
The same example is explained in more detail in :doc:`api`.
For one example that combines several customizations in a single script,
see :ref:`customization options <Customization>` in the API guide.


.. _pinning-requirements:

What can I do if my requirements are not pinned?
------------------------------------------------

req2flatpak expects every requirement to be pinned to an exact version with ``==``.
It rejects, for example, ``requests>=2.0`` with an error.
This is by design: req2flatpak does not resolve dependencies.

Use another tool to create a fully pinned ``requirements.txt`` first.
Each of the following also includes the dependencies of your dependencies:

.. code-block:: bash

   # pip-tools
   pip-compile requirements.in -o requirements.txt

   # uv
   uv pip compile requirements.in -o requirements.txt

   # poetry (needs the poetry-plugin-export plugin)
   poetry export --without-hashes -o requirements.txt

Then pass the resulting file to req2flatpak.
Make sure that the versions are resolved for the python version of the flatpak runtime, not for your development machine.
For example, ``uv pip compile`` has the option ``--python-version`` for this.


How do I choose the target platform?
------------------------------------

A target platform describes the python and the system on which the packages will be used:
the python version and the system architecture.
req2flatpak uses this to choose downloads that are compatible with it.

The string format is ``<python version>-<architecture>``, for example ``cp314-x86_64`` or ``cp314-aarch64``.
Use the python version of the flatpak runtime, for example 3.14 if the runtime ships python 3.14.
Wheels that are built for another python version typically cannot be installed.

If you build for more than one platform, create one platform object for each platform.
On the commandline, pass the platforms as separate arguments, as in ``--target-platforms cp314-x86_64 cp314-aarch64``.
Do not pass them as one quoted argument.

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_platforms_start
   :end-before: recipe_platforms_end
   :language: python
   :dedent:

If you want to be exact, run ``req2flatpak --platform-info`` on the target system and save the output to a file.
The output contains the python version and the complete list of tags that the system supports.
You can create a platform object from it:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_platform_info_start
   :end-before: recipe_platform_info_end
   :language: python
   :dedent:

Note that ``--platform-info`` describes the system that it runs on.
Run it on, or in an environment that matches, the platform that you are building for.


How do I use source packages instead of binary wheels?
------------------------------------------------------

By default, req2flatpak prefers wheels (prebuilt binary packages) and uses a source package (sdist) only if no suitable wheel exists.
To prefer source packages, choose downloads with ``sdist_or_wheel`` instead of ``wheel_or_sdist``:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_sdist_start
   :end-before: recipe_sdist_end
   :language: python
   :dedent:

Things to keep in mind:

- ``sdist_or_wheel`` falls back to a wheel if a release has no source package.
  Use ``DownloadChooser.sdist`` if you never want a wheel.
  It returns ``None`` if a release has no source package.
- The generated pip command uses ``--no-index`` and ``--no-build-isolation``.
  Packages built from source therefore find their build dependencies
  (for example ``setuptools``, ``wheel`` or ``cython``) only if these are installed already
  or if you add them to your requirements.
- A source package is not specific to an architecture,
  so the same download is used for all target platforms.


How do I use source packages, except for some packages?
-------------------------------------------------------

Some packages are difficult to build from source, for example packages with compiled extensions
that need a compiler, system libraries or a long build time.
You may want source packages for most packages, but binary wheels for these few.

The ``DownloadChooser`` methods used above are not the only way to choose a download.
A download chooser is simply a function that takes a release and a platform and returns one download of this release.
You can write your own function with any logic that you need, and use it instead of ``DownloadChooser.sdist_or_wheel``.
Your function can also call the ``DownloadChooser`` methods.
The following example prefers source packages, except for the packages that are listed in ``install_as_wheel``:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_custom_chooser_start
   :end-before: recipe_custom_chooser_end
   :language: python
   :dedent:

For more complex rules, ``DownloadChooser.downloads(release, platform)`` yields all downloads that are compatible with the platform,
in the order of preference, and you can pick from them as you wish, for example by looking at a download's ``filename``.
See :doc:`api` for details about choosing downloads.


How do I skip packages?
-----------------------

There are several reasons why you may not want req2flatpak to install a package.
For example:

- The flatpak runtime or the base app already provides the package.
  (Check the runtime that your app runs on, not the SDK that it is built in, because the SDK contains more packages.
  The next recipe explains this in more detail.)
- You install the package in another way, for example with a separate flatpak module or an install script of your own.
- You do not need the package in your flatpak, for example because it is only needed for development.

With the commandline interface, remove the packages from the requirements file before you run req2flatpak.
For example, to skip ``jinja2`` and ``markupsafe``:

.. code-block:: bash

   grep -v -i -E '^(jinja2|markupsafe)==' requirements.txt > requirements-flatpak.txt
   uvx req2flatpak --requirements-file requirements-flatpak.txt --target-platforms cp314-x86_64

With the Python API, filter the list of requirements before querying PyPI:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_skip_start
   :end-before: recipe_skip_end
   :language: python
   :dedent:

The filter can use any criterion, and you can also add requirements, for example build dependencies.

Note that req2flatpak installs exactly the packages that are in your list of requirements.
A fully pinned ``requirements.txt`` also lists the dependencies of your packages.
If you skip a package, then check whether you also want to skip its dependencies.


How do I pass additional options to pip, for example ``--ignore-installed``?
----------------------------------------------------------------------------

The generated build module runs ``pip3 install`` with a fixed set of options.
Sometimes you need more options.
A typical example is ``--ignore-installed``,
which makes pip install a package even if a package of the same name is already installed.

If you are using req2flatpak's commandline interface, 
you can add commandline options for the pip install command
by post-processing the build module generated by req2flatpak, 
for example with ``sed``:

.. code-block:: bash

   uvx req2flatpak --requirements-file requirements.txt --target-platforms cp314-x86_64 \
     | sed 's/pip3 install/pip3 install --ignore-installed/' > build-module.json

If you are using the Python API, you can modify the pip install command
as shown in the following example,
by modifying the pip_install_template:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_pip_options_start
   :end-before: recipe_pip_options_end
   :language: python
   :dedent:
