"""Tests for req2flatpak's commandline interface."""

import io
import json
import os
import subprocess
import tempfile
import unittest
from abc import ABC
from collections.abc import Generator, Sequence
from contextlib import contextmanager, nullcontext, redirect_stdout
from itertools import product
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch

try:
    import yaml
except ImportError:
    yaml = None

from req2flatpak import (
    Download,
    DownloadChooser,
    FlatpakGenerator,
    PlatformFactory,
    PypiClient,
    Release,
    RequirementsParser,
    main,
)


class ExampleCustomizationTest(unittest.TestCase):
    """Test to ensure that the customization code example keeps working."""

    requirements_txt = "requests == 2.28.1"
    pypi_url = "https://pypi.org/pypi/requests/2.28.1/json"
    pypi_response = '{"info":{"author":"Kenneth Reitz","author_email":"me@kennethreitz.org","home_page":"https://requests.readthedocs.io","license":"Apache 2.0","name":"requests","package_url":"https://pypi.org/project/requests/","project_url":"https://pypi.org/project/requests/","summary":"Python HTTP for Humans.","version":"2.28.1"},"urls":[{"digests":{"md5":"d18f682863389367f878339e288817f2","sha256":"8fefa2a1a1365bf5520aac41836fbee479da67864514bdb821f31ce07ce65349"},"filename":"requests-2.28.1-py3-none-any.whl","packagetype":"bdist_wheel","url":"https://files.pythonhosted.org/packages/ca/91/6d9b8ccacd0412c08820f72cebaa4f0c0441b5cda699c90f618b6f8a1b42/requests-2.28.1-py3-none-any.whl"},{"digests":{"md5":"796ea875cdae283529c03b9203d9c454","sha256":"7c5599b102feddaa661c826c56ab4fee28bfd17f5abca1ebbe3e7f19d7c97983"},"filename":"requests-2.28.1.tar.gz","packagetype":"sdist","url":"https://files.pythonhosted.org/packages/a5/61/a867851fd5ab77277495a8709ddda0861b28163c4613b011bc00228cc724/requests-2.28.1.tar.gz"}]}'  # pylint: disable=line-too-long

    def test(self):
        """Regression test to ensure that the customization example keeps working."""
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
            self.assertTrue(
                build_module["build-commands"],
                "No build-commands section was found in the build module.",
            )
            self.assertTrue(
                build_module["sources"], "No sources were found in the build module."
            )
            self.assertEqual(build_module["sources"][0]["type"], "file")
            self.assertIn(
                "requests",
                build_module["build-commands"][0],
                "The requests package was not found in the build module's build command.",
            )
            self.assertIn(
                "requests",
                build_module["sources"][0]["url"],
                "The requests package was not found in the build module's sources.",
            )

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def example_usage(self):
        """Show how to customize req2flatpak in your own script."""
        # example_customization1_start
        # define your target platforms
        platforms = [PlatformFactory.from_string("cp314-x86_64")]

        # Optionally pre-process or otherwise tweak your requirements
        # before feeding them into req2flatpak,
        # e.g., using pip-compile.

        # Read (or otherwise create) your requirements list:
        requirements = RequirementsParser.parse_file("requirements.txt")

        # Optionally tweak the requirements list that was parsed by req2flatpak.
        # For example, you may wish to remove package "example" because it comes pre-installed:
        requirements = {r for r in requirements if r.package != "example"}

        # Optionally query other package indices by implementing a class similar to PyPiClient:
        class MyClient(PypiClient):
            """Custom client for querying another package index instead of PyPi."""

        releases = MyClient.get_releases(requirements)

        # Choose downloads with one of the ``DownloadChooser`` methods.
        # (Use ``sdist_or_wheel`` instead if you prefer source packages over wheels.)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }

        # Optionally tweak the downloads list.

        # Optionally modify the commandline options that will be passed to pip-install
        # by defining a custom pip_install template. E.g., to ignore preinstalled packages:
        custom_template = FlatpakGenerator.default_pip_install_template.replace(
            "pip3 install", "pip3 install --ignore-installed"
        )

        # Generate the flatpak build module:
        build_module = FlatpakGenerator.build_module(
            requirements, downloads, pip_install_template=custom_template
        )

        # Optionally, tweak the build module that was generated by req2flatpak.
        # For example, to provide a meaningful name for your build module:
        build_module["name"] = "my-custom-name"

        # Convert to JSON or YAML as you wish:
        json_str = FlatpakGenerator.build_module_as_str(
            requirements, downloads, pip_install_template=custom_template
        )
        yaml_str = FlatpakGenerator.build_module_as_yaml_str(
            requirements, downloads, pip_install_template=custom_template
        )
        # example_customization1_end
        self.assertIn("--ignore-installed", build_module["build-commands"][0])
        self.assertIn("--ignore-installed", json_str)
        self.assertIn("--ignore-installed", yaml_str)
        return build_module


