#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from lxml import etree
from xsdata.models import xsd
from ocx_schema_parser.parser import LxmlElement


class SchemaTransformer:
    def transform(self, xs_element: etree.Element, target_namespace: str) -> xsd.Element:
        e = xsd.Element()
        e.target_namespace = target_namespace
        e.name = LxmlElement.get_name(xs_element)
        e.ref = LxmlElement.get_reference(xs_element)
        e.abstract = LxmlElement.is_abstract(xs_element)
        return e
