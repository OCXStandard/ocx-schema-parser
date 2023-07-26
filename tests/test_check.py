#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from ocx_schema_parser.parser import OcxSchema
from ocx_schema_parser.check import SchemaCheck


class TestSchemaCheck:
    """Test class for the SchemaCheck methods."""

    def test_check_annotations(self, process_schema: OcxSchema):
        """Spelling check of a text."""
        schema_check = SchemaCheck(process_schema)
        vessel = process_schema.get_ocx_element_from_type("ocx:Vessel")
        text = vessel.get_annotation()
        misspelled = schema_check.check_annotation(text)
        assert len(misspelled) == 0

    def test_is_camel_case(self):
        """Camel case conformance check."""
        assert SchemaCheck.is_camel_case('TBar') is True

    def test_is_dromedary_case(self):
        """Dromedary case conformance check."""
        assert SchemaCheck.is_dromedary_case('functionType') is True

    def test_check_schema_name_conformance(self, process_schema):
        schema_check = SchemaCheck(process_schema)
        assert schema_check.check_schema_name_conformance() is True
