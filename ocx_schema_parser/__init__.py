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
