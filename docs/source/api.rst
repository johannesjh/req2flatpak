Using the Python API
====================

You can use req2flatpak's python api to write a custom python script
that makes use of req2flatpak's functionality.

This allows to programmatically tweak and tune your script's behavior as needed.
The script's logic typically boils down to:

.. code:: python3

   platforms = [PlatformFactory.from_string("310-x86_64")]
   requirements = RequirementsParser.parse_file("requirements.txt")
   releases = PypiClient.get_releases(requirements)
   downloads = {
       DownloadChooser.wheel_or_sdist(release, platform)
       for release in releases
       for platform in platforms
   }
   manifest = FlatpakGenerator.manifest(requirements, downloads)


For further inspiration, you can have a look at how req2flatpak's ``main()`` method is implemented,
it is really not that complicated.

The benefits of writing a custom script is:
You have all the freedom in the world to modify each step as you see fit.
For example, in your custom script...

* You may want to query other package indices instead of pypi.
* You may prefer wheels or sdists for certain packages.
* You may want to exclude specific packages.

All of this can be freely implemented in a custom script. Of
course, it is also possible to fork and modify req2flatpak.
