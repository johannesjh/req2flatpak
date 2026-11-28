#!/usr/bin/env python3

# req2flatpak is MIT-licensed.
#
# Copyright 2022-2024 johannesjh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
req2flatpak converts python package requirements to a flatpak build module.

The req2flatpak script takes python package requirements as input, e.g., as
``requirements.txt`` file. It allows to specify the target platform’s
python version and architecture. The script outputs an automatically
generated ``flatpak-builder`` build module. The build module, if included
into a flatpak-builder build manifest, will install the python packages
using pip.
"""

import argparse
import inspect
import json
import logging
import os
import pathlib
import re
import shelve
import subprocess
import sys
import urllib.request
from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager, nullcontext, suppress
from dataclasses import asdict, dataclass, field
from functools import cached_property
from importlib import metadata
from itertools import product
from typing import Any, ClassVar, TextIO
from urllib.parse import urlparse

import packaging.requirements as packaging_reqs
import packaging.tags
from packaging.utils import canonicalize_name, parse_wheel_filename
from packaging.version import InvalidVersion, Version

logger = logging.getLogger(__name__)

try:
    import yaml
except ImportError:
    yaml = None

# =============================================================================
# Helper functions / semi vendored code
# =============================================================================


class InvalidWheelFilename(Exception):
    """An invalid wheel filename was found, users should refer to PEP 427."""


def tags_from_wheel_filename(filename: str) -> set[str]:
    """
    Parse a wheel filename into a list of compatible platform tags.

    Implemented using functionality from ``packaging.utils.parse_wheel_filename``.
    """
    _, _, _, tags = parse_wheel_filename(filename)
    return {str(tag) for tag in tags}


# =============================================================================
# Data Structures
# =============================================================================


@dataclass(frozen=True)
class Requirement:
    """Represents a python package requirement."""

    package: str
    """A python package name."""

    version: str
    """The exact version of the package."""


@dataclass(frozen=True)
class Platform:
    """Represents a target platform for python package installations."""

    python_version: list[str]
    """A list of python version numbers, similar to ``platform.python_version_tuple()``."""

    python_tags: list[str]
    """A list of platform tags, similar to ``packaging.tags.sys_tags()``."""

    arch: str | None = None
    """The system architecture, either ``"x86_64"`` or ``"aarch64"``."""

    glibc_version: str | None = None
    """The version of the C library, for example ``"2.44"``."""

    runtime: str | None = None
    """The flatpak runtime ref that this platform was read from."""

    installed_packages: dict[str, str] = field(default_factory=dict)
    """The python packages that are already installed, as a dict of name to version."""

    def without_installed(
        self, requirements: Iterable[Requirement]
    ) -> list[Requirement]:
        """
        Return the requirements that are not already installed on this platform.

        Helper method to filter a list of requirements, omitting those that come installed as part of the platform.
        Requirements are omitted if they have the same normalized package name and same version as what comes installed.
        """
        installed = {
            canonicalize_name(name): version
            for name, version in self.installed_packages.items()
        }

        def is_installed(requirement: Requirement) -> bool:
            version = installed.get(canonicalize_name(requirement.package))
            if version is None:
                return False
            try:
                return Version(version) == Version(requirement.version)
            except InvalidVersion:
                return version == requirement.version

        return [r for r in requirements if not is_installed(r)]


def _platform_as_dict(platform: Platform) -> dict[str, Any]:
    """Return a platform as dict, leaving out the fields that have no value."""
    return {key: value for key, value in asdict(platform).items() if value}


@dataclass(frozen=True)
class Download(Requirement):
    """Represents a python package download."""

    filename: str
    url: str
    sha256: str

    @cached_property
    def is_wheel(self):
        """Return True if this download is a wheel."""
        return self.filename.endswith(".whl")

    @cached_property
    def is_sdist(self):
        """Return True if this download is a source distribution."""
        return not self.is_wheel and not self.filename.endswith(".egg")

    @cached_property
    def tags(self) -> set[str] | None:
        """Return a list of tags that this download is compatible for."""
        # https://packaging.pypa.io/en/latest/utils.html#packaging.utils.parse_wheel_filename
        # https://packaging.pypa.io/en/latest/utils.html#packaging.utils.parse_sdist_filename
        if not self.is_sdist and self.filename.endswith(".whl"):
            return tags_from_wheel_filename(self.filename)
        return None

    @cached_property
    def arch(self) -> str | None:
        """Return a wheel's target architecture, and None for sdists."""
        if not self.is_sdist and self.is_wheel and self.tags:
            if any(tag.endswith("x86_64") for tag in self.tags):
                return "x86_64"
            if any(tag.endswith("aarch64") for tag in self.tags):
                return "aarch64"
        return None

    def __lt__(self, other):
        """Make this class sortable."""
        # Note: Implementing __lt__ is sufficient to make a class sortable,
        # see, e.g., https://stackoverflow.com/a/7152796

        def sort_keys(download: Download) -> tuple[str, str, str]:
            """Use a tuple of package, version and architecture as key for sorting."""
            return download.package, download.version, download.arch or ""

        return sort_keys(self) < sort_keys(other)


