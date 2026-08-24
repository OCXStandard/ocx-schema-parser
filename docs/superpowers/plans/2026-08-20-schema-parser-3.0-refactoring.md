# Schema Parser 3.0 Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hand-rolled lxml XSD traversal with xsdata's `SchemaParser`, producing a typed, frozen Pydantic v2 model (`OcxSchema`) that serializes to JSON, plus a small CLI — released as a clean-break version 3.0.0.

**Architecture:** A three-stage pipeline: `load(source)` downloads/reads XSD files and parses each into `xsdata.models.xsd.Schema` objects; `resolve(schemas)` walks those dataclasses (indexing, type-ancestry flattening, attribute/child expansion, substitution groups, enums, schema changes) and builds the immutable `OcxSchema` Pydantic model; `OcxSchema.model_dump_json()` produces the JSON export used by the `ocx-schema-parser` CLI.

**Tech Stack:** Python >=3.10, `xsdata[lxml]~=26.2`, `pydantic>=2`, `loguru`, `uv` for all package management, `pytest` + `pytest-regressions` for snapshot tests.

**Spec:** `docs/superpowers/specs/2026-08-20-schema-parser-refactoring-design.md`

---

## File Structure

```
ocx_schema_parser/
    __init__.py      # version 3.0.0, public exports, DEFAULT_SCHEMA / WORKING_DRAFT URLs
    errors.py        # OcxParserError
    model.py         # frozen Pydantic v2 models: OcxSchema, GlobalElement, ...
    loader.py        # load(source) -> list[xsd.Schema]  (local file/folder or URL)
    resolver.py      # resolve(schemas) -> OcxSchema
    downloader.py    # SchemaDownloader (moved up from ocxdownloader/)
    cli.py           # argparse CLI: ocx-schema-parser export <source>
tests/
    conftest.py      # parse_fragment helper + session fixtures
    test_model.py
    test_loader.py
    test_resolver_index.py
    test_resolver_attributes.py
    test_resolver_children.py
    test_resolver_assembly.py
    test_cli.py
    test_snapshot.py
    data/OCX_Schema.xsd                  (kept)
    data/unitsmlSchema_lite-0.9.18.xsd   (kept)
    data/xml.xsd                         (kept)
```

**Deleted at the end (Task 10):** `ocx_schema_parser/xelement.py`, `xparse.py`, `ocxparser.py`, `elements.py`, `helpers.py`, `check.py`, `documentor.py`, `data_classes.py`, `config.py`, `transformer.py`, `utils/`, `ocxdownloader/`, root `main.py`, `poetry.lock`, `pyproject.old`, `docs/utils.rst`, all legacy tests (deleted early in Task 2).

**xsdata 26.2 API facts (verified against the installed package — do not second-guess these):**
- Parse a file: `SchemaParser(location=path.as_uri()).parse(str(path), xsd.Schema)` — the `xsd.Schema` clazz argument is REQUIRED.
- Parse in-memory text: `SchemaParser().parse(io.BytesIO(text.encode()), xsd.Schema)` (raw `bytes` fails in lxml iterparse).
- `maxOccurs="unbounded"` parses to `sys.maxsize`; treat `None` or values `>= 2**31` as unbounded.
- `xsd.Attribute.use` is a `UseType` enum — compare with `.value` (`"optional"`/`"required"`/`"prohibited"`); `None` means optional.
- `Appinfo.content` is a list of `AnyElement` objects with `qname`, `text`, `attributes`, `children`.
- `Documentation.content` is a mixed list of strings and elements — join only the `str` items.

---

### Task 1: Project scaffolding (pyproject.toml + dependencies)

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update `[project]` metadata, dependencies and scripts**

In `pyproject.toml`, replace the `version`, `description`, and `dependencies` values and add a `[project.scripts]` table:

```toml
[project]
name = "ocx-schema-parser"
version = "3.0.0"
description = "A python package for parsing the OCX schema and exporting it as a typed JSON model."
readme = "README.md"
authors = [
    { name = "ocastrup", email = "ole.christian.astrup@dnv.com" }
]
requires-python = ">=3.10"
dependencies = [
    "xsdata[lxml]~=26.2",
    "pydantic>=2",
    "loguru>=0.7",
]

[project.scripts]
ocx-schema-parser = "ocx_schema_parser.cli:main"
```

(Keep `[project.urls]` and `[tool.setuptools.packages.find]` unchanged.)

- [ ] **Step 2: Update the dev dependency group**

Replace `pytest-datadir` with `pytest-regressions` in `[dependency-groups]`:

```toml
[dependency-groups]
dev = [
    "pre-commit>=4.0",
    "pytest>=8.3",
    "pytest-cov>=6.0",
    "pytest-regressions>=2.5",
    "tbump>=6.11",
]
```

(Keep the `docs` group unchanged.)

- [ ] **Step 3: Update tbump current version**

```toml
[tool.tbump.version]
current = "3.0.0"
```

(Keep the regex and the rest of the tbump config unchanged.)

- [ ] **Step 4: Sync the environment**

Run: `uv sync --group dev`
Expected: succeeds; installs `xsdata`, `pydantic`, `loguru`, `pytest-regressions`; removes `ocx-common`, `pyspellchecker`, `pyyaml`, `pytest-datadir`.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: 3.0.0 scaffolding - xsdata/pydantic deps, CLI entry point

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 2: Delete legacy tests, write new conftest

The old tests import `ocx-common` and legacy modules that no longer resolve after Task 1, so they are deleted now. The bundled schema files in `tests/data/` are kept.

**Files:**
- Delete: all `tests/test_*.py` files and `tests/conftest.py` (legacy)
- Keep: `tests/data/OCX_Schema.xsd`, `tests/data/unitsmlSchema_lite-0.9.18.xsd`, `tests/data/xml.xsd`
- Create: `tests/conftest.py`

- [ ] **Step 1: Delete legacy tests**

```powershell
Get-ChildItem tests -Filter *.py | Remove-Item
```

- [ ] **Step 2: Write the new conftest**

Create `tests/conftest.py`:

```python
"""Shared fixtures for the ocx-schema-parser test suite."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from xsdata.codegen.parser import SchemaParser
from xsdata.models import xsd

SCHEMA_FOLDER = Path(__file__).parent / "data"


def parse_fragment(source: str) -> xsd.Schema:
    """Parse an in-memory XSD document into an xsdata Schema object."""
    parser = SchemaParser()
    return parser.parse(io.BytesIO(source.encode("utf-8")), xsd.Schema)


@pytest.fixture(scope="session")
def schema_folder() -> Path:
    return SCHEMA_FOLDER


@pytest.fixture(scope="session")
def ocx_schemas(schema_folder: Path) -> list[xsd.Schema]:
    from ocx_schema_parser.loader import load

    return load(schema_folder)


@pytest.fixture(scope="session")
def ocx_model(ocx_schemas):
    from ocx_schema_parser.resolver import resolve

    return resolve(ocx_schemas)
```

- [ ] **Step 3: Verify collection is clean**

Run: `uv run pytest --collect-only -q`
Expected: `no tests ran` (0 errors — conftest imports must succeed; the two loader/resolver fixtures are lazy so the missing modules do not break collection).

- [ ] **Step 4: Commit**

```bash
git add -A tests
git commit -m "test: remove legacy tests, add 3.0 conftest with parse_fragment helper

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 3: errors.py and model.py (TDD)

**Files:**
- Create: `ocx_schema_parser/errors.py`
- Create: `ocx_schema_parser/model.py`
- Test: `tests/test_model.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_model.py`:

```python
"""Tests for the Pydantic schema model."""

import pytest
from pydantic import ValidationError

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import (
    Attribute,
    Cardinality,
    ChildElement,
    EnumType,
    EnumValue,
    GlobalElement,
    OcxSchema,
    SchemaChange,
    SimpleType,
)


def test_error_is_exception():
    assert issubclass(OcxParserError, Exception)


def test_cardinality_str():
    assert str(Cardinality(lower=1, upper=1)) == "[1, 1]"
    assert str(Cardinality(lower=0, upper=None)) == "[0, \u221e]"


def test_models_are_frozen():
    card = Cardinality(lower=1, upper=1)
    with pytest.raises(ValidationError):
        card.lower = 2


def test_attribute_defaults():
    attr = Attribute(name="id", prefix="ocx", type="xs:ID")
    assert attr.use == "optional"
    assert attr.default is None
    assert attr.fixed is None
    assert attr.description == ""


def test_child_element_defaults():
    child = ChildElement(
        name="Point3D",
        prefix="ocx",
        type="ocx:Point3D_T",
        cardinality=Cardinality(lower=1, upper=1),
    )
    assert child.is_choice is False
    assert child.from_substitution_group is None
    assert child.inherited_from is None


