#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from ocx_schema_parser.check import SchemaCheck
from ocx_schema_parser.transformer import Transformer


class TestSchemaCheck:
    """Test class for the SchemaCheck methods."""

    def test_check_annotations(self, transformer_from_folder: Transformer):
        """Spelling check of a text."""
        checker = SchemaCheck(transformer_from_folder)
        vessel = transformer_from_folder.get_ocx_element_from_type("ocx:Vessel")
        text = vessel.get_annotation()
        misspelled = checker.check_annotation(text)
        assert len(misspelled) == 0

    def test_is_camel_case(self):
        """Camel case conformance check."""
        assert SchemaCheck.is_camel_case("TBar") is True

    def test_is_dromedary_case(self):
        """Dromedary case conformance check."""
        assert SchemaCheck.is_dromedary_case("functionType") is True

    def test_check_schema_name_conformance(self, transformer_from_folder: Transformer):
        checker = SchemaCheck(transformer_from_folder)
        result, failures = checker.check_schema_name_conformance()
        assert result is True
