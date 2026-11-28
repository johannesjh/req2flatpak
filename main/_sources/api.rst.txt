Python API
==========

You can use req2flatpak's python api to write a custom python script that makes use of req2flatpak's functionality.
This lets you programmatically tweak and tune the behavior as needed.


Example
-------

You can use the following code as an example to get started with your script.
The code demonstrates how to generate a flatpak-builder build module
in order to install python packages on a specific flatpak target platform.

.. literalinclude:: ../../tests/test_getting_started.py
   :start-after: example_getting_started_start
   :end-before: example_getting_started_end
   :language: python
   :dedent:

The code starts with a header that declares req2flatpak as a dependency,
so that you can run the script with ``uv run``, which installs req2flatpak automatically.
It continues with the imports from req2flatpak that you need.
It then uses req2flatpak to generate a build module in five steps:

#. define the target platforms,
#. specify the python packages to be installed,
#. query PyPI about available downloads,
#. choose downloads that are compatible with the target platforms,
#. generate the flatpak-builder build module and save it to a file.

...if you include the resulting build module in a flatpak build,
the module will install the required packages.


Using the python API has the benefit that you can modify and tweak the behavior in a very flexible way.
E.g., in each step in the above script, you could modify or tweak the data and/or invocations.
For further details, see section :ref:`Customization`
and the sections below.

The following sections explain in detail how you can use req2flatpak's python api in your custom script.
For further inspiration you can also have a look at how req2flatpak's :py:meth:`~req2flatpak.main` method is implemented.



Specifying Target Platforms
---------------------------

A target platform describes everything that pip (or req2flatpak) needs to know
when choosing package downloads to install on this platform.

Platforms
^^^^^^^^^

Target platforms are represented in req2flatpak as a dataclass, as follows.

.. currentmodule:: req2flatpak

.. autoclass:: Platform
   :members:
   :undoc-members:

There are many options how to create platform objects.
You can create platform objects any way you wish in your script.
And you can use functionality from req2flatpak, as described below.


PlatformFactory
^^^^^^^^^^^^^^^

The PlatformFactory provides methods for creating platform objects.

For example:

.. literalinclude:: ../../tests/test_platform_factory.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


.. _api-choose-target-platform:

There are three ways to specify a target platform with the ``PlatformFactory``.
Use the python version of the flatpak runtime, for example 3.14 if the runtime ships python 3.14.
Wheels that are built for another python version typically cannot be installed.
If you build for more than one platform, create one platform object for each platform.

**From a platform string.**
The quickest way is a platform string in the format ``<python version>-<architecture>``,
for example ``cp314-x86_64`` or ``cp314-aarch64``.
Such a platform is an approximation:
req2flatpak estimates the wheel tags that the system supports,
and the platform does not know which python packages are installed on the system.

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_platforms_start
   :end-before: recipe_platforms_end
   :language: python
   :dedent:

.. _api-manylinux-max:

The estimated tags cover glibc versions up to 2.35 by default.
If the target platform has a newer glibc, set ``manylinux_max`` as shown above.
Reading the platform from a runtime (next) avoids estimating.

**From a flatpak runtime.**
To be exact, read the platform from the flatpak runtime that you build for.
The runtime must be installed already.
req2flatpak runs a small probe inside the runtime,
which reads the python version, the glibc version, the wheel tags
and the python packages that the runtime provides.
The ref of the runtime has the form ``NAME/ARCH/BRANCH``,
where an empty ``ARCH`` means the architecture of this machine.

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_flatpak_runtime_start
   :end-before: The platform knows
   :language: python
   :dedent:

**From a platform info file.**
A platform that was read from a runtime can be saved to a platform info file
(``req2flatpak --platform-info REF``, see :doc:`cli`),
which you can check into your repository.
Then your build does not need the runtime to be installed:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_platform_info_start
   :end-before: recipe_platform_info_end
   :language: python
   :dedent:

For reproducible and exact results, read the platform from the runtime once,
save it to a platform info file, and use this file as target platform.
Use a platform string if you only want to try something out quickly.


Documentation of all methods provided by the ``PlatformFactory`` class:

.. autoclass:: PlatformFactory
   :members:

.. autoexception:: PlatformProbeError


.. _api-requirements:

Specifying Package Requirements
-------------------------------

A requirement describes the name and exact version of a python package that shall be installed.

