from pathlib import Path

import pytest

from scripts.extract_changelog import extract_section

CHANGELOG = """\
# ocx-schema-parser: Changelog

## [Unreleased]

### Added

* Something pending.

## [3.1.0] - 2026-09-01

### Added

* New feature A.

### Fixed

* Bug B.

## [3.0.0] - 2026-08-20

### Changed

* Old stuff.
"""


def test_extracts_single_version_section(tmp_path: Path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    notes = extract_section(path, "3.1.0")
    assert "New feature A." in notes
    assert "Bug B." in notes
    assert "Old stuff." not in notes
    assert "Something pending." not in notes
    assert "## [3.1.0]" not in notes  # heading itself excluded


def test_missing_version_raises(tmp_path: Path):
    path = tmp_path / "CHANGELOG.md"
    path.write_text(CHANGELOG, encoding="utf-8")
    with pytest.raises(SystemExit):
        extract_section(path, "9.9.9")