@dataclass(frozen=True)
class Release(Requirement):
    """Represents a package release as name, version, and downloads."""

    package: str
    version: str
    downloads: list[Download] = field(default_factory=list)


# =============================================================================
# Operations
# =============================================================================


class PlatformProbeError(RuntimeError):
    """Reading the platform from a flatpak runtime failed."""


def _probe():
    """
    Return facts about the python installation that runs this function.

    This function is executed inside a flatpak runtime: only its source code is
    sent there, as the argument of ``python3 -c``. Therefore, it has to be
    self-contained. It imports everything it needs by itself, it only uses the
    standard library, and it uses nothing from the req2flatpak module.
    The code has to stay compatible with python 3.8.
    """
    import importlib
    import importlib.metadata
    import os
    import platform

    if platform.python_implementation() != "CPython":
        raise RuntimeError(
            f"Unsupported python implementation {platform.python_implementation()!r}, "
            "only CPython is supported."
        )

    try:
        glibc = os.confstr("CS_GNU_LIBC_VERSION")
    except (AttributeError, ValueError, OSError):
        glibc = None
    if not glibc or not glibc.startswith("glibc "):
        raise RuntimeError(f"Unsupported C library {glibc!r}, only glibc is supported.")

    packages = {}
    for distribution in importlib.metadata.distributions():
        name = None
        if "Name" in distribution.metadata:
            name = distribution.metadata["Name"]
        if name and name not in packages:
            packages[name] = distribution.version

    tags = None
    for module_name in (
        "packaging.tags",
        "setuptools._vendor.packaging.tags",
        "pip._vendor.packaging.tags",
    ):
        try:
            module = importlib.import_module(module_name)
            tags = [str(tag) for tag in module.sys_tags()]
            break
        except ImportError:
            continue

    return {
        "implementation": platform.python_implementation(),
        "python_version": list(platform.python_version_tuple()),
        "glibc": glibc,
        "machine": platform.machine(),
        "packages": packages,
        "tags": tags,
    }