def test_ocx_schema_get_by_name():
    elem = GlobalElement(
        name="Vessel",
        prefix="ocx",
        tag="{urn:test}Vessel",
        type="ocx:Vessel_T",
        cardinality=Cardinality(lower=1, upper=1),
    )
    schema = OcxSchema(
        schema_version="3.0.0",
        target_namespace="urn:test",
        namespaces={"ocx": "urn:test"},
        elements=[elem],
    )
    assert schema.get("Vessel") is elem
    assert schema.get("ocx:Vessel") is elem
    assert schema.get("NoSuchElement") is None


def test_schema_serializes_to_json():
    schema = OcxSchema(
        schema_version="3.0.0", target_namespace="urn:test", namespaces={}
    )
    data = schema.model_dump_json()
    assert '"schema_version":"3.0.0"' in data


def test_enum_and_simple_type():
    enum = EnumType(
        name="functionType",
        prefix="ocx",
        tag="{urn:test}functionType",
        values=[EnumValue(value="cargo oil", description="")],
    )
    assert enum.values[0].value == "cargo oil"
    st = SimpleType(
        name="guid",
        prefix="ocx",
        tag="{urn:test}guid",
        base="xs:string",
        restriction={"pattern": r"\{.*\}"},
    )
    assert st.restriction["pattern"] == r"\{.*\}"


def test_schema_change():
    change = SchemaChange(
        version="3.0.0", author="OCX", date="2023-01-01", description="Initial"
    )
    assert change.version == "3.0.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_model.py -v --no-cov`
Expected: FAIL / collection error — `ModuleNotFoundError: No module named 'ocx_schema_parser.errors'`

- [ ] **Step 3: Write errors.py**

Create `ocx_schema_parser/errors.py`:

```python
"""Errors raised by the ocx-schema-parser package."""


class OcxParserError(Exception):
    """Raised when loading or resolving an OCX schema fails."""
```

- [ ] **Step 4: Write model.py**

Create `ocx_schema_parser/model.py`:

```python
"""Typed, immutable data model of a resolved OCX schema (Pydantic v2)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Base model: immutable after construction."""

    model_config = ConfigDict(frozen=True)


class Cardinality(FrozenModel):
    """Occurrence bounds of an element. ``upper=None`` means unbounded."""

    lower: int
    upper: Optional[int]

    def __str__(self) -> str:
        upper = "\u221e" if self.upper is None else str(self.upper)
        return f"[{self.lower}, {upper}]"


class Attribute(FrozenModel):
    """A resolved XML attribute of a global element or complex type."""

    name: str
    prefix: str
    type: str
    use: Literal["required", "optional"] = "optional"
    default: Optional[str] = None
    fixed: Optional[str] = None
    description: str = ""


class ChildElement(FrozenModel):
    """A resolved child element (particle) of a global element or complex type."""

    name: str
    prefix: str
    type: str
    cardinality: Cardinality
    is_choice: bool = False
    from_substitution_group: Optional[str] = None  # prefixed head tag when expanded
    inherited_from: Optional[str] = None
    description: str = ""


class GlobalElement(FrozenModel):
    """A global element declaration with its fully flattened content model."""

    name: str
    prefix: str
    tag: str
    type: str
    abstract: bool = False
    cardinality: Cardinality
    description: str = ""
    parents: list[str] = []
    attributes: list[Attribute] = []
    children: list[ChildElement] = []
    substitution_group: Optional[str] = None


class ComplexType(FrozenModel):
    """A named complex type that is not the type of any global element."""

    name: str
    prefix: str
    tag: str
    abstract: bool = False
    description: str = ""
    parents: list[str] = []
    attributes: list[Attribute] = []
    children: list[ChildElement] = []


class EnumValue(FrozenModel):
    """One enumeration facet value."""

    value: str
    description: str = ""


class EnumType(FrozenModel):
    """A simple type restricted to an enumeration."""

    name: str
    prefix: str
    tag: str
    description: str = ""
    values: list[EnumValue] = []


class SimpleType(FrozenModel):
    """A non-enumeration simple type with its restriction facets."""

    name: str
    prefix: str
    tag: str
    base: str
    description: str = ""
    restriction: dict[str, str] = {}


class SchemaChange(FrozenModel):
    """A SchemaChange appinfo record."""

    version: str
    author: str = ""
    date: str = ""
    description: str = ""


class OcxSchema(FrozenModel):
    """The fully resolved OCX schema."""

    schema_version: str
    target_namespace: str
    namespaces: dict[str, str]
    elements: list[GlobalElement] = []
    complex_types: list[ComplexType] = []
    enumerations: list[EnumType] = []
    simple_types: list[SimpleType] = []
    attribute_groups: dict[str, list[Attribute]] = {}
    substitution_groups: dict[str, list[str]] = {}
    schema_changes: list[SchemaChange] = []

    def get(self, name: str) -> Optional[GlobalElement]:
        """Look up a global element by ``name`` or ``prefix:name``."""
        _, _, local = name.rpartition(":")
        for element in self.elements:
            if element.name == local:
                return element
        return None
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_model.py -v --no-cov`
Expected: all 8 tests PASS

- [ ] **Step 6: Commit**

```bash
git add ocx_schema_parser/errors.py ocx_schema_parser/model.py tests/test_model.py
git commit -m "feat: add OcxParserError and frozen Pydantic schema model

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 4: Move downloader.py up (TDD)

The existing `ocx_schema_parser/ocxdownloader/downloader.py` moves to `ocx_schema_parser/downloader.py`. Behaviour change: errors raise `OcxParserError` instead of `print()`.

**Files:**
- Create: `ocx_schema_parser/downloader.py`
- Delete: `ocx_schema_parser/ocxdownloader/` (whole folder)
- Test: `tests/test_downloader.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_downloader.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_downloader.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'ocx_schema_parser.downloader'`

- [ ] **Step 3: Write downloader.py**

Create `ocx_schema_parser/downloader.py`:

```python
#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
"""Download an XSD schema and all its referenced schemas into one folder."""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from loguru import logger
from xsdata.codegen import opener
from xsdata.utils.downloader import Downloader

from ocx_schema_parser.errors import OcxParserError


def is_valid_uri(uri: str) -> bool:
    """Return True if ``uri`` is a URI with a scheme (http, https, file, ...)."""
    try:
        parsed = urlparse(uri)
        if not parsed.scheme:
            return False
        if parsed.scheme == "file":
            return bool(parsed.path)
        return bool(parsed.netloc)
    except Exception:
        return False


class SchemaDownloader(Downloader):
    """Downloader specialisation: writes all referenced schemas into one folder.

    Args:
        output: The path to the schema download folder.
    """

    def __init__(self, output: Path):
        super().__init__(output)
        self.schema_folder = output

    def write_file(self, uri: str, location: Optional[str], content: str):
        """Write a downloaded schema into the single download folder."""
        name = Path(uri).name
        file_path = self.schema_folder / name
        file_path.write_text(content, encoding="utf-8")
        logger.debug(
            f"Writing schema {file_path.resolve()} to folder {self.schema_folder.resolve()}"
        )
        self.downloaded[uri] = file_path
        if location:
            self.downloaded[location] = file_path

    def wget(self, uri: str, location: Optional[str] = None):
        """Download ``uri`` (remote URI or local file path) with circular protection.

        Raises:
            OcxParserError: If the source cannot be fetched or parsed.
        """
        try:
            if uri in self.downloaded:
                return

            self.downloaded[uri] = None
            if location:
                self.downloaded[location] = None

            if is_valid_uri(uri):
                logger.info(f"Fetching {uri}")
                input_stream = opener.open(uri).read()  # nosec
            else:
                input_file = Path(uri).resolve()
                logger.info(f"Fetching local file {input_file}")
                with open(str(input_file), "rb") as file:
                    input_stream = file.read()

            if uri.endswith("wsdl"):
                self.parse_definitions(uri, input_stream)
            else:
                self.parse_schema(uri, input_stream)
                self.write_file(uri, location, input_stream.decode())

        except FileNotFoundError as exc:
            raise OcxParserError(f"The file at {uri} was not found.") from exc
        except OcxParserError:
            raise
        except Exception as exc:
            raise OcxParserError(f"Failed to download {uri}: {exc}") from exc
```

- [ ] **Step 4: Delete the old package**

```powershell
Remove-Item -Recurse -Force ocx_schema_parser\ocxdownloader
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_downloader.py -v --no-cov`
Expected: all 3 tests PASS

- [ ] **Step 6: Commit**

```bash
git add -A ocx_schema_parser tests/test_downloader.py
git commit -m "refactor: move SchemaDownloader to ocx_schema_parser.downloader, raise OcxParserError

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 5: loader.py (TDD)

