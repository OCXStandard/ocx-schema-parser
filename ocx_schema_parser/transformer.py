#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""Schema transformer"""

# System imports

from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterator, List, Union

# Third party imports
from loguru import logger
from lxml.etree import Element, QName

# Application imports
from ocx_schema_parser.data_classes import (
    OcxEnumerator,
    OcxSchemaAttribute,
    OcxSchemaChild,
    SchemaAttribute,
)
from ocx_schema_parser.elements import OcxGlobalElement
from ocx_schema_parser.helpers import SchemaHelper
from ocx_schema_parser.ocxdownloader.downloader import SchemaDownloader
from ocx_schema_parser.ocxparser import OcxParser
from ocx_schema_parser.xparse import LxmlElement


def resolve_source(source: str, recursive: bool) -> Iterator[str]:
    """Resolve the source url.

    Args:
        source:
        recursive: True if
    """
    if "://" in source and not source.startswith("file://"):
        yield source
    else:
        path = Path(source).resolve()
        match = "**/*" if recursive else "*"
        if path.is_dir():
            for ext in ["wsdl", "xsd", "dtd", "xml", "json"]:
                yield from (x.as_uri() for x in path.glob(f"{match}.{ext}"))
        else:  # is file
            yield path.as_uri()


def download_schema_from_url(url: str, schema_folder: Path) -> List:
    """ "Download the schemas from an url before processing.

    Args:
        url: The location of the schema
        schema_folder: The download folder. Will be created if not existing. If existing,
                    any ``.xsd`` files will be deleted.

    Returns:
        True if the was downloaded , false otherwise:
    """

    schema_folder.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Created download folder: {schema_folder.resolve()}")
    # Delete any content if existing
    for file in schema_folder.glob("*.xsd"):
        logger.debug(f"Deleting file: {file}")
        Path(file).unlink()
    downloader = SchemaDownloader(schema_folder)
    downloader.wget(url)
    uris = []
    for key in downloader.downloaded:
        if key is not None:
            uris.append(key)
            logger.debug(f"Downloading from uri: {key}")
    files = list(schema_folder.glob("*.xsd"))
    for file in files:
        logger.debug(f"Downloaded schema file: {file}")
    return uris


def filter_ocx(name: str, prefix: str, ocx: OcxGlobalElement) -> bool:
    """Filter function for looking up an ocx instance by name and prefix."""
    return name == ocx.get_name() and prefix == ocx.get_prefix()


