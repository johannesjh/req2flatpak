Installation
============

Installing req2flatpak is easy.
Multiple installation methods are available.


Installing the Python Package
-----------------------------

You can install req2flatpak as a python package.
This is the default and recommended installation method.

For example:

.. code-block:: bash

   pip install req2flatpak
   req2flatpak --help


The first command will install the latest release of req2flatpak.
The second command will display req2flatpak's help,
allowing you to verify that req2flatpak was installed successfully.


Installing from Git
-------------------

It is possible to install req2flatpak from a git repository.
This installation method is useful if you want to install and test
a new, experimental version of req2flatpak that has not yet been officially released.

To install req2flatpak from a git repository, run this command:

.. code-block:: bash

   pip install git+https://github.com/johannesjh/req2flatpak


The above command will install req2flatpak from the git repository's main branch.

You can, of course, specify other git repositories,
for example in order to install from a forked repository of req2flatpak.
And it is possible to specify specific branches, commits and tags,
see `pip's documentation on VCS support <https://pip.pypa.io/en/stable/topics/vcs-support/>`_.


Simply Downloading and Copying the Script
-----------------------------------------

You can download the ``req2flatpak.py`` script to your computer and run it.
Simple as that.