class PlatformFactory:
    """Provides methods for creating platform objects."""

    _ARCHITECTURES = ("x86_64", "aarch64")

    @classmethod
    def _check_arch(cls, arch: str) -> None:
        if arch not in cls._ARCHITECTURES:
            raise ValueError(
                f"Unsupported architecture {arch!r}, "
                f"must be one of {', '.join(cls._ARCHITECTURES)}."
            )

    @staticmethod
    def _check_manylinux_max(manylinux_max: int) -> None:
        if manylinux_max < 17:
            raise ValueError(
                f"Unsupported manylinux_max {manylinux_max!r}, "
                "the glibc minor version must be at least 17."
            )

    @staticmethod
    def _get_current_python_version() -> list[str]:
        # pylint: disable=import-outside-toplevel
        import platform

        return list(platform.python_version_tuple())

    @staticmethod
    def _get_current_python_tags() -> list[str]:
        tags = [str(tag) for tag in packaging.tags.sys_tags()]
        return tags

    @classmethod
    def from_current_interpreter(cls) -> Platform:
        """
        Return a platform object that describes the current interpreter and system.

        This method requires the ``packaging`` package to be installed
        because functionality from this package is used to generate the list of
        tags that are supported by the current platform.

        The platform object returned by this method obviously depends on the
        specific python interpreter and system architecture used to run the
        req2flatpak script. The reason why is that this method reads platform
        properties from the current interpreter and system.
        """
        return Platform(
            python_version=cls._get_current_python_version(),
            python_tags=cls._get_current_python_tags(),
        )

    _PROBE_TIMEOUT_SECONDS = 120
    """Time limit for running the probe in a flatpak runtime, in seconds."""

    @classmethod
    def from_flatpak_runtime(
        cls, ref: str, installation: str | None = None
    ) -> Platform:
        """
        Return a platform object by reading the platform from a flatpak runtime.

        The runtime must be installed already. A small probe script is run inside
        the runtime, using ``flatpak run``. It reads the python version, the
        glibc version, the architecture, the python packages that the runtime
        provides, and the supported wheel tags.
        If the runtime offers no way to list the wheel tags, they are derived
        from the glibc version, and a warning is logged.

        :param ref: a flatpak runtime ref of the form ``NAME/ARCH/BRANCH``, e.g.,
          ``org.gnome.Platform//51`` or ``org.gnome.Platform/aarch64/51``.
          An empty architecture means the architecture of the current machine.
        :param installation: ``"user"`` or ``"system"``, or the name of another
          flatpak installation. By default, flatpak chooses the installation,
          and it fails if the runtime is installed in more than one.
        :raises PlatformProbeError: if the platform cannot be read.
        """
        data = cls._run_probe(ref, installation)

        machine = data["machine"]
        if machine not in cls._ARCHITECTURES:
            raise PlatformProbeError(
                f"Unsupported architecture {machine!r} in runtime {ref}, "
                f"must be one of {', '.join(cls._ARCHITECTURES)}."
            )
        ref_parts = ref.split("/")
        if len(ref_parts) > 1 and ref_parts[1] and ref_parts[1] != machine:
            raise PlatformProbeError(
                f"Runtime {ref} reports architecture {machine!r}, "
                f"but {ref_parts[1]!r} was requested."
            )

        glibc_match = re.match(r"^glibc (\d+)\.(\d+)", data["glibc"])
        if glibc_match is None:
            raise PlatformProbeError(
                f"Unsupported C library {data['glibc']!r} in runtime {ref}, "
                "only glibc is supported."
            )
        glibc_minor = int(glibc_match.group(2))

        python_version = [str(part) for part in data["python_version"]]
        tags = data["tags"]
        if tags is None:
            logger.warning(
                "Runtime %s offers no way to list the supported wheel tags "
                "(no 'packaging' in python, setuptools or pip). "
                "The tags are derived from the glibc version instead.",
                ref,
            )
            try:
                tags = cls.from_python_version_and_arch(
                    minor_version=int(python_version[1]),
                    arch=machine,
                    manylinux_max=glibc_minor,
                ).python_tags
            except ValueError as error:
                raise PlatformProbeError(
                    f"Cannot derive wheel tags for runtime {ref}: {error}"
                ) from error

        installed_packages: dict[str, str] = {}
        for name, version in data["packages"].items():
            installed_packages.setdefault(canonicalize_name(name), version)

        return Platform(
            python_version=python_version,
            python_tags=list(tags),
            arch=machine,
            glibc_version=f"{glibc_match.group(1)}.{glibc_minor}",
            runtime=ref,
            installed_packages=installed_packages,
        )

    @classmethod
    def _run_probe(cls, ref: str, installation: str | None) -> dict[str, Any]:
        """Run the probe in a flatpak runtime and return its parsed output."""
        command = ["flatpak", "run"]
        if installation in ("user", "system"):
            command.append(f"--{installation}")
        elif installation:
            command.append(f"--installation={installation}")
        script = (
            inspect.getsource(_probe) + "\nimport json\nprint(json.dumps(_probe()))\n"
        )
        command += ["--command=python3", ref, "-c", script]

        try:
            result = subprocess.run(  # noqa: S603  # fixed command, the ref is passed as a single argument
                command,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=cls._PROBE_TIMEOUT_SECONDS,
                check=False,
            )
        except FileNotFoundError as error:
            raise PlatformProbeError(
                "The 'flatpak' command was not found. Is flatpak installed?"
            ) from error
        except subprocess.TimeoutExpired as error:
            raise PlatformProbeError(
                f"Reading the platform from {ref} timed out "
                f"after {cls._PROBE_TIMEOUT_SECONDS} seconds."
            ) from error

        if result.returncode != 0:
            raise PlatformProbeError(cls._explain_failure(ref, result.stderr))

        try:
            data = json.loads(result.stdout)
            missing = {"python_version", "glibc", "machine", "packages", "tags"} - set(
                data
            )
            if missing:
                raise KeyError(f"missing keys {sorted(missing)}")
        except (ValueError, KeyError, TypeError) as error:
            raise PlatformProbeError(
                f"Runtime {ref} returned invalid probe output: {error!r}"
            ) from error
        return data

    @staticmethod
    def _explain_failure(ref: str, stderr: str) -> str:
        """Return an error message for a failed ``flatpak run``."""
        stderr = stderr.strip()
        if "not installed" in stderr:
            return (
                f"Runtime {ref} is not installed. Install it with "
                "'flatpak install', and for another architecture, "
                f"use the ref with architecture and 'flatpak install --arch'.\n{stderr}"
            )
        if "Similar installed refs found" in stderr or "No ref chosen" in stderr:
            return (
                f"Runtime {ref} is installed more than once, "
                f"use --user, --system or --installation to choose.\n{stderr}"
            )
        if "Exec format error" in stderr:
            return (
                f"Runtime {ref} cannot be executed on this machine. "
                "For a foreign architecture, qemu-user and binfmt_misc "
                f"emulation must be installed.\n{stderr}"
            )
        if "execvp python3" in stderr:
            return f"Runtime {ref} does not provide python3.\n{stderr}"
        return f"Reading the platform from {ref} failed:\n{stderr}"

    @classmethod
    def from_file(cls, path: str | pathlib.Path) -> Platform:
        """
        Return a platform object by reading a platform info file.

        The file contains the fields of :py:class:`~req2flatpak.Platform` as JSON,
        or as YAML if the file name ends with ``.yaml`` or ``.yml``.
        Such a file is created by ``req2flatpak --platform-info``.

        :raises FileNotFoundError: if the file does not exist.
        :raises ValueError: if the file content is not a valid platform description.
        """
        path = pathlib.Path(path)
        with open(path, encoding="utf-8") as file:
            if path.suffix.casefold() in (".yaml", ".yml"):
                if not yaml:
                    raise ImportError(
                        "Package `pyyaml` has to be installed for the yaml format."
                    )
                data = yaml.safe_load(file)
            else:
                try:
                    data = json.load(file)
                except json.JSONDecodeError as error:
                    raise ValueError(f"{path}: invalid JSON: {error}") from error
        if not isinstance(data, dict):
            raise ValueError(  # noqa: TRY004  # documented as ValueError
                f"{path}: expected a mapping of platform fields."
            )
        try:
            return Platform(**data)
        except TypeError as error:
            raise ValueError(f"{path}: invalid platform info: {error}") from error

    @classmethod
    def from_string(cls, platform_string: str) -> Platform | None:
        """
        Return a platform object by parsing a platform string.

        :param platform_string: A string specifying python version and system
          architecture. The string format is
          "{python_version}-{system_architecture}".
          For example: "cp313-x86_64" or "cp314-aarch64".
          Acceptable values are the same as in
          :py:meth:`~req2flatpak.PlatformFactory.from_python_version_and_arch`.
        """
        match = re.match(r"^(?:py|cp)?(\d)(\d+)-(.*)$", platform_string)
        if match is None:
            logger.warning("Could not parse platform string %s", platform_string)
            return None
        _, minor, arch = match.groups()
        return cls.from_python_version_and_arch(minor_version=int(minor), arch=arch)

    @classmethod
    def from_python_version_and_arch(
        cls,
        minor_version: int | None = None,
        arch="x86_64",
        manylinux_max: int = 35,
    ) -> Platform:
        """
        Return a platform object that roughly describes a cpython installation on linux.

        The tags in the platform object are a rough approximation, trying to match what
        `packaging.tags.sys_tags` would return if invoked on a linux system with cpython.
        No guarantees are made about how closely this approximation matches a real system.

        :param minor_version: the python 3 minor version, specified as int.
          Defaults to the current python version.
        :param arch: either "x86_64" or "aarch64".
        :param manylinux_max: the newest glibc minor version to generate
          manylinux tags for, e.g., 44 for glibc 2.44. Must be at least 17.
        """
        if not minor_version:
            minor_version = int(cls._get_current_python_version()[1])
        cls._check_arch(arch)
        cls._check_manylinux_max(manylinux_max)
        return Platform(
            python_version=["3", str(minor_version)],
            python_tags=list(
                cls._cp3_linux_tags(
                    minor_version=minor_version,
                    arch=arch,
                    manylinux_max=manylinux_max,
                )
            ),
        )

    @classmethod
    def _cp3_linux_tags(
        cls,
        minor_version: int | None = None,
        arch="x86_64",
        manylinux_max: int = 35,
    ) -> Generator[str, None, None]:
        """Yield python platform tags for cpython3 on linux, without duplicates."""
        seen: set[str] = set()
        for tag in cls._cp3_linux_tags_with_duplicates(
            minor_version=minor_version, arch=arch, manylinux_max=manylinux_max
        ):
            if tag not in seen:
                seen.add(tag)
                yield tag

    @classmethod
    def _cp3_linux_tags_with_duplicates(
        cls,
        minor_version: int | None = None,
        arch="x86_64",
        manylinux_max: int = 35,
    ) -> Generator[str, None, None]:
        """Yield python platform tags for cpython3 on linux."""
        # pylint: disable=too-many-branches

        if minor_version is None:
            raise ValueError("The python minor version must be specified.")
        cls._check_arch(arch)
        cls._check_manylinux_max(manylinux_max)

        def seq(start: int, end: int) -> Iterable[int]:
            """Return a range of numbers, from start to end, in steps of +/- 1."""
            step = 1 if start < end else -1
            return range(start, end + step, step)

        platforms = [f"manylinux_2_{v}" for v in seq(manylinux_max, 17)] + [
            "manylinux2014"
        ]
        if arch == "x86_64":
            platforms += (
                [f"manylinux_2_{v}" for v in seq(16, 12)]
                + ["manylinux2010"]
                + [f"manylinux_2_{v}" for v in seq(11, 5)]
                + ["manylinux1"]
            )
        platforms += ["linux"]
        platform_tags = [f"{platform}_{arch}" for platform in platforms]

        # current cpython version, all abis, all platforms:
        for py in [f"cp3{minor_version}"]:
            for abi in [f"cp3{minor_version}", "abi3", "none"]:
                for platform in platform_tags:
                    yield (f"{py}-{abi}-{platform}")

        # older cpython versions, abi3, all platforms:
        for py in [f"cp3{v}" for v in seq(minor_version - 1, 2)]:
            for abi in ["abi3"]:
                for platform in platform_tags:
                    yield (f"{py}-{abi}-{platform}")

        # current python version, abi=none, all platforms:
        for py in [f"py3{minor_version}"]:
            for abi in ["none"]:
                for platform in platform_tags:
                    yield (f"{py}-{abi}-{platform}")

        # current major python version (py3), abi=none, all platforms:
        for py in ["py3"]:
            for abi in ["none"]:
                for platform in platform_tags:
                    yield (f"{py}-{abi}-{platform}")

        # older python versions, abi=none, all platforms:
        for py in [f"py3{v}" for v in seq(minor_version - 1, 0)]:
            for abi in ["none"]:
                for platform in platform_tags:
                    yield (f"{py}-{abi}-{platform}")

        # current python version, abi=none, platform=any
        yield f"py3{minor_version}-none-any"

        # current major python version, abi=none, platform=any
        yield "py3-none-any"

        # older python versions, abi=none, platform=any
        for py in [f"py3{v}" for v in seq(minor_version - 1, 0)]:
            yield f"{py}-none-any"


