"""OCX Schema conformance checks"""
#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from collections import defaultdict
from typing import Dict, Set, Tuple

import inflection

#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from spellchecker import SpellChecker

from ocx_schema_parser import ALLOWED_WORDS, NAME_EXCEPTIONS
from ocx_schema_parser.transformer import Transformer


class SchemaCheck:
    """The SchemaCheck provides functionality for checking the conformance of the OCX schema XSD.

    Args:
        parser: the OCX schema parser

    Attributes:
        _parser: The instance of the OCX parser
        _spell_check: The spell checker. Default language='en'

    """

    def __init__(self, transformer: Transformer):
        self._transformer = transformer
        self._spell_check = SpellChecker()
        self.allowed_schema_names()
        self._spell_check.word_frequency.load_words(ALLOWED_WORDS)

    def allowed_schema_names(self):
        """Add the OCX schema types as allowed words to the dictionary list."""
        known_words = []
        for ocx in self._transformer.ocx_iterator():
            #  Strip off the namespace
            known_words.append(ocx.get_name())
        self._spell_check.word_frequency.load_words(known_words)

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

    def check_schema_name_conformance(self) -> Tuple[bool, Dict]:
        """Check the conformance of the OCX schema names.

        Returns:
            True if all names conform, False otherwise and the names that failed the check.

        """
        result = True
        failures = defaultdict(list)
        for e in self._transformer.ocx_iterator():
            name = e.get_name()
            if self.is_camel_case(name) is not True and name not in NAME_EXCEPTIONS:
                result = False
                failures["camel_case"].append(name)
            children = e.get_children()
            for child in children:
                name = child.name
                if self.is_camel_case(name) is not True and name not in NAME_EXCEPTIONS:
                    print(name)
                    failures["camel_case"].append(name)
            attributes = e.get_attributes()
            for attr in attributes:
                name = attr.name
                if (
                    self.is_dromedary_case(name) is not True
                    and name not in NAME_EXCEPTIONS
                ):
                    print(name)
                    failures["dromedary_case"].append(name)
        return result, failures

    def check_schema_conformance(self, namespace: str) -> bool:
        """Verify the OCX schema conformance.

        Arguments:
            namespace: Only schema elements with the namespace will be verified.
        """

        pass
