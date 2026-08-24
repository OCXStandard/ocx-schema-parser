"""Shared fixtures for the ocx-schema-parser test suite."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from xsdata.codegen.parsers.schema import SchemaParser
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
