"""Automated tests for :class:req2flatpak.RequirementsParser."""

import pathlib
import unittest
from unittest.mock import patch

from req2flatpak import RequirementsParser


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that code examples in the documentation keep working."""

    requirements_txt = """
    # some popular python packages as exemplary requirements:
    numpy == 1.23.4
    pandas == 1.5.1
    matplotlib == 3.6.1
    scikit-learn == 1.1.3
    """

    def example_usage(self):
        """Demonstrates how to parse a requirements.txt file."""
        # example_usage1_start
        requirements = RequirementsParser.parse_file("requirements.txt")
        # example_usage1_end
        return requirements

    def test(self):
        """Ensures that the code example keeps working."""

        def mocked_pathlib_path_read_text(*_, **__) -> str:
            """A mock version of pathlib.Path.read_text."""
            return self.requirements_txt

        with patch.object(pathlib.Path, "read_text", mocked_pathlib_path_read_text):
            requirements = self.example_usage()

        assert len(requirements) == 4
