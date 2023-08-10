#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""Tests for OcxGlobalElement class
"""
import pytest
from ocx_schema_parser.transformer import Transformer
from ocx_schema_parser.elements import OcxGlobalElement

class TestOcxGlobalElement:
    def test_get_ocx_type(self, transformer: Transformer):
        vessel = transformer.get_ocx_element_from_type("ocx:Panel")
        assert vessel.get_type() == "ocx:Panel_T"

    def test_get_ocx_prefix(self, transformer: Transformer):
        vessel = transformer.get_ocx_element_from_type("ocx:Panel")
        assert vessel.get_prefix() == "ocx"

    def test_get_untsml_type(self, transformer: Transformer):
        vessel = transformer.get_ocx_element_from_type("unitsml:RootUnits")
        assert vessel.get_type() == "RootUnitsType"


    def test_get_unitsml_prefix(self, transformer: Transformer):
        vessel = transformer.get_ocx_element_from_type("unitsml:RootUnits")
        assert vessel.get_prefix() == "unitsml"
