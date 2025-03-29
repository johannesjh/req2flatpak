"""Tests for req2flatpak's commandline interface."""

import json
import subprocess
import tempfile
import unittest
from abc import ABC
from contextlib import contextmanager
from itertools import product
from pathlib import Path
from typing import Generator, List
from unittest import skipUnless
from unittest.mock import patch

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

from req2flatpak import (
    DownloadChooser,
    FlatpakGenerator,
    PlatformFactory,
    PypiClient,
    RequirementsParser,
)


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that the code usage example keeps working."""

    requirements_txt = "requests == 2.28.1"
    pypi_url = "https://pypi.org/pypi/requests/2.28.1/json"
    pypi_response = '{"info":{"author":"Kenneth Reitz","author_email":"me@kennethreitz.org","home_page":"https://requests.readthedocs.io","license":"Apache 2.0","name":"requests","package_url":"https://pypi.org/project/requests/","project_url":"https://pypi.org/project/requests/","summary":"Python HTTP for Humans.","version":"2.28.1"},"urls":[{"digests":{"md5":"d18f682863389367f878339e288817f2","sha256":"8fefa2a1a1365bf5520aac41836fbee479da67864514bdb821f31ce07ce65349"},"filename":"requests-2.28.1-py3-none-any.whl","packagetype":"bdist_wheel","url":"https://files.pythonhosted.org/packages/ca/91/6d9b8ccacd0412c08820f72cebaa4f0c0441b5cda699c90f618b6f8a1b42/requests-2.28.1-py3-none-any.whl"},{"digests":{"md5":"796ea875cdae283529c03b9203d9c454","sha256":"7c5599b102feddaa661c826c56ab4fee28bfd17f5abca1ebbe3e7f19d7c97983"},"filename":"requests-2.28.1.tar.gz","packagetype":"sdist","url":"https://files.pythonhosted.org/packages/a5/61/a867851fd5ab77277495a8709ddda0861b28163c4613b011bc00228cc724/requests-2.28.1.tar.gz"}]}'  # pylint: disable=line-too-long

    # pylint: disable=duplicate-code
    def example_usage(self):
        """Example showing how to use req2flatpak in your own script."""
        # example_usage1_start
        platforms = [PlatformFactory.from_string("cp310-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")
        releases = PypiClient.get_releases(requirements)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # example_usage1_end
        return build_module

    def test(self):
        """Regression test to ensure that the example code above keeps working."""

        # mock the requirements.txt file:
        with patch.object(
            RequirementsParser,
            "parse_file",
            return_value=RequirementsParser.parse_string(self.requirements_txt),
        ):
            # mock pypi response:
            PypiClient.cache[self.pypi_url] = self.pypi_response

            # generate the flatpak build module
            build_module = self.example_usage()

            # validate the generated build module
            assert build_module["build-commands"], (
                "No build-commands section was found in the build module."
            )
            assert build_module["sources"], "No sources were found in the build module."
            assert build_module["sources"][0]["type"] == "file"
            assert "requests" in build_module["build-commands"][0], (
                "The requests package was not found in the build module's build command."
            )
            assert "requests" in build_module["sources"][0]["url"], (
                "The requests package was not found in the build module's sources."
            )


class Req2FlatpakBaseTest(ABC):
    """Base class for testing req2flatpak using both its CLI and API."""

    requirements: List[str]

    target_platforms: List[str]

    def validate_build_module(self, build_module: dict) -> None:
        """To be implemented by subclasses."""
        raise NotImplementedError

    @contextmanager
    def requirements_file(
        self,
    ) -> Generator[tempfile._TemporaryFileWrapper, None, None]:
        """Create a temporary requirements file."""
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8") as req_file:
            req_file.write("\n".join(self.requirements))
            req_file.flush()
            req_file.seek(0)
            yield req_file

    def _run_r2f(self, args: List[str]) -> subprocess.CompletedProcess:
        """Runs req2flatpak's cli in a subprocess."""
        cwd = Path(__file__).parent / ".."
        cmd = ["python3", "req2flatpak.py"]
        return subprocess.run(cmd + args, cwd=cwd, capture_output=True, check=True)

    def test_cli_with_reqs_as_args(self):
        """Runs req2flatpak by passing requirements as commandline arguments."""
        args = ["--requirements"] + self.requirements
        args += ["--target-platforms"] + self.target_platforms
        result = self._run_r2f(args)
        build_module = json.loads(result.stdout)
        self.validate_build_module(build_module)

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def test_cli_with_reqs_as_args_yaml(self):
        """Runs req2flatpak in yaml mode by passing requirements as cmdline arg."""
        args = ["--requirements"] + self.requirements
        args += ["--target-platforms"] + self.target_platforms
        args += ["--yaml"]
        result = self._run_r2f(args)
        build_module = yaml.safe_load(result.stdout)
        self.validate_build_module(build_module)

    def test_cli_with_reqs_as_file(self):
        """Runs req2flatpak by passing requirements as requirements.txt file."""
        with self.requirements_file() as req_file:
            args = ["--requirements-file", req_file.name]
            args += ["--target-platforms"] + self.target_platforms
            result = self._run_r2f(args)
            build_module = json.loads(result.stdout)
            self.validate_build_module(build_module)

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def test_cli_with_reqs_as_file_yaml(self):
        """Runs req2flatpak by passing requirements as requirements.txt file."""
        with self.requirements_file() as req_file:
            args = ["--requirements-file", req_file.name]
            args += ["--target-platforms"] + self.target_platforms
            args += ["--yaml"]
            result = self._run_r2f(args)
            build_module = yaml.safe_load(result.stdout)
            self.validate_build_module(build_module)

    def test_api(self):
        """Runs req2flatpak by calling its python api."""
        platforms = [
            PlatformFactory.from_string(platform) for platform in self.target_platforms
        ]
        requirements = RequirementsParser.parse_string("\n".join(self.requirements))
        releases = PypiClient.get_releases(requirements)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        self.validate_build_module(build_module)


class SinglePlatformTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving a single requirement and a single target platform."""

    requirements = ["requests==2.28.1"]
    target_platforms = ["cp310-x86_64"]

    def validate_build_module(self, build_module):
        """Validates that the build module installs requests."""
        self.assertIn("requests", build_module["build-commands"][0])
        self.assertIn("requests", build_module["sources"][0]["url"])


class MultiPlatformTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving a single requirement with platform-specific wheels."""

    requirements = ["scikit-learn==1.1.3"]
    target_platforms = ["cp310-x86_64", "cp310-aarch64"]

    def validate_build_module(self, build_module):
        """Validates that the build module installs scikit-learn."""
        self.assertIn("scikit-learn", build_module["build-commands"][0])
        self.assertTrue(build_module["sources"])

        # each url must contain scikit-learn:
        for source in build_module["sources"]:
            self.assertIn("scikit_learn", source["url"])

        # each architecture must be found in the urls:
        for arch in ["x86_64", "aarch64"]:
            self.assertTrue(
                any(arch in source["url"] for source in build_module["sources"]),
                "The architecture {arch} was not found in the build module's sources.",
            )


class MultiReqTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving multiple requirements for multiple target platforms."""

    requirements = ["numpy==1.23.4", "pandas==1.5.1"]
    target_platforms = ["cp310-x86_64", "cp310-aarch64"]

    def validate_build_module(self, build_module):
        """Validates that the build module installs the required packages."""
        packages = map(lambda r: r.split("==")[0].strip(), self.requirements)
        architectures = map(lambda a: a.split("-")[1], self.target_platforms)

        # each package must be found in the build command:
        for package in packages:
            self.assertIn(package, build_module["build-commands"][0])

        # each package and architecture must be found in the urls:
        for package, arch in product(packages, architectures):
            self.assertTrue(
                any(
                    package in source["url"] and arch in source["url"]
                    for source in build_module["sources"]
                ),
                f"The package {package} and architecture {arch} was not found in the build module's sources.",
            )


class EggTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving a package that publishes eggs."""

    requirements = ["beancount==2.3.5"]
    target_platforms = ["cp310-x86_64", "cp310-aarch64"]

    def validate_build_module(self, build_module):
        """Validates that the build module installs beancount."""

        # validate that the build command includes beancount:
        self.assertIn("beancount", build_module["build-commands"][0])

        # validate that at least one beancount source has been added:
        self.assertTrue(
            any("beancount" in source["url"] for source in build_module["sources"])
        )
