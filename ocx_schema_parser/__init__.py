#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

__version__ = "1.7.1"

# Third party imports
from loguru import logger

# Application imports
from ocx_schema_parser.config import config

SCHEMA_FOLDER = config.get("SchemaParserSettings", "schema_folder")
TMP_FOLDER = config.get("SchemaParserSettings", "tmp_folder")
WORKING_DRAFT = config.get("SchemaParserSettings", "working_draft")
DEFAULT_SCHEMA = config.get("SchemaParserSettings", "schema_url")
keys = config.get("SchemaParserSettings", "w3c_schema_builtin_keys")
values = config.get("SchemaParserSettings", "w3c_schema_builtin_values")
W3C_SCHEMA_BUILT_IN_TYPES = dict(zip(keys, values))
PROCESS_SCHEMA_TYPES = config.get(
    "SchemaParserSettings", "process_schema_types"
).split()
ALLOWED_WORDS = config.get("SchemaParserSettings", "known_word_list").split()
OCX_NAME_EXCEPTIONS = config.get("SchemaParserSettings", "ocx_name_exceptions").split()

logger.disable(__name__)
