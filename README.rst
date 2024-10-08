req2flatpak
===========

.. inclusion-marker-do-not-remove

``req2flatpak`` is a script to convert python package requirements
to a flatpak-builder build module.
The module will install the required python packages
as part of a flatpak build.


Intended Use
------------

req2flatpak is for programmers
who want to package a python application using flatpak.

The req2flatpak script takes python package requirements as input, e.g., as
``requirements.txt`` file. It allows to specify the target platform’s
python version and architecture. The script outputs an automatically
generated ``flatpak-builder`` build module. The build module, if included
into a flatpak-builder build manifest, will install the python packages
using pip.

Getting Started
---------------

Install req2flatpak using pip (or any other python package installer),
e.g., by running ``pip install req2flatpak``.

Prepare a ``requirements.txt`` file with the packages that you want to install as part of a flatpak build.
You need to specify exact versions for all the packages including their dependencies.
(Various tools exist to help creating such a requirements file with fully resolved dependencies and frozen package versions;
for example, you can use
`pip-compile <https://pypi.org/project/pip-tools/>`_ or 
`poetry export <https://pypi.org/project/poetry-plugin-export/>`_ to export a suitable ``requirements.txt`` file).

Run req2flatpak. 
For example, run this command to generate a ``flatpak-builder`` build module
from your ``requirements.txt`` file:

.. code:: bash

   ./req2flatpak.py --requirements-file requirements.txt --target-platforms 310-x86_64 310-aarch64

When invoked like this, req2flatpak will
read the requirements file,
query pypi about available downloads for the requirements,
choose appropriate downloads for the specified target platforms,
and generate a flatpak-builder build module.
The module, if included in a flatpak-builder build manifest,
will install the required packages using pip.
The commandline option to define target platforms uses the format ``<pythonversion>-<architecture>``.
To learn more about available commandline options,
run ``req2flatpak.py --help``.

Note that programmatic usage of req2flatpak is also possible.
This means you can write a python script to invoke req2flatpak,
which allows to tweak the desired behavior in many ways.

Go read the `documentation <https://johannesjh.github.io/req2flatpak/>`__
to learn more about req2flatpak's commandline and Python APIs.
The documentation includes further examples to help you get started quickly.


Documentation
-------------

See https://johannesjh.github.io/req2flatpak/


Contributing
------------

req2flatpak is developed in an open-source, community-driven way, as a
voluntary effort in the authors’ free time.

All contributions are greatly appreciated… pull requests are welcome,
and so are bug reports and suggestions for improvement.
See req2flatpak’s documentation for how to set up a development environment
and how to contribute back to req2flatpak.

Related Work
------------

The
`flatpak-pip-generator <https://github.com/flatpak/flatpak-builder-tools/blob/master/pip/flatpak-pip-generator>`__
script is very similar to this project. Both scripts basically serve the same purpose,
and this project took a lot of inspiration from
flatpak-pip-generator. In fact, this project was created when we
discussed feature request
`#296 <https://github.com/flatpak/flatpak-builder-tools/issues/296>`__
in flatpak-pip-generator. A prototype followed from this feature
request, and since it was written from scratch, the prototype became
this separate project.

Comparison between ``flatpak-pip-generator`` and ``req2flatpak.py``:
Each of the two projects has its own benefits.
A comparison will likely change over time.
As in Oct, 2022, in my personal opinion (johannesjh),
I see the following similarities and differences:

*  Both projects generate build modules for flatpak-builder.

*  Both projects consist of a single script file with minimal
   dependencies, and are thus very easy to install.

*  ``flatpak-pip-generator`` resolves dependencies and freezes
   dependency versions, whereas ``req2flatpak.py`` asks the user to
   provide a fully resolved list of dependencies with frozen dependency
   versions. Various tools exist which make this easy, e.g.,
   pip, pip-compile and poetry.

*  ``flatpak-pip-generator`` is older and thus likely to be more mature.
   It supports more commandline options and probably has a more complete
   feature set.

*  ``req2flatpak.py`` is faster. The script itself runs faster because
   it does not need to download package files in order to generate the
   build module. And the flatpak build runs faster because all packages
   (from the entire ``requirements.txt`` file) are installed in a single
   call to ``pip install``.

*  ``req2flatpak.py`` re-implements some functionality of pip. In
   contrast, ``flatpak-pip-generator`` uses pip’s official
   functionality. Specifically, ``req2flatpak.py`` re-implements how pip
   queries available downloads from pypi and how pip chooses suitable
   downloads to match a given target platform.

*  ``req2flatpak.py`` prefers binary wheels, whereas
   ``flatpak-pip-generator`` prefers source packages.

License
-------

req2flatpak is MIT-licensed, see the ``COPYING`` file.
