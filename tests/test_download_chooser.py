"""Automated tests for :class:req2flatpak.DownloadChooser."""

import unittest
from typing import Optional

from req2flatpak import Download, DownloadChooser, Platform, PlatformFactory, Release

# pylint: disable=line-too-long
scikit_learn_release = Release(
    package="scikit-learn",
    version="1.1.3",
    downloads=[
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp310-cp310-macosx_10_9_x86_64.whl",
            url="https://files.pythonhosted.org/packages/22/17/0b7adb6df00a30bc2c4a9e30e7f1c0c611035e2a5e22721b1bec0c2a5ffc/scikit_learn-1.1.3-cp310-cp310-macosx_10_9_x86_64.whl",
            sha256="8e9dd76c7274055d1acf4526b8efb16a3531c26dcda714a0c16da99bf9d41900",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            url="https://files.pythonhosted.org/packages/23/b9/78099838802cca1c8bfd985212c2df098a062e9b1df70845764e65685e3e/scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            sha256="da5a2e95fef9805b1750e4abda4e834bf8835d26fc709a391543b53feee7bd0e",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            url="https://files.pythonhosted.org/packages/23/b6/5d339516e3fbb6cde8ad87e85d9f17a3270c9e508c860785f0b6239ea33a/scikit_learn-1.1.3-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            sha256="701181792a28c82fecae12adb5d15d0ecf57bffab7cf4bdbb52c7b3fd428d540",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp310-cp310-win_amd64.whl",
            url="https://files.pythonhosted.org/packages/fe/28/2b78c8efceeb07e73cef24af458dd8241cc6c4b39abc7bf375ba38b07d28/scikit_learn-1.1.3-cp310-cp310-win_amd64.whl",
            sha256="30e27721adc308e8fd9f419f43068e43490005f911edf4476a9e585059fa8a83",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            url="https://files.pythonhosted.org/packages/0b/b2/317c4f9001567057cd197eb56a4baeb3567da86509c890d2ed9edac5ffa8/scikit_learn-1.1.3-cp38-cp38-manylinux_2_17_aarch64.manylinux2014_aarch64.whl",
            sha256="cd55c6fbef7608dbce1f22baf289dfcc6eb323247daa3c3542f73d389c724786",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            url="https://files.pythonhosted.org/packages/f9/90/b76a42bb6e97d3296787c8926e7610b0485918a2efa219a9614eb1a068b2/scikit_learn-1.1.3-cp38-cp38-manylinux_2_17_x86_64.manylinux2014_x86_64.whl",
            sha256="38814f66285318f2e241305cca545eaa9b4126c65aa5dd78c69371f235f78e2b",
        ),
        Download(
            package="scikit-learn",
            version="1.1.3",
            filename="scikit_learn-1.1.3-cp38-cp38-win_amd64.whl",
            url="https://files.pythonhosted.org/packages/67/41/55197045c3ea6b443977eb0222a98b4f5276a3aae3856baa57f39fdfea8e/scikit_learn-1.1.3-cp38-cp38-win_amd64.whl",
            sha256="f4931f2a6c06e02c6c17a05f8ae397e2545965bc7a0a6cb38c8cd7d4fba8624d",
        ),
    ],
)


class ExampleUsageTest(unittest.TestCase):
    """Test to ensure that code examples in the documentation keep working."""

    def example_usage(self, release: Release, platform: Platform) -> Optional[Download]:
        """Demonstrates how to use the DownloadChooser class."""
        # example_usage1_start
        # choose the best wheel for a target platform:
        wheel = DownloadChooser.wheel(release, platform)
        # example_usage1_end
        return wheel

    def test(self):
        """Ensures that the code example keeps working."""
        wheel = self.example_usage(
            scikit_learn_release, PlatformFactory.from_string("cp310-x86_64")
        )
        assert wheel.is_wheel
        assert wheel.arch == "x86_64"
        assert "scikit_learn" in wheel.filename
        assert "cp310" in wheel.filename
        assert "manylinux" in wheel.filename
