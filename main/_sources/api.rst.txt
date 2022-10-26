Using the Python API
====================

You can use req2flatpak's python api to write a custom python script that makes use of req2flatpak's functionality.
This allows to programmatically tweak and tune your script's behavior as needed.


Example
-------

You can use the following code example to get started with your script.

.. literalinclude:: ../../tests/example_usage_test.py
   :language: python
   :pyobject: example_usage
   :dedent:

The benefit of writing a custom script is:
You have all the freedom in the world to modify each step as you see fit.
For example, in your custom script:

* you may want to query other package indices instead of pypi,
* you may prefer wheels or sdists for certain packages, or
* you may want to exclude specific packages.

All of this can be freely implemented in a custom script.
Of course, it is also possible to fork and modify req2flatpak.

Note that for further inspiration about how to use req2flatpak's classes and methods,
you can also have a look at how req2flatpak's ``main()`` method is implemented.


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
You can create platform objects manually in your script.
And you can use functionality from req2flatpak, as described below.


PlatformFactory
^^^^^^^^^^^^^^^

The PlatformFactory provides methods for creating platform objects.

For example:

.. code-block:: python

    platform = PlatformFactory.from_string("cp310-x86_64")


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

.. code-block:: python

   requirements = RequirementsParser.parse_file("requirements.txt")


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

The ``PypiClient`` class allows to query the "PyPi" python package index
about available releases.

Documentation of all methods provided by the ``PypiClient`` class:

.. autoclass:: PypiClient
   :members:

Caching:
PypiClient caches responses to reduce traffic when querying PyPi.
By default, a simple ``dict`` is used as an in-memory cache.
To improve caching, you can use a persistent cache as follows:

.. code-block:: python

    import shelve

    with shelve.open("pypi_cache.tmp") as cache:
        PypiClient.cache = cache
        releases = PypiClient.get_releases(requirements)

The above code instantiates a persistent ``shelve.Shelf`` cache, using ``pypi_cache.tmp`` as filename.
Prior to querying pypi, the code then configures the PypiClient class to use the shelf for caching.

Clients for other package indices instead of Pypi are not included in req2flatpak.
You are free, of course, to implement your own client for another package index in you own script.


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

.. code-block:: python

   # choose the best wheel for a target platform:
   wheel = DownloadChooser.wheel(release, platform)


Documentation of all methods provided by the ``DownloadChooser`` class:

.. autoclass:: DownloadChooser
   :members:
   :member-order: bysource


Generating a Build Module for flatpak-builder
---------------------------------------------

flatpak-builder creates flatpak packages by processing build manifests.
A manifest can consist of multiple build modules.
Each module adds to the things that shall be included in the resulting flatpak package.

FlatpakGenerator
^^^^^^^^^^^^^^^^

req2flatpak's ``FlatpakGenerator`` class provides methods for generating a build module
that will instruct flatpak-builder to install the required python packages.

Example usage:

.. code-block:: python

   # generate a flatpak build module for given requirements,
   # including chosen package downloads:
   manifest = FlatpakGenerator.manifest(requirements, downloads)


Documentation of all methods provided by the ``FlatpakGenerator`` class:

.. autoclass:: FlatpakGenerator
   :members:


Exporting to JSON
^^^^^^^^^^^^^^^^^

You can easily export the generated manifest to json
using built-in functionality from python's standards library.
For example:

.. code-block:: python

   # export a manifest to json
   import json

   # export the manifest to a json string:
   json_string = json.dumps(manifest, indent=2)

   # export the manifest by writing to an output stream or to a file:
   json.dump(manifest, file, indent=2)
