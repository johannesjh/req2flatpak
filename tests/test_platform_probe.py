"""Automated tests for reading platform info from a flatpak runtime.

No test runs flatpak: the calls of ``subprocess.run`` are replaced.
"""

import ast
import contextlib
import inspect
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import req2flatpak
from req2flatpak import (
    Platform,
    PlatformFactory,
    PlatformProbeError,
    Requirement,
    _probe,
)

PROBE_OUTPUT = {
    "implementation": "CPython",
    "python_version": ["3", "14", "9"],
    "glibc": "glibc 2.44",
    "machine": "x86_64",
    "packages": {"Jinja2": "3.1.6", "MarkupSafe": "3.0.2", "jinja2": "0.0"},
    "tags": ["cp314-cp314-manylinux_2_44_x86_64", "py3-none-any"],
}


def completed(stdout="", stderr="", returncode=0):
    """Return what ``subprocess.run`` returns for a finished process."""
    return subprocess.CompletedProcess(
        args=[], returncode=returncode, stdout=stdout, stderr=stderr
    )


def probe_result(**changes):
    """Return a successful result of the probe, with optional changes."""
    return completed(stdout=json.dumps({**PROBE_OUTPUT, **changes}) + "\n")


class ProbeTest(unittest.TestCase):
    """Tests for the function that runs inside the flatpak runtime."""

    def test_structure(self):
        """Ensure that the probe returns the facts with the agreed keys."""
        data = _probe()
        self.assertEqual(
            set(data),
            {
                "implementation",
                "python_version",
                "glibc",
                "machine",
                "packages",
                "tags",
            },
        )
        self.assertEqual(data["implementation"], "CPython")
        self.assertEqual(len(data["python_version"]), 3)
        self.assertTrue(data["glibc"].startswith("glibc "))
        self.assertIn("packaging", {name.lower() for name in data["packages"]})
        self.assertIn("py3-none-any", data["tags"])
        json.dumps(data)

    def test_packages_have_no_duplicates(self):
        """Ensure that the first one wins if a package occurs twice."""

        class Distribution:
            def __init__(self, name, version):
                self.metadata = {"Name": name}
                self.version = version

        distributions = [Distribution("foo", "1"), Distribution("foo", "2")]
        with patch("importlib.metadata.distributions", return_value=distributions):
            self.assertEqual(_probe()["packages"], {"foo": "1"})

    def test_is_self_contained(self):
        """Ensure that the source code runs without the req2flatpak module."""
        source = inspect.getsource(_probe)
        namespace: dict = {}
        exec(source, namespace)  # noqa: S102  # runs our own source code
        data = namespace["_probe"]()
        self.assertEqual(data["implementation"], "CPython")

    def test_is_python38_syntax(self):
        """Ensure that the source code parses as python 3.8."""
        ast.parse(inspect.getsource(_probe), feature_version=(3, 8))

    def test_source_is_a_module_level_function(self):
        """Ensure that the source is not indented, so that it can be executed."""
        self.assertTrue(inspect.getsource(_probe).startswith("def _probe():"))

    def test_without_tag_source_tags_are_none(self):
        """Ensure that missing tag sources result in ``tags: None``."""
        with patch("importlib.import_module", side_effect=ImportError):
            self.assertIsNone(_probe()["tags"])

    def test_tags_come_from_the_next_source(self):
        """Ensure that the probe tries one source after the other."""

        class Tags:
            @staticmethod
            def sys_tags():
                return ["py3-none-any"]

        def import_module(name):
            if name == "pip._vendor.packaging.tags":
                return Tags
            raise ImportError(name)

        with patch("importlib.import_module", side_effect=import_module):
            self.assertEqual(_probe()["tags"], ["py3-none-any"])

    def test_musl_is_rejected(self):
        """Ensure that a missing glibc results in a clear error."""
        with (
            patch("os.confstr", return_value=""),
            self.assertRaisesRegex(RuntimeError, "glibc"),
        ):
            _probe()

    def test_other_implementation_is_rejected(self):
        """Ensure that an interpreter other than CPython results in a clear error."""
        with (
            patch("platform.python_implementation", return_value="PyPy"),
            self.assertRaisesRegex(RuntimeError, "CPython"),
        ):
            _probe()


