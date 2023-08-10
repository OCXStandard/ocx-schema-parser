#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
import pytest
from ocx_schema_parser.transformer import Transformer
from ocx_schema_parser.check import SchemaCheck



class TestSchemaCheck:
    """Test class for the SchemaCheck methods."""

    def test_check_annotations(self, transformer: Transformer):
        """Spelling check of a text."""
        checker = SchemaCheck(transformer)
        vessel = transformer.get_ocx_element_from_type("ocx:Vessel")
        text = vessel.get_annotation()
        misspelled = checker.check_annotation(text)
        assert len(misspelled) == 0

    def test_is_camel_case(self):
        """Camel case conformance check."""
        assert SchemaCheck.is_camel_case('TBar') is True

    def test_is_dromedary_case(self):
        """Dromedary case conformance check."""
        assert SchemaCheck.is_dromedary_case('functionType') is True

    def test_check_schema_name_conformance(self, transformer: Transformer):
        checker = SchemaCheck(transformer)
        result, failures = checker.check_schema_name_conformance()
        assert result is True
