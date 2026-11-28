Related Work
============

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
As of October 2022, in the personal opinion of the author (johannesjh),
the two projects compare as follows:

*  Both projects generate build modules for flatpak-builder.

*  Both projects have minimal dependencies.

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
   queries available downloads from PyPI and how pip chooses suitable
   downloads to match a given target platform.

*  ``req2flatpak.py`` prefers binary wheels, whereas
   ``flatpak-pip-generator`` prefers source packages.