**Files:**
- Create: `ocx_schema_parser/loader.py`
- Test: `tests/test_loader.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_loader.py`:

```python
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
    assert (
        schemas[0].target_namespace
        == "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    )


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_loader.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'ocx_schema_parser.loader'`

- [ ] **Step 3: Write loader.py**

Create `ocx_schema_parser/loader.py`:

```python
"""Load OCX schemas from a local file, folder, or remote URL into xsdata Schema objects."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

from loguru import logger
from xsdata.codegen.parser import SchemaParser
from xsdata.models import xsd

from ocx_schema_parser.downloader import SchemaDownloader
from ocx_schema_parser.errors import OcxParserError


def _is_url(source: str) -> bool:
    return urlparse(source).scheme in ("http", "https")


def _parse_file(path: Path) -> xsd.Schema:
    try:
        parser = SchemaParser(location=path.resolve().as_uri())
        return parser.parse(str(path), xsd.Schema)
    except Exception as exc:
        raise OcxParserError(f"Failed to parse {path}: {exc}") from exc


def _schema_files(folder: Path) -> list[Path]:
    files = sorted(folder.glob("*.xsd"))
    if not files:
        raise OcxParserError(f"No XSD files found in {folder}")
    return files


def load(
    source: Union[str, Path],
    download_folder: Optional[Path] = None,
) -> list[xsd.Schema]:
    """Load ``source`` and return one parsed ``xsd.Schema`` per XSD file.

    Args:
        source: A local ``.xsd`` file, a folder of ``.xsd`` files, or an http(s) URL.
        download_folder: Where remote schemas are downloaded. Defaults to a
            temporary folder. The folder is cleared before downloading.

    Raises:
        OcxParserError: If the source is missing, empty, or fails to parse.
    """
    if isinstance(source, str) and _is_url(source):
        folder = download_folder or Path(tempfile.mkdtemp(prefix="ocx_schema_"))
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        logger.info(f"Downloading {source} to {folder}")
        downloader = SchemaDownloader(folder)
        downloader.wget(source)
        return [_parse_file(f) for f in _schema_files(folder)]

    path = Path(source)
    if not path.exists():
        raise OcxParserError(f"The source {path} does not exist")
    if path.is_dir():
        return [_parse_file(f) for f in _schema_files(path)]
    return [_parse_file(path)]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_loader.py -v --no-cov`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ocx_schema_parser/loader.py tests/test_loader.py
git commit -m "feat: add loader.load for local files, folders and remote URLs

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 6: resolver.py — index, namespaces, reference resolution (TDD)

The resolver is built over Tasks 6–9. This task creates the file with module constants, small helpers, the `_Node` wrapper and the `_Resolver` class with its index pass and reference utilities.

**Files:**
- Create: `ocx_schema_parser/resolver.py`
- Test: `tests/test_resolver_index.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_resolver_index.py`:

```python
"""Tests for the resolver index pass and reference resolution."""

from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver, _cardinality, _description

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:element name="Thing" type="t:Thing_T">
    <xs:annotation><xs:documentation>A thing.</xs:documentation></xs:annotation>
  </xs:element>
  <xs:complexType name="Thing_T">
    <xs:sequence>
      <xs:element name="Part" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:simpleType name="guid">
    <xs:restriction base="xs:string"/>
  </xs:simpleType>
  <xs:attribute name="id" type="xs:ID"/>
  <xs:attributeGroup name="idGroup">
    <xs:attribute ref="t:id"/>
  </xs:attributeGroup>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_index_pass():
    r = make_resolver()
    assert "{urn:test}Thing" in r.elements
    assert "{urn:test}Thing_T" in r.complex_types
    assert "{urn:test}guid" in r.simple_types
    assert "{urn:test}id" in r.global_attributes
    assert "{urn:test}idGroup" in r.attribute_groups


def test_namespaces_and_prefixes():
    r = make_resolver()
    assert r.namespaces["t"] == "urn:test"
    assert r.prefixed("{urn:test}Thing") == "t:Thing"
    assert r.prefixed("{http://www.w3.org/2001/XMLSchema}string") == "xs:string"


def test_qref():
    r = make_resolver()
    schema = r.schemas[0]
    assert r.qref("t:Thing_T", schema) == "{urn:test}Thing_T"
    assert r.qref("xs:string", schema) == "{http://www.w3.org/2001/XMLSchema}string"


def test_is_builtin():
    r = make_resolver()
    assert r.is_builtin("{http://www.w3.org/2001/XMLSchema}string")
    assert not r.is_builtin("{urn:test}Thing_T")


def test_description_helper():
    r = make_resolver()
    node = r.elements["{urn:test}Thing"]
    assert _description(node.obj) == "A thing."


def test_cardinality_helper():
    r = make_resolver()
    ct = r.complex_types["{urn:test}Thing_T"].obj
    part = ct.sequence.elements[0]
    card = _cardinality(part)
    assert card.lower == 0
    assert card.upper is None  # unbounded


def test_index_full_ocx_schema(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    assert f"{{{tns}}}Vessel" in r.elements
    assert len(r.elements) > 300  # ocx + unitsml + xml global elements
    assert r.namespaces["ocx"] == tns
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_resolver_index.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'ocx_schema_parser.resolver'`

- [ ] **Step 3: Write resolver.py (index pass + helpers)**

Create `ocx_schema_parser/resolver.py`:

```python
"""Resolve parsed xsdata Schema objects into the OcxSchema Pydantic model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger
from xsdata.models import xsd

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import (
    Attribute,
    Cardinality,
    ChildElement,
    ComplexType,
    EnumType,
    EnumValue,
    GlobalElement,
    OcxSchema,
    SchemaChange,
    SimpleType,
)

XSD_NS = "http://www.w3.org/2001/XMLSchema"
BUILTIN_NAMESPACES = {
    XSD_NS,
    "http://www.w3.org/XML/1998/namespace",
    "http://www.w3.org/2001/XMLSchema-instance",
}
#: maxOccurs values at or above this are treated as unbounded (xsdata uses sys.maxsize)
UNBOUNDED = 2**31


def _description(node) -> str:
    """Join the documentation strings of an annotated xsd node."""
    parts: list[str] = []
    for annotation in getattr(node, "annotations", []) or []:
        for doc in annotation.documentations:
            for item in doc.content:
                if isinstance(item, str):
                    parts.append(item.strip())
    return " ".join(p for p in parts if p)


def _cardinality(node) -> Cardinality:
    """Build a Cardinality from a particle's min/max occurs."""
    lower = node.min_occurs if node.min_occurs is not None else 1
    upper = node.max_occurs
    if upper is None or upper >= UNBOUNDED:
        return Cardinality(lower=lower, upper=None)
    return Cardinality(lower=lower, upper=upper)


@dataclass
class _Node:
    """A schema component together with the schema that declares it."""

    obj: object
    schema: xsd.Schema
    tag: str


class _Resolver:
    """Walks xsdata Schema dataclasses and builds the OcxSchema model."""

    def __init__(self, schemas: list[xsd.Schema]):
        if not schemas:
            raise OcxParserError("No schemas to resolve")
        self.schemas = schemas
        self.elements: dict[str, _Node] = {}
        self.complex_types: dict[str, _Node] = {}
        self.simple_types: dict[str, _Node] = {}
        self.global_attributes: dict[str, _Node] = {}
        self.attribute_groups: dict[str, _Node] = {}
        self.groups: dict[str, _Node] = {}
        self.namespaces: dict[str, str] = {}
        self.uri_to_prefix: dict[str, str] = {}
        self._unresolved: set[str] = set()
        self._index()

    # ------------------------------------------------------------- index
    def _index(self) -> None:
        for schema in self.schemas:
            tns = schema.target_namespace or ""
            for prefix, uri in (schema.ns_map or {}).items():
                if prefix and prefix not in self.namespaces:
                    self.namespaces[prefix] = uri
                if prefix:
                    self.uri_to_prefix.setdefault(uri, prefix)

            def add(store: dict[str, _Node], items) -> None:
                for item in items:
                    if item.name:
                        store[f"{{{tns}}}{item.name}"] = _Node(
                            item, schema, f"{{{tns}}}{item.name}"
                        )

            add(self.elements, schema.elements)
            add(self.complex_types, schema.complex_types)
            add(self.simple_types, schema.simple_types)
            add(self.global_attributes, schema.attributes)
            add(self.attribute_groups, schema.attribute_groups)
            add(self.groups, schema.groups)

    # -------------------------------------------------------- references
    def qref(self, ref: str, schema: xsd.Schema) -> str:
        """Resolve a ``prefix:Name`` reference to a ``{uri}Name`` tag."""
        prefix, _, local = ref.rpartition(":")
        ns_map = schema.ns_map or {}
        if prefix and prefix in ns_map:
            return f"{{{ns_map[prefix]}}}{local}"
        if not prefix and schema.target_namespace:
            return f"{{{schema.target_namespace}}}{local}"
        return f"{{{prefix}}}{local}" if prefix else local

    def prefixed(self, tag: str) -> str:
        """Convert a ``{uri}Name`` tag to ``prefix:Name``."""
        if not tag.startswith("{"):
            return tag
        uri, _, local = tag[1:].partition("}")
        prefix = self.uri_to_prefix.get(uri)
        return f"{prefix}:{local}" if prefix else local

    def split(self, tag: str) -> tuple[str, str]:
        """Return (prefix, local_name) for a ``{uri}Name`` tag."""
        prefixed = self.prefixed(tag)
        prefix, _, local = prefixed.rpartition(":")
        return prefix, local

    def is_builtin(self, tag: str) -> bool:
        """True if the tag belongs to an XSD built-in namespace."""
        if not tag.startswith("{"):
            return False
        uri = tag[1:].partition("}")[0]
        return uri in BUILTIN_NAMESPACES

    def _missing(self, tag: str, kind: str) -> None:
        """Log an unresolved reference once."""
        if tag not in self._unresolved:
            self._unresolved.add(tag)
            logger.warning(f"Unresolved {kind} reference: {tag}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_resolver_index.py -v --no-cov`
