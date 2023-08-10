#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE


from ocx_schema_parser.transformer import Transformer
from ocx_schema_parser import WORKING_DRAFT

class TestTransformer:



    def test_is_transformed(self, transformer: Transformer):
        assert transformer.is_transformed()


    def test_get_ocx_elements(self, transformer: Transformer):
        assert len(transformer.get_ocx_elements()) == 327


    def test_get_ocx_element_from_type(self, transformer: Transformer):
        vessel = transformer.get_ocx_element_from_type('ocx:Vessel')
        assert vessel


    def test_get_enumerators(self, data_regression, transformer: Transformer):

        enums = transformer.get_enumerators()
        result =  {
            enum: enums[enum].to_dict() for enum in enums
        }
        data_regression.check(result)


    def test_get_global_attributes(self, data_regression, transformer: Transformer):
        result =  {
            enum.name: enum.to_dict() for enum in transformer.get_global_attributes()
        }
        data_regression.check(result)


    def test_get_simple_types(self, data_regression, transformer: Transformer):
        result =  {
            enum.name: enum.to_dict() for enum in transformer.get_simple_types()
        }
        data_regression.check(result)
