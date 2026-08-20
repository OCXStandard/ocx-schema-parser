"""Tests for loader.load()."""
from pathlib import Path

import pytest
from xsdata.models import xsd

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.loader import load


def test_load_folder(schema_folder: Path):
    schemas = load(schema_folder)
    assert len(schemas) == 3
    assert all(isinstance(s, xsd.Schema) for s in schemas)


def test_load_single_file(schema_folder: Path):
    schemas = load(schema_folder / "OCX_Schema.xsd")
    assert len(schemas) == 1
    assert schemas[0].target_namespace == "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"


def test_load_accepts_str(schema_folder: Path):
    schemas = load(str(schema_folder / "OCX_Schema.xsd"))
    assert len(schemas) == 1


def test_load_missing_path_raises(tmp_path: Path):
    with pytest.raises(OcxParserError, match="does not exist"):
        load(tmp_path / "nope.xsd")


def test_load_empty_folder_raises(tmp_path: Path):
    with pytest.raises(OcxParserError, match="No XSD files"):
        load(tmp_path)


def test_load_invalid_xsd_raises(tmp_path: Path):
    bad = tmp_path / "bad.xsd"
    bad.write_text("<not-a-schema>", encoding="utf-8")
    with pytest.raises(OcxParserError, match="Failed to parse"):
        load(bad)
