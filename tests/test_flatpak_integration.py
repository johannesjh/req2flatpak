"""Integration tests that run flatpak for real.

These tests need flatpak and an installed GNOME 51 runtime, the aarch64 test
also needs the aarch64 runtime and an emulation (qemu-user with binfmt_misc).
Tests are skipped if something is missing, so that they can run on machines
without flatpak, e.g., in CI.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from req2flatpak import PlatformFactory, PlatformProbeError

RUNTIME = "org.gnome.Platform//51"
RECORDED = Path(__file__).parent / "org.gnome.Platform-51-x86_64.platforminfo.json"


def runtime_installed(ref: str, installation: str = "user") -> bool:
    """Return True if flatpak is available and the runtime is installed."""
    if not shutil.which("flatpak"):
        return False
    result = subprocess.run(  # noqa: S603
        ["flatpak", "info", f"--{installation}", ref],  # noqa: S607
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )
    return result.returncode == 0


class FlatpakRuntimeIntegrationTest(unittest.TestCase):
    """Tests that read the platform from a real flatpak runtime."""

    @unittest.skipUnless(
        runtime_installed("org.gnome.Platform/x86_64/51"),
        "flatpak or the GNOME 51 runtime (user installation) is not available",
    )
    def test_x86_64_matches_recorded_file(self):
        """Ensure that the recorded example file still matches the runtime."""
        platform = PlatformFactory.from_flatpak_runtime(RUNTIME, installation="user")
        with open(RECORDED, encoding="utf-8") as file:
            recorded = json.load(file)
        self.assertEqual(platform.arch, "x86_64")
        self.assertEqual(platform.python_version, recorded["python_version"])
        self.assertEqual(platform.glibc_version, recorded["glibc_version"])
        self.assertLessEqual(set(recorded["python_tags"]), set(platform.python_tags))
        self.assertEqual(platform.installed_packages, recorded["installed_packages"])

    @unittest.skipUnless(
        runtime_installed("org.gnome.Platform/aarch64/51"),
        "flatpak or the GNOME 51 aarch64 runtime (user installation) is not available",
    )
    def test_aarch64(self):
        """Ensure that the aarch64 runtime is read, if the emulation works."""
        try:
            platform = PlatformFactory.from_flatpak_runtime(
                "org.gnome.Platform/aarch64/51", installation="user"
            )
        except PlatformProbeError as error:
            if "qemu-user" in str(error):
                self.skipTest("no emulation for aarch64 (qemu-user, binfmt_misc)")
            raise
        self.assertEqual(platform.arch, "aarch64")
        self.assertTrue(
            any(tag.endswith("manylinux_2_17_aarch64") for tag in platform.python_tags)
        )

    @unittest.skipUnless(
        runtime_installed("org.gnome.Platform/x86_64/51"),
        "flatpak or the GNOME 51 runtime (user installation) is not available",
    )
    def test_runtime_not_installed(self):
        """Ensure that flatpak's answer for a missing runtime is recognized."""
        with self.assertRaisesRegex(PlatformProbeError, "not installed"):
            PlatformFactory.from_flatpak_runtime(
                "org.gnome.Platform//99", installation="user"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