Expected: all 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ocx_schema_parser/resolver.py tests/test_resolver_index.py
git commit -m "feat: resolver index pass, namespace and reference resolution

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 7: resolver.py — type ancestry and attribute flattening (TDD)

**Files:**
- Modify: `ocx_schema_parser/resolver.py` (append methods/helpers)
- Test: `tests/test_resolver_attributes.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_resolver_attributes.py`:

```python
"""Tests for type ancestry and attribute flattening."""

from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:attributeGroup name="idGroup">
    <xs:attribute name="id" type="xs:ID" use="required">
      <xs:annotation><xs:documentation>Unique id.</xs:documentation></xs:annotation>
    </xs:attribute>
    <xs:attribute name="secret" type="xs:string" use="prohibited"/>
  </xs:attributeGroup>
  <xs:complexType name="Base_T">
    <xs:attribute name="name" type="xs:string" default="unnamed"/>
    <xs:attributeGroup ref="t:idGroup"/>
  </xs:complexType>
  <xs:complexType name="Middle_T">
    <xs:complexContent>
      <xs:extension base="t:Base_T">
        <xs:attribute name="version" type="xs:string" fixed="3.0.0"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:complexType name="Leaf_T">
    <xs:complexContent>
      <xs:extension base="t:Middle_T">
        <xs:attribute name="name" type="xs:token"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_ancestors_nearest_first():
    r = make_resolver()
    parents = r.ancestors("{urn:test}Leaf_T")
    assert parents == ["{urn:test}Middle_T", "{urn:test}Base_T"]


def test_ancestors_stop_at_builtin():
    r = make_resolver()
    assert r.ancestors("{urn:test}Base_T") == []


def test_attributes_flattened_and_sorted():
    r = make_resolver()
    attrs = r.attributes_of("{urn:test}Leaf_T")
    names = [a.name for a in attrs]
    assert names == sorted(names)
    assert set(names) == {"id", "name", "version"}  # prohibited 'secret' skipped


def test_nearest_definition_wins():
    r = make_resolver()
    attrs = {a.name: a for a in r.attributes_of("{urn:test}Leaf_T")}
    assert attrs["name"].type == "xs:token"  # Leaf_T overrides Base_T


def test_attribute_details():
    r = make_resolver()
    attrs = {a.name: a for a in r.attributes_of("{urn:test}Leaf_T")}
    assert attrs["id"].use == "required"
    assert attrs["id"].description == "Unique id."
    assert attrs["version"].fixed == "3.0.0"
    base_attrs = {a.name: a for a in r.attributes_of("{urn:test}Base_T")}
    assert base_attrs["name"].default == "unnamed"


def test_full_schema_vessel_type(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    parents = r.ancestors(f"{{{tns}}}Vessel_T")
    assert any(p.endswith("}DocumentBase_T") for p in parents)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_resolver_attributes.py -v --no-cov`
Expected: FAIL — `AttributeError: '_Resolver' object has no attribute 'ancestors'`

- [ ] **Step 3: Add ancestry and attribute code**

Append to `ocx_schema_parser/resolver.py`, module level (after `_cardinality`):

```python
def _base_ref(ct: xsd.ComplexType) -> Optional[str]:
    """Return the base type reference of a complex type's derivation, if any."""
    for content in (ct.complex_content, ct.simple_content):
        if content is None:
            continue
        derivation = content.extension or content.restriction
        if derivation is not None and derivation.base:
            return derivation.base
    return None


def _attribute_holders(ct: xsd.ComplexType) -> list:
    """Return the objects on ``ct`` that may carry attributes/attribute_groups."""
    holders = [ct]
    for content in (ct.complex_content, ct.simple_content):
        if content is None:
            continue
        for derivation in (content.extension, content.restriction):
            if derivation is not None:
                holders.append(derivation)
    return holders
```

And these methods inside `_Resolver`:

```python
# ---------------------------------------------------------- ancestry
def ancestors(self, type_tag: str) -> list[str]:
    """Base-type chain of a complex type, nearest first, builtins excluded."""
    result: list[str] = []
    seen = {type_tag}
    current = type_tag
    while True:
        node = self.complex_types.get(current)
        if node is None:
            break
        base_ref = _base_ref(node.obj)
        if base_ref is None:
            break
        base_tag = self.qref(base_ref, node.schema)
        if self.is_builtin(base_tag) or base_tag in seen:
            break
        if base_tag not in self.complex_types:
            if base_tag not in self.simple_types:
                self._missing(base_tag, "base type")
            break
        seen.add(base_tag)
        result.append(base_tag)
        current = base_tag
    return result


# -------------------------------------------------------- attributes
def _make_attribute(
    self, attr: xsd.Attribute, schema: xsd.Schema
) -> Optional[Attribute]:
    """Build an Attribute model; resolve refs; skip prohibited. None if skipped."""
    if attr.ref:
        tag = self.qref(attr.ref, schema)
        node = self.global_attributes.get(tag)
        if node is None:
            self._missing(tag, "attribute")
            return None
        return self._make_attribute(node.obj, node.schema)
    use = attr.use.value if attr.use is not None else "optional"
    if use == "prohibited":
        return None
    type_ref = attr.type
    if (
        type_ref is None
        and attr.simple_type is not None
        and attr.simple_type.restriction
    ):
        type_ref = attr.simple_type.restriction.base
    type_name = self.prefixed(self.qref(type_ref, schema)) if type_ref else "xs:string"
    prefix, _ = self.split(f"{{{schema.target_namespace or ''}}}{attr.name}")
    return Attribute(
        name=attr.name or "",
        prefix=prefix,
        type=type_name,
        use=use,
        default=attr.default,
        fixed=attr.fixed,
        description=_description(attr),
    )


def _expand_attributes(
    self, holder, schema: xsd.Schema, seen_groups: set[str]
) -> list[Attribute]:
    """Collect attributes on ``holder``, expanding attributeGroup refs recursively."""
    result: list[Attribute] = []
    for attr in getattr(holder, "attributes", []) or []:
        made = self._make_attribute(attr, schema)
        if made is not None:
            result.append(made)
    for group in getattr(holder, "attribute_groups", []) or []:
        ref = group.ref or group.name
        if not ref:
            continue
        tag = (
            self.qref(ref, schema)
            if group.ref
            else f"{{{schema.target_namespace}}}{group.name}"
        )
        if tag in seen_groups:
            continue
        seen_groups.add(tag)
        node = self.attribute_groups.get(tag)
        if node is None:
            self._missing(tag, "attribute group")
            continue
        result.extend(self._expand_attributes(node.obj, node.schema, seen_groups))
    return result


def attributes_of(self, type_tag: str) -> list[Attribute]:
    """All attributes of a complex type, own + inherited, nearest wins, sorted by name."""
    merged: dict[str, Attribute] = {}
    for tag in [type_tag, *self.ancestors(type_tag)]:
        node = self.complex_types.get(tag)
        if node is None:
            continue
        for holder in _attribute_holders(node.obj):
            for attr in self._expand_attributes(holder, node.schema, set()):
                merged.setdefault(attr.name, attr)  # nearest definition wins
    return sorted(merged.values(), key=lambda a: a.name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_resolver_attributes.py -v --no-cov`
