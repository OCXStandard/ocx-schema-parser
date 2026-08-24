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


def test_list_elements(schema_folder: Path, capsys):
    exit_code = main(["list", "elements", str(schema_folder)])
    assert exit_code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines
    assert all(":" in line for line in lines)
    prefixes = {line.split(":", 1)[0] for line in lines}
    assert "ocx" in prefixes
    names = {line.split(":", 1)[1] for line in lines}
    assert "Vessel" in names


def test_list_complex_types(schema_folder: Path, capsys):
    exit_code = main(["list", "complex-types", str(schema_folder)])
    assert exit_code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines
    assert all(":" in line for line in lines)


def test_list_simple_types(schema_folder: Path, capsys):
    exit_code = main(["list", "simple-types", str(schema_folder)])
    assert exit_code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines
    assert all(":" in line for line in lines)


def test_list_enumerations(schema_folder: Path, capsys):
    exit_code = main(["list", "enumerations", str(schema_folder)])
    assert exit_code == 0
    lines = capsys.readouterr().out.splitlines()
    assert lines
    assert all(":" in line for line in lines)


def test_list_name_details_case_insensitive(schema_folder: Path, capsys):
    exit_code = main(["list", "elements", str(schema_folder), "--name", "OCX:vessel"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("ocx:Vessel")
    assert "Attributes:" in out
    assert "Children:" in out
    assert "id" in out


def test_list_name_complex_type(schema_folder: Path, capsys):
    exit_code = main(["list", "complex-types", str(schema_folder), "--name", "ocx:vessel_t"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("ocx:Vessel_T")


def test_list_name_enumeration(schema_folder: Path, capsys):
    exit_code = main(["list", "enumerations", str(schema_folder), "--name", "ocx:classificationsociety"])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.startswith("ocx:classificationSociety")


def test_list_name_not_found(schema_folder: Path, capsys):
    exit_code = main(["list", "elements", str(schema_folder), "--name", "ocx:NoSuchThing"])
    assert exit_code == 1
    assert "not found" in capsys.readouterr().err


def test_summary(schema_folder: Path, capsys):
    exit_code = main(["summary", str(schema_folder)])
    assert exit_code == 0
    out = capsys.readouterr().out
    lines = out.splitlines()
    assert lines[0].split() == [
        "namespace",
        "elements",
        "complex-types",
        "simple-types",
        "attributes",
        "attribute-groups",
    ]
    rows = {line.split()[0]: line.split()[1:] for line in lines[1:] if line.strip()}
    ocx_ns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    assert ocx_ns in rows
    counts = [int(v) for v in rows[ocx_ns]]
    assert all(c >= 0 for c in counts)
    assert counts[0] >= 300  # ocx global elements
    assert counts[1] > 100  # ocx complex types
    assert rows["TOTAL"] == [str(sum(int(r[i]) for ns, r in rows.items() if ns != "TOTAL")) for i in range(5)]


def test_list_bad_source_returns_1(tmp_path: Path, capsys):
    exit_code = main(["list", "elements", str(tmp_path / "missing.xsd")])
    assert exit_code == 1
    assert "does not exist" in capsys.readouterr().err


def test_version_flag(capsys):
    import pytest

    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