class Transformer:
    """The OCX transformer class.


    Attributes:
        parser: The instance of the OcxParser
        _ocx_global_elements: Hash table as key-value pairs `(tag, OcxSchemaElement)` for all parsed schema elements
        _schema_enumerators: All schema enumerators
        _simple_types: All schema simple type elements
        -is_transformed: True if schema classes are transformed, False otherwise
    """

    def __init__(self):
        self.parser: OcxParser = OcxParser()
        self._ocx_global_elements: Dict = (
            {}
        )  # Hash table with tag as key, value pairs(tag, OcxGlobalElement)
        self._schema_enumerators: Dict = {}
        self._simple_types: List[SchemaAttribute] = []
        self._global_attributes: List[SchemaAttribute] = []
        self._is_transformed: bool = False

    def transform_schema_from_url(self, url: str, folder: Path) -> bool:
        """Transform the xsd schema with ``url`` into python objects.

        Returns:
            True if success, False otherwise.
        """
        if self._transform_schema_from_url(url, folder):
            self._transform_objects()
            self._is_transformed = True
        return self.is_transformed()

    def transform_schema_from_folder(self, folder: Path) -> bool:
        """Transform the xsd schemas in ``folder``.

        Returns:
            True if success, False otherwise.
        """
        if self._transform_schema_in_folder(folder):
            self._transform_objects()
            self._is_transformed = True
        return self.is_transformed()

    def is_transformed(self) -> bool:
        """Return transformation status."""
        return self._is_transformed

    def get_ocx_elements(self) -> List:
        """Return all global OCX instances."""
        return list(self._ocx_global_elements.values())

    def get_ocx_element_with_name(self, name: str) -> OcxGlobalElement:
        """Return a global OCX instances with name ``name``.

        Returns:
            OCX instance with ``name``

        """
        items = filter(lambda item: item.get_name() == name, self.get_ocx_elements())
        for ocx in items:
            return ocx

    def get_ocx_element_from_type(
        self, schema_type: str
    ) -> Union[OcxGlobalElement, None]:
        """Method to retrieve the schema ``element etree.Element`` with the key 'type'

        Args:
            schema_type: the ocx type on the form ``prefix:name``

        Returns:
            The ``OcxGlobalElement`` instance

        """
        object = None
        name = LxmlElement.strip_namespace_prefix(schema_type)
        prefix = LxmlElement.namespace_prefix(schema_type)
        result = filter(
            lambda ocx: filter_ocx(name, prefix, ocx), self.get_ocx_elements()
        )
        for item in result:
            object = item
        return object

    def ocx_iterator(self) -> Iterator:
        """Return an iterator of the OCX elements."""
        return iter(self._ocx_global_elements.values())

    def get_enumerators(self) -> Dict:
        """Return all enumeration instances."""
        return self._schema_enumerators

    def get_global_attributes(self) -> List[SchemaAttribute]:
        """Return all enumeration instances."""
        return self._global_attributes

    def get_simple_types(self) -> List:
        """Return all global simpleType instances."""
        return self._simple_types

    def get_enumerator_types(self) -> Dict:
        """Return the schema enumerator types.
        Returns: All enumerator types
        """
        tbl = defaultdict(list)
        enums = self.get_enumerators()
        for name, enum in enums.items():
            tbl["Name"].append(name)
            tbl["prefix"].append(enum.prefix)
            tbl["Tag"].append(enum.tag)
        return tbl

    def _transform_schema_from_url(self, url: str, folder: Path) -> bool:
        """Transform from a schema location given by a remote url.
            The schemas and any referenced schemas will be downloaded before transformed.

        Args:
            folder: The download folder.
            url: The remote location of the xsd schema.
        """

        result = False
        if download_schema_from_url(url, folder):
            # process downloaded schemas
            if self._transform_schema_in_folder(folder):
                result = True
        return result

    def _transform_schema_in_folder(self, location: Path) -> bool:
        """Transform all xsd schemas in the folder ``location``

        Args:
            location: The folder containing the xsd schemas.
        """
        files = resolve_source(str(location.resolve()), True)
        counter = 0
        # parse all schemas
        for file in files:
            self.parser.process_xsd_from_file(file)
            counter = +1
        return counter > 0

    def _add_global_ocx_element(self, tag: str, element: OcxGlobalElement):
        """Add a global OCX element to the hash table

        Args:
            tag: The hash key
            element: The global OCX element to add

        """
        self._ocx_global_elements[tag] = element

    def _find_all_my_parents(self, ocx: OcxGlobalElement):
        """Recursively find all the xsd schema parents of a global xsd element(parent, grandparent ...)
        The parents found is added to the ocx instance (child)

        Args:
            ocx: The global ocx instance to search from

        """
        # Get the unique tag of the global element
        tag = ocx.get_tag()
        # Find my parents
        self._find_parents(tag, ocx)

    def _find_parents(self, child_tag: str, ocx: OcxGlobalElement):
        """Recursively find all ancestors of the global element ``OxcGlobalElement``

        Args:
            child_tag: The unique tag of a child
            ocx: The global element (the root to start the search from)

        """
        # Look up the xsd element
        ocx.get_name()
        e = self.parser.get_element_from_tag(child_tag)
        if e is not None:
            # The element's type is the parent
            schema_type = SchemaHelper.get_type(e)
            if schema_type is None:
                return
            # Look up the parent element from its type
            parent_tag, parent_element = self.parser.get_element_from_type(schema_type)
            # Add the parent to the global ocx
            if parent_tag is not None:
                ocx.put_parent(parent_tag, parent_element)
                assertion = LxmlElement.find_assertion(parent_element)
                if assertion is not None:
                    ocx.add_assertion(assertion)
                self._find_parents(parent_tag, ocx)
        return

    def _transform_objects(self) -> None:
        """Transform all parsed elements to python objects"""
        # All schema elements of type element
        elements = self.parser.get_schema_element_types()
        for tag in elements:
            e = self.parser.get_element_from_tag(tag)
            qn = QName(tag)
            name = qn.localname
            logger.debug(f"Adding global element {name}")
            ocx = OcxGlobalElement(e, tag, self.parser._schema_namespaces)
            # store in look-up table
            self._add_global_ocx_element(tag, ocx)
            # Find all parents and add them to the instance
            self._find_all_my_parents(ocx)
            # Process all xs:attribute elements including all supertypes
            self._process_attributes(ocx)
            # Process ald children including super type children
            self._process_children(ocx, self.parser.get_substitution_groups())
        # Enumeration types
        for tag in self.parser.get_schema_enumerations():
            e = self.parser.get_element_from_tag(tag)
            name = LxmlElement.get_name(e)
            prefix = self.parser.get_prefix_from_namespace(QName(tag).namespace)
            enum = OcxEnumerator(name=name, prefix=prefix, tag=tag)
            values = []
            descriptions = []
            for enumeration in LxmlElement.iter(e, "{*}enumeration"):
                values.append(enumeration.get("value"))
                descriptions.append(LxmlElement.get_element_text(enumeration))
            enum.values = values
            enum.descriptions = descriptions
            self._add_schema_enumerator(enum)
        # Simple types
        for tag in self.parser.get_schema_simple_types():
            element = self.parser.get_element_from_tag(tag)
            name = LxmlElement.get_name(element)
            type = SchemaHelper.get_type(element)
            prefix = self.parser.get_prefix_from_namespace(QName(tag).namespace)
            restriction = LxmlElement.get_restriction(element)
            annotation = LxmlElement.get_element_text(element)
            attribute = SchemaAttribute(
                name=name,
                type=type,
                prefix=prefix,
                restriction=restriction,
                description=annotation,
            )
            self._simple_types.append(attribute)
        # Global attributes
        for tag in self.parser.get_schema_attribute_types():
            element = self.parser.get_element_from_tag(tag)
            name = LxmlElement.get_name(element)
            type = SchemaHelper.get_type(element)
            prefix = self.parser.get_prefix_from_namespace(QName(tag).namespace)
            restriction = LxmlElement.get_restriction(element)
            annotation = LxmlElement.get_element_text(element)
            attribute = SchemaAttribute(
                name=name,
                prefix=prefix,
                type=type,
                restriction=restriction,
                description=annotation,
            )
            self._add_global_attribute(attribute)
        return

    def _add_schema_enumerator(self, enum: OcxEnumerator):
        """Add a schema enumerator type.

        Args:
            enum: Schema enumerator

        """
        self._schema_enumerators[enum.name] = enum

    def _add_global_attribute(self, attrib: SchemaAttribute):
        """Add a schema attribute type.

        Args:
            attrib: Schema attribute

        """
        self._global_attributes.append(attrib)

    def _process_attributes(self, ocx: OcxGlobalElement) -> None:  # Simplify function
        """Process all xs:attributes of the global element

        Args:
            ocx: The parent OCX element

        """

        # Process all xs:attribute elements including all supertypes
        ns = ocx.get_namespace()
        attributes = LxmlElement.find_attributes(ocx.get_schema_element())
        for a in attributes:
            ocx.add_attribute(self._process_attribute(a, ns))
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            attributes = LxmlElement.find_attributes(parents[t])
            for a in attributes:
                ocx.add_attribute(self._process_attribute(a, ns))
        # Process all xs:attributeGroup elements including all supertypes attributeGroups
        groups = LxmlElement.find_attribute_groups(ocx.get_schema_element())
        for group in groups:
            # Get the reference
            ref = LxmlElement.get_reference(group)
            if ref is not None:
                tag, at_group = self.parser.get_element_from_type(ref)
                if at_group is not None:
                    attributes = LxmlElement.find_attributes(at_group)
                    for a in attributes:
                        ocx.add_attribute(self._process_attribute(a, ns))
                else:
                    logger.error(
                        f"Attribute group {ref} is not found in the global look-up table"
                    )
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            groups = LxmlElement.find_attribute_groups(parents[t])
            for group in groups:
                # Get the reference
                ref = LxmlElement.get_reference(group)
                if ref is not None:
                    tag, at_group = self.parser.get_element_from_type(ref)
                    if at_group is not None:
                        attributes = LxmlElement.find_attributes(at_group)
                        for a in attributes:
                            ocx.add_attribute(self._process_attribute(a, ns))
                    else:
                        logger.error(
                            f"Attribute group {ref} is not found in the global look-up table"
                        )
        return

    def _process_children(self, ocx: OcxGlobalElement, substitutions: Dict):
        """Process all xs:element of the global element

        Args:
            ocx: The parent OCX element

        """

        # Process all xs:element elements including all supertypes
        target_ns = ocx.get_namespace()
        elements = LxmlElement.find_all_children_with_name(
            ocx.get_schema_element(), "element"
        )
        for e in elements:
            name = f"{self.parser.get_prefix_from_namespace(target_ns)}:{LxmlElement.get_name(e)}"
            prefix = self.parser.get_prefix_from_namespace(target_ns)
            child = self._process_child(e, prefix)
            child.cardinality = LxmlElement.cardinality_string(e)
            child.is_choice = LxmlElement.is_choice(e)
            if name in substitutions:
                for tag in substitutions[name]:
                    element = self.parser.get_element_from_tag(tag)
                    subst = self._process_child(element, prefix)
                    subst.name = LxmlElement.get_name(element)
                    subst.type = SchemaHelper.get_type(element)
                    subst.description = LxmlElement.get_element_text(element)
                    subst.cardinality = child.cardinality
                    subst.is_choice = child.is_choice
                    ocx.add_child(subst)
                    logger.debug(f"{ocx.get_name()}: Adding child {subst.name}")
                else:
                    ocx.add_child(child)
                    logger.debug(f"{ocx.get_name()}: Adding child {child.name}")
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            elements = LxmlElement.find_all_children_with_name(parents[t], "element")
            for e in elements:
                name = f"{self.parser.get_prefix_from_namespace(target_ns)}:{LxmlElement.get_name(e)}"
                prefix = self.parser.get_prefix_from_namespace(target_ns)
                child = self._process_child(e, prefix)
                child.cardinality = LxmlElement.cardinality_string(e)
                child.is_choice = LxmlElement.is_choice(e)
                if name in substitutions:
                    for tag in substitutions[name]:
                        element = self.parser.get_element_from_tag(tag)
                        subst = self._process_child(element, prefix)
                        subst.name = LxmlElement.get_name(element)
                        subst.type = SchemaHelper.get_type(element)
                        subst.description = LxmlElement.get_element_text(element)
                        subst.cardinality = child.cardinality
                        subst.is_choice = child.is_choice
                        ocx.add_child(subst)
                        logger.debug(f"{ocx.get_name()}: Adding child {subst.name}")
                else:
                    ocx.add_child(child)
                    logger.debug(f"{ocx.get_name()}: Adding child {child.name}")
            return

    def _process_attribute(
        self, xs_attribute: Element, target_ns: str
    ) -> OcxSchemaAttribute:
        """Process an xs:attribute element
        Arguments:
            xs_attribute: The schema attribute
            target_ns: attribute target namespace

        Returns:
            An instance of the OcxSchemaAttribute

        """
        name = LxmlElement.get_name(xs_attribute)
        type = SchemaHelper.get_type(xs_attribute)
        use = LxmlElement.get_use(xs_attribute)
        fixed = xs_attribute.get("fixed")
        default = xs_attribute.get("default")
        annotation = LxmlElement.get_element_text(xs_attribute)
        prefix = self.parser.get_prefix_from_namespace(target_ns)
        attribute = OcxSchemaAttribute(
            name=name,
            prefix=prefix,
            type=type,
            fixed=fixed,
            use=use,
            default=default,
            description=annotation,
        )
        reference = LxmlElement.get_reference(xs_attribute)
        if reference is not None:
            # Get the referenced element
            tag, a = self.parser.get_element_from_type(reference)
            attribute.name = LxmlElement.get_name(a)
            # attribute.assign_referenced_attribute(a)
            if attribute.description == "":
                attribute.description = LxmlElement.get_element_text(a)
            attribute.type = SchemaHelper.get_type(a)
            return attribute
        else:
            if attribute.type is None:
                # logger.debug(f'The schema type {attribute.get_name()} has no type')
                qn = QName(xs_attribute)
                prefix = self.parser.get_prefix_from_namespace(qn.namespace)
                type = LxmlElement.strip_namespace_tag(xs_attribute.tag)
                attribute.type = f"{prefix}:{type}"
            return attribute

    def _process_child(self, xs_element: Element, prefix: str) -> OcxSchemaChild:
        """Process an xs:element child element

        Arguments:
            xs_element: The schema element
            unique_tag: The element unique tag

        Returns:
            An instance of the child

        """
        name = LxmlElement.get_name(xs_element)
        type = SchemaHelper.get_type(xs_element)
        annotation = LxmlElement.get_element_text(xs_element)
        cardinality = LxmlElement.cardinality_string(xs_element)
        lower, upper = LxmlElement.cardinality(xs_element)
        choice = LxmlElement.is_choice(xs_element)
        if lower == 0:
            use = "opt."
        else:
            use = "req."

        child = OcxSchemaChild(
            name=name,
            prefix=prefix,
            type=type,
            use=use,
            description=annotation,
            cardinality=cardinality,
            is_choice=choice,
        )
        reference = LxmlElement.get_reference(xs_element)
        if reference is not None:
            # Get the referenced element
            tag, a = self.parser.get_element_from_type(reference)
            child.name = LxmlElement.get_name(a)
            if child.description == "":
                child.description = LxmlElement.get_element_text(a)
            child.type = SchemaHelper.get_type(a)
        return child