Expected: all 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add ocx_schema_parser/resolver.py tests/test_resolver_attributes.py
git commit -m "feat: resolver type ancestry and flattened attribute resolution

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 8: resolver.py — child elements and substitution groups (TDD)

**Files:**
- Modify: `ocx_schema_parser/resolver.py`
- Test: `tests/test_resolver_children.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_resolver_children.py`:

```python
"""Tests for child element collection and substitution group expansion."""

from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:element name="Shape" type="t:Shape_T" abstract="true"/>
  <xs:element name="Circle" type="t:Shape_T" substitutionGroup="t:Shape"/>
  <xs:element name="Square" type="t:Shape_T" substitutionGroup="t:Shape"/>
  <xs:element name="Label" type="xs:string"/>
  <xs:complexType name="Shape_T"/>
  <xs:group name="extras">
    <xs:sequence>
      <xs:element name="Note" type="xs:string" minOccurs="0"/>
    </xs:sequence>
  </xs:group>
  <xs:complexType name="Base_T">
    <xs:sequence>
      <xs:element ref="t:Label"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="Drawing_T">
    <xs:complexContent>
      <xs:extension base="t:Base_T">
        <xs:sequence>
          <xs:element ref="t:Shape" maxOccurs="unbounded"/>
          <xs:choice>
            <xs:element name="Title" type="xs:string"/>
            <xs:element name="Caption" type="xs:string"/>
          </xs:choice>
          <xs:group ref="t:extras"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_substitution_group_index():
    r = make_resolver()
    assert r.substitution_groups["{urn:test}Shape"] == [
        "{urn:test}Circle",
        "{urn:test}Square",
    ]


def test_children_traversal_order_and_inheritance():
    r = make_resolver()
    children = r.children_of("{urn:test}Drawing_T")
    names = [c.name for c in children]
    # own children first (traversal order: elements, then groups, then choices),
    # inherited children afterwards
    assert names == ["Circle", "Square", "Note", "Title", "Caption", "Label"]
    by_name = {c.name: c for c in children}
    assert by_name["Label"].inherited_from == "t:Base_T"
    assert by_name["Circle"].inherited_from is None


def test_abstract_head_replaced_by_members():
    r = make_resolver()
    by_name = {c.name: c for c in r.children_of("{urn:test}Drawing_T")}
    assert "Shape" not in by_name  # abstract head not emitted
    assert by_name["Circle"].from_substitution_group == "t:Shape"
    assert by_name["Circle"].cardinality.upper is None  # inherits ref cardinality
    assert by_name["Note"].from_substitution_group is None


def test_choice_flag():
    r = make_resolver()
    by_name = {c.name: c for c in r.children_of("{urn:test}Drawing_T")}
    assert by_name["Title"].is_choice is True
    assert by_name["Caption"].is_choice is True
    assert by_name["Note"].is_choice is False


def test_full_schema_vessel_children(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    children = r.children_of(f"{{{tns}}}Vessel_T")
    assert len(children) > 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_resolver_children.py -v --no-cov`
Expected: FAIL — `AttributeError: '_Resolver' object has no attribute 'substitution_groups'`

- [ ] **Step 3: Add substitution-group index**

In `_Resolver.__init__`, after `self._unresolved: set[str] = set()` and before `self._index()`, add:

```python
        self.substitution_groups: dict[str, list[str]] = {}
```

At the end of `_Resolver._index`, add a second pass:

```python
        for schema in self.schemas:
            for element in schema.elements:
                if element.substitution_group and element.name:
                    head = self.qref(element.substitution_group, schema)
                    tag = f"{{{schema.target_namespace or ''}}}{element.name}"
                    self.substitution_groups.setdefault(head, []).append(tag)
        for head in self.substitution_groups:
            self.substitution_groups[head].sort()
```

- [ ] **Step 4: Add particle collection and children_of**

Append these methods to `_Resolver`:

```python
# ---------------------------------------------------------- children
def _make_children(
    self, element: xsd.Element, schema: xsd.Schema, is_choice: bool
) -> list[ChildElement]:
    """Build ChildElement(s) for one particle; expands abstract substitution heads."""
    card = _cardinality(element)
    if element.ref:
        tag = self.qref(element.ref, schema)
        node = self.elements.get(tag)
        if node is None:
            self._missing(tag, "element")
            return []
        target: xsd.Element = node.obj
        members = self.substitution_groups.get(tag, [])
        if target.abstract and members:
            head_prefixed = self.prefixed(tag)
            result = []
            for member_tag in members:
                member = self.elements.get(member_tag)
                if member is None:
                    continue
                prefix, local = self.split(member_tag)
                type_ref = member.obj.type
                type_name = (
                    self.prefixed(self.qref(type_ref, member.schema))
                    if type_ref
                    else local
                )
                result.append(
                    ChildElement(
                        name=local,
                        prefix=prefix,
                        type=type_name,
                        cardinality=card,
                        is_choice=is_choice,
                        from_substitution_group=head_prefixed,
                        description=_description(member.obj),
                    )
                )
            return result
        prefix, local = self.split(tag)
        type_name = (
            self.prefixed(self.qref(target.type, node.schema)) if target.type else local
        )
        return [
            ChildElement(
                name=local,
                prefix=prefix,
                type=type_name,
                cardinality=card,
                is_choice=is_choice,
                description=_description(target),
            )
        ]
    # local (inline) element declaration
    prefix, _ = self.split(f"{{{schema.target_namespace or ''}}}{element.name}")
    type_name = (
        self.prefixed(self.qref(element.type, schema))
        if element.type
        else (element.name or "")
    )
    return [
        ChildElement(
            name=element.name or "",
            prefix=prefix,
            type=type_name,
            cardinality=card,
            is_choice=is_choice,
            description=_description(element),
        )
    ]


def _collect_particles(
    self, container, schema: xsd.Schema, is_choice: bool, seen_groups: set[str]
) -> list[ChildElement]:
    """Recursively walk a sequence/choice/all container collecting children."""
    if container is None:
        return []
    result: list[ChildElement] = []
    for element in getattr(container, "elements", []) or []:
        result.extend(self._make_children(element, schema, is_choice))
    for group in getattr(container, "groups", []) or []:
        result.extend(self._collect_group(group, schema, is_choice, seen_groups))
    for choice in getattr(container, "choices", []) or []:
        result.extend(self._collect_particles(choice, schema, True, seen_groups))
    for sequence in getattr(container, "sequences", []) or []:
        result.extend(self._collect_particles(sequence, schema, is_choice, seen_groups))
    return result


def _collect_group(
    self, group: xsd.Group, schema: xsd.Schema, is_choice: bool, seen_groups: set[str]
) -> list[ChildElement]:
    """Resolve a named model group (possibly a ref) and collect its particles."""
    if group.ref:
        tag = self.qref(group.ref, schema)
        if tag in seen_groups:
            return []
        seen_groups.add(tag)
        node = self.groups.get(tag)
        if node is None:
            self._missing(tag, "group")
            return []
        return self._collect_group(node.obj, node.schema, is_choice, seen_groups)
    result: list[ChildElement] = []
    result.extend(
        self._collect_particles(group.sequence, schema, is_choice, seen_groups)
    )
    result.extend(self._collect_particles(group.choice, schema, True, seen_groups))
    result.extend(self._collect_particles(group.all, schema, is_choice, seen_groups))
    return result


def _own_children(self, ct: xsd.ComplexType, schema: xsd.Schema) -> list[ChildElement]:
    """Children declared directly on a complex type (incl. its derivation content)."""
    result: list[ChildElement] = []
    containers = [(ct.sequence, False), (ct.all, False), (ct.choice, True)]
    if ct.group is not None:
        result.extend(self._collect_group(ct.group, schema, False, set()))
    for content in (ct.complex_content, ct.simple_content):
        if content is None:
            continue
        for derivation in (content.extension, content.restriction):
            if derivation is None:
                continue
            containers.extend(
                [
                    (getattr(derivation, "sequence", None), False),
                    (getattr(derivation, "all", None), False),
                    (getattr(derivation, "choice", None), True),
                ]
            )
            group = getattr(derivation, "group", None)
            if group is not None:
                result.extend(self._collect_group(group, schema, False, set()))
    for container, is_choice in containers:
        result.extend(self._collect_particles(container, schema, is_choice, set()))
    return result


def children_of(self, type_tag: str) -> list[ChildElement]:
    """All children of a complex type: own first (declaration order), then inherited."""
    merged: dict[str, ChildElement] = {}
    result: list[ChildElement] = []
    for tag in [type_tag, *self.ancestors(type_tag)]:
        node = self.complex_types.get(tag)
        if node is None:
            continue
        inherited_from = self.prefixed(tag) if tag != type_tag else None
        for child in self._own_children(node.obj, node.schema):
            if child.name in merged:
                continue  # nearest definition wins
            if inherited_from is not None:
                child = child.model_copy(update={"inherited_from": inherited_from})
            merged[child.name] = child
            result.append(child)
    return result
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_resolver_children.py tests/test_resolver_index.py tests/test_resolver_attributes.py -v --no-cov`
Expected: all tests PASS (earlier resolver tests still green)

