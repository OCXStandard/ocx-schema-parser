#  Copyright (c) 2022. OCX Consortium https://3docx.org. See the LICENSE

from loguru import logger
import os
import sys
from pathlib import Path
from typing import Union

import pytest
import requests
from requests import HTTPError

# To make sure that the tests import the modules this has to come before the import statements
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ocx_schema_parser import DEFAULT_SCHEMA
from ocx_schema_parser.parser import LxmlParser
from ocx_schema_parser.parser import OcxSchema



@pytest.fixture
def load_schema_from_file(shared_datadir) -> LxmlParser:
    """Load the schema from file and make it available for processing."""
    parser = LxmlParser()
    file = shared_datadir / 'OCX_Schema.xsd'
    parser.parse(file.absolute())
    assert parser.lxml_version() == (4, 9, 3, 0)
    return parser


@pytest.fixture
def process_schema(shared_datadir, load_schema_from_file) -> OcxSchema:
    """Process the schema and make it available for testing."""
    file_name = Path(load_schema_from_file.doc_url()).name
    test_data = shared_datadir / file_name
    url = str(test_data.resolve())
    schema_folder = shared_datadir
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(folder)
    result = schema_reader.process_schema(url)
    assert result is True
    return schema_reader
