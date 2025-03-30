"""Test for the parsing of tags in wheel filenames."""

import unittest
from typing import Dict, Set

import req2flatpak


class TestTagsFromWheelFilename(unittest.TestCase):
    """
    Compatibility test for py:meth:`~req2flatpak.tags_from_wheel_filename`.

    This tests serves as future-compatibility test to safeguard against changes
    in the packaging package.
    """

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

    def test(self):
        """Tests the behavior of ``tags_from_wheel_filename``."""
        for filename, expected_tags in self.data.items():
            with self.subTest(filename=filename):
                parsed_tags = req2flatpak.tags_from_wheel_filename(filename)  # pylint: disable=not-callable
                self.assertEqual(parsed_tags, expected_tags)
                self.assertEqual(parsed_tags, expected_tags)