class RequirementsParser:
    """
    Parses requirements.txt files in a very simple way.

    This methods expects all versions to be pinned, and it does not
    resolve dependencies.
    """

    @classmethod
    def parse_string(cls, requirements_txt: str) -> list[Requirement]:
        """Parse requirements.txt string content into a list of Requirement objects."""

        def validate_requirement(req: packaging_reqs.Requirement) -> None:
            if len(req.specifier) != 1:
                raise ValueError(
                    "Error parsing requirements: A single version number must be specified."
                )
            if next(iter(req.specifier)).operator != "==":
                raise ValueError(
                    "Error parsing requirements: The exact version must specified as 'package==version'."
                )

        def make_requirement(req: packaging_reqs.Requirement) -> Requirement:
            validate_requirement(req)
            return Requirement(
                package=req.name, version=next(iter(req.specifier)).version
            )

        requirements = []
        for line in requirements_txt.splitlines():
            if not (line := line.strip()):
                continue
            if line.startswith("#"):
                continue
            req = packaging_reqs.Requirement(line)
            requirements.append(make_requirement(req))

        return requirements

    @classmethod
    def parse_file(cls, file) -> list[Requirement]:
        """Parse a requirements.txt file into a list of Requirement objects."""
        if hasattr(file, "read"):
            req_txt = file.read()
        else:
            req_txt = pathlib.Path(file).read_text(encoding="utf-8")
        return cls.parse_string(req_txt)


