"""Tests for SchemaDownloader."""

from pathlib import Path

import pytest

from ocx_schema_parser.downloader import SchemaDownloader, is_valid_uri
from ocx_schema_parser.errors import OcxParserError


def test_is_valid_uri():
    assert is_valid_uri("https://example.com/schema.xsd")
    assert is_valid_uri("file:///c:/temp/schema.xsd")
    assert not is_valid_uri("c:/temp/schema.xsd")
    assert not is_valid_uri("not a uri")


def test_wget_local_file_downloads_referenced_schemas(
    schema_folder: Path, tmp_path: Path
):
    downloader = SchemaDownloader(tmp_path)
    downloader.wget(str(schema_folder / "OCX_Schema.xsd"))
    written = sorted(p.name for p in tmp_path.glob("*.xsd"))
    assert "OCX_Schema.xsd" in written
    assert "unitsmlSchema_lite-0.9.18.xsd" in written
    assert "xml.xsd" in written


def test_wget_missing_file_raises(tmp_path: Path):
    downloader = SchemaDownloader(tmp_path)
    with pytest.raises(OcxParserError, match="not found"):
        downloader.wget(str(tmp_path / "no_such_file.xsd"))
