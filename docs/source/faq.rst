Frequently Asked Questions
==========================

This page answers common questions briefly and points to the place in the documentation
that explains the answer, for the commandline interface (CLI) and for the python API.
Use the links for the way that you use req2flatpak.


Should I use the CLI or the Python API?
---------------------------------------

Both work.
The CLI is simple and covers the basic use case, the API lets you modify data and behavior in each step.
Use only one of them. The default recommendation is to use the Python API because it provides greater flexibility.

- **CLI:** :doc:`cli`
- **API:** :doc:`api`


What can I do if my requirements are not pinned?
------------------------------------------------

The requirements are whatever python packages your app depends on.
You want to pass your requirements to req2flatpak in order to create a flatpak build module
(that you can then use to build your app using flatpak builder).
You must fully resolve and pin your requirements before passing them to req2flatpak.
This is done using other tools instead of req2flatpak, such as, e.g., ``uv pip compile`` or poetry export or the like.
You can find further information here:

- **CLI:** :ref:`Resolve and pin the requirements <pinning-requirements>`
- **API:** :ref:`Specifying package requirements <api-requirements>`


How do I choose the target platform?
------------------------------------

The target platform describes the flatpak runtime for your app, such as, for example, GNOME 51, 
and more specifically, the python version and packages that are shipped as part of that runtime.
You need to tell req2flatpak what platform you are targeting so it can do its work.
The most precise way for you to specify the platform is to have req2flatpak read all the info it needs straight from the flatpak runtime.
Alternatively, a short string such as ``cp314-x86_64`` (which in this example stands for for CPython 3.14 on x86_64 architecture) is often sufficient as a quick approximation.

- **CLI:** :ref:`Choose the target platform <choose-target-platform>`
- **API:** :ref:`Choosing the target platform <api-choose-target-platform>`


How do I read the platform from a flatpak runtime?
--------------------------------------------------

req2flatpak provides API and CLI methods for reading platform info straight from a given flatpak target platfrom.
To do so, it runs a probe (a short python script) in the installed runtime, and the script returns infos about the platform
such as python version, installed packages, etc.

Reading platform info from a flatpak runtime works for both architectures, x86_64 as well as aarch64. 
You will need to have the flatpak runtimes installed, as well as quemu if you want work with a different platform than what your host is.

- **CLI:** :ref:`From a flatpak runtime <cli-platform-from-runtime>`
- **API:** :ref:`Choosing the target platform <api-choose-target-platform>`


How do I support newer glibc (manylinux) versions?
--------------------------------------------------

Some python wheels are built for specific glibc (manylinux) versions.
In this case, req2flatpak needs to know the glibc (manylinux) version of your target platform in order to choose the right wheels.
The best way for you to specify this information is to read this platform info from the flatpak runtime.

- **CLI:** :ref:`From a flatpak runtime <cli-platform-from-runtime>` and :ref:`from a platform info file <cli-platform-from-file>`
- **API:** :ref:`Argument manylinux_max <api-manylinux-max>`, or read the platform from the runtime


How do I prefer source packages over binary wheels?
---------------------------------------------------

The CLI always prefers wheels and uses a source package only if no suitable wheel exists; this is by design.
With the API, you have more flexibility, e.g., you can choose downloads with ``sdist_or_wheel``, or write a download chooser of your own.

- **CLI:** not available, use the API
- **API:** :ref:`Preferring source packages <api-source-packages>` and :ref:`except for some packages <api-custom-chooser>`


How do I skip packages, for example those that the runtime provides?
--------------------------------------------------------------------

req2flatpak installs exactly the packages that you give it, so remove the unwanted ones first.
You can use tools such as ``uv pip compile`` to do that.
If you are using the API, you can also skip or filter packages in your script as you wish.

- **CLI:** :ref:`Skipping packages <cli-skip-packages>`
- **API:** :ref:`Skipping packages <api-skip-packages>`


How do I pass additional options to pip install?
------------------------------------------------

The generated build module runs ``pip3 install`` with a fixed set of options.
You can change that command by post-processing the output of req2flatpak.
If you are using the API, you can also change the command in your script.

- **CLI:** :ref:`Passing additional options to pip <cli-pip-options>`
- **API:** :ref:`Passing additional options to pip <api-pip-options>`
