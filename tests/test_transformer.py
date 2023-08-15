#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

import pytest
from ocx_schema_parser.transformer import Transformer
from ocx_schema_parser import WORKING_DRAFT


class TestTransformer:

    def test_is_transformed(self, transformer_from_folder: Transformer):
        assert transformer_from_folder.is_transformed()

    def test_get_ocx_elements(self, transformer_from_folder: Transformer):
        assert len(transformer_from_folder.get_ocx_elements()) == 327

    def test_get_ocx_element_from_type(self, transformer_from_folder: Transformer):
        vessel = transformer_from_folder.get_ocx_element_from_type('ocx:Vessel')
        assert vessel

    def test_get_enumerators(self, data_regression, transformer_from_folder: Transformer):
        enums = transformer_from_folder.get_enumerators()
        result = {
            name: {'Prefix': enum.prefix, 'Tag': enum.tag} for name, enum in
            transformer_from_folder.get_enumerators().items()
        }
        data_regression.check(result)

    def test_get_global_attributes(self, data_regression, transformer_from_folder: Transformer):
        result = {
            enum.name: enum.to_dict() for enum in transformer_from_folder.get_global_attributes()
        }
        data_regression.check(result)

    def test_get_simple_types(self, data_regression, transformer_from_folder: Transformer):
        result = {
            enum.name: enum.to_dict() for enum in transformer_from_folder.get_simple_types()
        }
        data_regression.check(result)

    def test_is_transformed_from_url(self, transformer_from_url: Transformer):
        assert transformer_from_url.is_transformed()

    def test_get_ocx_elementsfrom_url(self, transformer_from_url: Transformer):
        assert len(transformer_from_url.get_ocx_elements()) == 327

    def test_get_ocx_element_from_type_from_url(self, transformer_from_url: Transformer):
        vessel = transformer_from_url.get_ocx_element_from_type('ocx:Vessel')
        assert vessel

    def test_get_enumerators_from_url(self, data_regression, transformer_from_url: Transformer):
        enums = transformer_from_url.get_enumerators()
        result = {
            enum: enums[enum].to_dict() for enum in enums
        }
        data_regression.check(result)

    def test_get_global_attributes_from_url(self, data_regression, transformer_from_url: Transformer):
        result = {
            enum.name: enum.to_dict() for enum in transformer_from_url.get_global_attributes()
        }
        data_regression.check(result)

