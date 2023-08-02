"""The OCX Schema content classes."""
#  Copyright (c) 2022-2023. OCX Consortium https://3docx.org. See the LICENSE

from collections import defaultdict
from loguru import logger
from typing import Dict
from typing import List
from typing import Union

from lxml.etree import Element
from lxml.etree import QName

from .helpers import SchemaHelper
from .xelement import LxmlElement
from .data_classes import SchemaEnumerator


class OcxAttribute:
    """Global schema attribute class capturing the XSD schema definition of a global ``xs:attribute``.

    Args:
        xs_attribute: The ``lxml.etree.Element`` instance

    Attributes:
        _xs_attribute: The ``lxml.etree.Element`` instance
        _name : The attribute name
        _type : The attribute type
        _use : Whether the attribute is optional or required
        _fixed: Whether the attribute has a fixed value if any
        _default: The default value of the attribute if any
        _annotation: The attribute description
        _is_global: True if the element is global, False otherwise
        _enumerator: Enumerator values. None if the attribute is not an enum.

    """

    def __init__(self, xs_attribute: Element, prefix: str):
        # Private
        self._xs_attribute = xs_attribute
        self._ns_prefix: str = prefix
        self._name: str = LxmlElement.get_name(xs_attribute)
        self._type: str = SchemaHelper.get_type(xs_attribute)
        self._use: str = LxmlElement.get_use(xs_attribute)
        self._fixed: str = xs_attribute.get("fixed")
        self._default: str = xs_attribute.get("default")
        self._annotation:str = LxmlElement.get_element_text(xs_attribute)
        self._is_global: bool = False
        self._enumerator: Union[SchemaEnumerator, None] = self.find_enumerations()



    def get_use(self) -> str:
        """The xs:attribute use (optional or required)

        Returns:
            Returns either 'required' or 'optional'

        """
        return self._use

    def assign_referenced_attribute(self, reference: Element):
        """Assign the actual referenced attribute and update members.

        Args:
            reference: The reference to the attribute ``xs:attribute`` definition

        """

        self._xs_attribute = reference
        self._enumerator = self.find_enumerations()

    def get_fixed(self) -> str:
        """The fixed value of the xs:attribute

        Returns:
            Returns the fixed value of the attribute or an empty string if None

        """
        return "" if self._fixed is None else self._fixed

    def get_default(self) -> str:
        """The default value of the xs:attribute

        Returns:
            Returns the default value of the attribute or an empty string if None

        """
        return "" if self._default is None else self._default

    def get_name(self) -> str:
        """The name of the xs:attribute

        Returns:
            The name of the attribute

        """
        return self._name

    def get_type(self) -> str:
        """The type of the xs:attribute

        Returns:
            The attribute type

        """
        return self._type

    def get_prefix(self) -> str:
        """The prefix of the xs:attribute

        Returns:
            The namespace prefix

        """
        return self._ns_prefix

    def get_description(self) -> str:
        """The annotation string of the xs:attribute

        Returns:
            The attribute description text

        """
        return self._annotation

    def put_description(self, text: str):
        """Set the xs:attribute documentation string

        Returns:
            None

        """
        self._annotation = text



    def put_use(self, use: str):
        """Set the xs:attribute use string

        Returns:
            None

        """
        self._use = use

    def put_type(self, type: str):
        """Set the xs:attribute type string

        Returns:
            None

        """
        self._type = type

    def put_name(self, name: str):
        """Set the xs:attribute name

        Returns:
            None

        """
        self._name = name


    def attributes_to_dict(self) -> Dict:
        """A dictionary of the OcxAttribute values

        Returns:
            table: A dictionary of all ``OcxAttribute`` attribute values with columns:

            .. list-table:: Heading titles
               :widths: 25 25 25 25 25 50

               * - Attribute
                 - Type
                 - Use
                 - Default
                 - Fixed
                 - Description

        """
        return {
            "Attribute": self.get_name(),
            "Type": self.get_type(),
            "Use": self.get_use(),
            "Default": self.get_default(),
            "Fixed": self.get_fixed(),
            "Description": self.get_description(),
        }

    def is_enumerator(self):
        """True if the attribute is an enumeration, False otherwise."""
        return len(LxmlElement.find_all_children_with_name(self._xs_attribute, 'enumeration')) > 0

    def find_enumerations(self) -> Union[SchemaEnumerator, None]:
        """Find any enumeration values."""
        enum = None
        if self.is_enumerator():
            prefix = self._ns_prefix
            enum = SchemaEnumerator(name=self.get_name(), prefix=prefix)
            values = []
            descriptions = []
            for e in LxmlElement.iter(self._xs_attribute, '{*}enumeration'):
                values.append(e.get('value'))
                descriptions.append(LxmlElement.get_element_text(e))
            enum.values = values
            enum.descriptions = descriptions
        return enum

    def get_enumerations(self) -> SchemaEnumerator:
        """Return the enumerator data class."""
        return self._enumerator