class FromFlatpakRuntimeTest(unittest.TestCase):
    """Tests for ``PlatformFactory.from_flatpak_runtime``."""

    def read(self, ref="org.gnome.Platform//51", installation=None, **kwargs):
        """Call from_flatpak_runtime, with subprocess.run replaced."""
        with patch("subprocess.run", **kwargs) as run:
            platform = PlatformFactory.from_flatpak_runtime(ref, installation)
        return platform, run

    def test_success(self):
        """Ensure that the platform is built from the facts of the probe."""
        platform, run = self.read(return_value=probe_result())
        self.assertEqual(platform.python_version, ["3", "14", "9"])
        self.assertEqual(platform.python_tags, PROBE_OUTPUT["tags"])
        self.assertEqual(platform.arch, "x86_64")
        self.assertEqual(platform.glibc_version, "2.44")
        self.assertEqual(platform.runtime, "org.gnome.Platform//51")
        self.assertEqual(
            platform.installed_packages, {"jinja2": "3.1.6", "markupsafe": "3.0.2"}
        )
        command = run.call_args.args[0]
        self.assertEqual(command[:2], ["flatpak", "run"])
        self.assertEqual(command[2:4], ["--command=python3", "org.gnome.Platform//51"])
        self.assertEqual(command[4], "-c")
        self.assertIn("def _probe():", command[5])
        self.assertIn("print(json.dumps(_probe()))", command[5])
        self.assertEqual(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(run.call_args.kwargs["timeout"], 120)

    def test_the_probe_source_runs(self):
        """Ensure that the source sent to the runtime really prints the facts."""
        _, run = self.read(return_value=probe_result())
        script = run.call_args.args[0][5]
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-c", script], capture_output=True, text=True, check=True
        )
        self.assertEqual(json.loads(result.stdout)["implementation"], "CPython")

    def test_installation_options(self):
        """Ensure that the installation is passed on to flatpak."""
        for installation, option in [
            ("user", "--user"),
            ("system", "--system"),
            ("mine", "--installation=mine"),
        ]:
            with self.subTest(installation=installation):
                _, run = self.read(
                    installation=installation, return_value=probe_result()
                )
                self.assertEqual(run.call_args.args[0][2], option)

    def test_ref_with_matching_architecture(self):
        """Ensure that an architecture in the ref is accepted if it matches."""
        platform, _ = self.read(
            ref="org.gnome.Platform/aarch64/51",
            return_value=probe_result(machine="aarch64"),
        )
        self.assertEqual(platform.arch, "aarch64")
        self.assertEqual(platform.runtime, "org.gnome.Platform/aarch64/51")

    def test_wrong_architecture(self):
        """Ensure that an architecture that differs from the ref is an error."""
        with self.assertRaisesRegex(PlatformProbeError, "aarch64"):
            self.read(ref="org.gnome.Platform/aarch64/51", return_value=probe_result())

    def test_unsupported_architecture(self):
        """Ensure that an unsupported architecture is an error."""
        with self.assertRaisesRegex(PlatformProbeError, "riscv64"):
            self.read(return_value=probe_result(machine="riscv64"))

    def test_musl(self):
        """Ensure that a runtime without glibc is an error."""
        with self.assertRaisesRegex(PlatformProbeError, "glibc"):
            self.read(return_value=probe_result(glibc="musl"))

    def test_without_tags_the_heuristic_is_used(self):
        """Ensure that tags are derived from the glibc version, with a warning."""
        with self.assertLogs("req2flatpak", level="WARNING") as logs:
            platform, _ = self.read(return_value=probe_result(tags=None))
        self.assertIn("derived", logs.output[0])
        self.assertEqual(
            platform,
            Platform(
                python_version=["3", "14", "9"],
                python_tags=PlatformFactory.from_python_version_and_arch(
                    minor_version=14, manylinux_max=44
                ).python_tags,
                arch="x86_64",
                glibc_version="2.44",
                runtime="org.gnome.Platform//51",
                installed_packages={"jinja2": "3.1.6", "markupsafe": "3.0.2"},
            ),
        )

    def test_without_tags_and_old_glibc(self):
        """Ensure that a glibc that is too old is a clear error."""
        with (
            self.assertLogs("req2flatpak", level="WARNING"),
            self.assertRaisesRegex(PlatformProbeError, "17"),
        ):
            self.read(return_value=probe_result(tags=None, glibc="glibc 2.12"))

    def test_runtime_not_installed(self):
        """Ensure that the message tells how to install the runtime."""
        with self.assertRaisesRegex(PlatformProbeError, "flatpak install"):
            self.read(
                return_value=completed(
                    stderr="error: app/org.gnome.Platform/x86_64/99 not installed\n",
                    returncode=1,
                )
            )

    def test_ambiguous_installation(self):
        """Ensure that the message points to --user and --system."""
        for stderr in [
            "error: Similar installed refs found for 'x', choose one:\n",
            "error: No ref chosen to resolve matches for 'x'\n",
        ]:
            with (
                self.subTest(stderr=stderr),
                self.assertRaisesRegex(PlatformProbeError, "--user, --system"),
            ):
                self.read(return_value=completed(stderr=stderr, returncode=1))

    def test_foreign_architecture_without_emulation(self):
        """Ensure that the message names qemu-user and binfmt."""
        stderr = (
            "bwrap: execvp ldconfig: Exec format error\n"
            "error: ldconfig failed, exit status 256\n"
        )
        with self.assertRaisesRegex(PlatformProbeError, "qemu-user"):
            self.read(return_value=completed(stderr=stderr, returncode=1))

    def test_python_missing(self):
        """Ensure that a runtime without python3 is an error."""
        stderr = "bwrap: execvp python3: No such file or directory\n"
        with self.assertRaisesRegex(PlatformProbeError, "python3"):
            self.read(return_value=completed(stderr=stderr, returncode=1))

    def test_probe_failure_shows_stderr(self):
        """Ensure that the error of the probe is part of the message."""
        with self.assertRaisesRegex(PlatformProbeError, "only glibc is supported"):
            self.read(
                return_value=completed(
                    stderr="RuntimeError: only glibc is supported.\n", returncode=1
                )
            )

    def test_flatpak_missing(self):
        """Ensure that a missing flatpak command is an error."""
        with self.assertRaisesRegex(PlatformProbeError, "'flatpak' command"):
            self.read(side_effect=FileNotFoundError)

    def test_invalid_json(self):
        """Ensure that invalid output of the probe is an error."""
        for stdout in ["not json", "[]", json.dumps({"machine": "x86_64"})]:
            with (
                self.subTest(stdout=stdout),
                self.assertRaisesRegex(PlatformProbeError, "invalid"),
            ):
                self.read(return_value=completed(stdout=stdout))

    def test_timeout(self):
        """Ensure that a timeout is an error."""
        with self.assertRaisesRegex(PlatformProbeError, "timed out"):
            self.read(side_effect=subprocess.TimeoutExpired("flatpak", 120))


