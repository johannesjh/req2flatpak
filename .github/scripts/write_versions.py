"""Writes versions.txt, which lists all published docs versions.

The version switcher in docs/source/_templates/layout.html reads this file.
Versions are the directories on the gh-pages branch plus the directories that
are about to be published. They are sorted as: main, tags (newest first), rest.
"""

import subprocess
import sys
from pathlib import Path


def git_lines(*args: str) -> list[str]:
    """Run git and return the non-empty output lines."""
    out = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True
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
