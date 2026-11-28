req2flatpak
===========

Documentation:  
https://johannesjh.github.io/req2flatpak/

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
``requirements.txt`` file. It lets you specify the target platform’s
python version and architecture. The script outputs an automatically
generated ``flatpak-builder`` build module. The build module, if included
into a flatpak-builder build manifest, will install the python packages
using pip.

Getting Started
---------------

1. Start from a ``requirements.txt`` file in which all requirements are resolved
   and pinned to exact versions (tools like pip-compile, uv or poetry can create it).

2. Write a script like the following exemplary `build_module.py`:

   .. code:: python

      # /// script
      # dependencies = ["req2flatpak"]
      # ///
      import req2flatpak

      platform = req2flatpak.PlatformFactory.from_string("cp314-x86_64")
      requirements = req2flatpak.RequirementsParser.parse_file("requirements.txt")
      releases = req2flatpak.PypiClient.get_releases(requirements)
      downloads = [req2flatpak.DownloadChooser.wheel_or_sdist(r, platform) for r in releases]
      req2flatpak.FlatpakGenerator.write_build_module_as_json("python3-packages.json", requirements, downloads)

   Why write your own script? - 
   Because in the long run, a script gives you much more flexibility than if you were just using the CLI.
   Now you can run your script with ``uv run build_module.py``
   to generate a flatpak build module ``python3-packages.json`` for your app.

3. Done, you can now include ``python3-packages.json`` as a module of your flatpak-builder app build manifest.

For more information, and for other ways of installing and using req2flatpak, see the documentation. 

CLI or Python API?
------------------

req2flatpak can be used in two ways.

- The python API is more flexible.
  It lets you modify the data and the behavior in each step, in a short script of your own.
  We recommend it because it is just as easy to get started, but provides more flexibility in the long term.
- The commandline interface (CLI) is deliberately simple.
  It covers the basic use case with only a few options,
  and it is all that many users need.


Contributing
------------

req2flatpak is developed in an open-source, community-driven way, as a
voluntary effort in the authors’ free time.

All contributions are greatly appreciated… pull requests are welcome,
and so are bug reports and suggestions for improvement.
The documentation describes how to set up a development environment
and how to contribute back to req2flatpak.

License
-------

req2flatpak is MIT-licensed, see the ``COPYING`` file.