# Cache typealias
# This is meant for caching responses when querying package information.
# A cache can either be a dict for in-memory caching, or a shelve.Shelf
Cache = dict | shelve.Shelf


class PypiClient:
    """Queries package information from the PyPi package index."""

    cache: ClassVar[Cache] = {}
    """A dict-like object for caching responses from PyPi."""

    @classmethod
    def _query_from_cache(cls, url) -> str | None:
        try:
            return cls.cache[url]
        except KeyError:
            return None

    @classmethod
    def _query_from_pypi(cls, url) -> str:
        # url scheme might be `file:/`
        if not urlparse(url).scheme == "https":
            raise ValueError("URL scheme not `https`.")
        with urllib.request.urlopen(url) as response:  # noqa: S310  # scheme is restricted to https above
            json_string = response.read().decode("utf-8")
        cls.cache[url] = json_string
        return json_string

    @classmethod
    def _query(cls, url) -> str:
        return cls._query_from_cache(url) or cls._query_from_pypi(url)

    @classmethod
    def get_release(cls, req: Requirement) -> Release:
        """Query pypi regarding available releases for this requirement."""
        url = f"https://pypi.org/pypi/{req.package}/{req.version}/json"
        json_string = cls._query(url)
        json_dict = json.loads(json_string)
        if not json_dict["urls"]:
            raise RuntimeError(f"Release {req} has no URLs: maybe too old?")
        return Release(
            package=req.package,
            version=req.version,
            downloads=[
                Download(
                    package=req.package,
                    version=req.version,
                    filename=url["filename"],
                    url=url["url"],
                    sha256=url["digests"]["sha256"],
                )
                for url in json_dict["urls"]
            ],
        )

    @classmethod
    def get_releases(cls, reqs: Iterable[Requirement]) -> list[Release]:
        """Query pypi regarding available releases for these requirements."""
        return [cls.get_release(req) for req in reqs]


