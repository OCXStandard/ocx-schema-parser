#  Copyright (c) 2022-2023. OCX Consortium https://3docx.org. See the LICENSE

# Sys imports
import re
from typing import Any, Dict, List, Union

# Third party imports
from loguru import logger
from lxml import etree
from lxml.etree import Element, ElementTextIterator, QName


class LxmlElement:
    """A wrapper class for the lxml etree.Element class main functions."""

    @staticmethod
    def items(element: Element) -> List:
        """Gets element attributes, as a sequence. The attributes are returned in an arbitrary order.

        Args:
            element: The current etree.Element node

        Returns:
            A List of all attributes of ``element``

        """
        return element.items()

    @staticmethod
    def get_root(element: Element) -> Element:
        """Return Element root node of the document that contains this element.

        Args:
            element: The current etree.Element node

        Returns:
            The root Element node of the document for this element

        """
        et = element.getroottree()
        return et.getroot()

    @staticmethod
    def get_base(element: Element) -> str:
        """The base URI of the document holding the Element (the location of the document)

        Args:
            element: The current etree.Element node

        Returns:
            The base URI of the document or empty string if unknown

        """
        base = element.base
        if base is None:
            return ""
        else:
            return base

    @staticmethod
    def get_source_line(element: Element) -> int:
        """Original line number as found by the parser or None if unknown.

        Args:
            element: The current etree.Element node

        Returns:
            The line number of the ``element`` in the source

        """
        return element.sourceline

    @staticmethod
    def get_parent(element: Element) -> Element:
        """Returns the parent of this element or None for the root element.

        Args:
            element: The current ``etree.Element`` node

        Returns:
            The parent Element node of the document for this element or none if ``element`` is the root

        """
        return element.getparent()

    @staticmethod
    def get_children(element: Element) -> List[Element]:
        """Returns all direct children of the xml element

        Args:
            element: The XML parent node

        Returns:
            A List of all children of 'element' excluding the parent itself.

        """
        return element.findall(".//")

    @staticmethod
    def get_xml_attrib(element: Element) -> Dict:
        """The XML attributes of an element

        Args:
            element: The XML parent node

        Returns:
            A dictionary of ``(key,value)`` pairs of the element attributes

        """
        return element.attrib

    @staticmethod
    def get_localname(element: Element) -> str:
        """The local name (type) of an XML element

        Args:
            element: The XML parent node

        Returns:
            The element local name

        """
        qn = QName(element)
        return qn.localname

    @classmethod
    def unique_tag(cls, element: Element) -> Any:
        """The unique tag of an XML element: ``{namespace}name``

        Args:
            element: The XML parent node

        Returns:
            The element unique tag

        """
        name = element.get("name")
        ns = cls.get_namespace(element)
        return f"{LxmlElement.namespaces_decorate(ns)}{name}"

    @staticmethod
    def get_name(element: Element) -> Any:
        """The name of an XML element defined by the attribute ``name``

        Args:
            element: The XML parent node

        Returns:
            The element local name or None if no name

        """
        name = element.get("name")
        if name is None:
            name = LxmlElement.strip_namespace_prefix(element.get("ref"))
        return name

    @staticmethod
    def get_use(element: Element) -> Any:
        """Whether XML element is required or optional given by the attribute value ``use``

        Args:
            element: The XML parent node

        Returns:

            The element use as a string, either ``required`` or ``optional``

        """
        use = element.get("use")
        if use is None:
            return "opt."
        if use == "required":
            use = "req."
        return use

    @staticmethod
    def get_reference(element: Element) -> Any:
        """The referenced XML element defined by the attribute ``ref``

        Args:
            element: The XML parent node

        Returns:

            The referenced element including namespace prefix if any. None if there is no reference

        """
        return element.get("ref")

    @staticmethod
    def is_enumeration(element: Element) -> bool:
        """Whether the attribute is an enumeration or not

        Args:
            element: The XML parent node

        Returns:

            true if the attribute is an enumeratos, false otherwise

        """
        return LxmlElement.has_child_with_name(element, "enumeration")

    @staticmethod
    def is_reference(element: Element) -> bool:
        """Whether the element is a reference or not

        Args:
            element: The XML parent node

        Returns:

            true if the element is a reference, false otherwise

        """
        return element.get("use") is not None

    @staticmethod
    def is_mandatory(element: Element) -> bool:
        """The element use. True if required, False otherwise

        Args:
            element: The element node

        Returns:

            True if the element is mandatory, false otherwise

        """
        lower, upper = LxmlElement.cardinality(element)
        if lower == 0:
            return False
        else:
            return True

    @classmethod
    def cardinality_string(cls, element) -> str:
        """Return the element cardinality formatted string."""
        lower, upper = cls.cardinality(element)
        if upper == "unbounded":
            upper = "\u221E"  # UTF-8 Infinity symbol
        return f"[{lower}, {upper}]"

    @staticmethod
    def cardinality(element) -> tuple:
        """Establish the cardinality of the ``Element``

        Args:
            element: the ``etree.Element`` instance

        Returns:

            The tuple of the element lower and upper bounds (lower, upper)

        """

        attributes = LxmlElement.get_xml_attrib(element)
        if "minOccurs" in attributes:
            lower = int(attributes["minOccurs"])
        else:
            use = attributes.get("use")
            if use is not None:
                if use == "req" or use == "required":
                    lower = 1
                else:
                    lower = 0
            else:
                lower = 1
        if "maxOccurs" in attributes:
            upper = attributes["maxOccurs"]
        else:
            upper = 1
        # Find the closest xs:sequence or xs:choice ancestor which overrules mandatory use
        for item in element.iterancestors("{*}sequence", "{*}choice"):
            attributes = item.attrib
            if "minOccurs" in attributes:
                lower = int(attributes["minOccurs"])
            if "maxOccurs" in attributes:
                upper = attributes["maxOccurs"]
            break
        return lower, upper

    @staticmethod
    def is_choice(element) -> bool:
        """Return True if the element ancestor is an xs:choice, False otherwise

        Args:
            element: the etree.Element instance

        Returns:

            True if the element node is a choice, false otherwise

        """
        choice = False
        # Find the closest sequence or choice ancestor which overrules mandatory use
        for item in element.iterancestors("{*}sequence", "{*}choice"):
            qn = QName(item)
            if qn.localname == "choice":
                choice = True
            break
        return choice

    @staticmethod
    def is_substitution_group(element) -> bool:
        """Return True if the element is a substitution

        Args:
            element: the etree.Element instance

        Returns:

            True if the element is a  substitutionGroup, false otherwise

        """
        attributes = LxmlElement.get_xml_attrib(element)
        if "substitutionGroup" in attributes:
            return True
        else:
            return False

    @staticmethod
    def is_abstract(element) -> bool:
        """Return True if the element is abstract

        Args:
            element: the ``etree.Element`` instance

        Returns:

            True if the element abstract, false otherwise

        """
        attributes = LxmlElement.get_xml_attrib(element)
        if "abstract" in attributes:
            return True
        else:
            return False

    @staticmethod
    def get_substitution_group(element: Element) -> str:
        """Return the name of the element's substitutionGroup

        Args:
            element: the ``etree.Element`` instance

        Returns:
            name of substitutionGroup, None if no substitutionGroup

        """
        attributes = LxmlElement.get_xml_attrib(element)
        return attributes.get("substitutionGroup")

    @staticmethod
    def get_restriction(element: Element) -> str:
        """Return the element restriction

        Args:
            element: the ``etree.Element`` instance

        Returns:
            restriction type

        """
        restriction = ""
        for item in LxmlElement.iter(element, "{*}restriction"):
            restriction = item.get("base")
        return restriction

    @staticmethod
    def get_element_text(element: Element) -> str:
        """The text between the element's start and end tags without any tail text.

        Args:
            element: the etree.Element instance

        Returns:

            The element text stripped of any special characters

        """
        text = ""
        description = ""
        for text in ElementTextIterator(element, with_tail=False):
            description = description + text
            break
        text = re.sub("[\n\t\r]", "", description)  # Strip off special characters
        return text

    @staticmethod
    def get_namespace(element: Element) -> str:
        """The namespace of an XML element

        Args:
            element: The XML parent node

        Returns:

            The element namespace

        """
        qn = QName(element)
        return qn.namespace

    @staticmethod
    def iter(element: Element, tag=None, *tags) -> etree.ElementDepthFirstIterator:
        """Iterate over all elements in the subtree in document order (depth first pre-order),
            starting with this element.

            Can be restricted to find only elements with specific tags: pass ``{ns}localname`` as tag.
            Either or both of ns and localname can be * for a wildcard; ns can be empty for no namespace.
            ``localname`` is equivalent to ``{}localname`` (i.e. no namespace)
            but ``*`` is ``{*}*`` (any or no namespace), not ``{}*``.

            Passing multiple tags (or a sequence of tags) instead of a single tag
            will let the iterator return all elements matching any of these tags, in document order.

        Args:
            element: The etree.Element node to search from
            tag: The name of the child
        Returns:
            An iterator filtered by tags if specified.

        Example:
            .. highlight:: python
            .. code-block:: python

                for type in LxmlElement.iter(root, {*}complexType)
                    print(type.tag)

            will iterate over all ``complexType`` tags and print the tag starting from the document root .

        """
        return element.iter(tag, *tags)

    @staticmethod
    def find_all_children_with_name(
        element: Element, child_name: str, namespace: str = "*"
    ) -> List:
        """Find all the XML element's children with  name ``child_name``

        Args:
            element: The XML parent node to search from
            child_name: The name of the child
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:

            A list of elements. Empty list if no children can be found

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}{child_name}"
        return element.findall(xpath)

    @staticmethod
    def find_child_with_name(
        element: Element, child_name: str, namespace: str = "*"
    ) -> Element:
        """Find the first direct child of the XML element's children with  name ``child_name``

        Args:
            element: The XML parent node to search from
            child_name: The name of the child
            namespace: The search namespace. Default is the wildcard '*' matching any namespace

        Returns:
            The child element as etree.Element. None if no child can be found

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}{child_name}"
        return element.find(xpath)

    @staticmethod
    def find_attributes(element: Element, namespace: str = "*") -> List[Element]:
        """Find all sub elements of type xs:attribute

        Args:
            element: The XML parent node to search from
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:

            The list of the xs:attribute type found

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}attribute"
        return element.findall(xpath)

    @staticmethod
    def find_attribute_groups(element: Element, namespace: str = "*") -> List[Element]:
        """Find all sub elements of type ``xs:attributeGroup``

        Args:
            element: The XML parent node to search from
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:
            Attribute groups

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}attributeGroup"
        return element.findall(xpath)

    @staticmethod
    def has_child_with_name(
        element: Element, child_name: str, namespace: str = "*"
    ) -> bool:
        """Check if the element has a child with  name 'child_name'

        Args:
            element: The XML parent node to search from
            child_name: The name of the child
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:
            True if the element has a child with name ``child_name`` False otherwise

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}{child_name}"
        return len(element.findall(xpath)) > 0

    @staticmethod
    def find_all_children_with_attribute_value(
        element: Element,
        name: str,
        attrib_name: str,
        attrib_value: str,
        namespace: str = "*",
    ) -> List:
        """Find all the XML elements with the attribute name 'attrib_name' having a given value  'attrib_value'

        Args:
            element: The XML parent node to search from
            name: The name of the element with attrib_name and attrib_value
            attrib_name: The name of the attribute
            attrib_value: The value of the attribute
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:
            All children having attributes with name ``attrib_name`` and value ``attrib_value``.
            Empty list if no children can be found

        """
        xpath = f'.//{LxmlElement.namespaces_decorate(namespace)}{name}[@{attrib_name}="{attrib_value}"]'
        return element.findall(xpath)

    @staticmethod
    def find_all_children_with_name_and_attribute(
        element: Element, child_name: str, attrib_name: str, namespace: str = "*"
    ) -> List:
        """Find all the XML elements with name ``name`` and attribute name ``attrib_name``

        Args:
            element: The XML parent node to search from
            child_name: The name of the children elements
            attrib_name: The name of the attribute
            namespace: The search namespace. Default is the wildcard matching any namespace


        Returns:
            All elements having attributes with name ``attrib_name``.
            An empty list if no children can be found

        """
        xpath = f".//{LxmlElement.namespaces_decorate(namespace)}{child_name}[@{attrib_name}]"
        return element.findall(xpath)

    @staticmethod
    # Finding the assertion in the code.
    def find_assertion(element: Element, namespace="*") -> Union[str, None]:
        """Find any assertions under the ``element``

        Args:
            element: The XML parent node to search from
            namespace: The search namespace. Default is the wildcard ``*`` matching any namespace

        Returns:
            The assertion test as a string.
            None if no assertion tag is found

        """
        test = None
        # Assertions
        xpath = f'.//{LxmlElement.namespaces_decorate(namespace)}{"assert"}'
        asserts = element.findall(xpath)
        if len(asserts) > 0:
            attrib = asserts[0].attrib
            if "test" in attrib:
                test = attrib["test"]
        return test

    @staticmethod
    def namespace_prefix(element: str) -> Union[str, None]:
        """Returns the namespace prefix of an element if any

        Args:

            element: The element name with or without prefix as a string

        Returns:

            The element prefix string or None if no prefix

        """
        i = element.find(":")
        if not i == -1:
            element = element[0:i]
            return element
        return None

    @staticmethod
    def replace_ns_tag_with_ns_prefix(element: str, namespaces: Dict) -> str:
        """Replace the namespace tag with a mapped namespace prefix.

        Args:

            element: The element name with or without prefix as a string
            namespaces: the namespace tag to prefix mapping

        Returns:

            the element with prefix

        """

        nsprefix = list(iter(namespaces))
        nstags = list(iter(namespaces.values()))
        qn = QName(element)
        prefix = ""
        try:
            index = nstags.index(qn.namespace)
            prefix = nsprefix[index]
            if prefix is None:
                nstags.pop(index)
                nsprefix.pop(index)
                index = nstags.index(qn.namespace)
                prefix = nsprefix.index(index)
        except ValueError as e:
            logger.error(f"{qn.namespace} is not in the namespace list: {e}")
        if prefix == "":
            logger.debug(f"Empty namespace prefix in element {qn.localname}")
        return f"{prefix}:{qn.localname}"

    @staticmethod
    def namespaces_decorate(ns: str) -> str:
        """Decorate a string with curly brackets to form a valid XML namespace

        Args:
            ns: The namespace

        Returns:
            The curly decorated namespace

        """
        return "{" + ns + "}"

    @staticmethod
    def strip_namespace_prefix(element: str) -> str:
        """Returns the element name without the namespace prefix

        Args:
            element: The element name with or without prefix as a string

        Returns:
            The element without namespace prefix

        """
        i = element.find(":")
        if not i == -1:
            element = element[i + 1 : len(element)]
        return element

    @staticmethod
    def strip_namespace_tag(element: str) -> str:
        """Returns the element name without the namespace tag

        Args:
            element: The element name with or without namespace as a string

        Returns:
            The element without namespace tag

        """
        i = element.find("}")
        if not i == -1:
            element = element[i + 1 : len(element)]
        return element