class OcxChildElement:
    """Class capturing the OCX xsd schema definition of a child or sub element ``xs:element``.

    Args:
        xs_element: The lxml.etree.Element class

    Attributes:
        _tag: The unique tag of th schema element
        _element: The ``xs:element`` instance
        _name : The attribute name
        _type : The attribute type
        _use : Whether the child is optional or required
        _cardinality : The cardinality of the element
        _annotation: The element description
        _is_choice: The child element is a ``xs:choice``

    """

    def __init__(self, xs_element: Element, unique_tag: str):
        # Private
        self._element: Element = xs_element
        self._tag:str  = unique_tag
        self._name:str  = LxmlElement.get_name(xs_element)
        self._type:str  = SchemaHelper.get_type(xs_element)
        self._cardinality = LxmlElement.cardinality(xs_element)
        self._annotation: str = LxmlElement.get_element_text(xs_element)
        self._is_choice: bool = LxmlElement.is_choice(xs_element)

    def get_use(self) -> str:
        """Mandatory or optional sub element

        Returns:
            The element use, either ``req.`` or ``opt.``

        """
        lower, upper = self._cardinality
        if lower == 0:
            return "opt."
        else:
            return "req."

    def get_cardinality(self) -> str:
        """Get the cardinality of the ``OcxChildElement``

        Returns:
            The cardinality as sting represented by ``[lower, upper]``

        """
        lower, upper = self._cardinality
        if upper == "unbounded":
            upper = "\u221E"  # UTF-8 Infinity symbol
        return f"[{lower}, {upper}]"

    def get_name(self) -> str:
        """The name of the xs:attribute

        Returns:
            The name of the attribute

        """
        return self._name

    def get_type(self) -> str:
        """The type of the xs:attribute

        Returns:
            The attribute type

        """
        return self._type

    def get_description(self) -> str:
        """The annotation text of the element

        Returns:
            The description of the element

        """
        return self._annotation

    def put_description(self, text: str):
        """Set the xs:attribute documentation string

        Returns:
            None

        """
        self._annotation = text

    def put_use(self, use: str):
        """Set the xs:attribute use string

        Returns:
            None

        """
        self._use = use

    def put_choice(self, choice: bool):
        """Set the xs:element choice

        Returns:
            None

        """
        self._is_choice = choice


    def put_reference(self, tag: str):
        """Set the tag reference to the global schema element

        Returns:
            None

        """
        self._tag = tag

    def put_cardinality(self, element: Element):
        """Override the cardinality for a substitution group member

        Args:
            element: the etree.Element node

        """
        self._cardinality = LxmlElement.cardinality(element)

    def is_mandatory(self) -> bool:
        """Whether the element mandatory or not

        Returns:
            True if the element is mandatory, False otherwise

        """
        lower, upper = self._cardinality
        return lower != 0

    def is_choice(self) -> bool:
        """Whether the element is a choice or not

        Returns:
            True if the element is a choice, False otherwise

        """
        return self._is_choice

    def is_global(self) -> bool:
        """Whether the element is a global schema element

        Returns:
            True if the element is global, False otherwise

        """
        return self._tag != ""

    def put_type(self, type: str):
        """Set the xs:attribute type string

        Returns:
            None

        """
        self._type = type

    def put_name(self, name: str):
        """Set the xs:attribute name

        Returns:
            None

        """
        self._name = name

    def attributes_to_dict(self) -> Dict:
        """A dictionary of the ''OcxChildElement'' values

        Returns:
            table: dictionary of all OcxAttribute attribute values with columns:

            .. list-table:: Heading titles
               :widths: 25 25 25 25 50

               * - Child
                 - Cardinality
                 - Choice
                 - Global
                 - Description

        """
        return {
            "Child": self.get_name(),
            "Type": self.get_type(),
            "Use": self.get_use(),
            "Cardinality": self.get_cardinality(),
            "Choice": self.is_choice(),
            "Global": self.is_global(),
            "Description": self.get_description(),
        }


