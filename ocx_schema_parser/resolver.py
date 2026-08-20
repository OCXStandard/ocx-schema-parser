"""Resolve parsed xsdata Schema objects into the OcxSchema Pydantic model."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from loguru import logger
from xsdata.models import xsd

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import (
    Attribute,
    Cardinality,
    ChildElement,
    ComplexType,
    EnumType,
    EnumValue,
    GlobalElement,
    OcxSchema,
    SchemaChange,
    SimpleType,
)

XSD_NS = "http://www.w3.org/2001/XMLSchema"
BUILTIN_NAMESPACES = {
    XSD_NS,
    "http://www.w3.org/XML/1998/namespace",
    "http://www.w3.org/2001/XMLSchema-instance",
}
#: maxOccurs values at or above this are treated as unbounded (xsdata uses sys.maxsize)
UNBOUNDED = 2**31


def _description(node) -> str:
    """Join the documentation strings of an annotated xsd node."""
    parts: list[str] = []
    for annotation in getattr(node, "annotations", []) or []:
        for doc in annotation.documentations:
            for item in doc.content:
                if isinstance(item, str):
                    parts.append(item.strip())
    return " ".join(p for p in parts if p)


def _cardinality(node) -> Cardinality:
    """Build a Cardinality from a particle's min/max occurs."""
    lower = node.min_occurs if node.min_occurs is not None else 1
    upper = node.max_occurs
    if upper is None or upper >= UNBOUNDED:
        return Cardinality(lower=lower, upper=None)
    return Cardinality(lower=lower, upper=upper)


@dataclass
class _Node:
    """A schema component together with the schema that declares it."""

    obj: object
    schema: xsd.Schema
    tag: str


class _Resolver:
    """Walks xsdata Schema dataclasses and builds the OcxSchema model."""

    def __init__(self, schemas: list[xsd.Schema]):
        if not schemas:
            raise OcxParserError("No schemas to resolve")
        self.schemas = schemas
        self.elements: dict[str, _Node] = {}
        self.complex_types: dict[str, _Node] = {}
        self.simple_types: dict[str, _Node] = {}
        self.global_attributes: dict[str, _Node] = {}
        self.attribute_groups: dict[str, _Node] = {}
        self.groups: dict[str, _Node] = {}
        self.namespaces: dict[str, str] = {}
        self.uri_to_prefix: dict[str, str] = {}
        self.substitution_groups: dict[str, list[str]] = {}
        self._unresolved: set[str] = set()
        self._index()

    # ------------------------------------------------------------- index
    def _index(self) -> None:
        for schema in self.schemas:
            tns = schema.target_namespace or ""
            for prefix, uri in (schema.ns_map or {}).items():
                if prefix and prefix not in self.namespaces:
                    self.namespaces[prefix] = uri
                if prefix:
                    self.uri_to_prefix.setdefault(uri, prefix)

            def add(store: dict[str, _Node], items) -> None:
                for item in items:
                    if item.name:
                        store[f"{{{tns}}}{item.name}"] = _Node(item, schema, f"{{{tns}}}{item.name}")

            add(self.elements, schema.elements)
            add(self.complex_types, schema.complex_types)
            add(self.simple_types, schema.simple_types)
            add(self.global_attributes, schema.attributes)
            add(self.attribute_groups, schema.attribute_groups)
            add(self.groups, schema.groups)

    # -------------------------------------------------------- references
    def qref(self, ref: str, schema: xsd.Schema) -> str:
        """Resolve a ``prefix:Name`` reference to a ``{uri}Name`` tag."""
        prefix, _, local = ref.rpartition(":")
        ns_map = schema.ns_map or {}
        if prefix and prefix in ns_map:
            return f"{{{ns_map[prefix]}}}{local}"
        if not prefix and schema.target_namespace:
            return f"{{{schema.target_namespace}}}{local}"
        return f"{{{prefix}}}{local}" if prefix else local

    def prefixed(self, tag: str) -> str:
        """Convert a ``{uri}Name`` tag to ``prefix:Name``."""
        if not tag.startswith("{"):
            return tag
        uri, _, local = tag[1:].partition("}")
        prefix = self.uri_to_prefix.get(uri)
        return f"{prefix}:{local}" if prefix else local

    def split(self, tag: str) -> tuple[str, str]:
        """Return (prefix, local_name) for a ``{uri}Name`` tag."""
        prefixed = self.prefixed(tag)
        prefix, _, local = prefixed.rpartition(":")
        return prefix, local

    def is_builtin(self, tag: str) -> bool:
        """True if the tag belongs to an XSD built-in namespace."""
        if not tag.startswith("{"):
            return False
        uri = tag[1:].partition("}")[0]
        return uri in BUILTIN_NAMESPACES

    def _missing(self, tag: str, kind: str) -> None:
        """Log an unresolved reference once."""
        if tag not in self._unresolved:
            self._unresolved.add(tag)
            logger.warning(f"Unresolved {kind} reference: {tag}")
