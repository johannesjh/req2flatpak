"""Example usage demo, with a regression test to make sure the demo keeps working."""

import unittest
from unittest.mock import patch

from req2flatpak import (
    DownloadChooser,
    FlatpakGenerator,
    PlatformFactory,
    PypiClient,
    RequirementsParser,
)


class ExampleUsageTest(unittest.TestCase):
    """Regression test to ensure that the code for the above usage example keeps working."""

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
            assert build_module[
                "build-commands"
            ], "No build-commands section was found in the build module."
            assert build_module["sources"], "No sources were found in the build module."
            assert build_module["sources"][0]["type"] == "file"
            assert (
                "requests" in build_module["build-commands"][0]
            ), "The requests package was not found in the build module's build command."
            assert (
                "requests" in build_module["sources"][0]["url"]
            ), "The requests package was not found in the build module's sources."


if __name__ == "__main__":
    unittest.main()
