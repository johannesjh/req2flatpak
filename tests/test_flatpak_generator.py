"""Automated tests for :class:req2flatpak.FlatpakGenerator."""

import unittest

from req2flatpak import Download, FlatpakGenerator, Requirement


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that code examples in the documentation keep working."""

    def setUp(self):
        """Create fresh data for each test, like a user would hold in a script."""
        self.requirements = [
            Requirement(package="scikit-learn", version="1.1.3"),
            Requirement(package="requests", version="2.28.1"),
        ]

        # pylint: disable=line-too-long
        self.downloads = {
            Download(
                package="scikit-learn",
                version="1.1.3",
                filename="scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
                url="https://files.pythonhosted.org/packages/23/b6/5d339516e3fbb6cde8ad87e85d9f17a3270c9e508c860785f0b6239ea33a/scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
                sha256="701181792a28c82fecae12adb5d15d0ecf57bffab7cf4bdbb52c7b3fd428d540",
            ),
            Download(
                package="requests",
                version="2.28.1",
                filename="requests-2.28.1-py3-none-any.whl",
                url="https://files.pythonhosted.org/packages/ca/91/6d9b8ccacd0412c08820f72cebaa4f0c0441b5cda699c90f618b6f8a1b42/requests-2.28.1-py3-none-any.whl",
                sha256="8fefa2a1a1365bf5520aac41836fbee479da67864514bdb821f31ce07ce65349",
            ),
        }

    def example_usage(self, requirements, downloads):
        """Demonstrates how to generate a build module."""
        # example_usage1_start
        # generate a flatpak build module:
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # example_usage1_end
        return build_module

    def test(self):
        """Ensures that the code example keeps working."""
        build_module = self.example_usage(self.requirements, self.downloads)
        self.assertIn("scikit-learn", build_module["build-commands"][0])
        self.assertIn("requests", build_module["build-commands"][0])
        self.assertTrue(
            any("scikit_learn" in source["url"] for source in build_module["sources"])
        )
        self.assertTrue(
            any("requests" in source["url"] for source in build_module["sources"])
        )


class MissingDownloadTest(unittest.TestCase):
    """Test the handling of missing downloads."""

    def setUp(self):
        """Create fresh data for each test."""
        self.requirements = [Requirement(package="requests", version="2.28.1")]
        self.downloads = {
            Download(
                package="requests",
                version="2.28.1",
                filename="requests-2.28.1-py3-none-any.whl",
                url="https://example.org/requests-2.28.1-py3-none-any.whl",
                sha256="0" * 64,
            )
        }

    def test_missing_download_raises_value_error(self):
        """Verify that a missing download gives a clear error instead of a TypeError."""
        for downloads in ({None}, {None, *self.downloads}):
            with self.subTest(downloads=downloads), self.assertRaises(ValueError):
                FlatpakGenerator.build_module(self.requirements, downloads)  # ty: ignore[invalid-argument-type]
