"""Tests for the ocx-schema-parser CLI."""
import json
from pathlib import Path

from ocx_schema_parser.cli import main


def test_export_to_stdout(schema_folder: Path, capsys):
    exit_code = main(["export", str(schema_folder / "OCX_Schema.xsd")])
    assert exit_code == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["schema_version"] == "3.0.0"
    assert "elements" in data


def test_export_to_file(schema_folder: Path, tmp_path: Path, capsys):
    out_file = tmp_path / "schema.json"
    exit_code = main(["export", str(schema_folder), "-o", str(out_file)])
    assert exit_code == 0
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["schema_version"] == "3.0.0"
    # summary goes to stderr, not stdout
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "elements" in captured.err


def test_export_bad_source_returns_1(tmp_path: Path, capsys):
    exit_code = main(["export", str(tmp_path / "missing.xsd")])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_version_flag(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
