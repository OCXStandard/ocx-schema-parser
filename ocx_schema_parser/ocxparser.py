#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""ocxparser module."""
from collections import defaultdict
from typing import Any, DefaultDict, Dict, Iterator, List, Tuple, Union

import lxml

# Third party imports
from loguru import logger
from lxml.etree import Element, QName

# Application imports
from ocx_schema_parser import (
    W3C_SCHEMA_BUILT_IN_TYPES,
)
from ocx_schema_parser.helpers import SchemaHelper
from ocx_schema_parser.xparse import LxmlElement, LxmlParser


class OcxParser:
    """
    The OcxSchema provides functionality for parsing the OCX xsd schema and storing all the elements.

    Args:

    Attributes:
        _schema_namespaces: All namespaces on the form (prefix, namespace) key-value pairs resulting from
            parsing all schema files, `W3C <https://www.w3.org/TR/xml-names/#sec-namespaces>`_.
        _is_parsed: True if a schema has been parsed, False otherwise
        _schema_version: The version of the parsed schema
       _schema_changes: A list of all schema changes described by the tag SchemaChange contained in the xsd file.
        _schema_types: The list of xsd types to be parsed. Only these types will be stored.
        _substitution_groups: Collection of all substitution groups with its members.
        _schema_enumerators: All schema enumerators
        _builtin_xs_types: W3C primitive data types.
            `www.w3.org <https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes>`_. Defined in ``config.yaml``
        _schema_ns: The schema target ns with the schema version as key

    """

    def __init__(self):
        # Default namespace map for the reserved prefix xml. See https://www.w3.org/TR/xml-names/#sec-namespaces
        self._schema_namespaces: Dict = {"xml": "http://www.w3.org/XML/1998/namespace"}
        self._target_ns: str = ""
        self._is_parsed: bool = False
        self._root: lxml.etree.Element = None
        self._all_schema_elements: Dict = (
            {}
        )  # Hash table with tag as key schema_elements[tag] = lxml.etree.Element
        self._all_types: DefaultDict[List] = defaultdict(
            list
        )  # Hash table with tag as key: all_types[tag] = lxml.etree.Element
        self._schema_types: List = []
        self._schema_version: Any[str, None] = None
        self._schema_changes: DefaultDict[List] = defaultdict(list)
        self._substitution_groups: DefaultDict[List] = defaultdict(list)
        # w3c primitive data types ref https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes
        self._builtin_xs_types: Dict = W3C_SCHEMA_BUILT_IN_TYPES
        self._schema_ns: Dict = (
            {}
        )  # Store the schema target ns with the schema version as key
        self._schema_enumerators: Dict = {}
        self._simple_types: List = []

    def process_xsd_from_file(self, file: str) -> bool:
        """Process the xsd with file name ``file``.

        Args:
            file: The file name of the xsd.

        Returns:
            True if processed, False otherwise.

        """
        if self._parse_xsd_from_file(file):
            self._create_lookup_tables()
            return True
        return False

    def _set_target_ns(self, target_ns) -> None:
        """

        Args:
            target_ns: the target name space of the parsed schema

        """
        self._target_ns = target_ns

    def get_target_namespace(self) -> str:
        """Return the target namespcae of the parsed schema.

        Returns:
            The target namespace.

        """
        return self._target_ns

    def get_lookup_table(self) -> Dict:
        """Return the lookup table of parsed schema types.

        Returns:
            The lookup table.

        """
        return self._all_schema_elements

    def element_iterator(self) -> Iterator:
        """Iterator of the parsed schem elements.

        Returns:
            Element iterator

        """
        yield iter(self._all_schema_elements)

    def get_prefix_from_namespace(self, namespace: str) -> str:
        """Find the namespace prefix.

        Returns:
            The namespace prefix

        """
        nsprefix = list(iter(self._schema_namespaces))
        nstags = list(iter(self._schema_namespaces.values()))
        prefix = ""
        try:
            index = nstags.index(namespace)
            prefix = nsprefix[index]
            if prefix is None:
                nstags.pop(index)
                nsprefix.pop(index)
                index = nstags.index(namespace)
                prefix = nsprefix.index(index)
        except ValueError as e:
            logger.error(f"{namespace} is not in the namespace list: {e}")
        return prefix

    def _add_namespace(self, namespace: Dict) -> int:
        """Add new namespaces to the global namespace dict

        Returns:
            The number of new namespaces added

        """
        ns_size = len(self._schema_namespaces)
        # Check if any keys exists
        for prefix in self._schema_namespaces:
            if prefix in namespace:
                logger.debug(
                    f'The _namespace prefix "{prefix}" already exists. '
                    f"Dropping new _namespace {namespace[prefix]} from the _namespace table"
                )
                logger.debug(
                    f'The existing namespace with prefix "{prefix}" is: {self._schema_namespaces[prefix]}'
                )
                del namespace[prefix]
        self._schema_namespaces = {**self._schema_namespaces, **namespace}
        return len(self._schema_namespaces) - ns_size

    def _parse_xsd_from_file(self, file: str) -> bool:
        """Parse an xsd schema file with name ``file``.

        Args:
            file: the path to the xsd file.

        Returns:
            True if parsed successfully, false otherwise

        """
        parser = LxmlParser()
        if result := parser.parse(file):
            num_ns = self._add_namespace(parser.get_namespaces())
            logger.debug(f'Added {num_ns} new namespaces for schema "{file}"')
            target_ns = parser.get_target_namespace()
            if target_ns not in self._schema_namespaces.values():
                logger.error(
                    f'The target _namespace "{target_ns}" is not registered in '
                    f"the _namespace listing {self._schema_namespaces}"
                )
                return False
            self._set_target_ns(target_ns)
            self._root = parser.get_root()
            # Retrieve the OCX schema version
            version = SchemaHelper.get_schema_version(self._root)
            if version != "Missing":
                self._schema_version = version
                self._schema_ns[version] = target_ns
        return result

    def _create_lookup_tables(self) -> None:
        """Create the global lookup tables of Schema data classes with the tag as key."""

        root = self._root
        # Add all global elements
        type = "element"
        self._schema_types.append(type)
        for e in LxmlElement.find_all_children_with_name_and_attribute(
            root, type, "name"
        ):
            self._add_element_to_lookup_table(e, self.get_target_namespace())
        # Add all complex elements
        type = "complexType"
        self._schema_types.append(type)
        for e in LxmlElement.find_all_children_with_name_and_attribute(
            root, type, "name"
        ):
            self._add_element_to_lookup_table(e, self.get_target_namespace())
        # Add all simple types
        type = "simpleType"
        self._schema_types.append(type)
        for e in LxmlElement.find_all_children_with_name_and_attribute(
            root, type, "name"
        ):
            self._add_element_to_lookup_table(e, self.get_target_namespace())
        # Add all attributeGroups
        type = "attributeGroup"
        self._schema_types.append(type)
        for e in LxmlElement.find_all_children_with_name_and_attribute(
            root, type, "name"
        ):
            self._add_element_to_lookup_table(e, self.get_target_namespace())
        # Add all global attributes (these are refs)
        glob_attr = LxmlElement.find_all_children_with_name_and_attribute(
            root, "attribute", "ref"
        )
        names = {LxmlElement.get_name(a) for a in glob_attr}
        for name in names:
            element = LxmlElement.find_all_children_with_attribute_value(
                root, "attribute", "name", name
            )
            if len(element) == 1:
                self._add_element_to_lookup_table(
                    element[0], self.get_target_namespace()
                )

    def _add_element_to_lookup_table(self, element: Element, target_ns) -> None:
        """Add a schema element to the lookup table.

        Arguments:
            element: The schema element to be added.
            target_ns: The target namespace of the element

        """
        name = LxmlElement.get_name(element)
        if name is not None:
            # add the schema type
            tag = SchemaHelper.unique_tag(name, target_ns)
            schema_type = LxmlElement.get_localname(element)
            self._add_schema_element(tag, element)
            if LxmlElement.is_enumeration(element) and schema_type in [
                "attribute",
                "attributeGroup",
            ]:
                self._add_schema_type("enumeration", tag)
            else:
                self._add_schema_type(schema_type, tag)
            # Add to substitution group if any
            if LxmlElement.is_substitution_group(element):
                group = LxmlElement.get_substitution_group(element)
                self._add_member_to_substitution_group(
                    group,
                    SchemaHelper.unique_tag(LxmlElement.get_name(element), target_ns),
                )

    def _add_schema_element(self, tag: str, element: Element):
        """Add a new schema element to the hash table.

        Args:
            tag: The hash key
            element: The schema ``Element`` to add

        """
        self._all_schema_elements[tag] = element

    def _add_schema_type(self, schema_type: str, tag: str):
        """Add a new schema type to the hash table.

        Args:
            tag: The hash key
            schema_type: The schema type

        """
        self._all_types[schema_type].append(tag)

    def _add_member_to_substitution_group(self, group: str, element: Element):
        """Add an ``xs:element`` to a substitution group collection.

        Args:
            group: The name of the substitution group
            element: The global OCX element to add

        """
        self._substitution_groups[group].append(element)

    def _get_schema_types(self, schema_type: str) -> List[str]:
        """Internal function to retrieve a list of tags of ``lxml.etree.Element`` schema elements of a specific type.

        Returns:
            The sorted list of all tags of ``lxml.etree.Element`` of type ``schema_type``

        """
        elements = list(self._all_types[schema_type])
        return sorted(elements)

    def get_schema_version(self) -> str:
        """The OCX schema version.

        Returns:
            The coded version string of the OCX schema

        """
        return self._schema_version

    def get_namespaces(self) -> Dict:
        """The parsed namespaces.

        Returns:
            The dict of namespaces as (namespace,prefix) key-value pairs

        """
        return self._schema_namespaces

    def get_schema_namespace(self, version: str) -> str:
        """The schema namespace of the schema with ``version``.

        Returns:
            The target namespace

        """
        ns = self._schema_ns.get(version)
        return "Missing" if ns is None else ns

    def get_xs_types(self) -> Dict:
        """All builtin xs types.

        Returns:
            The list of all defined xs types

        """
        return self._builtin_xs_types

    def get_schema_element_types(self) -> List:
        """All schema elements of type ``element``.

        Returns:
            The list of all etree.Element of type ``element``

        """
        return self._get_schema_types("element")

    def get_schema_complex_types(self) -> List[str]:
        """All tags for schema elements of type ``complexType``.

        Returns:
            The list of tags of all ``etree.Element`` of type ``complexType``

        """
        return self._get_schema_types("complexType")

    def get_schema_simple_types(self) -> List[str]:
        """All schema elements of type ``simpleType``.

        Returns:
            The list of tags of all etree.Element of type ``simpleType``

        """
        return self._get_schema_types("simpleType")

    def get_schema_enumerations(self) -> List[str]:
        """All schema elements of type ``enumeration``.

        Returns:
            The list of tags of all etree.Element of type ``enumeration``

        """
        return self._get_schema_types("enumeration")

    def get_schema_attribute_types(self) -> List[str]:
        """All schema elements of type ``attribute``.

        Returns:
            The list of unique tags for all etree.Element of type ``attribute``

        """

        return self._get_schema_types("attribute")

    def get_schema_attribute_group_types(self) -> List[str]:
        """All schema elements of type ``attributeGroup``.

        Returns:
            The list of all etree.Element of type ``attributeGroup``

        """
        return self._get_schema_types("attributeGroup")

    def get_substitution_groups(self) -> Dict:
        """The collection of the schema  ``substitutionGroup``.

        Returns:
            Substitution groups with members

        """
        return self._substitution_groups

    def get_element_from_tag(self, tag: str) -> Union[Element, None]:
        """Return get the ``etree.Element`` with the key ``tag``.

        Returns:
            The schema element instance

        """
        if tag in self._builtin_xs_types:
            logger.debug(
                f"{__class__}: The tag {tag} is a built-in type {self._builtin_xs_types[tag]}"
            )
            return None
        if tag not in self._all_schema_elements.keys():
            logger.debug(f"{__class__}: The tag {tag} is not in the look-up table")
            return None
        return self._all_schema_elements.get(tag)

    def get_element_from_type(self, schema_type: str) -> Tuple[Any, Any]:
        """Retrieve the schema element ``etree.Element`` with the key ``schema_type``.

        Args:
            schema_type: The schema type to retrive on the form ``ns_prefix:name``

        Returns:
            A tuple of the element unique tag and the element (tag, Element)

        """
        name = LxmlElement.strip_namespace_prefix(schema_type)
        if LxmlElement.namespace_prefix(schema_type) in self._schema_namespaces:
            namespace = self._schema_namespaces[
                LxmlElement.namespace_prefix(schema_type)
            ]
        else:
            logger.debug(f"The type {schema_type} has an unknown _namespace prefix")
            return None, None
        tag = SchemaHelper.unique_tag(name, namespace)
        if tag in self._builtin_xs_types:
            logger.debug(
                f"The tag {tag} is a built-in type {self._builtin_xs_types[tag]}"
            )
            return None, None
        if tag in self._all_schema_elements:
            return tag, self.get_element_from_tag(tag)
        logger.debug(f"{__class__}: The tag {tag} is not in the look-up table")
        return None, None

    def tbl_summary(self, short: bool = True) -> Dict:
        """The summary of the parsed schema and any referenced schemas.

        Arguments:
            short: If true, only report number of schema types, otherwise report names of types.

        Returns:
            The schema summary content dataclasses

        """
        summary = {}
        for prefix, namespace in self._schema_namespaces.items():
            content = {"Version": [self.get_schema_version()], "Prefix": [prefix]}
            for type in self._all_types:
                items = list(
                    filter(
                        lambda x: QName(x).namespace == namespace, self._all_types[type]
                    )
                )
                if short:
                    content[type] = [
                        len(list(map(lambda name: QName(name).localname, items)))
                    ]
                else:
                    content[type] = list(map(lambda name: QName(name).localname, items))
            summary[namespace] = content
        return summary

    def tbl_attribute_groups(self) -> Dict:
        """All parsed ``attributeGroup`` types in the schema and any referenced schemas.

        Returns:
             List of  ``SchemaType`` data class holding ``attributeGroup`` attributes.

        """

        elements = self.get_schema_attribute_group_types()
        return {QName(tag).localname: tag for tag in elements}

    def tbl_simple_types(self) -> Dict:
        """The table of all parsed ``simpleType`` elements in the schema and any referenced schemas.

        Returns:
            The ``SchemaType`` data class attributes of ``simpleType``

        """

        elements = self.get_schema_simple_types()
        return {QName(tag).localname: tag for tag in elements}

    def tbl_enumerators(self) -> Dict:
        """The table of all parsed ``enumerator`` elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``simpleType``

        """

        elements = self.get_schema_simple_types()
        return {QName(tag).localname: tag for tag in elements}

    def tbl_attribute_types(self) -> Dict:
        """The table of all parsed attribute elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``attributeType``

        """

        elements = self.get_schema_attribute_types()
        return {QName(tag).localname: tag for tag in elements}

    def tbl_element_types(self) -> Dict:
        """The table of all parsed elements of type element in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``element``

        """

        elements = self.get_schema_element_types()
        return {QName(tag).localname: tag for tag in elements}

    def tbl_complex_types(self) -> Dict:
        """The table of all parsed complexType elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``complexType``

        """

        elements = self.get_schema_complex_types()
        return {QName(tag).localname: tag for tag in elements}