To provide some context, there are many options for how you may want to manage requirements in your projects.
You will most likely want to use additional tools such as poetry or pip-compile in addition to req2flatpak.
The reason for this is that req2flatpak, by design, does not resolve or freeze dependencies.
In other words, req2flatpak does not resolve or freeze abstract requirement specifications (such as, e.g., ``packaging >= 24.1``) to specific version numbers (such as, e.g., ``packaging==24.2``).
Instead, you need to provide specific ("frozen") version numbers to req2flatpak. 
You can use tools such 
`pip-compile <https://pypi.org/project/pip-tools/>`__ or
`poetry export <https://pypi.org/project/poetry-plugin-export/>`__
(or ``uv pip compile``)
to resolve and freeze dependencies and to export them into a requirements.txt file.
Resolve the versions for the python version of the flatpak runtime, not for your development machine,
for example with the option ``--python-version`` of ``uv pip compile``.
This is where req2flatpak comes into play. 
It can read your requirements.txt file and convert it into a flatpak-builder build module.
  

Requirements
^^^^^^^^^^^^

Package requirements are represented in req2flatpak as a dataclass, as follows:

.. autoclass:: Requirement
   :members:
   :undoc-members:


RequirementsParser
^^^^^^^^^^^^^^^^^^

There are many options for how to create a requirement object in your code.
One option is to use methods from req2flatpak's ``RequirementsParser`` class,
as in the following example:

.. literalinclude:: ../../tests/test_requirements_parser.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


Documentation of all methods provided by the ``RequirementsParser`` class:

.. autoclass:: RequirementsParser
   :members:


It is important to note that req2flatpak's ``RequirementsParser`` expects all package versions to be fully specified.
For example, it will not accept a package version specification such as ``requests >= 2.0``.
Instead, it expects all versions to be pinned using the ``==`` operator, such as, e.g., ``requests == 2.0``.
Otherwise, it raises an error.

.. _api-skip-packages:

Skipping packages
^^^^^^^^^^^^^^^^^

There are several reasons why you may not want req2flatpak to install a package.
For example, the flatpak runtime or the base app already provides it,
you install it in another way, or you do not need it in your flatpak.
(Check the runtime that your app runs on, not the SDK that it is built in, because the SDK contains more packages.)

req2flatpak installs exactly the packages that are in your list of requirements.
To skip packages, filter the list before querying PyPI.
The filter can use any criterion, and you can also add requirements, for example build dependencies:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_skip_start
   :end-before: recipe_skip_end
   :language: python
   :dedent:

A fully pinned ``requirements.txt`` also lists the dependencies of your packages.
If you skip a package, then check whether you also want to skip its dependencies.

If the packages are skipped because the runtime provides them,
read the platform from the runtime, see :ref:`choosing the target platform <api-choose-target-platform>`.
This platform knows the python packages that the runtime provides.
``platform.without_installed(requirements)`` leaves out the requirements
that the runtime provides in exactly the same version.
Requirements with another version, and packages that the runtime does not provide, are kept:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_flatpak_runtime_start
   :end-before: recipe_flatpak_runtime_end
   :language: python
   :dedent:



Querying Package Indices for Available Releases
-----------------------------------------------

A release describes what is offered by package index (or multiple indices) for a given package requirement.

Release
^^^^^^^

Releases are represented in req2flatpak as a dataclass, as follows:

.. autoclass:: Release
   :members:
   :undoc-members:

In other words, a release object combines the name and version of a required package
with a list of available downloads.
You can create release objects in your code as you wish,
or you can use req2flatpak's ``PypiClient`` for this purpose.

PypiClient
^^^^^^^^^^

The ``PypiClient`` class lets you query the "PyPI" python package index about available releases.
For example:

.. literalinclude:: ../../tests/test_pypi_client.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


Documentation of all methods provided by the ``PypiClient`` class:

.. autoclass:: PypiClient
   :members:

**Caching.**
PypiClient caches responses to reduce traffic when querying PyPI.
By default, a simple ``dict`` is used as an in-memory cache.
To improve caching, you can use a persistent cache as follows:

.. literalinclude:: ../../tests/test_pypi_client.py
   :start-after: example_usage2_start
   :end-before: example_usage2_end
   :language: python
   :dedent:

The above code instantiates a persistent ``shelve.Shelf`` cache using ``pypi_cache.tmp`` as filename.
The code then configures the PypiClient class to use the shelf for caching,
and then uses the cache when querying PyPI.

Clients for other package indices instead of PyPI are not included in req2flatpak.
You are free, of course, to implement your own clients for additional package indices in your own script.


