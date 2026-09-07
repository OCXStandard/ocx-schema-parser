# ocx-schema-parser: Changelog

All notable changes to the ``ocx-schema-parser`` will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to the Python [PEP 440 versioning recommendations](https://peps.python.org/pep-0440/).

### Types of changes
* ``Added`` for new features.
* ``Changed`` for changes in existing functionality.
* ``Deprecated`` for soon-to-be removed features.
* ``Removed`` for now removed features.
* ``Fixed`` for any bug fixes.
* ``Security`` in case of vulnerabilities.

## [3.1.0] - 2026-09-07

bump to [v3.1.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v3.1.0)

### Added

* `summary` CLI command: entity counts (elements, complex types, simple types,
  global attributes, attribute groups) grouped by target namespace.
* `list <kind> --name prefix:name` (case-insensitive): prints the entity's
  documentation plus tabular listings of its attributes and children.

### Changed

* `DEFAULT_SCHEMA` bumped to the V320 schema URL.
* Exported `complex_types` now include **all** named complex types; previously
  types used as the type of a global element were omitted.

### Fixed

* Enumerations declared as anonymous simple types on global attributes
  (e.g. `ocx:liquidCargoType`, `ocx:grade`) are now resolved and listed.
* Inline attribute enumerations declared on local attributes inside
  `xsd:attributeGroup`s or complex types (e.g. `unitsml:prefix`,
  `unitsml:unit`) are now synthesized as `EnumType`s too; previously only
  global attributes were scanned.
* Attributes carrying an inline enumeration now resolve their `type` to the
  synthesized enum's prefixed name (e.g. `Bracket.functionType` →
  `ocx:functionType`, `EnumeratedRootUnit.prefix` → `unitsml:prefix`)
  instead of the restriction base type, so consumers can link attributes to
  their enumerations.

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

## [2.0.1] - 2026-02-28

bump to [v2.0.1](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v2.0.1)

### Change

* Add building documentation to CI workflow
* Fix GitHub Actions workflow to correctly build and publish documentation

## [2.0.0] - 2026-02-28

bump to [v2.0.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v2.0.0)

### Change

* Fixed bug in OCX global element not returning children from parent types
* Updated baselines and tests

## [1.8.5] - 2025-01-17
bump to [v1.8.5](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.8.5)

### Change
* Fixed bug in SchemaDownloader to correctly handling a local file as input
* Updated baselines and tests


## [1.8.0] - 2024-12-11
bump to [v1.8.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.8.0)

### Change
* Fixed bug in unzipping built-in schema types

## [1.7.1] - 2024-03-11
bump to [v1.7.1](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.7.1)

### Change
* Add publish authority to package repository on pypi


## [1.7.0] - 2024-03-11
bump to [v1.7.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.7.0)

### Change
* Downgrade to Python 3.10

## [1.6.0] - 2023-12-09
bump to [v1.6.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.6.0)

## Changes
* Changed from config.yaml to Configparser app configuration

## [1.4.0] - 2023-11-29
bump to [v1.4.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.4.0)

### Changed
 - Removed invalid dependencies
 - Upgraded to Python 3.11

## [1.3.1] - 2023-09-28
bump to [v1.3.10](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.3.1)

## 1.0.0 - 2023-09-27
bump to [v1.0.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v1.0.0)

### Changed
  - Fix missing substitution groups
  - Add test for substitution groups
### Documentation
  - Update API documentation

## 0.8.0 - 2023-08-15
Bumped to [v.0.8.0](https://github.com/OCXStandard/ocx-schema-parser/releases/tag/v0.8.0)
### Changed
  - Add tests
  - Fix missing namespace prefix
