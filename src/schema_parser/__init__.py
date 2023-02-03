#  Copyright (c) 2023.  OCX Consortium https://3docx.org. See the LICENSE

from pathlib import Path

from utils import utilities

__version__ = '0.2.0'

config_file = Path(utilities.root_dir()) / "schema_parser" / "configs" / "schema_config.yaml"  # The schema config

app_config = utilities.load_yaml_config(config_file)  # safe yaml load

DEFAULT_SCHEMA = app_config.get("DEFAULT_SCHEMA")
SCHEMA_FOLDER = app_config.get("SCHEMA_FOLDER")
W3C_SCHEMA_BUILT_IN_TYPES = app_config.get("W3C_SCHEMA_BUILT_IN_TYPES")
PROCESS_SCHEMA_TYPES = app_config.get("PROCESS_SCHEMA_TYPES")
SUB_COMMAND = app_config.get("SUB_COMMAND")
