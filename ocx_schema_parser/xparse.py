#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""xparse module."""
# System imports
from typing import Dict

# Third party imports
from loguru import logger
from lxml import etree
from lxml.etree import Element, XMLSyntaxError

# Application imports
from .xelement import LxmlElement


class LxmlParser:
    """A wrapper of the lxml etree document tree and parser.

    Attributes:
        _tree : The ``lxml.etree`` DOM

    """

    def __init__(self):
        self._tree: Element = None

    def parse(self, file: str, store_ids: bool = False) -> bool:
        """Parses an XML file.

        Args:
            file: The file name of the xml document to be parsed. The parser can only parse from a local file.
            store_ids: If set to True, the parser will create a hash table of the xml IDs

        Returns:
            The return value. True for success, False otherwise.

        """
        # Parsing the XML file.
        parsed = False
        try:
            my_parser = etree.XMLParser(
                remove_comments=False,
                remove_blank_text=True,
                ns_clean=True,
                collect_ids=store_ids,
            )
            self._tree = etree.parse(file, parser=my_parser)
            parsed = True
        except XMLSyntaxError as e:
            logger.error(e)
        except OSError:
            logger.error("Failed to open file %s" % file, exc_info=True)
        return parsed

    def get_root(self) -> Element:
        """The XML root.

        Returns:
            The XML root node

        """
        return self._tree.getroot()

    def lxml_version(self) -> str:
        """lxml version tag.

        Returns:
            The lxml version tag

        """
        return etree.LXML_VERSION

    def doc_public_id(self) -> str:
        """

        Returns:
            The XML document type

        """
        return self._tree.docinfo.public_id

    def doc_url(self) -> str:
        """
        Returns:
            The XML document url

        """
        return self._tree.docinfo.URL

    def doc_encoding(self) -> str:
        """

        Returns:
            The XML document encoding

        """
        return self._tree.docinfo.encoding

    def doc_root_name(self) -> str:
        """

        Returns:
            The XML document root name

        """
        return self._tree.docinfo.root_name

    def doc_system_url(self) -> str:
        """

        Returns:
            The XML document system URL

        """
        return self._tree.docinfo.system_url

    def doc_xml_version(self) -> str:
        """

        Returns:
           The XML document version

        """
        return self._tree.docinfo.xml_version

    def get_namespaces(self) -> Dict:
        """The dict of the defined namespaces of (prefix, namespace) as (key,value) pairs.

        Returns:
            (prefix, namespace) as (key,value) pairs

        """
        root = self.get_root()
        if __debug__:
            if root is None:
                raise AssertionError(f"{__name__}: The root node is None")
        return root.nsmap

    def get_target_namespace(self) -> str:
        """The target namespace of the schema.

        Returns:
            The target namespace as a str

        """
        root = self.get_root()
        if __debug__:
            if root is None:
                raise AssertionError(f"{__name__}: The root node is None")
        return root.get("targetNamespace")

    def get_referenced_files(self) -> Dict:
        """The XML imports  (xs:import tags).

        Returns:
            A dict of key, value pairs (namespace: location/URL) of all xs:import tags.

        """
        root = self.get_root()
        if __debug__:
            if root is None:
                raise AssertionError(f"{__name__}: The root node is None")
        urls = {}
        references = LxmlElement.find_all_children_with_name(root, "import")
        for ref in references:
            loc = ref.get("schemaLocation")
            ns = ref.get("namespace")
            urls[ns] = loc
        return urls
