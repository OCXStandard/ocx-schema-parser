#  Copyright (c) 3-2023.  OCX Consortium https://3docx.org. See the LICENSE
# System imports
from collections import defaultdict
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union
# Third party imports
from loguru import logger
import requests
from lxml.etree import Element
from lxml.etree import QName
from requests import HTTPError
# Application imports
from ocx_schema_parser import DEFAULT_SCHEMA
from ocx_schema_parser import PROCESS_SCHEMA_TYPES
from ocx_schema_parser import SCHEMA_FOLDER
from ocx_schema_parser import W3C_SCHEMA_BUILT_IN_TYPES
from .data_classes import SchemaSummary
from .data_classes import SchemaType
from .data_classes import SchemaEnumerator
from .elements import OcxAttribute, OcxChildElement, OcxGlobalElement
from .helpers import SchemaHelper
from .xparse import LxmlElement
from .xparse import LxmlParser
from ocx_schema_parser.ocxtransformer.transformer import SchemaTransformer


class OcxSchema:
    """The OcxSchema provides functionality for parsing the OCX xsd schema and storing all the elements.

    Args:
        logger: The main python logger

    Attributes:
        _namespace: The dict of all namespaces on the form (prefix, namespace) key-value pairs resulting from
            parsing all schema files, `W3C <https://www.w3.org/TR/xml-names/#sec-namespaces>`_.
        _ocx_global_elements: Hash table as key-value pairs `(tag, OcxSchemaElement)` for all parsed schema elements
        _is_parsed: True if a schema has been parsed, False otherwise
        _schema_version: The version of the parsed schema
        _local_folder: The local folder where any external schemas will be downloaded
        _schema_changes: A list of all schema changes described by the tag SchemaChange contained in the xsd file.
        _schema_types: The list of xsd types to be parsed. Only these types will be stored.
        _default_schema: The default schema to be parsed
        _builtin_xs_types: W3C primitive data types.
            `www.w3.org <https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes>`_. Defined in ``config.yaml``


    """

    def __init__(self, log: logger, local_folder: str = SCHEMA_FOLDER):
        self._parser = LxmlParser(log)
        self.log = log
        # Default namespace map for the reserved prefix xml. See https://www.w3.org/TR/xml-names/#sec-namespaces
        self._namespace = {"xml": "http://www.w3.org/XML/1998/namespace"}
        self._is_parsed = False
        self._local_folder = local_folder
        Path(self._local_folder).mkdir(parents=True, exist_ok=True)
        self._default_schema = DEFAULT_SCHEMA
        self._all_schema_elements = {}  # Hash table with tag as key schema_elements[tag] = lxml.etree.Element
        self._ocx_global_elements = {}  # Hash table with tag as key, value pairs(tag, OcxGlobalElement)
        self._all_types = defaultdict(list)  # Hash table with tag as key: all_types[tag] = lxml.etree.Element
        self._schema_types = PROCESS_SCHEMA_TYPES
        self._schema_version = None
        self._schema_changes = defaultdict(list)
        # w3c primitive data types ref https://www.w3.org/TR/xmlschema-2/#built-in-primitive-datatypes
        self._builtin_xs_types = W3C_SCHEMA_BUILT_IN_TYPES

    def _add_global_ocx_element(self, tag: str, element: OcxGlobalElement):
        """Add a global OCX element to the hash table

        Args:
            tag: The hash key
            element: The global OCX element to add

        """
        #  self.log.debug(f'(Added schema element with tag {tag}')
        self._ocx_global_elements[tag] = element

    def _add_schema_element(self, tag: str, element: Element):
        """Add a new schema element to the hash table

        Args:
            tag: The hash key
            element: The schema ``Element`` to add

        """
        #  self.log.debug(f'(Added schema element with tag {tag}')
        self._all_schema_elements[tag] = element

    def _add_schema_type(self, schema_type: str, tag: str):
        """Add a new schema type to the hash table

        Args:
            tag: The hash key
            schema_type: The schema type

        """
        #  self.log.debug(f'(Added schema element with type {schema_type} and tag {tag}')
        self._all_types[schema_type].append(tag)

    def process_schema(self, schema_url: str = DEFAULT_SCHEMA) -> bool:
        """Process the XSD schema file and create all hash tables of global elements.

        Returns:
            True of processed OK, False otherwise.

        """
        if self._parse_schema(schema_url):
            self._process_ocx_elements()
            # Sort the hash table
            # self._sort_schema_elements() ToDo: This function changes the dict to a list. Fix it!
            return True
        else:
            return False

    def get_schema_folder(self) -> str:
        """Return the local folder where the schemas are stored. The local folder is relative to the project root.

        Returns:
            The relative path to the local schema folder.

        """
        return self._local_folder

    def put_schema_folder(self, local_folder: str):
        """Set the local folder where the schemas are stored. The local folder is relative to the project root."""
        self._local_folder = local_folder

    def put_default_schema(self, schema_url: str):
        """Return the default schema to be parsed.

        Args:
            schema_url: The location of the schema

        """
        self._default_schema = schema_url

    def get_default_schema(self) -> str:
        """Return the default schema to be parsed.

        Returns:
            The default schema url.

        """
        return self._default_schema

    def _parse_schema(self, schema_url: str = DEFAULT_SCHEMA) -> bool:
        """Parse the OCX xsd schema. The method will traverse any referenced (using the tag xs:import)
            schemas and parse these also. If the referenced schema url is not a local file,
            the method will download the file before the schema is parsed.

        Args:
            schema_url: the path or URL to the xsd file

        Returns:
            True if all schemas are parsed successfully, else returns False

        """

        if "http" not in schema_url:
            if not Path(schema_url).exists():
                self.log.error(f"The xsd file {schema_url} does not exist")
                return False
        else:
            try:
                remote_file = Path(schema_url).name
                file = Path(self._local_folder) / remote_file
                r = requests.get(schema_url)
                with open(file, "wb") as f:
                    f.write(r.content)
                self.log.debug(f'Successfully downloaded remote schema "{schema_url}" ' f'to local folder "{self._local_folder}"')
                schema_url = file
            except HTTPError as e:
                self.log.error(f'Failed to access schema from "{schema_url}: {e}""')
                return False
        try:
            self._is_parsed = self._parser.parse(schema_url)
        except BaseException as e:
            self.log.error(e.with_traceback)
            return False
        if self._is_parsed:
            self.log.debug(f'Successfully parsed xsd schema with location "{schema_url}"')
            root = self._parser.get_root()
            ns = self._parser.get_namespaces()
            # Add the ns to the global namespace dict
            n = self._add_namespace(ns)
            # The target namespace for the current schema
            target_ns = self._parser.get_target_namespace()
            if target_ns not in self._namespace.values():
                self.log.error(f'The target _namespace "{target_ns}" is not registered in the _namespace listing {self._namespace}')
                self._is_parsed = False
                return False
            # Retrieve the OCX schema version
            version = SchemaHelper.get_schema_version(root)
            if version != "Missing":
                self._schema_version = version
            self.log.debug(f'Added {n} new namespaces for schema "{schema_url}"')
            if LxmlElement.has_child_with_name(root, "SchemaChange"):
                changes = SchemaHelper.find_schema_changes(root)
                if len(changes) > 0:
                    self._schema_changes = changes
            # Build the look-up tables for all global element types
            for schema_type in self._schema_types:  # Only search for selected element types
                types = LxmlElement.find_all_children_with_name_and_attribute(root, schema_type, "name")
                for e in types:
                    # Add element to look-up table
                    name = LxmlElement.get_name(e)
                    if name is not None:
                        # add the schema type
                        tag = SchemaHelper.unique_tag(name, target_ns)
                        schema_type = LxmlElement.get_localname(e)
                        # Only process the selected element types and store in hash tables
                        if schema_type in self._schema_types:
                            self._add_schema_element(tag, e)
                            self._add_schema_type(schema_type, tag)
            # Parse any imported schemas
            references = self._parser.get_referenced_files()
            for ns in references:
                url = references[ns]
                self._is_parsed = self._parse_schema(url)
                if self._is_parsed:
                    if ns not in list(self.get_namespaces().values()):
                        self.log.error(f'Mismatched _namespace "{ns}" in xsd with url: "{url}"')
                else:
                    break
        return self._is_parsed

    def is_parsed(self) -> bool:
        return self._is_parsed

    def _process_ocx_elements(self):
        """Process all parsed elements and build the hash table of OcxSchemaElement"""
        # All schema elements of type element
        elements = self._get_schema_element_types()
        for tag in elements:
            e = self._get_element(tag)
            qn = QName(tag)
            name = qn.localname
            self.log.debug(f"Adding global element {name}")
            ocx = OcxGlobalElement(e, tag, self.log)
            transformer = SchemaTransformer()
            xsd_element = transformer.transform(e, LxmlElement.get_namespace(e))
            # store in look-up table
            self._add_global_ocx_element(tag, ocx)
            # Find all parents and add them to the instance
            self._find_all_my_parents(ocx)
            # Process all xs:attribute elements including all supertypes
            self._process_attributes(ocx)
            # Process ald children including super type children
            self._process_children(ocx)
        return

    def _process_attributes(self, ocx: OcxGlobalElement):
        """Process all xs:attributes of the global element

        Args:
            ocx: The parent OCX element

        """

        # Process all xs:attribute elements including all supertypes
        attributes = LxmlElement.find_attributes(ocx.get_schema_element())
        for a in attributes:
            ocx.add_attribute(self._process_attribute(a))
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            attributes = LxmlElement.find_attributes(parents[t])
            for a in attributes:
                ocx.add_attribute(self._process_attribute(a))
        # Process all xs:attributeGroup elements including all supertypes attributeGroups
        groups = LxmlElement.find_attribute_groups(ocx.get_schema_element())
        for group in groups:
            # Get the reference
            ref = LxmlElement.get_reference(group)
            if ref is not None:
                tag, at_group = self._get_element_from_type(ref)
                if at_group is not None:
                    attributes = LxmlElement.find_attributes(at_group)
                    for a in attributes:
                        ocx.add_attribute(self._process_attribute(a))
                else:
                    self.log.error(f"Attribute group {ref} is not found in the global look-up table")
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            groups = LxmlElement.find_attribute_groups(parents[t])
            for group in groups:
                # Get the reference
                ref = LxmlElement.get_reference(group)
                if ref is not None:
                    tag, at_group = self._get_element_from_type(ref)
                    if at_group is not None:
                        attributes = LxmlElement.find_attributes(at_group)
                        for a in attributes:
                            ocx.add_attribute(self._process_attribute(a))
                    else:
                        self.log.error(f"Attribute group {ref} is not found in the global look-up table")
        return

    def _process_children(self, ocx: OcxGlobalElement):
        """Process all xs:element of the global element

        Args:
            ocx: The parent OCX element

        """

        # Process all xs:element elements including all supertypes
        elements = LxmlElement.find_all_children_with_name(ocx.get_schema_element(), "element")
        for e in elements:
            ocx.add_child(self._process_child(e))
        # Iterate over parents
        parents = ocx.get_parents()
        for t in parents:
            elements = LxmlElement.find_all_children_with_name(parents[t], "element")
            for e in elements:
                ocx.add_child(self._process_child(e))
        return

    def _process_attribute(self, xs_attribute: Element) -> OcxAttribute:
        """Process an xs:attribute element

        Returns:
            An instance of the OcxAttribute

        """
        attribute = OcxAttribute(xs_attribute)
        reference = LxmlElement.get_reference(xs_attribute)
        if reference is not None:
            # Get the referenced element
            tag, a = self._get_element_from_type(reference)
            attribute.put_name(LxmlElement.get_name(a))
            attribute.assign_referenced_attribute(a)
            if attribute.get_description() == "":
                attribute.put_description(LxmlElement.get_element_text(a))
            attribute.put_type(SchemaHelper.get_type(a))
        return attribute

    def _process_child(self, xs_element: Element) -> OcxChildElement:
        """Process an xs:element child element

        Returns:
            An instance of the OcxChildElement

        """
        child = OcxChildElement(xs_element)
        reference = LxmlElement.get_reference(xs_element)
        if reference is not None:
            # Get the referenced element
            tag, a = self._get_element_from_type(reference)
            child.put_name(LxmlElement.get_name(a))
            if child.get_description() == "":
                child.put_description(LxmlElement.get_element_text(a))
            child.put_type(SchemaHelper.get_type(a))
            child.put_reference(tag)
        return child

    def _get_element(self, tag: str) -> Union[Element, None]:
        """Private function to get the ``etree.Element`` with the key 'tag'

        Returns:
            The ``OcxGlobalElement`` instance

        """
        if tag in self._builtin_xs_types:
            self.log.debug(f"{__class__}: The tag {tag} is a built-in type {self._builtin_xs_types[tag]}")
            return None
        if tag not in self._all_schema_elements.keys():
            self.log.debug(f"{__class__}: The tag {tag} is not in the look-up table")
        return self._all_schema_elements.get(tag)

    def _get_element_from_type(self, schema_type: str) -> Tuple[Any, Any]:
        """Private method to retrieve the schema element ``etree.Element`` with the key 'type'

        Returns:
            A tuple of the element unique tag and the element (tag, Element)

        """
        name = LxmlElement.strip_namespace_prefix(schema_type)
        if LxmlElement.namespace_prefix(schema_type) in self._namespace:
            namespace = self._namespace[LxmlElement.namespace_prefix(schema_type)]
        else:
            self.log.debug(f"The type {schema_type} has an unknown _namespace prefix")
            return None, None
        tag = SchemaHelper.unique_tag(name, namespace)
        if tag in self._builtin_xs_types:
            self.log.debug(f"The tag {tag} is a built-in type {self._builtin_xs_types[tag]}")
            return None, None
        if tag not in self._all_schema_elements:
            self.log.debug(f"{__class__}: The tag {tag} is not in the look-up table")
            return None, None
        else:
            return tag, self._all_schema_elements.get(tag)

    def _find_parents(self, child_tag: str, ocx: OcxGlobalElement):
        """Recursively find all ancestors of the global element ``OxcGlobalElement``

        Args:
            child_tag: The unique tag of a child
            ocx: The global element (the root to start the search from)

        """
        # Look up the xsd element
        ocx.get_name()
        e = self._get_element(child_tag)
        if e is not None:
            # The element's type is the parent
            schema_type = SchemaHelper.get_type(e)
            if schema_type is not None:
                # Look up the parent xsd element from its type
                parent_tag, parent_element = self._get_element_from_type(schema_type)
                # Add the parent to the global ocx
                if parent_tag is not None:
                    ocx.put_parent(parent_tag, parent_element)
                    assertion = LxmlElement.find_assertion(parent_element)
                    if assertion is not None:
                        ocx.add_assertion(assertion)
                    self._find_parents(parent_tag, ocx)
            else:
                return
        return

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

    def get_ocx_element_from_type(self, schema_type: str) -> Union[OcxGlobalElement, None]:
        """Method to retrieve the schema ``element etree.Element`` with the key 'type'

        Args:
            schema_type: the ocx type on the form ``prefix:name``

        Returns:
            The ``OcxGlobalElement`` instance

        """
        nsprefix = LxmlElement.namespace_prefix(schema_type)
        name = LxmlElement.strip_namespace_prefix(schema_type)
        if nsprefix not in self._namespace.values():
            for prefix in self._namespace:
                if prefix == LxmlElement.namespace_prefix(schema_type):
                    namespace = self._namespace[prefix]
                    tag = SchemaHelper.unique_tag(name, namespace)
                    if tag not in self._all_schema_elements:
                        self.log.debug(f"{__class__}: The tag {tag} is not in the look-up table")
                        return None
                    else:
                        return self._ocx_global_elements[tag]
        else:
            self.log.debug(f'{__class__}: The _namespace prefix  "{nsprefix}" is not defined')
            return None

    def get_ocx_children_data(self, schema_type: str) -> Dict:
        """Method to retrieve the ocx ``OcxGlobalElement`` children data

        Args:
            schema_type: the ocx type on the form ``prefix:name``

        Returns:
            All children data attributes of the element

        """
        element = self.get_ocx_element_from_type(schema_type)
        if element:
            return element.children_to_dict()
        return {}

    def get_ocx_attribute_data(self, schema_type: str) -> Dict:
        """Method to retrieve the ocx ``OcxGlobalElement`` attribute data

        Args:
            schema_type: the ocx type on the form ``prefix:name``

        Returns:
            All the ocx element attribute data

        """
        element = self.get_ocx_element_from_type(schema_type)
        if element:
            return element.attributes_to_dict()
        return {}

    def _get_prefix_from_namespace(self, namespace: str) -> str:
        """Return the namespace prefix

        Returns:
            the namespace prefix

        """
        prefix = "None"
        if namespace not in list(self._namespace.values()):
            self.log.debug(f"The _namespace {namespace} is not in the global _namespace dict")
        for item in self._namespace:
            if namespace == self._namespace[item]:
                prefix = item
        return prefix

    def _add_namespace(self, namespace: dict) -> int:
        """Add new namespaces to the global namespace dict'

        Returns:
            The number of new namespaces added

        """
        ns = self._namespace
        # Check if any keys exists
        for prefix in ns:
            if prefix in namespace.keys():
                self.log.debug(
                    f'The _namespace prefix "{prefix}" already exists. '
                    f"Dropping new _namespace {namespace[prefix]} from the _namespace table"
                )
                self.log.debug(f'The existing _namespace with prefix "{prefix}" is: {self._namespace[prefix]}')
                del namespace[prefix]
        self._namespace = {**self._namespace, **namespace}
        return len(self._namespace) - len(ns)

    def get_namespaces(self) -> Dict:
        """The parsed namespaces'

        Returns:
            The dict of namespaces as (namespace,prefix) key-value pairs

        """
        return self._namespace

    def get_all_schema_elements(self) -> Dict:
        """Return all OCX schema elements.

        Returns:
            The dict of all global XSD ``lxml.etree.Element`` elements with the unique tag ``{namespace}name`` as key.

        """
        return self._all_schema_elements

    def _sort_schema_elements(self):
        """Sorts the schema hash table"""
        sorted_dict = sorted(self._all_schema_elements.items(), key=lambda kv: kv[0])
        self._all_schema_elements = sorted_dict

    def _get_schema_types(self, schema_type: str) -> List[str]:
        """Internal function to retrieve a list of tags of ``lxml.etree.Element`` schema elements of a specific type.

        Returns:
            The sorted list of all tags of ``lxml.etree.Element`` of type ``schema_type``

        """
        elements = []
        for tag in self._all_types[schema_type]:
            elements.append(tag)
        return sorted(elements)

    def get_ocx_elements(self) -> List[OcxGlobalElement]:
        """All ocx ``OcxGlobalElement`` elements.

        Returns:
            The list of all parsed ``OcxGlobalElement`` instances

        """
        return list(self._ocx_global_elements.values())

    def get_schema_version(self) -> str:
        """The OCX schema version

        Returns:
            The coded version string of the OCX schema

        """
        return self._schema_version

    def get_schema_changes(self) -> Dict:
        """The OCX schema change history.

        Returns:
            The schema changes for all schema versions

        """
        return self._schema_changes

    def _get_schema_element_types(self) -> List:
        """All schema elements of type ``element``.

        Returns:
            The list of all etree.Element of type ``element``

        """
        return self._get_schema_types("element")

    def _get_schema_complex_types(self) -> List[str]:
        """All tags for schema elements of type ``complexType``.

        Returns:
            The list of tags of all ``etree.Element`` of type ``complexType``

        """
        return self._get_schema_types("complexType")

    def _get_schema_simple_types(self) -> List[str]:
        """Alle schema elements of type ``simpleType``.

        Returns:
            The list of tags of all etree.Element of type ``simpleType``

        """
        return self._get_schema_types("simpleType")

    def _get_schema_attribute_tyepes(self) -> List[str]:
        """All schema elements of type ``attribute'

        Returns:
            The list of unique tags for all etree.Element of type ``attribute``.

        """

        return self._get_schema_types("attribute")

    def _get_schema_attribute_group_types(self) -> List[str]:
        """All schema elements of type ``attributeGroup``.

        Returns:
            The list of all etree.Element of type ``attributeGroup``
        """
        return self._get_schema_types("attributeGroup")

    def tbl_summary(self) -> SchemaSummary:
        """The summary of the parsed schema and any referenced schemas'

        Returns:
            The schema summary
        """

        schema_version = [("Schema Version", self.get_schema_version())]
        schema_types = [(schema_type, len(self._all_types[schema_type])) for schema_type in self._all_types]
        namespaces = [(ns, self._namespace[ns]) for ns in self._namespace]
        return SchemaSummary(schema_version, schema_types, namespaces)

    def tbl_attribute_groups(self) -> Dict:
        """All parsed ``attributeGroup`` types in the schema and any referenced schemas.

        Returns:

             List of  ``SchemaType`` data class holding ``attributeGroup`` attributes.
        """

        table = {}
        elements = self._get_schema_attribute_group_types()
        for tag in elements:
            table[tag] = self._get_schema_type_data_class(tag).to_dict()
        return table

    def tbl_simple_types(self) -> Dict:
        """The table of all parsed ``simpleType`` elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``simpleType``

        """

        table = {}
        elements = self._get_schema_simple_types()
        for tag in elements:
            table[tag] = self._get_schema_type_data_class(tag).to_dict()
        return table

    def tbl_attribute_types(self) -> Dict:
        """The table of all parsed attribute elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``attributeType``
        """

        table = {}
        elements = self._get_schema_attribute_tyepes()
        for tag in elements:
            table[tag] = self._get_schema_type_data_class(tag).to_dict()
        return table

    def tbl_element_types(self) -> Dict:
        """The table of all parsed elements of type element in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``element``
        """

        table = {}
        elements = self._get_schema_element_types()
        for tag in elements:
            table[tag] = self._get_schema_type_data_class(tag).to_dict()
        return table

    def tbl_complex_types(self) -> Dict:
        """The table of all parsed complexType elements in the schema and any referenced schemas.

        Returns:

            The ``SchemaType`` data class attributes of ``complexType``
        """

        table = {}
        elements = self._get_schema_complex_types()
        for tag in elements:
            table[tag] = self._get_schema_type_data_class(tag).to_dict()
        return table

    def _get_schema_type_data_class(self, tag: str) -> SchemaType:
        """Return the ``SchemaType`` dataclass of the schema type with ``tag``.
            Args:
                tag: the schema ``tag``

            Returns:

                A ``dataclass`` with the attributes of the element with the ``tag``
        '"""

        e = self._get_element(tag)
        qn = QName(tag)
        prefix = self._get_prefix_from_namespace(qn.namespace)
        if prefix == "None":
            self.log.error(f"Tag {tag} has an unknown _namespace")
        return SchemaType(prefix, LxmlElement.get_name(e), tag, LxmlElement.get_source_line(e))
