"""Test for the parsing of tags in wheel filenames."""

import unittest
from importlib import reload
from typing import Callable, Dict, Optional, Set
from unittest import mock

import req2flatpak


class TestTagsFromWheelFilename(unittest.TestCase):
    """
    Compatibility test for py:meth:`~req2flatpak.tags_from_wheel_filename`.

    The need for this test comes from the fact that req2flatpak contains two
    alternative implementations of ``tags_from_wheel_filename``:
    A vendored implementation that does not need the packaging package.
    And another implementation that relies on functionality from the packaging
    package.

    Both implementations of ``tags_from_wheel_filename`` are tested using the
    same testdata to ensure that their behavior is correct and equal.
    The test thus serves as regression test for the vendored implementation.
    And it also serves as future-compatibility test to safeguard against changes
    in the packaging package.
    """

    implementations: Dict[str, Optional[Callable]] = {
        "with_packaging": None,
        "without_packaging": None,
    }

    data: Dict[str, Set[str]] = {
        "pandas-1.5.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl": {
            "cp310-cp310-manylinux_2_17_aarch64",
            "cp310-cp310-manylinux2014_aarch64",
        },
        "requests-2.28.1-py3-none-any.whl": {"py3-none-any"},
        "scikit_learn-1.1.3-cp311-cp311-win_amd64.whl": {"cp311-cp311-win_amd64"},
        "scikit_learn-1.1.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl": {
            "cp311-cp311-manylinux_2_17_x86_64",
            "cp311-cp311-manylinux2014_x86_64",
        },
    }

    @classmethod
    def setUpClass(cls):
        """Retrieves the two implementations of ``tags_from_wheel_filename``."""

        # get the implementation that does not use the ``packaging`` package
        # related work:
        # - how to mock a ModuleNotFoundError: https://stackoverflow.com/a/67884737
        # - how to ignore certain imports: https://stackoverflow.com/a/63353431
        with mock.patch.dict("sys.modules", {"packaging.utils": None}):
            reload(req2flatpak)
            cls.implementations[
                "without_packaging"
            ] = req2flatpak.tags_from_wheel_filename

        # get the implementation that uses the ``packaging`` package
        reload(req2flatpak)
        cls.implementations["with_packaging"] = req2flatpak.tags_from_wheel_filename

        # ensure that we got two different implementations
        assert (
            cls.implementations["without_packaging"]
            != cls.implementations["with_packaging"]
        )

    def test(self):
        """Tests the behavior of ``tags_from_wheel_filename``."""
        for filename, expected_tags in self.data.items():
            for description, func in self.implementations.items():
                with self.subTest(filename=filename, impl=description):
                    parsed_tags = func(filename)  # pylint: disable=not-callable
                    self.assertEqual(parsed_tags, expected_tags)