Choosing Compatible Downloads
-----------------------------

req2flatpak provides methods for choosing the best compatible download for a given target platform.

Background Information
^^^^^^^^^^^^^^^^^^^^^^

Choosing compatible downloads is important because, generally speaking,
only a subset of downloads are compatible with a given target platform.
For example, a release may contain wheels for older python interpreters
or different system architectures.

In python packaging, the compatibility requirements of any download
are encoded in the filename as a set of "tags", as explained, for example,
in `pypa's packaging documentation about tags <https://packaging.pypa.io/en/latest/tags.html>`__.
A download is compatible with a target platform if (at least) one of the
package tags equals one of the target platform's system tags.

Choosing the "best" compatible download is important because multiple downloads may be compatible,
but only one download is needed for installing a package.
Pip's algorithm for choosing the best download uses ranked platform tags;
the best download is the one that matches the highest-ranked platform tag.

Multiple implementations exist in related work for choosing the best compatible download:

- Pip's internal behavior is the official reference implementation,
  but pip recommends against accessing internal pip apis from outside packages,
  which makes it difficult to re-use the implementation.
- Pyodide's implementation of its
  `find_matching_wheels <https://github.com/pyodide/pyodide/blob/97cd5bdc1cf62f4e5e44a305a7682d92b556a1e0/pyodide-build/pyodide_build/common.py#L74>`_
  function is easy to understand and can serve for inspiration.
- req2flatpak includes its own implementation in the ``DownloadChooser`` class.


DownloadChooser
^^^^^^^^^^^^^^^

The ``DownloadChooser`` class provides the following methods
for filtering compatible downloads and for choosing the "best" download.
For example:

.. literalinclude:: ../../tests/test_download_chooser.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


.. _api-source-packages:

**Preferring source packages.**
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

.. _api-custom-chooser:

**Preferring source packages, except for some packages.**
Some packages are difficult to build from source, for example packages with compiled extensions
that need a compiler, system libraries or a long build time.
You may want source packages for most packages, but binary wheels for these few.

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


Documentation of all methods provided by the ``DownloadChooser`` class:

.. autoclass:: DownloadChooser
   :members:
   :member-order: bysource


Generating a Build Module for flatpak-builder
---------------------------------------------

The output of req2flatpak is a build module,
intended to be processed by ``flatpak-builder``
as part of a build manifest.

flatpak-builder creates flatpak packages by processing build manifests.
A manifest can consist of multiple build modules.
Each module adds to the things to be included in the resulting flatpak package.
The build modules generated by req2flatpak are no different;
when processed by flatpak-builder, they install required python packages
to include them into the flatpak package.


FlatpakGenerator
^^^^^^^^^^^^^^^^

req2flatpak's ``FlatpakGenerator`` class provides methods for generating a build module
that will instruct flatpak-builder to install the required python packages.

Example usage:

.. literalinclude:: ../../tests/test_flatpak_generator.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


To save a build module to a file, use ``write_build_module_as_json``
(as in the example at the top of this page)
or ``write_build_module_as_yaml``, which needs the optional ``pyyaml`` package.
The methods ``build_module_as_str`` and ``build_module_as_yaml_str`` return the text instead.


.. _api-pip-options:

**Passing additional options to pip.**
The generated build module runs ``pip3 install`` with a fixed set of options.
Sometimes you need more options.
A typical example is ``--ignore-installed``,
which makes pip install a package even if a package of the same name is already installed.
To change the command, modify the ``pip_install_template``:

.. literalinclude:: ../../tests/test_recipes.py
   :start-after: recipe_pip_options_start
   :end-before: recipe_pip_options_end
   :language: python
   :dedent:


Documentation of all methods provided by the ``FlatpakGenerator`` class:

.. autoclass:: FlatpakGenerator
   :members:


.. _Customization:

Customization Options
---------------------

Using req2flatpak's Python API gives many options for customization. 
You have all the freedom in the world to modify each step as you see fit.

For example:

.. literalinclude:: ../../tests/test_req2flatpak.py
   :start-after: example_customization1_start
   :end-before: example_customization1_end
   :language: python
   :dedent:


More examples of how to customize req2flatpak are in the sections above,
for example how to prefer source packages over wheels (:ref:`source packages <api-source-packages>`),
how to skip packages (:ref:`skipping packages <api-skip-packages>`),
and how to pass additional options to the ``pip install`` command (:ref:`pip options <api-pip-options>`).
