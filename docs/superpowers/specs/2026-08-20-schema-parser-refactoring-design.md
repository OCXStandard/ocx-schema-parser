# OCX Schema Parser 3.0 — Refactoring Design

**Date:** 2026-08-20
**Status:** Approved for planning
**Version target:** 3.0.0 (clean break, no deprecation shims)

## Goal

Replace the hand-rolled lxml XSD traversal with xsdata's schema parser and
produce a clean, typed, Pydantic v2 model of the OCX schema that serializes
to JSON. The typed model is the product; rendering is out of scope.

## Decisions

| Question | Decision |
| --- | --- |
| API compatibility | Not required — only the owner's tools consume the package |
| Primary purpose | Typed schema model; JSON export |
| Parsing backend | xsdata `SchemaParser` (`xsdata.codegen.parsers.schema`) + `xsdata.models.xsd` |
| Model technology | Pydantic v2 |
| Model scope | Flattened inheritance, substitution groups, enums, cardinality, annotations, SchemaChange history, namespaces. **No assertions** — XSD 1.0 only |
| check.py / rendering | Dropped from the package |
| CLI | Yes: `ocx-schema-parser export <url|path> -o model.json` |
| Tests | Fresh suite: unit tests + JSON snapshot tests (pytest-regressions) |

xsdata 26.2 is already available transitively via `ocx-common`; it becomes an
explicit dependency. `xsdata.models.xsd` is semi-internal API, so xsdata is
pinned and covered by snapshot tests.

## Architecture

Three-stage pipeline with one-way dependencies:
`loader.load(source)` → `resolver.resolve(schemas)` → `OcxSchema` → `.model_dump_json()`.

```
ocx_schema_parser/
├── __init__.py          # __version__, public API re-exports, default schema URL constants
├── loader.py            # url/path/folder → list[xsd.Schema]
├── model.py             # Pydantic v2 models
├── resolver.py          # list[xsd.Schema] → OcxSchema
├── downloader.py        # SchemaDownloader (moved up from ocxdownloader/)
├── cli.py               # argparse CLI, [project.scripts] entry point
└── errors.py            # OcxParserError
```

**Deleted modules:** `xelement.py`, `xparse.py`, `ocxparser.py`, `elements.py`,
`helpers.py`, `check.py`, `documentor.py`, `data_classes.py`, `config.py`,
`utils/`, `ocxdownloader/`, `main.py`.

**Dependencies:** add `xsdata` (pinned) and `pydantic>=2`; drop
`pyspellchecker`, `pyyaml`; keep `ocx-common` only if the downloader requires
it. Dev: restore `pytest-regressions` (previously removed under the misnamed
`pytest-regression`).

## Typed model (`model.py`)

Pydantic v2, `frozen=True` where practical.

```python
class Cardinality(BaseModel):
    lower: int
    upper: int | None                     # None = unbounded; str() renders "[1, ∞]"

class Attribute(BaseModel):
    name: str
    prefix: str
    type: str                             # "prefix:Name"
    use: Literal["required", "optional"]
    default: str | None
    fixed: str | None
    description: str

class ChildElement(BaseModel):
    name: str
    prefix: str
    type: str
    cardinality: Cardinality
    is_choice: bool
    from_substitution_group: str | None   # provenance when expanded
    inherited_from: str | None            # ancestor type tag if inherited
    description: str

class GlobalElement(BaseModel):
    name: str
    prefix: str
    tag: str                              # "{namespace}Name"
    type: str
    abstract: bool
    cardinality: Cardinality
    description: str
    parents: list[str]                    # resolved ancestor tags, nearest first
    attributes: list[Attribute]           # own + inherited (flattened)
    children: list[ChildElement]          # own + inherited (flattened)
    substitution_group: str | None

class EnumValue(BaseModel):   # value, description
class EnumType(BaseModel):    # name, prefix, tag, values: list[EnumValue]
class SimpleType(BaseModel):  # name, prefix, tag, type, restriction, description
class SchemaChange(BaseModel) # version, author, date, description

class OcxSchema(BaseModel):
    schema_version: str
    target_namespace: str
    namespaces: dict[str, str]            # prefix → uri
    elements: list[GlobalElement]
    complex_types: list[GlobalElement]    # documented types without a global element
    simple_types: list[SimpleType]
    enumerations: list[EnumType]
    attribute_groups: dict[str, list[Attribute]]
    substitution_groups: dict[str, list[str]]
    schema_changes: list[SchemaChange]
    # lookup helper: get(name_or_prefixed_name) -> GlobalElement | None
```

Improvements over 2.x: `inherited_from`/`from_substitution_group` provenance
(currently lost), structured cardinality instead of `"[1, ∞]"` strings, real
`None` instead of `"None"` strings.

## Loader (`loader.py`)

- `load(source: str | Path, download_folder: Path | None = None) -> list[xsd.Schema]`
- Remote URL → download via `SchemaDownloader` (all imports collected into one
  folder; folder cleaned first). Local file/folder → glob `*.xsd`.
- Each file parsed with xsdata `SchemaParser` (namespaces, target namespace,
  source locations come typed for free).
- Parse failure raises `OcxParserError` naming the file and cause — no silent
  boolean returns.

## Resolver (`resolver.py`)

`resolve(schemas: list[xsd.Schema]) -> OcxSchema`

1. **Index pass:** tag → node lookup for all named elements, complexTypes,
   simpleTypes, attributes, attributeGroups; collect namespaces, substitution
   groups, schema version (fixed `schemaVersion` attribute), SchemaChange
   annotations.
2. **Type resolution:** one shared, cycle-guarded `ancestors(type_ref)` walk
   over extension/restriction bases (replaces three copy-pasted loops in 2.x).
3. **Flattening:** for each global element/complexType, merge own + ancestor
   attributes (expanding attributeGroup refs) and children, tagging
   `inherited_from`. Substitution-group members expand abstract children,
   tagged `from_substitution_group` (fixes the 2.x `for/else` bug that added
   both the abstract child and its substitutes).
4. **Enums/simple types:** direct mapping from xsd restriction facets.

**Error handling:** unresolvable type refs are logged (loguru) and recorded
once; resolution continues. W3C built-ins are recognized by namespace, not by
a hardcoded list. **Determinism:** all output lists sorted by name so the JSON
export is diff-stable.

## CLI (`cli.py`)

stdlib argparse, registered under `[project.scripts]`:

```
ocx-schema-parser export <url|path> [-o model.json] [--download-folder tmp] [--indent 2]
```

One-line summary (version, counts) to stderr; JSON to file or stdout.

## Testing

- **Unit tests:** resolver pieces (ancestor walk, attributeGroup expansion,
  substitution-group expansion, cardinality) against small handcrafted xsd
  fragments.
- **Snapshot test:** full JSON export of bundled `tests/data/OCX_Schema.xsd`
  via pytest-regressions `data_regression`.
- **CLI smoke test.**
- Old test files and yml snapshots are deleted with the old API.

## Migration & cleanup

- Version → 3.0.0; tbump config updated.
- README rewritten with model-first usage example + CLI.
- CHANGELOG entry documenting the break and dropped features (check.py,
  rendering, XSD 1.1 assertions).
- Sphinx automodapi targets updated to the new modules.
- Package management with `uv` throughout.
