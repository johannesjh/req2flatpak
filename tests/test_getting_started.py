"""Test the getting-started example of the recipes, using exactly the imports shown in the docs.

Do not import anything from req2flatpak at module level in this file.
The example function imports everything that it needs by itself.
If an import is missing in the example, the test fails with a ``NameError``,
because no other import can provide the name.
"""

import json
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import patch

PYPI_URL = "https://pypi.org/pypi/requests/2.28.1/json"
PYPI_RESPONSE = json.dumps(
    {
        "urls": [
            {
                "filename": filename,
                "url": f"https://files.example.org/{filename}",
                "digests": {"sha256": "0" * 64},
            }
            for filename in (
                "requests-2.28.1-py3-none-any.whl",
                "requests-2.28.1.tar.gz",
            )
        ]
    }
)


class GettingStartedTest(unittest.TestCase):
    """Test that the getting-started example runs with the imports that are shown."""

    def example(self):
        """Show how to get started with req2flatpak's python api."""
        # example_getting_started_start
        from req2flatpak import (
            DownloadChooser,
            FlatpakGenerator,
            PlatformFactory,
            PypiClient,
            RequirementsParser,
        )

        platforms = [PlatformFactory.from_string("cp314-x86_64")]
        requirements = RequirementsParser.parse_file("requirements.txt")
        releases = PypiClient.get_releases(requirements)
        downloads = {
            DownloadChooser.wheel_or_sdist(release, platform)
            for release in releases
            for platform in platforms
        }
        build_module = FlatpakGenerator.build_module(requirements, downloads)
        # example_getting_started_end
        return build_module

    def test(self):
        """Run the example in a directory with a requirements file, without network access."""
        with (
            tempfile.TemporaryDirectory() as tmp,
            chdir(tmp),
            patch.dict("req2flatpak.PypiClient.cache", {PYPI_URL: PYPI_RESPONSE}),
        ):
            Path("requirements.txt").write_text("requests==2.28.1\n", encoding="utf-8")
            build_module = self.example()

        self.assertIn("requests", build_module["build-commands"][0])
        self.assertEqual(len(build_module["sources"]), 1)
        self.assertTrue(build_module["sources"][0]["url"].endswith(".whl"))