class DownloadChooser:
    """
    Provides methods for choosing package downloads.

    This class implements logic for filtering wheel and sdist downloads
    that are compatible with a given target platform.
    """

    @classmethod
    def matches(cls, download: Download, platform_tag: str) -> bool:
        """Return whether a download is compatible with a target platform tag."""
        if download.is_sdist:
            return True

        return platform_tag in (download.tags or [])

    @classmethod
    def downloads(
        cls,
        release: Release,
        platform: Platform,
        wheels_only=False,
        sdists_only=False,
    ) -> Iterator[Download]:
        """
        Yield suitable downloads for a specific platform.

        The order of downloads matches the order of platform tags, i.e.,
        preferred downloads are returned first.
        """
        cache = set()
        for platform_tag, download in product(platform.python_tags, release.downloads):
            if download in cache:
                continue
            if wheels_only and not download.is_wheel:
                continue
            if sdists_only and not download.is_sdist:
                continue
            if cls.matches(download, platform_tag):
                cache.add(download)
                yield download

    @classmethod
    def wheel(
        cls,
        release: Release,
        platform: Platform,
    ) -> Download | None:
        """Return the preferred wheel download for this release."""
        try:
            return next(cls.downloads(release, platform, wheels_only=True))
        except StopIteration:
            return None

    @classmethod
    def sdist(cls, release: Release) -> Download | None:
        """Return the source package download for this release."""
        try:
            return next(filter(lambda d: d.is_sdist, release.downloads))
        except StopIteration:
            return None

    @classmethod
    def wheel_or_sdist(cls, release: Release, platform: Platform) -> Download | None:
        """Return a wheel or an sdist for this release, in this order of preference."""
        return cls.wheel(release, platform) or cls.sdist(release)

    @classmethod
    def sdist_or_wheel(cls, release: Release, platform: Platform) -> Download | None:
        """Return an sdist or a wheel for this release, in this order of preference."""
        return cls.sdist(release) or cls.wheel(release, platform)


class FlatpakGenerator:
    """Provides methods for generating a flatpak-builder build module."""

    default_pip_install_template: str = (
        "pip3 install --verbose --exists-action=i "
        '--no-index --find-links="file://${PWD}" '
        "--prefix=${FLATPAK_DEST} --no-build-isolation "
    )
    """The default pip command. To use another command, pass it as ``pip_install_template`` argument."""

    @staticmethod
    def build_module(
        requirements: Iterable[Requirement],
        downloads: Iterable[Download],
        module_name="python3-package-installation",
        pip_install_template: str = default_pip_install_template,
    ) -> dict:
        """Generate a build module for inclusion in a flatpak-builder build manifest."""
        downloads = list(downloads)
        if any(download is None for download in downloads):
            raise ValueError(
                "Cannot generate a build module: a download is missing (None). "
                "Check that every requirement has a suitable wheel or sdist."
            )

        def source(download: Download) -> dict:
            source: dict[str, Any] = {
                "type": "file",
                "url": download.url,
                "sha256": download.sha256,
            }
            if download.arch:
                source["only-arches"] = [download.arch]
            return source

        def sources(downloads: Iterable[Download]) -> list[dict]:
            return [source(download) for download in sorted(downloads)]

        return {
            "name": module_name,
            "buildsystem": "simple",
            "build-commands": [
                pip_install_template + " ".join([req.package for req in requirements])
            ],
            "sources": sources(downloads),
        }

    @classmethod
    def build_module_as_str(cls, *args, indent: int = 2, **kwargs) -> str:
        """
        Generate JSON build module for inclusion in a flatpak-builder build manifest.

        The args and kwargs are the same as in
        :py:meth:`~req2flatpak.FlatpakGenerator.build_module`.
        The ``indent`` keyword argument sets the number of spaces used for indentation.
        """
        return json.dumps(cls.build_module(*args, **kwargs), indent=indent)

    @classmethod
    def build_module_as_yaml_str(cls, *args, indent: int = 2, **kwargs) -> str:
        """
        Generate YAML build module for inclusion in a flatpak-builder build manifest.

        The args and kwargs are the same as in
        :py:meth:`~req2flatpak.FlatpakGenerator.build_module`.
        The ``indent`` keyword argument sets the number of spaces used for indentation.
        """
        # optional dependency, not imported at top
        if not yaml:
            raise ImportError(
                "Package `pyyaml` has to be installed for the yaml format."
            )

        return yaml.dump(
            cls.build_module(*args, **kwargs),
            default_flow_style=False,
            sort_keys=False,
            indent=indent,
        )

    @staticmethod
    def _write(file: str | os.PathLike | TextIO, text: str) -> None:
        """Write text to a text stream, or to a file that is created once the text is ready."""
        if isinstance(file, (str, os.PathLike)):
            with open(file, "w", encoding="utf-8") as stream:
                stream.write(text)
        else:
            file.write(text)

    @classmethod
    def write_build_module_as_json(
        cls, file: str | os.PathLike | TextIO, *args, indent: int = 2, **kwargs
    ) -> None:
        """
        Write a JSON build module for inclusion in a flatpak-builder build manifest.

        :param file: The path of the output file, or a text stream.
        :param indent: The number of spaces used for indentation.

        The other args and kwargs are the same as in
        :py:meth:`~req2flatpak.FlatpakGenerator.build_module`.
        """
        cls._write(file, cls.build_module_as_str(*args, indent=indent, **kwargs))

    @classmethod
    def write_build_module_as_yaml(
        cls, file: str | os.PathLike | TextIO, *args, indent: int = 2, **kwargs
    ) -> None:
        """
        Write a YAML build module for inclusion in a flatpak-builder build manifest.

        This needs the optional ``pyyaml`` package.

        :param file: The path of the output file, or a text stream.
        :param indent: The number of spaces used for indentation.

        The other args and kwargs are the same as in
        :py:meth:`~req2flatpak.FlatpakGenerator.build_module`.
        """
        cls._write(file, cls.build_module_as_yaml_str(*args, indent=indent, **kwargs))


