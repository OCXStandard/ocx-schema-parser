"""The OCX Schema content classes."""
#  Copyright (c) 2022-2023. OCX Consortium https://3docx.org. See the LICENSE
from collections import defaultdict
from typing import Dict, List, Union

from loguru import logger

# Third party imports
from lxml.etree import Element, QName

from ocx_schema_parser.data_classes import OcxSchemaAttribute, OcxSchemaChild

# Module imports
from ocx_schema_parser.helpers import SchemaHelper
from ocx_schema_parser.xelement import LxmlElement


class OcxGlobalElement:
    """Global schema element class capturing the xsd schema definition of a global ``xs:element``.

    Args:
        xsd_element: The lxml.etree.Element class


    Attributes:
        _element: The ``lxml.Element`` instance
        _attributes: The attributes of the global element including the attributes of all schema supertypes
         _tag: The unique global tag of the ``OcXGlobalElement``
        _parents: Hash table of references to all parent schema types with tag as key
        _children: List of references to all children schema types with tag as key.
                        Includes also children of all super-types.
        -assertions: List of any assertions associated with the ``xs:element``

    """

    def __init__(self, xsd_element: Element, unique_tag: str, namespaces: Dict):
        # Private
        self._element: Element = xsd_element
        self._attributes: List[OcxSchemaAttribute] = []
        self._namespace: str = QName(unique_tag).namespace
        self._tag: str = unique_tag
        self._cardinality: tuple = LxmlElement.cardinality(xsd_element)
        self._children: List = []
        self._parents: Dict = {}
        self._assertions: List = []
        self._namespaces: Dict = namespaces

    def add_attribute(self, attribute: OcxSchemaAttribute):
        """Add attributes to the global element.

        Arguments:
            attribute : The attribute instance to be added

        """
        self._attributes.append(attribute)

    def add_child(self, child: OcxSchemaChild):
        """Add a child of an OCX global element'

        Arguments:
            child: The added  child instance

        Returns:
            Nothing

        """
        self._children.append(child)

    def add_assertion(self, test: str):
        """Add an assertion test associated to me

        Arguments:
            test: The definition of the assertion represented as a string

        Returns:
            Nothing

        """
        self._assertions.append(test)

    def has_assertion(self) -> bool:
        """Whether the element has assertions or not'

        Returns:
             Tru if the global element as assertions, False otherwise

        """
        return len(self._assertions) > 0

    def put_parent(self, tag: str, parent: Element):
        """Add a parent element

        Arguments:
            tag: The unique tag of the parent element
            parent: The parent xsd schema element

        Returns:
            None

        """
        self._parents[tag] = parent

    def get_parents(self) -> dict:
        """Return all my parents

        Returns:
            Return all parents as a dict of key-value pairs ``(tag, Element)``

        """
        return self._parents

    def get_parent_names(self) -> List:
        """Get all my parent names

        Returns:
            Return all parents names in a list

        """
        return [LxmlElement.strip_namespace_tag(tag) for tag in self._parents]

    def get_assertion_tests(self) -> List:
        """Get all my assertions

        Returns:
            Assertion tests in a list

        """
        return self._assertions

    def get_children(self) -> List:
        """Get all my children XSD types.

        Returns:
            Return all children as a dict of key-value pairs ``(tag, OCXChildElement)``

        """
        return self._children

    def get_namespace(self) -> str:
        """The element _namespace

        Returns:
            The _namespace of the global schema element as a str

        """
        return self._namespace

    def get_attributes(self) -> List:
        """The global element attributes including also parent attributes

        Returns:
            A dict of all attributes including also parent attributes

        """
        return self._attributes

    def get_name(self) -> str:
        """The global element name

        Returns:
            The name of the global schema element as a str

        """
        return LxmlElement.get_name(self._element)

    def get_annotation(self) -> str:
        """The global element annotation or description

        Returns:
            The annotation string of the element

        """
        annotation = LxmlElement.find_child_with_name(self._element, "annotation")
        if annotation is not None:
            return LxmlElement.get_element_text(annotation)

    def get_type(self) -> str:
        """The global element type

        Returns:
            The type of the global schema element as a str

        """
        return SchemaHelper.get_type(self._element)

    def get_prefix(self) -> str:
        """The global element _namespace prefix

        Returns:
            The namespace prefix of the global schema element

        """
        nsprefix = list(iter(self._namespaces))
        nstags = list(iter(self._namespaces.values()))
        prefix = ""
        try:
            index = nstags.index(self._namespace)
            prefix = nsprefix[index]
            if prefix is None:
                nstags.pop(index)
                nsprefix.pop(index)
                index = nstags.index(self._namespace)
                prefix = nsprefix.index(index)
        except ValueError as e:
            logger.error(f"{self._namespace} is not in the namespace list: {e}")
        if prefix == "":
            logger.debug(f"Empty namespace prefix in global elem,ent {self.get_name()}")
        return prefix

    def get_schema_element(self) -> Element:
        """Get the schema xsd element of the ``OcxSchemeElement`` object

        Returns:
            My xsd schema element

        """
        return self._element

    def put_cardinality(self, element: Element):
        """Override the cardinality of the OcxGlobalElement

        Args:
            element: the etree.Element node

        """
        self._cardinality = LxmlElement.cardinality(element)

    def get_cardinality(self) -> str:
        """Get the cardinality of the OcxGlobalElement

        Returns:
            The cardinality as sting represented by [lower, upper]

        """
        lower, upper = self._cardinality
        if upper == "unbounded":
            upper = "\u221E"  # UTF-8 Infinity symbol
        return f"[{lower}, {upper}]"

    def is_reference(self) -> bool:
        """Whether the element has a reference or not

        Returns:
            is_reference : True if the element has a reference, False otherwise

        """
        return LxmlElement.is_reference(self._element)

    def is_mandatory(self) -> bool:
        """Whether the element mandatory or not

        Returns:
            Returns True if the element is mandatory, False otherwise

        """
        return LxmlElement.is_mandatory(self._element)

    def is_choice(self) -> bool:
        """Whether the element is a choice or not

        Returns:
            True if the element is a choice, False otherwise

        """
        return LxmlElement.is_choice(self._element)

    def is_substitution_group(self) -> bool:
        """Whether the element is part of a substitutionGroup

        Returns:
            True if the element is a substitutionGroup, False otherwise

        """
        return LxmlElement.is_substitution_group(self._element)

    def is_abstract(self) -> bool:
        """Whether the element is abstract

        Returns:
            True if the element is abstract, False otherwise

        """
        return LxmlElement.is_abstract(self._element)

    def get_substitution_group(self) -> Union[str, None]:
        """Return the name of the substitutionGroup

        Returns:
            The name of the ``substitutionGroup``, None otherwise

        """
        return LxmlElement.get_substitution_group(self._element)

    def get_tag(self) -> str:
        """The global schema element unique tag

        Returns:
            The element tag on the form  ``{prefix}name``

        """
        return self._tag

    def get_use(self) -> str:
        """The element's use, required or optional

        Returns:
            The element use:  ``req.`` if mandatory, else ``opt``

        """
        use = "opt"
        if self.is_mandatory():
            use = "req"
        return use

    def get_properties(self) -> Dict:
        """A dictionary of all ``OcxGlobalElement`` property values

        Returns:
           main: A dictionary of property values with heading keys:

            .. list-table:: Heading keys
               :widths: 25 25 25 25 25 50

               * - Name
                 - Type
                 - Use
                 - Cardinality
                 - Fixed
                 - Description

        """
        table = defaultdict(list)
        table["Name"].append(self.get_name())
        table["Type"].append(self.get_type())
        table["Use"].append(self.get_use())
        table["Cardinality"].append(self.get_cardinality())
        table["Description"].append(self.get_annotation())
        return table

    def attributes_to_dict(self) -> Dict:
        """A dictionary of all ``OcxGlobalElement`` attribute values

        Returns:
            A dictionary of attribute values with heading keys

            .. list-table:: Heading keys
               :widths: 25 25 25 25 25 50

               * - Attribute
                 - Type
                 - Use
                 - Default
                 - Fixed
                 - Description

        """
        table = defaultdict(list)
        for attr in self._attributes:
            attributes = attr.to_dict()
            for a in attributes:
                table[a].append(attributes[a])
        return table

    def children_to_dict(self) -> Dict:
        """A dictionary of all ``OcxGlobalElement`` children values

        Returns:
            main: A dictionary of attribute values with heading keys:

            .. list-table:: Heading keys
               :widths: 25 25 25 25 50

               * - Child
                 - Type
                 - Use
                 - Cardinality
                 - Description

        """
        table = defaultdict(list)
        for child in sorted(self._children, key=lambda x: x.name):
            attributes = child.to_dict()
            for a in attributes:
                table[a].append(attributes[a])
        return table