class DataModelTest(unittest.TestCase):
    """Tests for the additional fields of the platform, files and filtering."""

    platform = Platform(
        python_version=["3", "14", "9"],
        python_tags=["cp314-cp314-manylinux_2_44_x86_64", "py3-none-any"],
        arch="x86_64",
        glibc_version="2.44",
        runtime="org.gnome.Platform//51",
        installed_packages={"jinja2": "3.1.6"},
    )

    def test_old_platform_has_defaults(self):
        """Ensure that platforms without the new fields keep working."""
        platform = Platform(python_version=["3", "14"], python_tags=["py3-none-any"])
        self.assertIsNone(platform.arch)
        self.assertIsNone(platform.glibc_version)
        self.assertIsNone(platform.runtime)
        self.assertEqual(platform.installed_packages, {})
        self.assertEqual(
            req2flatpak._platform_as_dict(platform),
            {"python_version": ["3", "14"], "python_tags": ["py3-none-any"]},
        )

    def test_old_files_load_unchanged(self):
        """Ensure that the existing platform info files can be loaded."""
        for path in Path(__file__).parent.glob("cp310-*.platforminfo.json"):
            with self.subTest(path=path.name), open(path, encoding="utf-8") as file:
                expected = Platform(**json.load(file))
                self.assertEqual(PlatformFactory.from_file(path), expected)

    def test_recorded_example_file(self):
        """Ensure that the platform info recorded from GNOME 51 can be loaded."""
        path = Path(__file__).parent / "org.gnome.Platform-51-x86_64.platforminfo.json"
        platform = PlatformFactory.from_file(path)
        self.assertEqual(platform.runtime, "org.gnome.Platform//51")
        self.assertEqual(platform.arch, "x86_64")
        self.assertEqual(platform.glibc_version, "2.44")
        self.assertEqual(platform.python_version[:2], ["3", "14"])
        self.assertIn("cp314-cp314-manylinux_2_44_x86_64", platform.python_tags)
        self.assertEqual(len(platform.python_version), 3)
        self.assertIn("jinja2", platform.installed_packages)

    def test_roundtrip(self):
        """Ensure that object, JSON and object give the same platform."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.platforminfo.json"
            path.write_text(json.dumps(req2flatpak._platform_as_dict(self.platform)))
            self.assertEqual(PlatformFactory.from_file(path), self.platform)

    def test_yaml(self):
        """Ensure that YAML files are read."""
        if not req2flatpak.yaml:
            self.skipTest("pyyaml is not installed")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "x.platforminfo.yaml"
            path.write_text(
                req2flatpak.yaml.dump(req2flatpak._platform_as_dict(self.platform))
            )
            self.assertEqual(PlatformFactory.from_file(path), self.platform)

    def test_invalid_files(self):
        """Ensure that invalid files raise errors that name the file."""
        with tempfile.TemporaryDirectory() as directory:
            for name, content in [
                ("unknown.json", '{"python_version": [], "python_tags": [], "x": 1}'),
                ("missing.json", '{"python_version": []}'),
                ("broken.json", "{"),
                ("list.json", "[]"),
            ]:
                with self.subTest(name=name):
                    path = Path(directory) / name
                    path.write_text(content)
                    with self.assertRaisesRegex(ValueError, name):
                        PlatformFactory.from_file(path)
            with self.assertRaises(FileNotFoundError):
                PlatformFactory.from_file(Path(directory) / "nothing.json")

    def test_without_installed(self):
        """Ensure that only requirements in the same version are removed."""
        requirements = [
            Requirement("Jinja2", "3.1.6"),
            Requirement("MarkupSafe", "3.0.2"),
            Requirement("jinja2-extra", "1.0"),
            Requirement("foo", "1.0"),
        ]
        platform = Platform(
            python_version=["3", "14"],
            python_tags=[],
            installed_packages={
                "jinja2": "3.1.6",
                "MarkupSafe": "3.0.1",
                "foo": "1.0.0",
                "jinja2-extra": "bad version",
            },
        )
        self.assertEqual(
            platform.without_installed(requirements),
            [Requirement("MarkupSafe", "3.0.2"), Requirement("jinja2-extra", "1.0")],
        )
        self.assertEqual(len(requirements), 4)


class CommandlineTest(unittest.TestCase):
    """Tests for the commandline options of platform info."""

    def run_main(self, *args, **kwargs):
        """Run main() and return (exit code, stdout, stderr)."""
        stdout, stderr = io.StringIO(), io.StringIO()
        code = 0
        with (
            patch.object(sys, "argv", ["req2flatpak", *args]),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
            patch("subprocess.run", **kwargs) as self.subprocess_run,
        ):
            try:
                req2flatpak.main()
            except SystemExit as exit_:
                code = exit_.code or 0
        return code, stdout.getvalue(), stderr.getvalue()

    def test_platform_info_without_ref_is_unchanged(self):
        """Ensure that the current platform is described, without the new fields."""
        code, stdout, _ = self.run_main("--platform-info")
        self.assertEqual(code, 0)
        self.assertEqual(set(json.loads(stdout)), {"python_version", "python_tags"})

    def test_platform_info_for_runtime(self):
        """Ensure that the platform of a runtime is printed, and --user is passed."""
        code, stdout, _ = self.run_main(
            "--platform-info",
            "org.gnome.Platform//51",
            "--user",
            return_value=probe_result(),
        )
        self.assertEqual(code, 0)
        data = json.loads(stdout)
        self.assertEqual(
            list(data),
            [
                "python_version",
                "python_tags",
                "arch",
                "glibc_version",
                "runtime",
                "installed_packages",
            ],
        )
        self.assertEqual(data["runtime"], "org.gnome.Platform//51")

    def test_installation_option_is_passed(self):
        """Ensure that --installation reaches flatpak."""
        self.run_main(
            "--platform-info",
            "x//1",
            "--installation",
            "mine",
            return_value=probe_result(),
        )
        self.assertEqual(
            self.subprocess_run.call_args.args[0][2], "--installation=mine"
        )

    def test_installation_options_need_a_ref(self):
        """Ensure that --user and friends are rejected without a ref."""
        for args in [("--user",), ("--platform-info", "--system")]:
            with self.subTest(args=args):
                code, _, stderr = self.run_main(*args)
                self.assertEqual(code, 2)
                self.assertIn("require --platform-info REF", stderr)

    def test_installation_options_are_exclusive(self):
        """Ensure that only one of the installation options is allowed."""
        code, _, _ = self.run_main("--platform-info", "x//1", "--user", "--system")
        self.assertEqual(code, 2)

    def test_probe_error_exits_with_2(self):
        """Ensure that errors are reported with exit code 2."""
        code, stdout, stderr = self.run_main(
            "--platform-info", "x//1", side_effect=FileNotFoundError
        )
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("'flatpak' command", stderr)


class TargetPlatformsTest(unittest.TestCase):
    """Tests for ``-t`` with files and strings."""

    def setUp(self):
        """Create a platform info file, and replace the access to PyPI."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.file = Path(directory.name) / "gnome.platforminfo.json"
        self.file.write_text(
            json.dumps(
                req2flatpak._platform_as_dict(
                    Platform(
                        python_version=["3", "14", "9"],
                        python_tags=["cp314-cp314-manylinux_2_44_x86_64"],
                    )
                )
            )
        )
        self.platforms = []

        def wheel_or_sdist(release, platform):
            self.platforms.append(platform)
            return req2flatpak.Download(
                package="foo",
                version="1.0",
                filename="foo-1.0.tar.gz",
                url="https://example.org/foo-1.0.tar.gz",
                sha256="0" * 64,
            )

        patchers = [
            patch.object(
                req2flatpak.PypiClient,
                "get_releases",
                return_value=[req2flatpak.Release("foo", "1.0")],
            ),
            patch.object(
                req2flatpak.DownloadChooser,
                "wheel_or_sdist",
                side_effect=wheel_or_sdist,
            ),
        ]
        for patcher in patchers:
            patcher.start()
            self.addCleanup(patcher.stop)

    def run_main(self, *targets):
        """Run main() with the targets, and return the exit code."""
        argv = ["req2flatpak", "--requirements", "foo==1.0", "-t", *targets]
        with (
            patch.object(sys, "argv", argv),
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            try:
                req2flatpak.main()
            except SystemExit as exit_:
                return exit_.code
        return 0

    def test_file(self):
        """Ensure that a platform info file is used as target platform."""
        self.assertEqual(self.run_main(str(self.file)), 0)
        self.assertEqual(self.platforms, [PlatformFactory.from_file(self.file)])

    def test_string(self):
        """Ensure that short strings still work."""
        self.assertEqual(self.run_main("314-x86_64"), 0)
        self.assertEqual(self.platforms, [PlatformFactory.from_string("314-x86_64")])

    def test_file_and_string_in_given_order(self):
        """Ensure that files and strings can be mixed."""
        self.assertEqual(self.run_main("314-aarch64", str(self.file)), 0)
        self.assertEqual(
            self.platforms,
            [
                PlatformFactory.from_string("314-aarch64"),
                PlatformFactory.from_file(self.file),
            ],
        )

    def test_errors_exit_with_2(self):
        """Ensure that unusable target platforms are errors."""
        for target in [
            "missing.platforminfo.json",
            "garbage",
            "314-riscv",
            "314-x86_64 314-aarch64",
        ]:
            with self.subTest(target=target):
                self.assertEqual(self.run_main(target), 2)
        self.assertEqual(self.platforms, [])

    def test_invalid_file_exits_with_2(self):
        """Ensure that an invalid file is an error."""
        self.file.write_text('{"python_version": []}')
        self.assertEqual(self.run_main(str(self.file)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