# =============================================================================
# CLI commandline interface
# =============================================================================


def cli_parser() -> argparse.ArgumentParser:
    """Return the req2flatpak commandline interface parser."""
    parser = argparse.ArgumentParser(
        description="req2flatpak generates a flatpak-builder build module for installing required python packages."
    )
    parser.add_argument(
        "--requirements",
        nargs="*",
        help="One or more requirements can be specified as commandline arguments, e.g., 'pandas==1.4.4'.",
    )
    parser.add_argument(
        "--requirements-file",
        "-r",
        nargs="?",
        help="Requirements can be read from a specified requirements.txt file.",
    )
    parser.add_argument(
        "--target-platforms",
        "-t",
        nargs="+",
        help="""
            Target platforms can be specified as, e.g., '313-x86_64' or '314-aarch64',
            or as a platform info file, e.g., 'gnome51.platforminfo.json',
            as created by '--platform-info REF'.
        """,
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        default=False,
        help="Uses a persistent cache when querying pypi.",
    )
    parser.add_argument(
        "--yaml",
        action="store_true",
        help="Write YAML instead of the default JSON.  Needs the 'pyyaml' package.",
    )

    parser.add_argument(
        "--outfile",
        "-o",
        nargs="?",
        help="""
            By default, writes JSON but specify a '.yaml' extension and YAML
            will be written instead, provided you have the 'pyyaml' package.
        """,
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        metavar="N",
        help="Number of spaces used for indentation in JSON and YAML output (default: 2).",
    )
    parser.add_argument(
        "--platform-info",
        nargs="?",
        const="",
        default=None,
        metavar="REF",
        help="""
            Prints information about a platform: by default the current platform.
            If REF is given, the platform is read from this installed flatpak runtime,
            e.g., 'org.gnome.Platform//51' or 'org.gnome.Platform/aarch64/51'
            (the format is NAME/ARCH/BRANCH, and an empty ARCH is the architecture
            of this machine).
        """,
    )
    installation = parser.add_mutually_exclusive_group()
    installation.add_argument(
        "--user",
        action="store_true",
        help="Read the runtime given as REF from the flatpak user installation.",
    )
    installation.add_argument(
        "--system",
        action="store_true",
        help="Read the runtime given as REF from the flatpak system installation.",
    )
    installation.add_argument(
        "--installation",
        metavar="NAME",
        help="Read the runtime given as REF from the named flatpak installation.",
    )
    parser.add_argument(
        "--installed-packages",
        action="store_true",
        default=False,
        help="Prints installed packages in requirements.txt format.",
    )
    return parser


@contextmanager
def _open_output(path: str | None) -> Generator[TextIO, None, None]:
    """Open the output file, or use stdout if no file (or the file name "-") is given."""
    if path is None or path == "-":
        yield sys.stdout
    else:
        with open(path, "w", encoding="utf-8") as stream:
            yield stream


