#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
"""Tests for OcxGlobalElement class"""

from ocx_schema_parser.transformer import Transformer


class TestOcxGlobalElement:
    def test_get_ocx_type(self, transformer_from_folder: Transformer):
        vessel = transformer_from_folder.get_ocx_element_from_type("ocx:Panel")
        assert vessel.get_type() == "ocx:Panel_T"

    def test_get_ocx_prefix(self, transformer_from_folder: Transformer):
        vessel = transformer_from_folder.get_ocx_element_from_type("ocx:Panel")
        assert vessel.get_prefix() == "ocx"

    def test_get_untsml_type(self, transformer_from_folder: Transformer):
        vessel = transformer_from_folder.get_ocx_element_from_type("unitsml:RootUnits")
        assert vessel.get_type() == "RootUnitsType"

    def test_get_unitsml_prefix(self, transformer_from_folder: Transformer):
        vessel = transformer_from_folder.get_ocx_element_from_type("unitsml:RootUnits")
        assert vessel.get_prefix() == "unitsml"

    def test_attributes_to_dict(
        self, data_regression, transformer_from_folder: Transformer
    ):
        item = transformer_from_folder.get_ocx_element_from_type("ocx:Panel")
        result = {attr.name: attr.to_dict() for attr in item.get_attributes()}
        data_regression.check(result)

    def test_children_to_dict(
        self, data_regression, transformer_from_folder: Transformer
    ):
        item = transformer_from_folder.get_ocx_element_from_type("ocx:Panel")
        result = {attr.name: attr.to_dict() for attr in item.get_children()}
        data_regression.check(result)
