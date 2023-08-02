#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""Tests for OcxGlobalElement class
"""
from ocx_schema_parser.parser import OcxSchema
from ocx_schema_parser.elements import OcxGlobalElement
def test_get_ocx_type(process_schema: OcxSchema):
    vessel = process_schema.get_ocx_element_from_type("ocx:Panel")
    assert vessel.get_type() == "ocx:Panel_T"


def test_get_ocx_prefix(process_schema: OcxSchema):
    vessel = process_schema.get_ocx_element_from_type("ocx:Panel")
    assert vessel.get_prefix() == "ocx"

def test_get_untsml_type(process_schema: OcxSchema):
    vessel = process_schema.get_ocx_element_from_type("unitsml:RootUnits")
    assert vessel.get_type() == "RootUnitsType"


def test_get_unitsml_prefix(process_schema: OcxSchema):
    vessel = process_schema.get_ocx_element_from_type("unitsml:RootUnits")
    assert vessel.get_prefix() == "unitsml"