def main():  # pylint: disable=too-many-branches
    """Provide req2flatpak's commandline interface."""
    # process commandline arguments
    parser = cli_parser()
    options = parser.parse_args()

    # output goes to a file or to stdout, the file is only opened once there is output
    if options.outfile not in (None, "-") and pathlib.Path(
        options.outfile
    ).suffix.casefold() in (".yaml", ".yml"):
        options.yaml = True

    if options.yaml and not yaml:
        parser.error(
            "Outputing YAML requires 'pyyaml' package: try 'pip install pyyaml'"
        )

    # print platform info if requested, and exit
    if (options.user or options.system or options.installation) and not (
        options.platform_info
    ):
        parser.error("--user, --system and --installation require --platform-info REF")
    if options.platform_info is not None:
        if options.platform_info:
            try:
                platform = PlatformFactory.from_flatpak_runtime(
                    options.platform_info,
                    installation="user"
                    if options.user
                    else "system"
                    if options.system
                    else options.installation,
                )
            except PlatformProbeError as error:
                parser.error(str(error))
        else:
            platform = PlatformFactory.from_current_interpreter()
        info = _platform_as_dict(platform)
        with _open_output(options.outfile) as output_stream:
            if options.yaml and yaml is not None:
                yaml.dump(
                    info,
                    output_stream,
                    default_flow_style=False,
                    sort_keys=False,
                    indent=options.indent,
                )
            else:
                json.dump(info, output_stream, indent=options.indent)
        parser.exit()

    # print installed packages if requested, and exit
    if options.installed_packages:
        # pylint: disable=not-an-iterable
        pkgs = {
            p.metadata["Name"]: p.metadata["Version"] for p in metadata.distributions()
        }
        with _open_output(options.outfile) as output_stream:
            for pkg, version in pkgs.items():
                print(f"{pkg}=={version}", file=output_stream)
        parser.exit()

    # parse requirements
    requirements = []
    with suppress(AttributeError):
        if options.requirements:
            requirements += RequirementsParser.parse_string(
                "\n".join(options.requirements)
            )
        if options.requirements_file:
            requirements += RequirementsParser.parse_file(
                sys.stdin
                if options.requirements_file == "-"
                else options.requirements_file
            )
    if not requirements:
        parser.error(
            "Error parsing requirements: At least one requirement must be specified."
        )

    # parse target platforms
    if not options.target_platforms:
        parser.error(
            "Error parsing target platforms. "
            "Missing commandline argument, at least one target platform must "
            "be specified as, e.g., '313-x86_64' or '314-aarch64'."
        )
    platforms = []
    for target in options.target_platforms:
        try:
            if pathlib.Path(target).exists() or pathlib.Path(
                target
            ).suffix.casefold() in (
                ".json",
                ".yaml",
                ".yml",
            ):
                platform = PlatformFactory.from_file(target)
            else:
                platform = PlatformFactory.from_string(target)
        except (OSError, ValueError, ImportError) as error:
            parser.error(f"Error parsing target platform {target!r}: {error}")
        if platform is None:
            parser.error(
                f"Error parsing target platform {target!r}. "
                "It must be specified as, e.g., '313-x86_64' or '314-aarch64', "
                "or as the name of a platform info file."
            )
        platforms.append(platform)

    # query released downloads from PyPi, optionally using a shelve.Shelf to cache responses:
    with (
        shelve.open("pypi_cache") if options.cache else nullcontext()  # noqa: S301  # cache file is written by this tool and read by the same user
    ) as cache:
        PypiClient.cache = cache if cache is not None else {}
        releases = PypiClient.get_releases(requirements)

    # choose suitable downloads for the target platforms
    downloads = set()
    for release in releases:
        for platform in platforms:
            download = DownloadChooser.wheel_or_sdist(release, platform)
            if download is None:
                raise ValueError(
                    f"No suitable download found for {release.package}=={release.version}: "
                    f"neither a wheel for python {'.'.join(platform.python_version[:2])} "
                    f"(platform tag {platform.python_tags[0] if platform.python_tags else '?'}) "
                    "nor an sdist is available."
                )
            downloads.add(download)

    # generate flatpak-builder build module
    with _open_output(options.outfile) as output_stream:
        if options.yaml:
            try:
                name = pathlib.Path(__file__).name
            except NameError:
                name = "req2flatpak"
            output_stream.write(f"# Generated by {name} {' '.join(sys.argv[1:])}\n")
            FlatpakGenerator.write_build_module_as_yaml(
                output_stream, requirements, downloads, indent=options.indent
            )
        else:
            FlatpakGenerator.write_build_module_as_json(
                output_stream, requirements, downloads, indent=options.indent
            )


if __name__ == "__main__":
    main()
