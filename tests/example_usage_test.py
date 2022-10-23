"""Example usage demo, with a regression test to make sure the demo keeps working."""


import unittest
from unittest.mock import patch


def example_usage():
    """Example showing how to use req2flatpak in your own script."""
    from req2flatpak import (
        DownloadChooser,
        FlatpakGenerator,
        PlatformFactory,
        PypiClient,
        RequirementsParser,
    )

    platforms = [PlatformFactory.from_string("cp310-x86_64")]
    requirements = RequirementsParser.parse_file("requirements.txt")
    releases = PypiClient.get_releases(requirements)
    downloads = {
        DownloadChooser.wheel_or_sdist(release, platform)
        for release in releases
        for platform in platforms
    }
    return FlatpakGenerator.manifest(requirements, downloads)


class ExampleUsageTest(unittest.TestCase):
    """Regression test to ensure that the example code above keeps working."""

    def test(self):
        """Regression test to ensure that the example code above keeps working."""
        from req2flatpak import RequirementsParser

        with patch.object(
            RequirementsParser,
            "parse_file",
            return_value=RequirementsParser.parse_string("requests == 2.28.1"),
        ):
            manifest = example_usage()
            assert manifest[
                "build-commands"
            ], "No build-commands section was found in the manifest."
            assert manifest["sources"], "No sources were found in the manifest."
            assert manifest["sources"][0]["type"] == "file"
            assert (
                "requests" in manifest["build-commands"][0]
            ), "The requests package was not found in the manifest's build command."
            assert (
                "requests" in manifest["sources"][0]["url"]
            ), "The requests package was not found in the manifest's sources."


if __name__ == "__main__":
    unittest.main()