- [ ] **Step 6: Commit**

```bash
git add ocx_schema_parser/resolver.py tests/test_resolver_children.py
git commit -m "feat: resolver child elements, groups and substitution-group expansion

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 9: resolver.py — enums, simple types, schema changes, resolve() (TDD)

**Files:**
- Modify: `ocx_schema_parser/resolver.py`
- Test: `tests/test_resolver_assembly.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_resolver_assembly.py`:

```python
"""Tests for enum/simple-type extraction, schema changes, and resolve()."""

import pytest
from conftest import parse_fragment

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import OcxSchema
from ocx_schema_parser.resolver import resolve

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:annotation>
    <xs:appinfo>
      <SchemaChange version="1.1.0" author="OCX" date="2023-01-01">
        <Description>Added Thing.</Description>
      </SchemaChange>
    </xs:appinfo>
  </xs:annotation>
  <xs:element name="Thing" type="t:Thing_T"/>
  <xs:complexType name="Thing_T">
    <xs:attribute ref="t:schemaVersion" use="required"/>
  </xs:complexType>
  <xs:complexType name="Orphan_T">
    <xs:annotation><xs:documentation>No global element uses me.</xs:documentation></xs:annotation>
  </xs:complexType>
  <xs:attribute name="schemaVersion" type="xs:string" fixed="9.9.9"/>
  <xs:simpleType name="functionType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="cargo oil"/>
      <xs:enumeration value="ballast"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="guid">
    <xs:restriction base="xs:string">
      <xs:pattern value="[0-9a-f]+"/>
      <xs:minLength value="8"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>
