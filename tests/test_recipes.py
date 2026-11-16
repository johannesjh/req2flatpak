"""Tests for the code examples in the recipes section of the documentation.

All recipes run offline: the responses of PyPI are replaced by prepared data.
"""

import json
import unittest
from unittest.mock import mock_open, patch

from req2flatpak import (
    DownloadChooser,
    FlatpakGenerator,
    PlatformFactory,
    PypiClient,
    RequirementsParser,
)

FOO_FILENAMES = [
    "foo-1.0-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    "foo-1.0-cp314-cp314-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
    "foo-1.0.tar.gz",
]
JINJA2_FILENAMES = [
    "Jinja2-3.1.6-py3-none-any.whl",
]
BAR_FILENAMES = [
    "bar-3.0-cp314-cp314-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
    "bar-3.0.tar.gz",
]


def pypi_response(package: str, version: str, filenames: list[str]) -> str:
    """Return a response as it would be sent by PyPI's json api."""
    return json.dumps(
        {
            "urls": [
                {
                    "filename": filename,
                    "url": f"https://files.example.org/{filename}",
                    "digests": {"sha256": "0" * 64},
                }
                for filename in filenames
            ]
        }
    )


class RecipeTestCase(unittest.TestCase):
    """Provide a requirements file and the responses of PyPI for the recipes."""

    requirements_txt = "foo==1.0\nJinja2==3.1.6"

    def setUp(self):
        """Replace the requirements file and the responses of PyPI."""
        cache = {
            "https://pypi.org/pypi/foo/1.0/json": pypi_response(
                "foo", "1.0", FOO_FILENAMES
            ),
            "https://pypi.org/pypi/Jinja2/3.1.6/json": pypi_response(
                "Jinja2", "3.1.6", JINJA2_FILENAMES
            ),
            "https://pypi.org/pypi/bar/3.0/json": pypi_response(
                "bar", "3.0", BAR_FILENAMES
            ),
        }
        patcher = patch.object(PypiClient, "cache", cache)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(
            RequirementsParser,
            "parse_file",
            return_value=RequirementsParser.parse_string(self.requirements_txt),
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def urls(self, build_module: dict) -> list[str]:
        """Return the file names of the downloads in the build module."""
        return [source["url"].rsplit("/", 1)[-1] for source in build_module["sources"]]


class SourcePackagesRecipeTest(RecipeTestCase):
    """Recipe: use source packages instead of binary wheels."""

    def recipe(self):
        """Show how to prefer source packages over wheels."""
        # recipe_sdist_start
        platforms = [PlatformFactory.from_string("cp314-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")
        releases = PypiClient.get_releases(requirements)

        # sdist_or_wheel prefers the source package,
        # and falls back to a wheel if a release has no source package:
        downloads = {
            DownloadChooser.sdist_or_wheel(release, platform)
            for release in releases
            for platform in platforms
        }

        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # recipe_sdist_end
        return build_module

    def test(self):
        """Ensure that sdists are chosen, and wheels only if no sdist exists."""
        build_module = self.recipe()
        self.assertEqual(
            self.urls(build_module),
            [JINJA2_FILENAMES[0], "foo-1.0.tar.gz"],
        )

    def test_sdist_returns_none_without_source_package(self):
        """Ensure that DownloadChooser.sdist returns None if there is no sdist."""
        releases = PypiClient.get_releases(
            RequirementsParser.parse_file("requirements.txt")
        )
        missing = [r.package for r in releases if DownloadChooser.sdist(r) is None]
        self.assertEqual(missing, ["Jinja2"])


class CustomChooserRecipeTest(RecipeTestCase):
    """Recipe: use source packages, except for packages that are difficult to build."""

    requirements_txt = "foo==1.0\nbar==3.0"

    def recipe(self):
        """Show how to write your own function for choosing downloads."""
        # recipe_custom_chooser_start
        platforms = [PlatformFactory.from_string("cp314-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")
        releases = PypiClient.get_releases(requirements)

        # Packages that are difficult to build from source,
        # and that shall be installed from binary wheels:
        install_as_wheel = {"bar", "scipy"}

        def choose_download(release, platform):
            """Prefer source packages, except for the packages listed above."""
            if release.package in install_as_wheel:
                return DownloadChooser.wheel_or_sdist(release, platform)
            return DownloadChooser.sdist_or_wheel(release, platform)

        downloads = {
            choose_download(release, platform)
            for release in releases
            for platform in platforms
        }
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # recipe_custom_chooser_end
        return build_module

    def test(self):
        """Ensure that bar is installed from a wheel and foo from its sdist."""
        build_module = self.recipe()
        self.assertEqual(self.urls(build_module), [BAR_FILENAMES[0], "foo-1.0.tar.gz"])


class SkipPackagesRecipeTest(RecipeTestCase):
    """Recipe: skip packages, e.g., because the runtime already provides them."""

    def recipe(self):
        """Show how to leave out packages that shall not be installed."""
        # recipe_skip_start
        platforms = [PlatformFactory.from_string("cp314-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")

        # Remove the packages that this build module shall not install,
        # for example because the runtime provides them already.
        # Do this before querying PyPI, so that nothing is downloaded or installed for them.
        # (canonicalize_name makes "Jinja2", "jinja2" and "JINJA2" the same name.)
        from packaging.utils import canonicalize_name

        skipped_packages = {"jinja2", "markupsafe"}
        requirements = [
            r
            for r in requirements
            if canonicalize_name(r.package) not in skipped_packages
        ]

        releases = PypiClient.get_releases(requirements)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # recipe_skip_end
        return build_module

    def test(self):
        """Ensure that skipped packages appear neither in the command nor in the sources."""
        build_module = self.recipe()
        self.assertIn("foo", build_module["build-commands"][0])
        self.assertNotIn("Jinja2", build_module["build-commands"][0])
        self.assertTrue(all("Jinja2" not in u for u in self.urls(build_module)))
        self.assertTrue(self.urls(build_module))


class PipOptionsRecipeTest(RecipeTestCase):
    """Recipe: pass additional options to pip, for example ``--ignore-installed``."""

    def recipe(self):
        """Show how to change the options of the pip command."""
        # recipe_pip_options_start
        platforms = [PlatformFactory.from_string("cp314-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")
        releases = PypiClient.get_releases(requirements)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }

        # The build module runs a pip command to install the downloaded packages.
        # To change it, pass your own command as the pip_install_template argument.
        # Here, the default command is extended by one option:
        pip_install_template = FlatpakGenerator.default_pip_install_template.replace(
            "pip3 install", "pip3 install --ignore-installed"
        )
        build_module = FlatpakGenerator.build_module(
            requirements, downloads, pip_install_template=pip_install_template
        )
        # recipe_pip_options_end
        return build_module

    def test(self):
        """Ensure that the option ends up in the build command."""
        build_module = self.recipe()
        command = build_module["build-commands"][0]
        self.assertIn("pip3 install --ignore-installed --verbose", command)
        self.assertTrue(command.rstrip().endswith("foo Jinja2"))

    def test_default_template_is_used_without_argument(self):
        """Ensure that the default template is used if no template is passed."""
        build_module = FlatpakGenerator.build_module([], [])
        self.assertTrue(
            build_module["build-commands"][0].startswith(
                FlatpakGenerator.default_pip_install_template
            )
        )


class PlatformStringRecipeTest(unittest.TestCase):
    """Recipe: choose the target platform."""

    def test_platform_strings(self):
        """Show how to create one or several platforms from strings."""
        # recipe_platforms_start
        # The format is "<python version>-<architecture>".
        # Create one platform object per target platform:
        platforms = [
            PlatformFactory.from_string("cp314-x86_64"),
            PlatformFactory.from_string("cp314-aarch64"),
        ]

        # The same, without parsing a string:
        platform = PlatformFactory.from_python_version_and_arch(
            minor_version=14, arch="aarch64"
        )
        # recipe_platforms_end
        self.assertEqual(platforms[1], platform)
        self.assertEqual(platform.python_version, ["3", "14"])
        self.assertIn("cp314-cp314-manylinux_2_28_aarch64", platform.python_tags)

    def test_quoted_platforms_are_not_valid(self):
        """Ensure that several platforms in one string are rejected (issue #84)."""
        with self.assertRaises(ValueError):
            PlatformFactory.from_string("cp314-x86_64 cp314-aarch64")

    def test_platform_from_platform_info(self):
        """Show how to use the output of ``req2flatpak --platform-info``."""
        platform_info = (
            '{"python_version": ["3", "14", "0"], '
            '"python_tags": ["cp314-cp314-manylinux_2_28_x86_64", "py3-none-any"]}'
        )
        with patch("builtins.open", mock_open(read_data=platform_info)):
            # recipe_platform_info_start
            import json

            from req2flatpak import Platform

            # Run "req2flatpak --platform-info" on the target system and save the output to a file.
            # Then create a platform object from the data in this file:
            with open("platform-info.json", encoding="utf-8") as file:
                platform = Platform(**json.load(file))
            # recipe_platform_info_end
        self.assertEqual(platform.python_version, ["3", "14", "0"])
        self.assertEqual(len(platform.python_tags), 2)


class UnpinnedRequirementsRecipeTest(unittest.TestCase):
    """Recipe: requirements that are not pinned."""

    def test_unpinned_requirements_are_rejected(self):
        """Ensure that the parser rejects requirements that are not pinned."""
        with self.assertRaises(ValueError):
            RequirementsParser.parse_string("requests>=2.0")

    def test_pinned_requirements_are_accepted(self):
        """Ensure that the output of pip-compile style tools is accepted."""
        requirements = RequirementsParser.parse_string(
            "# This file is autogenerated by pip-compile\n"
            "requests==2.32.3\n"
            "    # via -r requirements.in\n"
        )
        self.assertEqual([r.package for r in requirements], ["requests"])
