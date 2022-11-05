"""Test for the parsing of tags in wheel filenames."""

import unittest
from importlib import reload
from typing import Callable, Dict, List
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

    tags_from_wheel_using_packaging_package: Callable
    tags_from_wheel_without_packaging_package: Callable

    testdata: Dict[str, List[str]] = {
        "pandas-1.5.1-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl": [
            "cp310-cp310-manylinux2014_aarch64",
            "cp310-cp310-manylinux_2_17_aarch64",
        ],
        "requests-2.28.1-py3-none-any.whl": ["py3-none-any"],
        "scikit_learn-1.1.3-cp311-cp311-win_amd64.whl": ["cp311-cp311-win_amd64"],
        "scikit_learn-1.1.3-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl": [
            "cp311-cp311-manylinux2014_x86_64",
            "cp311-cp311-manylinux_2_17_x86_64",
        ],
    }

    @classmethod
    def setUpClass(cls):
        """Retrieves the two implementations of ``tags_from_wheel_filename``."""

        # Related work:
        # How to mock an ImportError: https://stackoverflow.com/a/62456280
        # How to mock a ModuleNotFoundError: https://stackoverflow.com/a/67884737
        # How to ignore certain imports: https://stackoverflow.com/a/63353431

        # get the implementation that uses the ``packaging`` package
        cls.tags_from_wheel_using_packaging_package = staticmethod(
            req2flatpak.tags_from_wheel_filename
        )

        # get the implementation that does not use the ``packaging`` package
        with mock.patch.dict("sys.modules", {"packaging.utils": None}):
            reload(req2flatpak)
            cls.tags_from_wheel_without_packaging_package = staticmethod(
                req2flatpak.tags_from_wheel_filename
            )

        # make sure we got two different implementations
        assert (
            cls.tags_from_wheel_using_packaging_package
            != cls.tags_from_wheel_without_packaging_package
        )

    def test(self):
        """Tests the behavior of ``tags_from_wheel_filename``."""

        for filename, tags in self.testdata.items():
            for tags_from_wheel in [
                self.tags_from_wheel_without_packaging_package,
                self.tags_from_wheel_using_packaging_package,
            ]:
                with self.subTest(filename=filename, function=tags_from_wheel.__name__):
                    self.assertEqual(tags_from_wheel(filename), tags)
