Using the Python API
====================

You can use req2flatpak's python api to write a custom python script that makes use of req2flatpak's functionality.
This allows to programmatically tweak and tune the behavior as needed.


Example
-------

You can use the following code as an example to get started with your script.
The code demonstrates how to generate a flatpak-builder build module
in order to install python packages on a specific flatpak target platform.

.. literalinclude:: ../../tests/test_req2flatpak.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:

The above code uses req2flatpak to generate a build module in five steps:

#. define the target platforms,
#. specify the python packages to be installed,
#. query PyPi about available downloads,
#. choose downloads that are compatible with the target platforms,
#. generate the flatpak-builder build module.

...if you include the resulting build module in a flatpak build,
the module will install the required packages.

You will benefit from a writing a custom script
(in contrast to simply using req2flatpak's commandline interface)
if you want to change the modify or tweak the behavior.
In a custom script, you have all the freedom in the world
to modify each step as you see fit.
For example:

* you may want to query other package indices instead of pypi,
* you may prefer wheels or sdists for certain packages, or
* you may want to exclude specific packages.

The following subsections explain in detail how you can use req2flatpak's python api in your custom script.
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


Documentation of all methods provided by the ``PlatformFactory`` class:

.. autoclass:: PlatformFactory
   :members:


Specifying Package Requirements
-------------------------------

A requirement describes the name and exact version
of a python package that shall be installed.

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
Instead, it expects all versions to be pinned using the ``==`` operator, such as, e.g., s``requests == 2.0``.

The reason for this is that req2flatpak, by design, does not resolve or freeze dependencies.
You can use other tools like
`pip-compile <https://pypi.org/project/pip-tools/>`__ or
`poetry export <https://pypi.org/project/poetry/>`__
to resolve and freeze dependencies and to export them into a requirements.txt file.


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

The ``PypiClient`` class allows to query the "PyPi" python package index about available releases.
For example:

.. literalinclude:: ../../tests/test_pypi_client.py
   :start-after: example_usage1_start
   :end-before: example_usage1_end
   :language: python
   :dedent:


Documentation of all methods provided by the ``PypiClient`` class:

.. autoclass:: PypiClient
   :members:

Caching:
PypiClient caches responses to reduce traffic when querying PyPi.
By default, a simple ``dict`` is used as an in-memory cache.
To improve caching, you can use a persistent cache as follows:

.. literalinclude:: ../../tests/test_pypi_client.py
   :start-after: example_usage2_start
   :end-before: example_usage2_end
   :language: python
   :dedent:

The above code instantiates a persistent ``shelve.Shelf`` cache using ``pypi_cache.tmp`` as filename.
The code then configures the PypiClient class to use the shelf for caching,
and then uses the cache when querying PyPi.

Clients for other package indices instead of Pypi are not included in req2flatpak.
You are free, of course, to implement your own clients for additional package indices in you own script.


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


Documentation of all methods provided by the ``FlatpakGenerator`` class:

.. autoclass:: FlatpakGenerator
   :members:


Saving the Generated Build Module
---------------------------------

You can easily save a generated build module as a .json file
using built-in functionality from python's standard library.
For example:

.. code-block:: python

   # example showing how to export a build module to json
   import json

   # write the json data to file:
   with open("build-module.json", "w") as outfile:
    json.dump(build_module, outfile, indent=2)

The above code assumes a build module has been generated and is stored as a dict in the variable ``build_module``.
The code shows how to serialize the dict and save it to an output file.