class OcxGlobalElement:
    """Global schema element class capturing the xsd schema definition of a global ``xs:element``.

    Args:
        xsd_element: The lxml.etree.Element class
        logger: The main python logger

    Attributes:
        log: The Python logger instance
        _element: The ``lxml.Element`` instance
        _attributes: The attributes of the global element including the attributes of all schema supertypes
        _reference: The ``OcxGlobalElement`` hase reference to a global schema element. 'None' if no reference
        _tag: The unique global tag of the ``OcXGlobalElement``
        _parents: Hash table of references to all parent schema types with tag as key
        _children: List of references to all children schema types with tag as key.
                        Includes also children of all super-types.
        -assertions: List of any assertions associated with the ``xs:element``

    """

    def __init__(self, xsd_element: Element, unique_tag: str, namespaces: Dict):
        # Private
        self._element: Element = xsd_element
        self._attributes: List = []
        self._namespace:str  = QName(unique_tag).namespace
        self._tag:str  = unique_tag
        self._cardinality: str = LxmlElement.cardinality(xsd_element)
        self._children: List = []
        self._parents: Dict = {}
        self._assertions: List = []
        self._namespaces: Dict = namespaces

    def add_attribute(self, attribute: OcxAttribute):
        """Add attributes to the global element

        Arguments:
            attribute : The ``OcxAttribute`` instance to be added

        """
        self._attributes.append(attribute)

    def add_child(self, child: OcxChildElement):
        """Add a child of an OCX global element'

        Arguments:
            child: The added  child instance of a ``OcxChildElement`` class

        Returns:
            Nothing

        """
        self._children.append(child)

    def add_assertion(self, test: str):
        """Add an assertion test associated to me'

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

    def put_child(self, tag: str, child: OcxChildElement):
        """Add a child element of type ``OCxChildElement``

        Arguments:
            tag: The unique tag of the parent element
            child: The child xsd schema element

        Returns:
            None

        """
        self._children[tag] = child

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
        prefix =''
        try:
            index = nstags.index(self._namespace)
            prefix =  nsprefix[index]
            if prefix is None:
                nstags.pop(index)
                nsprefix.pop(index)
                index = nstags.index(self._namespace)
                prefix = nsprefix.index(index)
        except ValueError as e:
            logger.error(f'{self._namespace} is not in the namespace list')
        if prefix == '':
            logger.debug(f'Empty namespace prefix in global elem,ent {self.get_name()}')
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

    def get_reference(self) -> str:
        """Get the reference to a global element

        Returns:
            tag: The unique tag to the global referenced element

        """
        return self._reference

    def put_reference(self, tag):
        """Assign the reference to a global element

        Returns:
            tag: The unique tag to the global referenced element

        """
        self._reference = tag

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
           table: A dictionary of property values with heading keys:

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
            attributes = attr.attributes_to_dict()
            for a in attributes:
                table[a].append(attributes[a])
        return table

    def children_to_dict(self) -> Dict:
        """A dictionary of all ``OcxGlobalElement`` children values

        Returns:
            table: A dictionary of attribute values with heading keys:

            .. list-table:: Heading keys
               :widths: 25 25 25 25 50

               * - Child
                 - Type
                 - Use
                 - Cardinality
                 - Description

        """
        table = defaultdict(list)
        for child in sorted(self._children, key=lambda x: x.get_name()):
            attributes = child.attributes_to_dict()
            for a in attributes:
                table[a].append(attributes[a])
        return table
