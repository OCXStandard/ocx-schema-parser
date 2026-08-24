"""Extract one version's section from CHANGELOG.md.

Usage: python scripts/extract_changelog.py <version> [changelog-path]

Prints the body of the ``## [<version>] - <date>`` section (heading
excluded) to stdout. Exits non-zero if the section is missing, which
fails the GitHub Release job loudly.
"""

import re
import sys
from pathlib import Path


def extract_section(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if match is None:
        sys.exit(f"No CHANGELOG section found for version {version}")
    return match.group(1).strip() + "\n"


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: extract_changelog.py <version> [changelog-path]")
    version = sys.argv[1].lstrip("v")
    path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("CHANGELOG.md")
    sys.stdout.write(extract_section(path, version))


if __name__ == "__main__":
    main()
