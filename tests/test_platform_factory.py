"""Automated tests for :class:req2flatpak.PlatformFactory."""

import json
import re
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Union

from req2flatpak import PlatformFactory


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that code examples in the documentation keep working."""

    def example_usage(self):
        """Demonstrates how to create a platform object from string."""
        # example_usage1_start
        platform = PlatformFactory.from_string("cp310-x86_64")
        # example_usage1_end
        return platform

    def test(self):
        """Ensures that the code example keeps working."""
        platform = self.example_usage()
        assert platform.python_version == ["3", "10"]
        assert any("x86_64" in tag for tag in platform.python_tags)
        assert all("aarch" not in tag for tag in platform.python_tags)


@dataclass
class RegressionTestData:
    """Represents a target platform (minor_version, architecture) and saved platform info."""

    minor_version: int
    architecture: str
    platforminfo_file: Union[str, Path]


class RegressionTest(unittest.TestCase):
    """Regression test to verify that req2flatpak's platform factory returns correct platform tags."""

    platform_pattern = r"^(?:py|cp)?(\d)(\d+)-(.*)$"
    filename_pattern = r"^(?:py|cp)?(\d)(\d+)-(.*)\.platforminfo.json$"

    @staticmethod
    def _load_platform_tags_from_file(filename: Union[Path, str]) -> List[str]:
        """Returns the list of platform tags from a platforminfo .json file."""
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data["python_tags"]

    @classmethod
    def _testdata(cls) -> Iterable[RegressionTestData]:
        """Yields testdata for subtests."""
        platforminfo_files = [
            entry
            for entry in Path(__file__).parent.iterdir()
            if entry.is_file() and re.match(cls.filename_pattern, entry.name)
        ]
        for file in platforminfo_files:
            # parse platform string from filename:
            platform_string_match = re.match(r"(.*)\.platforminfo\.json", file.name)
            assert platform_string_match is not None
            platform_string = platform_string_match.group(1)

            # parse version and architecture from platform string:
            platform_string_match = re.match(cls.platform_pattern, platform_string)
            assert platform_string_match is not None
            major, minor, arch = platform_string_match.groups()
            assert major == "3"
            yield RegressionTestData(
                minor_version=int(minor), architecture=arch, platforminfo_file=file
            )

    def test(self):
        """Runs the test case."""

        for data in self._testdata():
            with self.subTest(platforminfo=data.platforminfo_file):
                expected_tags = self._load_platform_tags_from_file(
                    data.platforminfo_file
                )
                generated_tags = PlatformFactory.from_python_version_and_arch(
                    minor_version=int(data.minor_version), arch=data.architecture
                ).python_tags
                assert expected_tags == generated_tags


if __name__ == "__main__":
    unittest.main(verbosity=2)