class Req2FlatpakBaseTest(ABC):
    """Base class for testing req2flatpak using both its CLI and API."""

    requirements: Sequence[str]

    target_platforms: Sequence[str]

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

    def _run_r2f(self, args: list[str]) -> subprocess.CompletedProcess:
        """Run req2flatpak's cli in a subprocess."""
        cwd = Path(__file__).parent / ".."
        cmd = ["python3", "req2flatpak.py"]
        return subprocess.run(  # noqa: S603  # arguments are trusted test constants
            cmd + args, cwd=cwd, capture_output=True, check=True
        )

    def test_cli_with_reqs_as_args(self):
        """Runs req2flatpak by passing requirements as commandline arguments."""
        args = ["--requirements", *self.requirements]
        args += ["--target-platforms", *self.target_platforms]
        result = self._run_r2f(args)
        build_module = json.loads(result.stdout)
        self.validate_build_module(build_module)

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def test_cli_with_reqs_as_args_yaml(self):
        """Runs req2flatpak in yaml mode by passing requirements as cmdline arg."""
        args = ["--requirements", *self.requirements]
        args += ["--target-platforms", *self.target_platforms]
        args += ["--yaml"]
        result = self._run_r2f(args)
        if yaml is None:
            raise unittest.SkipTest(
                "The yaml extra dependency is needed for this feature."
            )
        build_module = yaml.safe_load(result.stdout)
        self.validate_build_module(build_module)

    def test_cli_with_reqs_as_file(self):
        """Runs req2flatpak by passing requirements as requirements.txt file."""
        with self.requirements_file() as req_file:
            args = ["--requirements-file", req_file.name]
            args += ["--target-platforms", *self.target_platforms]
            result = self._run_r2f(args)
            build_module = json.loads(result.stdout)
            self.validate_build_module(build_module)

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def test_cli_with_reqs_as_file_yaml(self):
        """Runs req2flatpak by passing requirements as requirements.txt file."""
        with self.requirements_file() as req_file:
            args = ["--requirements-file", req_file.name]
            args += ["--target-platforms", *self.target_platforms]
            args += ["--yaml"]
            result = self._run_r2f(args)
            if yaml is None:
                raise unittest.SkipTest(
                    "The yaml extra dependency is needed for this feature."
                )
            build_module = yaml.safe_load(result.stdout)
            self.validate_build_module(build_module)

    def test_api(self):
        """Runs req2flatpak by calling its python api."""
        platforms = []
        for platform_string in self.target_platforms:
            platform = PlatformFactory.from_string(platform_string)
            if platform is None:
                raise AssertionError(f"Invalid target platform: {platform_string}")
            platforms.append(platform)
        requirements = RequirementsParser.parse_string("\n".join(self.requirements))
        releases = PypiClient.get_releases(requirements)
        downloads = set()
        for release in releases:
            for platform in platforms:
                download = DownloadChooser.wheel_or_sdist(release, platform)
                if download is None:
                    raise AssertionError(f"No download found for {release.package}")
                downloads.add(download)
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        self.validate_build_module(build_module)


class SinglePlatformTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving a single requirement and a single target platform."""

    requirements = ("requests==2.28.1",)
    target_platforms = ("cp310-x86_64",)

    def validate_build_module(self, build_module):
        """Validate that the build module installs requests."""
        self.assertIn("requests", build_module["build-commands"][0])
        self.assertIn("requests", build_module["sources"][0]["url"])


class MultiPlatformTest(unittest.TestCase, Req2FlatpakBaseTest):
    """Test involving a single requirement with platform-specific wheels."""

    requirements = ("scikit-learn==1.1.3",)
    target_platforms = ("cp310-x86_64", "cp310-aarch64")

    def validate_build_module(self, build_module):
        """Validate that the build module installs scikit-learn."""
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

    requirements = ("numpy==1.23.4", "pandas==1.5.1")
    target_platforms = ("cp310-x86_64", "cp310-aarch64")

    def validate_build_module(self, build_module):
        """Validate that the build module installs the required packages."""
        packages = [r.split("==")[0].strip() for r in self.requirements]
        architectures = [a.split("-")[1] for a in self.target_platforms]

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

    requirements = ("beancount==2.3.5",)
    target_platforms = ("cp310-x86_64", "cp310-aarch64")

    def validate_build_module(self, build_module):
        """Validate that the build module installs beancount."""
        # validate that the build command includes beancount:
        self.assertIn("beancount", build_module["build-commands"][0])

        # validate that at least one beancount source has been added:
        self.assertTrue(
            any("beancount" in source["url"] for source in build_module["sources"])
        )


class CacheOptionTest(unittest.TestCase):
    """Test that the ``--cache`` option also works when the cache is still empty."""

    def test_empty_shelf_is_used_as_cache(self):
        """Verify that an empty shelf is used, and not replaced by a plain dict."""
        # an empty shelf is falsy, just like an empty dict:
        empty_shelf: dict = {}
        caches_used = []

        def fake_get_releases(_requirements):
            caches_used.append(PypiClient.cache)
            return []

        argv = [
            "req2flatpak.py",
            "--requirements",
            "requests==2.28.1",
            "--target-platforms",
            "cp310-x86_64",
            "--cache",
        ]
        with (
            open(os.devnull, "w", encoding="utf-8") as devnull,
            patch("sys.argv", argv),
            patch("shelve.open", return_value=nullcontext(empty_shelf)),
            patch.object(PypiClient, "cache", {}),
            patch.object(PypiClient, "get_releases", side_effect=fake_get_releases),
            redirect_stdout(devnull),
        ):
            main()

        self.assertEqual(len(caches_used), 1)
        self.assertIs(caches_used[0], empty_shelf)


class FileOptionsTest(unittest.TestCase):
    """Test how the commandline options for input and output files are handled."""

    requirement = "requests==2.28.1"

    def run_main(self, *args: str) -> list:
        """Run ``main`` offline, and return the requirements that were queried."""
        queried = []

        def fake_get_releases(requirements):
            queried.append(requirements)
            return []

        argv = ["req2flatpak.py", "--target-platforms", "cp310-x86_64", *args]
        with (
            patch("sys.argv", argv),
            patch.object(PypiClient, "cache", {}),
            patch.object(PypiClient, "get_releases", side_effect=fake_get_releases),
        ):
            main()
        return queried

    def test_output_goes_to_stdout_by_default(self):
        """Verify that json is written to stdout if no output file is given."""
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            self.run_main("--requirements", self.requirement)
        self.assertIn("build-commands", json.loads(stdout.getvalue()))

    def test_output_file_is_written(self):
        """Verify that the build module is written to the output file."""
        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "build-module.json"
            self.run_main("--requirements", self.requirement, "--outfile", str(outfile))
            self.assertIn(
                "build-commands", json.loads(outfile.read_text(encoding="utf-8"))
            )

    @skipUnless(yaml, "The yaml extra dependency is needed for this feature.")
    def test_yaml_extension_selects_yaml_output(self):
        """Verify that a .yaml extension of the output file selects yaml output."""
        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "build-module.yaml"
            self.run_main("--requirements", self.requirement, "--outfile", str(outfile))
            self.assertTrue(
                outfile.read_text(encoding="utf-8").startswith("# Generated by")
            )

    def test_no_output_file_is_created_on_error(self):
        """Verify that a failing run does not leave an empty output file behind."""
        with tempfile.TemporaryDirectory() as tmp:
            outfile = Path(tmp) / "build-module.json"
            with self.assertRaises(ValueError):
                self.run_main(
                    "--requirements", "requests>=2", "--outfile", str(outfile)
                )
            self.assertFalse(outfile.exists())

    def test_requirements_file(self):
        """Verify that requirements are read from the requirements file."""
        with tempfile.TemporaryDirectory() as tmp:
            req_file = Path(tmp) / "requirements.txt"
            req_file.write_text(self.requirement, encoding="utf-8")
            with redirect_stdout(io.StringIO()):
                queried = self.run_main("--requirements-file", str(req_file))
        self.assertEqual([r.package for r in queried[0]], ["requests"])

    def test_requirements_from_stdin(self):
        """Verify that "-" as requirements file reads the requirements from stdin."""
        with (
            patch("sys.stdin", io.StringIO(self.requirement)),
            redirect_stdout(io.StringIO()),
        ):
            queried = self.run_main("--requirements-file", "-")
        self.assertEqual([r.package for r in queried[0]], ["requests"])


class MissingDownloadTest(unittest.TestCase):
    """Test the error for packages without a suitable download."""

    windows_only = Release(
        package="winonly",
        version="1.0",
        downloads=[
            Download(
                package="winonly",
                version="1.0",
                filename="winonly-1.0-cp310-cp310-win_amd64.whl",
                url="https://example.org/winonly-1.0-cp310-cp310-win_amd64.whl",
                sha256="0" * 64,
            )
        ],
    )

    def run_main(self, releases) -> str:
        """Run ``main`` offline with the given releases and return stdout."""
        argv = [
            "req2flatpak.py",
            "--requirements",
            "winonly==1.0",
            "--target-platforms",
            "cp310-x86_64",
        ]
        stdout = io.StringIO()
        with (
            patch("sys.argv", argv),
            patch.object(PypiClient, "cache", {}),
            patch.object(PypiClient, "get_releases", return_value=releases),
            redirect_stdout(stdout),
        ):
            main()
        return stdout.getvalue()

    def test_no_suitable_download_gives_clear_error(self):
        """Verify the error message names package, version and python version."""
        with self.assertRaises(ValueError) as context:
            self.run_main([self.windows_only])
        message = str(context.exception)
        self.assertIn("winonly==1.0", message)
        self.assertIn("3.10", message)
