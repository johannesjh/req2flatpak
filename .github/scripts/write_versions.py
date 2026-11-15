"""Helper script for publishing the documentation: writes versions.txt.

The documentation is published on GitHub Pages, with one directory per version
(e.g., main, v0.3.2, or a docs branch). The CI action .github/actions/publish-docs
runs this script before it publishes, to update the list of all versions.
The script is not part of the req2flatpak package, and it is not used at runtime.

The script writes the list to versions.txt, one version per line. The version
switcher menu in docs/source/_templates/layout.html reads this file in the browser.

Versions are the directories on the gh-pages branch plus the directories that
are about to be published. They are sorted as: main, tags (newest first), rest.

Usage: python .github/scripts/write_versions.py <directory-to-be-published>
"""

import subprocess
import sys
from pathlib import Path


def git_lines(*args: str) -> list[str]:
    """Run git and return the non-empty output lines."""
    out = subprocess.run(  # noqa: S603  # arguments are fixed by this script
        ["git", *args],  # noqa: S607  # git is expected on the PATH
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def main(directory: Path, ref: str = "origin/gh-pages") -> None:
    """Write versions.txt into the given directory."""
    try:
        builds = set(git_lines("ls-tree", "-d", "--name-only", ref))
    except subprocess.CalledProcessError:
        builds = set()
        print(f"warning: cannot list directories of {ref}", file=sys.stderr)

    builds |= {child.name for child in directory.iterdir() if child.is_dir()}

    tags = git_lines("tag", "-l", "--sort=-v:refname")
    versions = [v for v in ["master", "main", *tags] if v in builds]
    versions += sorted(builds.difference(versions))

    print(f"Sorted versions: {versions}")
    (directory / "versions.txt").write_text("\n".join(versions) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} <pages-directory>")
    main(Path(sys.argv[1]))