"""


@pytest.fixture(scope="module")
def model() -> OcxSchema:
    return resolve([parse_fragment(FRAGMENT)])


def test_resolve_empty_raises():
    with pytest.raises(OcxParserError):
        resolve([])


def test_schema_version_from_fixed_attribute(model):
    assert model.schema_version == "9.9.9"


def test_target_namespace(model):
    assert model.target_namespace == "urn:test"


def test_enumerations(model):
    enums = {e.name: e for e in model.enumerations}
    assert [v.value for v in enums["functionType"].values] == ["ballast", "cargo oil"]


def test_simple_type_facets(model):
    st = {s.name: s for s in model.simple_types}["guid"]
    assert st.base == "xs:string"
    assert st.restriction["pattern"] == "[0-9a-f]+"
    assert st.restriction["min_length"] == "8"


def test_schema_changes(model):
    change = model.schema_changes[0]
    assert change.version == "1.1.0"
    assert change.author == "OCX"
    assert change.description == "Added Thing."


def test_orphan_complex_type_documented(model):
    names = [ct.name for ct in model.complex_types]
    assert "Orphan_T" in names
    assert "Thing_T" not in names  # used by global element Thing


def test_global_element(model):
    thing = model.get("t:Thing")
    assert thing is not None
    assert thing.type == "t:Thing_T"
    assert thing.cardinality.lower == 1 and thing.cardinality.upper == 1
    attrs = {a.name: a for a in thing.attributes}
    assert attrs["schemaVersion"].fixed == "9.9.9"


def test_resolve_full_ocx_schema(ocx_model):
    assert ocx_model.schema_version == "3.0.0"
    assert (
        ocx_model.target_namespace
        == "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    )
    assert ocx_model.get("ocx:Vessel") is not None
    assert len(ocx_model.elements) > 300
    assert len(ocx_model.enumerations) > 0
    assert len(ocx_model.substitution_groups) > 0
    names = [e.name for e in ocx_model.elements]
    assert names == sorted(names)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_resolver_assembly.py -v --no-cov`
Expected: FAIL — `ImportError: cannot import name 'resolve'`

- [ ] **Step 3: Add facet/schema-change helpers**

Append at module level in `resolver.py` (after `_attribute_holders`):

```python
_FACET_FIELDS = (
    "min_exclusive",
    "min_inclusive",
    "max_exclusive",
    "max_inclusive",
    "total_digits",
    "fraction_digits",
    "length",
    "min_length",
    "max_length",
    "white_space",
)


def _facets(restriction: xsd.Restriction) -> dict[str, str]:
    """Extract non-enumeration facets of a restriction as a name->value dict."""
    result: dict[str, str] = {}
    for field in _FACET_FIELDS:
        facet = getattr(restriction, field, None)
        if facet is not None and facet.value is not None:
            result[field] = str(facet.value)
    if restriction.patterns:
        result["pattern"] = "|".join(p.value for p in restriction.patterns if p.value)
    return result


def _schema_changes_from(element) -> list[SchemaChange]:
    """Recursively collect SchemaChange records from an appinfo AnyElement tree."""
    result: list[SchemaChange] = []
    qname = getattr(element, "qname", None) or ""
    if qname.endswith("SchemaChange"):
        attrs = getattr(element, "attributes", {}) or {}
        description = ""
        for child in getattr(element, "children", []) or []:
            child_qname = getattr(child, "qname", None) or ""
            if child_qname.endswith("Description") and getattr(child, "text", None):
                description = child.text.strip()
        result.append(
            SchemaChange(
                version=attrs.get("version", ""),
                author=attrs.get("author", ""),
                date=attrs.get("date", ""),
                description=description,
            )
        )
    for child in getattr(element, "children", []) or []:
        result.extend(_schema_changes_from(child))
    return result
```

- [ ] **Step 4: Add assembly methods and resolve()**

Append these methods to `_Resolver`:

```python
# ----------------------------------------------------------- assembly
def _main_schema(self) -> xsd.Schema:
    """The schema declaring the fixed ``schemaVersion`` attribute; else the first."""
    for schema in self.schemas:
        for attr in schema.attributes:
            if attr.name == "schemaVersion" and attr.fixed:
                return schema
    return self.schemas[0]


def _schema_version(self) -> str:
    for attr in self._main_schema().attributes:
        if attr.name == "schemaVersion" and attr.fixed:
            return attr.fixed
    return ""


def _type_tag_of(self, node: _Node) -> Optional[str]:
    """Tag of the (named or inline) complex type of a global element."""
    element: xsd.Element = node.obj
    if element.type:
        return self.qref(element.type, node.schema)
    return None


def _build_element(self, node: _Node) -> GlobalElement:
    element: xsd.Element = node.obj
    prefix, local = self.split(node.tag)
    type_tag = self._type_tag_of(node)
    if type_tag is not None:
        type_name = self.prefixed(type_tag)
        parents = [self.prefixed(t) for t in self.ancestors(type_tag)]
        attributes = self.attributes_of(type_tag)
        children = self.children_of(type_tag)
    elif element.complex_type is not None:
        # inline anonymous complex type: resolve its own content + base ancestry
        ct = element.complex_type
        type_name = local
        base_ref = _base_ref(ct)
        base_tag = self.qref(base_ref, node.schema) if base_ref else None
        parents = (
            [
                self.prefixed(base_tag),
                *(self.prefixed(t) for t in self.ancestors(base_tag)),
            ]
            if base_tag and not self.is_builtin(base_tag)
            else []
        )
        own_attrs = {
            a.name: a
            for holder in _attribute_holders(ct)
            for a in self._expand_attributes(holder, node.schema, set())
        }
        inherited = (
            {a.name: a for a in self.attributes_of(base_tag)}
            if base_tag and base_tag in self.complex_types
            else {}
        )
        attributes = sorted({**inherited, **own_attrs}.values(), key=lambda a: a.name)
        children = self._own_children(ct, node.schema)
        if base_tag and base_tag in self.complex_types:
            own_names = {c.name for c in children}
            for child in self.children_of(base_tag):
                if child.name not in own_names:
                    children.append(
                        child.model_copy(
                            update={"inherited_from": self.prefixed(base_tag)}
                        )
                    )
    else:
        type_name = (
            self.prefixed(self.qref(element.type, node.schema))
            if element.type
            else local
        )
        parents, attributes, children = [], [], []
    substitution = (
        self.prefixed(self.qref(element.substitution_group, node.schema))
        if element.substitution_group
        else None
    )
    return GlobalElement(
        name=local,
        prefix=prefix,
        tag=node.tag,
        type=type_name,
        abstract=bool(element.abstract),
        cardinality=Cardinality(lower=1, upper=1),
        description=_description(element),
        parents=parents,
        attributes=attributes,
        children=children,
        substitution_group=substitution,
    )


def _build_complex_types(self) -> list[ComplexType]:
    """Named complex types that are NOT the type of any global element."""
    used = {self._type_tag_of(node) for node in self.elements.values()}
    result = []
    for tag, node in self.complex_types.items():
        if tag in used:
            continue
        prefix, local = self.split(tag)
        result.append(
            ComplexType(
                name=local,
                prefix=prefix,
                tag=tag,
                abstract=bool(node.obj.abstract),
                description=_description(node.obj),
                parents=[self.prefixed(t) for t in self.ancestors(tag)],
                attributes=self.attributes_of(tag),
                children=self.children_of(tag),
            )
        )
    return sorted(result, key=lambda ct: ct.name)


def _build_simple_types(self) -> tuple[list[EnumType], list[SimpleType]]:
    enums: list[EnumType] = []
    simple: list[SimpleType] = []
    for tag, node in self.simple_types.items():
        st: xsd.SimpleType = node.obj
        prefix, local = self.split(tag)
        restriction = st.restriction
        if restriction is None:
            continue
        if restriction.enumerations:
            values = sorted(
                (
                    EnumValue(value=e.value or "", description=_description(e))
                    for e in restriction.enumerations
                ),
                key=lambda v: v.value,
            )
            enums.append(
                EnumType(
                    name=local,
                    prefix=prefix,
                    tag=tag,
                    description=_description(st),
                    values=values,
                )
            )
        else:
            base = (
                self.prefixed(self.qref(restriction.base, node.schema))
                if restriction.base
                else "xs:string"
            )
            simple.append(
                SimpleType(
                    name=local,
                    prefix=prefix,
                    tag=tag,
                    base=base,
                    description=_description(st),
                    restriction=_facets(restriction),
                )
            )
    return (
        sorted(enums, key=lambda e: e.name),
        sorted(simple, key=lambda s: s.name),
    )


def _build_attribute_groups(self) -> dict[str, list[Attribute]]:
    result = {}
    for tag, node in self.attribute_groups.items():
        _, local = self.split(tag)
        result[local] = sorted(
            {
                a.name: a for a in self._expand_attributes(node.obj, node.schema, {tag})
            }.values(),
            key=lambda a: a.name,
        )
    return dict(sorted(result.items()))


def _build_schema_changes(self) -> list[SchemaChange]:
    result: list[SchemaChange] = []
    for schema in self.schemas:
        for annotation in schema.annotations:
            for appinfo in annotation.app_infos:
                for item in appinfo.content:
                    result.extend(_schema_changes_from(item))
    return result


def build(self) -> OcxSchema:
    elements = sorted(
        (self._build_element(node) for node in self.elements.values()),
        key=lambda e: e.name,
    )
    enums, simple = self._build_simple_types()
    return OcxSchema(
        schema_version=self._schema_version(),
        target_namespace=self._main_schema().target_namespace or "",
        namespaces=dict(sorted(self.namespaces.items())),
        elements=elements,
        complex_types=self._build_complex_types(),
        enumerations=enums,
        simple_types=simple,
        attribute_groups=self._build_attribute_groups(),
        substitution_groups={
            self.prefixed(head): [self.prefixed(m) for m in members]
            for head, members in sorted(self.substitution_groups.items())
        },
        schema_changes=self._build_schema_changes(),
    )
```

Then add the public entry point at the bottom of the module:

```python
def resolve(schemas: list[xsd.Schema]) -> OcxSchema:
    """Resolve parsed schemas into the immutable OcxSchema model.

    Raises:
        OcxParserError: If ``schemas`` is empty.
    """
    return _Resolver(schemas).build()
```

- [ ] **Step 5: Run all resolver tests**

Run: `uv run pytest tests/test_resolver_assembly.py tests/test_resolver_index.py tests/test_resolver_attributes.py tests/test_resolver_children.py -v --no-cov`
Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add ocx_schema_parser/resolver.py tests/test_resolver_assembly.py
git commit -m "feat: resolver assembly - enums, simple types, schema changes, resolve()

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 10: Delete legacy modules, rewrite `__init__.py`

**Files:**
- Delete: `ocx_schema_parser/xelement.py`, `xparse.py`, `ocxparser.py`, `elements.py`, `helpers.py`, `check.py`, `documentor.py`, `data_classes.py`, `config.py`, `transformer.py`, `ocx_schema_parser/utils/` (folder), root `main.py`, `poetry.lock`, `pyproject.old`
- Modify: `ocx_schema_parser/__init__.py`

- [ ] **Step 1: Delete the legacy modules**

```powershell
Remove-Item ocx_schema_parser\xelement.py, ocx_schema_parser\xparse.py, ocx_schema_parser\ocxparser.py, ocx_schema_parser\elements.py, ocx_schema_parser\helpers.py, ocx_schema_parser\check.py, ocx_schema_parser\documentor.py, ocx_schema_parser\data_classes.py, ocx_schema_parser\config.py, ocx_schema_parser\transformer.py -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force ocx_schema_parser\utils -ErrorAction SilentlyContinue
Remove-Item main.py, poetry.lock, pyproject.old -ErrorAction SilentlyContinue
```

(Skip any file that does not exist; the `-ErrorAction SilentlyContinue` handles it.)

- [ ] **Step 2: Rewrite `ocx_schema_parser/__init__.py`**

Replace the entire content of `ocx_schema_parser/__init__.py` with:

```python
#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
"""ocx-schema-parser: parse the OCX XSD schema into a typed JSON model."""

from loguru import logger

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.loader import load
from ocx_schema_parser.model import (
    Attribute,
    Cardinality,
    ChildElement,
    ComplexType,
    EnumType,
    EnumValue,
    GlobalElement,
    OcxSchema,
    SchemaChange,
    SimpleType,
)
from ocx_schema_parser.resolver import resolve

__version__ = "3.0.0"

DEFAULT_SCHEMA = "https://3docx.org/fileadmin/ocx_schema/V310/OCX_Schema.xsd"
WORKING_DRAFT = "https://3docx.org/fileadmin//ocx_schema//V320rc8//OCX_Schema.xsd"

__all__ = [
    "Attribute",
    "Cardinality",
    "ChildElement",
    "ComplexType",
    "DEFAULT_SCHEMA",
    "EnumType",
    "EnumValue",
    "GlobalElement",
    "OcxParserError",
    "OcxSchema",
    "SchemaChange",
    "SimpleType",
    "WORKING_DRAFT",
    "load",
    "resolve",
]

# Library convention: silent unless the application enables logging.
logger.disable("ocx_schema_parser")
```

- [ ] **Step 3: Run the full suite**

Run: `uv run pytest`
Expected: all tests PASS (coverage report prints; no threshold enforced)

- [ ] **Step 4: Verify the public API imports**

Run: `uv run python -c "import ocx_schema_parser as p; print(p.__version__, p.DEFAULT_SCHEMA)"`
Expected output: `3.0.0 https://3docx.org/fileadmin/ocx_schema/V310/OCX_Schema.xsd`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "refactor!: remove legacy 2.x modules, new 3.0 public API

BREAKING CHANGE: OcxParser, XmlParser, SchemaHelper and utils are removed.
Use load()/resolve() and the OcxSchema model instead.

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 11: cli.py (TDD)

**Files:**
- Create: `ocx_schema_parser/cli.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v --no-cov`
Expected: FAIL — `ModuleNotFoundError: No module named 'ocx_schema_parser.cli'`

- [ ] **Step 3: Write cli.py**

Create `ocx_schema_parser/cli.py`:

```python
"""Command line interface: export the OCX schema model as JSON."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

