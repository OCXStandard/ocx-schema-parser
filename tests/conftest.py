#  Copyright (c) 2022. OCX Consortium https://3docx.org. See the LICENSE

from loguru import logger
import os
import sys
from pathlib import Path

import pytest


# To make sure that the tests import the modules this has to come before the import statements
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ocx_schema_parser import DEFAULT_SCHEMA
from ocx_schema_parser.xparse import LxmlParser
from ocx_schema_parser.ocxparser import OcxParser
from ocx_schema_parser.transformer import Transformer
from ocx_schema_parser.transformer import resolve_source



@pytest.fixture
def load_schema_from_file(shared_datadir) -> LxmlParser:
    """Load the schema from file and make it available for processing."""
    parser = LxmlParser()
    file = shared_datadir / 'OCX_Schema.xsd'
    parser.parse(file.absolute())
    assert parser.lxml_version() == (4, 9, 3, 0)
    return parser


@pytest.fixture
def process_schema(shared_datadir, load_schema_from_file) -> OcxParser:
    """Process the schema and make it available for testing."""
    file_name = Path(load_schema_from_file.doc_url()).name
    test_data = shared_datadir / file_name
    url = str(test_data.resolve())
    schema_folder = shared_datadir
    folder = schema_folder.resolve()
    parser = OcxParser()
    for file in resolve_source(str(folder), True):
        result = parser.process_xsd_from_file(file)
        assert result is True
    return parser

@pytest.fixture
def transformer(shared_datadir, load_schema_from_file) -> Transformer:
    """Process the schema and make it available for testing."""
    transformer = Transformer()
    transformer.transform_schema_from_folder(shared_datadir)
    assert transformer.is_transformed() is True
    return transformer
