#  Copyright (c) 2022. OCX Consortium https://3docx.org. See the LICENSE

import logging
import os
import sys
from pathlib import Path
from typing import Union

import pytest
import requests
from requests import HTTPError

# To make sure that the tests import the modules this has to come before the import statements
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from schema_parser import DEFAULT_SCHEMA
from schema_parser.parser import LxmlParser
from schema_parser.parser import OcxSchema

logger = logging.Logger(__name__)


@pytest.fixture
def download_schema(shared_datadir) -> (bool, Union[str, None]):  # The `shared_datadir` points to ./data in root
    """Download a schema to the global data folder `shared_datadir` from an url."""

    try:
        file_name = Path(DEFAULT_SCHEMA).name
        file = Path(shared_datadir) / file_name
        r = requests.get(DEFAULT_SCHEMA)
        with open(file, "wb") as f:
            f.write(r.content)
            assert Path(file).exists()
            return True, file
    except HTTPError as e:
        logger.error(f'Failed to access schema from "{DEFAULT_SCHEMA}: {e}""')
        return False, None


@pytest.fixture
def load_schema_from_file(shared_datadir, download_schema) -> LxmlParser:
    """Load the schema from file and make it available for processing."""
    assert download_schema[0] is True
    parser = LxmlParser(logger)
    file = download_schema[1]
    parser.parse(file)
    assert parser.lxml_version() == (4, 9, 2, 0)
    return parser


@pytest.fixture
def process_schema(shared_datadir, load_schema_from_file) -> OcxSchema:
    """Process the schema and make it available for testing."""
    file_name = Path(load_schema_from_file.doc_url()).name
    test_data = shared_datadir / file_name
    url = str(test_data.resolve())
    schema_folder = shared_datadir
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(logger, folder)
    result = schema_reader.process_schema(url)
    assert result is True
    return schema_reader