import ocx_schema_parser
from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.loader import load
from ocx_schema_parser.resolver import resolve


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ocx-schema-parser",
        description="Parse the OCX schema and export it as a typed JSON model.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {ocx_schema_parser.__version__}",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    export = subparsers.add_parser("export", help="Export a schema source to JSON")
    export.add_argument(
        "source",
        help="A local .xsd file, a folder of .xsd files, or an http(s) URL",
    )
    export.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output JSON file (default: stdout)",
    )
    export.add_argument(
        "--download-folder",
        type=Path,
        default=None,
        help="Folder for downloaded schemas when source is a URL (default: temp folder)",
    )
    export.add_argument(
        "--indent", type=int, default=2, help="JSON indentation (default: 2)"
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        schemas = load(args.source, download_folder=args.download_folder)
        model = resolve(schemas)
        payload = model.model_dump_json(indent=args.indent)
        if args.output is not None:
            args.output.write_text(payload, encoding="utf-8")
        else:
            print(payload)
        print(
            f"Resolved schema {model.schema_version}: "
            f"{len(model.elements)} elements, "
            f"{len(model.complex_types)} complex types, "
            f"{len(model.enumerations)} enumerations",
            file=sys.stderr,
        )
        return 0
    except OcxParserError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v --no-cov`
Expected: all 4 tests PASS

- [ ] **Step 5: Smoke test the installed entry point**

Run: `uv run ocx-schema-parser export tests/data -o schema.json; uv run python -c "import json; d=json.load(open('schema.json')); print(d['schema_version'], len(d['elements']))"; Remove-Item schema.json`
Expected: prints `3.0.0` and an element count > 300

- [ ] **Step 6: Commit**

```bash
git add ocx_schema_parser/cli.py tests/test_cli.py
git commit -m "feat: add ocx-schema-parser CLI with export subcommand

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 12: Snapshot regression test

Uses `pytest-regressions`. The first run writes the snapshot; subsequent runs compare against it, guarding the whole pipeline output.

**Files:**
- Test: `tests/test_snapshot.py`
- Generated: `tests/test_snapshot/test_full_schema_snapshot.yml` (committed)

- [ ] **Step 1: Write the snapshot test**

Create `tests/test_snapshot.py`:

```python
"""Full-pipeline snapshot regression test."""


def test_full_schema_snapshot(ocx_model, data_regression):
    data_regression.check(ocx_model.model_dump(mode="json"))
```

- [ ] **Step 2: Generate the snapshot**

Run: `uv run pytest tests/test_snapshot.py --force-regen --no-cov`
Expected: 1 test FAILS with "Files were regenerated" (this is how pytest-regressions reports a fresh snapshot).

- [ ] **Step 3: Verify the snapshot is stable**

Run: `uv run pytest tests/test_snapshot.py --no-cov` (run it twice)
Expected: PASS both times — output is deterministic.

Inspect `tests/test_snapshot/test_full_schema_snapshot.yml` briefly: it must contain `schema_version: 3.0.0`, a sorted `elements` list, and `schema_changes: []` (the bundled V300 test schema has no SchemaChange tags).

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_snapshot.py tests/test_snapshot
git commit -m "test: add full-pipeline snapshot regression test

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 13: Documentation, README, CHANGELOG

**Files:**
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/schema.rst` (full rewrite)
- Modify: `docs/index.rst`
- Delete: `docs/utils.rst`

- [ ] **Step 1: Rewrite README.md**

Replace the entire content of `README.md` with:

````markdown
![](docs/_static/logo.png)
# ocx-schema-parser

A Python library and CLI for parsing the [OCX](https://3docx.org) XSD schema
into a typed, immutable model that serializes to JSON.

## Installation

```
pip install ocx-schema-parser
```

## Usage

### CLI

```
# Export a remote schema to JSON
ocx-schema-parser export https://3docx.org/fileadmin/ocx_schema/V310/OCX_Schema.xsd -o ocx_schema.json

# Export a local schema file or folder
ocx-schema-parser export path/to/OCX_Schema.xsd
```

### Python API

```python
from ocx_schema_parser import load, resolve, DEFAULT_SCHEMA

schemas = load(DEFAULT_SCHEMA)          # URL, local .xsd file, or folder
model = resolve(schemas)                # -> OcxSchema (frozen Pydantic model)

vessel = model.get("ocx:Vessel")
print(vessel.description)
print([a.name for a in vessel.attributes])
print(model.model_dump_json(indent=2))  # full JSON export
```

## API documentation

Autogenerated with ``sphinx``: https://ocxstandard.github.io/ocx-schema-parser/

## Changelog
[Changelog](CHANGELOG.md)
````

- [ ] **Step 2: Add the CHANGELOG entry**

In `CHANGELOG.md`, insert directly above the `## [2.0.1] - 2026-02-28` line:

```markdown
## [3.0.0] - 2026-08-20

bump to [v3.0.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v3.0.0)

### Changed

* Complete rewrite: XSD parsing is now delegated to `xsdata`'s `SchemaParser`,
  and the parsed schema is resolved into a typed, frozen Pydantic v2 model
  (`OcxSchema`) that serializes to JSON.
* New public API: `load(source)`, `resolve(schemas)`, and the model classes.
* New `ocx-schema-parser export` CLI.

### Removed

* **BREAKING:** `OcxParser`, `Transformer`, `LxmlParser`, `LxmlElement`,
  `SchemaHelper`, `OcxGlobalElement`, the `data_classes` module, the `utils`
  package and the `ocxdownloader` sub-package (`SchemaDownloader` moved to
  `ocx_schema_parser.downloader`).
* Dependencies `ocx-common`, `pyspellchecker` and `pyyaml`.
```

- [ ] **Step 3: Rewrite docs/schema.rst**

Replace the entire content of `docs/schema.rst` with:

```rst
=========
Reference
=========

loader
======

.. automodule:: ocx_schema_parser.loader
   :members:

resolver
========

.. autofunction:: ocx_schema_parser.resolver.resolve

model
=====

.. automodule:: ocx_schema_parser.model
   :members:
   :undoc-members:
   :show-inheritance:

downloader
==========

.. autoclass:: ocx_schema_parser.downloader.SchemaDownloader
   :members:
   :show-inheritance:

cli
===

.. automodule:: ocx_schema_parser.cli
   :members:

errors
======

.. autoclass:: ocx_schema_parser.errors.OcxParserError
   :show-inheritance:
```

- [ ] **Step 4: Update docs/index.rst and delete docs/utils.rst**

In `docs/index.rst`, remove the `utils.rst` line from the toctree (keep `schema.rst`). Then:

```powershell
Remove-Item docs\utils.rst
```

- [ ] **Step 5: Verify the docs build**

Run: `uv run --group docs sphinx-build -W --keep-going -b html docs docs/_build`
Expected: build succeeds (fix any autodoc import warnings if they reference deleted modules). If the docs group fails to install or the config needs unrelated fixes, note it and continue — docs build failures unrelated to this refactor are out of scope.

- [ ] **Step 6: Commit**

```bash
git add README.md CHANGELOG.md docs
git commit -m "docs: rewrite README and API docs for 3.0

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

---

### Task 14: Final verification

- [ ] **Step 1: Full test suite from a clean sync**

Run: `uv sync --group dev; uv run pytest`
Expected: all tests PASS.

- [ ] **Step 2: Check nothing legacy remains**

```powershell
Get-ChildItem ocx_schema_parser -Recurse -Filter *.py | Select-Object -ExpandProperty Name
```

Expected exactly: `__init__.py`, `cli.py`, `downloader.py`, `errors.py`, `loader.py`, `model.py`, `resolver.py`.

- [ ] **Step 3: Verify tbump configuration is consistent**

Run: `uv run tbump --dry-run 3.0.0 --no-interactive`
Expected: dry run reports the current version is already 3.0.0 (or exits complaining new == current — either confirms consistency; the CHANGELOG `grep -q 3.0.0` hook is satisfied by Task 13).

- [ ] **Step 4: Commit any stragglers**

```bash
git status
git add -A
git commit -m "chore: 3.0.0 cleanup

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
```

(Skip the commit if the tree is clean.)

---

## Notes for the executor

**Deliberate deviations from the spec (approved rationale):**
- `complex_types` uses a dedicated `ComplexType` model instead of reusing `GlobalElement` — cardinality, `type` and `substitution_group` are meaningless for a type definition. Simpler and more honest.
- `transformer.py` is deleted although the spec's delete list omitted it — it is not part of the new architecture and depends on deleted modules.
- `SimpleType.restriction` is a `dict[str, str]` of facets (spec left the shape open).
- Task 7's full-schema ancestry test uses `ocxXML_T` instead of `Vessel_T` — verified against the bundled schema: `Vessel_T`'s chain is Form_T → EntityBase_T → DescriptionBase_T → IdBase_T (no DocumentBase_T), so the original expectation was factually wrong.

- **Always use `uv`** for package management and running commands (`uv sync`, `uv run pytest`, `uv run python`).
- Tests import `parse_fragment` from `conftest` directly (`from conftest import parse_fragment`) — this works because `pythonpath = ["."]` plus pytest's rootdir conftest handling puts `tests/` on the path during collection. If the import fails, use `from tests.conftest import parse_fragment` consistently in all test files.
- The bundled `tests/data/OCX_Schema.xsd` is OCX V300; its target namespace is `https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd` and its `schemaVersion` fixed value is `3.0.0`.
- `--no-cov` is used for targeted runs only to keep output focused; the final suites run with the configured coverage addopts.
- Exact counts in the full-schema assertions (`> 300` elements) are intentionally loose lower bounds; do not tighten them to exact numbers.
