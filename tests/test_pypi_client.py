"""Automated tests for :class:req2flatpak.PypiClient."""
import contextlib
import importlib
import unittest
from typing import List
from unittest.mock import patch

import tests
from req2flatpak import PypiClient, Release, Requirement, RequirementsParser


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that code examples in the documentation keep working."""

    requirements = RequirementsParser.parse_string("requests == 2.28.1")

    cache = {
        "https://pypi.org/pypi/requests/2.28.1/json": importlib.resources.files(tests)
        .joinpath("test_pypi_client_requests2.28.1.json")
        .read_text(encoding="utf-8")
    }

    def example_usage(self, requirements: List[Requirement]) -> List[Release]:
        """Demonstrates how to use PypiClient."""
        # example_usage1_start
        releases = PypiClient.get_releases(requirements)
        # example_usage1_end
        return releases

    def example_usage_with_caching(
        self, requirements: List[Requirement]
    ) -> List[Release]:
        """Demonstrates how to use caching when querying pypi."""
        # pylint: disable=import-outside-toplevel
        # example_usage2_start
        import shelve

        with shelve.open("pypi_cache.tmp") as cache:
            PypiClient.cache = cache
            releases = PypiClient.get_releases(requirements)
        # example_usage2_end
        return releases

    def test_example_usage(self):
        """Ensures that example_usage keeps working."""
        PypiClient.cache = self.cache
        releases = self.example_usage(self.requirements)
        assert len(releases) == 1
        assert releases[0].package == "requests"

    def test_example_usage_with_caching(self):
        """Ensures that example_usage keeps working."""

        # prepare mocked cache
        def mocked_shelve_open(*_, **__):
            """A mock version of ``shelve.open`` that returns a simple dict to be used as cache."""
            print("here the mocked contextmgr")
            return contextlib.nullcontext(enter_result=self.cache)

        # test with caching
        with patch("shelve.open", new=mocked_shelve_open):
            releases = self.example_usage_with_caching(self.requirements)
            assert len(releases) == 1
            assert releases[0].package == "requests"
