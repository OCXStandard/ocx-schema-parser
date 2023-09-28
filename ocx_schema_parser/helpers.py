#  Copyright (c) 2022-2023. OCX Consortium https://3docx.org. See the LICENSE

import re
from dataclasses import asdict
from typing import Dict, List, Union

from lxml.etree import Element, ElementTextIterator

from .data_classes import SchemaChange
from .xelement import LxmlElement


class SchemaHelper:
    """A utility class for retrieving OCX attributes and information from an OCX xsd element"""

    @classmethod
    def is_reference(cls, element: Element) -> bool:
        """Is a reference or not

        Returns:
            True if the element is a reference, False otherwise

        """
        reference = cls.get_reference(element) != "None"
        return reference

    @classmethod
    def get_reference(cls, element: Element) -> Union[str, None]:
        """The element reference

        Returns:
            The reference to a global element on the form ``prefix:name``.
            Returns None if the element is not a reference.

        """
        attributes = LxmlElement.get_xml_attrib(element)
        ref = attributes.get("ref")
        if ref is None:
            ref = "None"
        return ref

    @staticmethod
    def get_type(element: Element) -> str:  # ToDo: Simplify function
        """The element type given by the element attribute or by its ``complexContent``

        Returns:
            The global element type on the form ``prefix:name``.
            If the element has no type, ``untyped`` is returned.

        """
        schema_type = None
        attributes = LxmlElement.get_xml_attrib(element)
        if "type" in attributes:
            schema_type = attributes["type"]
        if "base" in attributes:
            schema_type = attributes["base"]
        if "ref" in attributes:
            schema_type = attributes["ref"]
        # The element may have complexContent
        if len(LxmlElement.find_all_children_with_name(element, "complexContent")) > 0:
            # complexContent has either an extension or a restriction
            # extension
            base = LxmlElement.find_all_children_with_name_and_attribute(
                element, "extension", "base"
            )
            if len(base) > 0:
                schema_type = base[0].get("base")
            # restriction
            base = LxmlElement.find_all_children_with_name_and_attribute(
                element, "restriction", "base"
            )
            if len(base) > 0:
                schema_type = base[0].get("base")
        # the element may be a simpleType
        simple_type = LxmlElement.find_all_children_with_name(element, "simpleType")
        if len(simple_type) > 0:
            # simpleType may have either an extension or a restriction
            # extension
            base = LxmlElement.find_all_children_with_name_and_attribute(
                simple_type[0], "extension", "base"
            )
            if len(base) > 0:
                schema_type = base[0].get("base")
            # restriction
            base = LxmlElement.find_all_children_with_name_and_attribute(
                simple_type[0], "restriction", "base"
            )
            if len(base) > 0:
                schema_type = base[0].get("base")
        # the element may be a List
        for item in LxmlElement.iter(element, "{*}list"):
            type = item.get("itemType")
            schema_type = f"List of type {type}"
        # the element may be a restriction
        for item in LxmlElement.iter(element, "{*}restriction"):
            type = item.get("base")
            schema_type = f"Restriction of type {type}"

        # if schemaType is not None:
        #     # Add any missing prefix
        #     if ns_prefix(schemaType) is None:
        #         base = element.base
        #         if base in self.schema.schemaBase:
        #             prefix = self.schema.schemaBase[base]
        #             schemaType = prefix + ":" + schemaType
        # else:
        #     schemaType = "untyped"
        return schema_type

    @staticmethod
    def unique_tag(name: str, namespace: str) -> str:
        """A unique global tag from the element name and namespace

        Args:
            name: The name of the element
            namespace: The namespace

        Returns:
            A unique element tag on the form ``{namespace}name``

        """

        tag = "{" + namespace + "}" + name
        return tag

    @staticmethod
    def get_schema_version(root: Element) -> str:
        """Get the current OCX schema version

        Args:
            root: The root element of the schema

        Returns:
            The  version of the OCX schema

        """
        version = "Missing"
        # root.findall('.//{*}attribute[@name="schemaVersion"]'
        element = LxmlElement.find_all_children_with_attribute_value(
            root, "attribute", "name", "schemaVersion"
        )
        if len(element) > 0:
            version = element[0].get("fixed")
        return version

    @staticmethod
    def find_schema_changes(root: Element) -> List[SchemaChange]:
        """Find any schema version changes with tag ``SchemaChange``

        Args:
            root: The root element of the schema

        Returns:

             A list of ``SchemaChange`` dataclasses

        """
        schema_changes = []
        changes = LxmlElement.find_all_children_with_name(root, "SchemaChange")
        for change in changes:
            # Retrieve the reason for change from the Description element
            description = LxmlElement.find_all_children_with_name(change, "Description")
            # Parse the text between start and end tag
            if len(description) > 0:
                description = text = ""
                for text in ElementTextIterator(change[0], with_tail=False):
                    description = description + text
                    text = re.sub("[\n\t\r]", "", description)
                description = text
            schema_change = SchemaChange(
                change.get("version"),
                change.get("author"),
                change.get("date"),
                description,
            )
            schema_changes.append(schema_change)
        return schema_changes

    @classmethod
    def schema_changes_data_grid(cls, root: Element) -> Dict:
        """A dictionary of the content  of all ``SchemaChange`` tags

        Args:
            root: The root element of the schema

        Returns:

             A dict dta grid with a unique id as key
        """
        changes = cls.find_schema_changes(root)
        data_grid = {}
        i = 0
        for change in changes:
            c = f"{i:05d}"
            data_grid[c] = asdict(change)
            i = i + 1
        return {key: value for key, value in sorted(data_grid.items())}
