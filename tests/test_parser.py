""" Tests for the OCXSchema class"""
from ocx_schema_parser.parser import OcxSchema


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

    def test_attribute_enumerator(self, process_schema: OcxSchema):
        panel = process_schema.get_ocx_element_from_type("ocx:Panel")
        attribute = None
        # attribute = [a for a in panel.get_attributes() if a.get_name == 'functionType'][0]
        for a in panel.get_attributes():
            if a.get_name() == 'functionType':
                attribute = a
        assert attribute.is_enumerator() is True

    def test_get_ocx_children_data(self, data_regression, process_schema: OcxSchema):
        result = process_schema.get_ocx_children_data('ocx:Vessel')[0]
        data_regression.check(result)
