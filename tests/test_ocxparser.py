#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

""" Tests for the OCXSchema class"""
from ocx_schema_parser.ocxparser import OcxParser


class TestOcxParser:

    def test_summary_table(self, data_regression, process_schema: OcxParser):
        summary = process_schema.tbl_summary()
        data_regression.check(summary)

    def test_tbl_attribute_groups(self, data_regression, process_schema: OcxParser):
        result = process_schema.tbl_attribute_groups()
        data_regression.check(result)

    def test_tbl_simple_types(self, data_regression, process_schema: OcxParser):
        result = process_schema.tbl_simple_types()
        data_regression.check(result)

    def test_element_types(self, data_regression, process_schema: OcxParser):
        result = process_schema.tbl_element_types()
        data_regression.check(result)

    def test_complex_types(self, data_regression, process_schema: OcxParser):
        result = process_schema.tbl_complex_types()
        data_regression.check(result)

    def test_attribute_types(self, data_regression, process_schema: OcxParser):
        result = process_schema.tbl_attribute_types()
        data_regression.check(result)

    def test_get_xs_types(self,  data_regression, process_schema: OcxParser):
        result = process_schema.get_xs_types()
        data_regression.check(result)
