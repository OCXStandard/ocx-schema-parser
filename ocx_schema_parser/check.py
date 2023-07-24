"""OCX Schema conformance checks"""
#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from spellchecker import SpellChecker
import inflection
from typing import Set
from ocx_schema_parser.xelement import LxmlElement
from ocx_schema_parser.parser import OcxSchema
from ocx_schema_parser import ALLOWED_WORDS, NAME_EXCEPTIONS


class SchemaCheck:
    """The SchemaCheck provides functionality for checking the conformance of the OCX schema XSD.

    Args:
        parser: the OCX schema parser

    Attributes:
        _parser: The instance of the OCX parser
        _spell_check: The spell checker. Default language='en'

    """

    def __init__(self, parser: OcxSchema):
        self._parser = parser
        self._spell_check = SpellChecker()
        self.allowed_schema_names()
        self._spell_check.word_frequency.load_words(ALLOWED_WORDS)

    def allowed_schema_names(self):
        """Add the OCX schema types as allowed words to the dictionary list."""
        known_words = []
        for tag in self._parser.get_all_schema_elements():
            #  Strip off the namespace
            name = LxmlElement.strip_namespace_tag(tag)
            known_words.append(name)
        self._spell_check.word_frequency.load_words(known_words)

    def get_ocx_parser(self) -> OcxSchema:
        """Return the OCX parser instance."""
        return self._parser

    def check_annotation(self, text: str) -> Set:
        """Spell check the schema annotation text.

        Arguments:
            text: The text to spell check

        Returns:
            A set of misspelled words. Empty set if everything is correct.
        """
        # Tokenize and split text into list of words
        words = self._spell_check.split_words(text)
        return self._spell_check.unknown(words)

    @staticmethod
    def is_camel_case(name: str) -> bool:
        """Return True if the name is camel case conform.

        Arguments:
            name: The name to verify


        """
        return inflection.camelize(name, True) == name

    @staticmethod
    def is_dromedary_case(name: str) -> bool:
        """Return True if the name is dromedary case conform.

        Arguments:
            name: The string to verify
        """
        return inflection.camelize(name, False) == name

    def check_schema_name_conformance(self) -> bool:
        """Check the conformance of the OCX schema names."""
        result = True
        elements = self._parser.get_ocx_elements()
        for e in elements:
            name = e.get_name()
            if self.is_camel_case(name) is not True and name not in NAME_EXCEPTIONS:
                result = False
                print(name)
            children = e.get_children()
            for child in children:
                name = child.get_name()
                if self.is_camel_case(name) is not True and name not in NAME_EXCEPTIONS:
                    print(name)
                    result = False
            attributes = e.get_attributes()
            for attr in attributes:
                name = attr.get_name()
                if self.is_dromedary_case(name) is not True and name not in NAME_EXCEPTIONS:
                    print(name)
                    result = False
        return result

    def check_schema_conformance(self, namespace: str) -> bool:
        """Verify the OCX schema conformance.

        Arguments:
            namespace: Only schema elements with the namespace will be verified.
        """

        for enum in LxmlElement.iter(self._xs_attribute, '{*}enumeration'):
            yield
