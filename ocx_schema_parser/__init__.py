#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from pathlib import Path

# Third party imports
from loguru import logger

# Application imports
from .utils import utilities

__version__ = "1.4.0"

current_dir = Path(__file__).parent
config_file = current_dir / "configs" / "schema_config.yaml"  # The schema config

app_config = utilities.load_yaml_config(config_file)  # safe yaml load

DEFAULT_SCHEMA = app_config.get("DEFAULT_SCHEMA")
SCHEMA_FOLDER = app_config.get("SCHEMA_FOLDER")
TMP_FOLDER = app_config.get("TMP_FOLDER")
W3C_SCHEMA_BUILT_IN_TYPES = app_config.get("W3C_SCHEMA_BUILT_IN_TYPES")
PROCESS_SCHEMA_TYPES = app_config.get("PROCESS_SCHEMA_TYPES")
SUB_COMMAND = app_config.get("SUB_COMMAND")
ALLOWED_WORDS = app_config.get("KNOWN_WORD_LIST")
NAME_EXCEPTIONS = app_config.get("OCX_NAME_EXCEPTIONS")
WORKING_DRAFT = app_config.get("WORKING_DRAFT")

logger.enable(__name__)
