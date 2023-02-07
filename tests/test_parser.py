""" Tests for the schema reader classes"""
from schema_parser.parser import OcxSchema


class TestOcxSchema:
    def test_get_ocx_element_from_type(self, process_schema: OcxSchema):
        vessel = process_schema.get_ocx_element_from_type("ocx:Vessel")
        assert vessel.get_name() == "Vessel"

    def test_summary_table(self, data_regression, process_schema: OcxSchema):
        summary = process_schema.tbl_summary()
        data_regression.check(summary.__dict__)

    def test_tbl_attribute_groups(self, data_regression, process_schema: OcxSchema):
        result = process_schema.tbl_attribute_groups()
        data_regression.check(result)

    def test_tbl_simple_types(self, data_regression, process_schema: OcxSchema):
        result = process_schema.tbl_simple_types()
        data_regression.check(result)

    def test_element_types(self, data_regression, process_schema: OcxSchema):
        result = process_schema.tbl_simple_types()
        data_regression.check(result)

    def test_complex_types(self, data_regression, process_schema: OcxSchema):
        result = process_schema.tbl_simple_types()
        data_regression.check(result)

    def test_attribute_types(self, data_regression, process_schema: OcxSchema):
        result = process_schema.tbl_simple_types()
        data_regression.check(result)
