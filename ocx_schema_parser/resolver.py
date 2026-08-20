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


def _base_ref(ct: xsd.ComplexType) -> Optional[str]:
    """Return the base type reference of a complex type's derivation, if any."""
    for content in (ct.complex_content, ct.simple_content):
        if content is None:
            continue
        derivation = content.extension or content.restriction
        if derivation is not None and derivation.base:
            return derivation.base
    return None


def _attribute_holders(ct: xsd.ComplexType) -> list:
    """Return the objects on ``ct`` that may carry attributes/attribute_groups."""
    holders = [ct]
    for content in (ct.complex_content, ct.simple_content):
        if content is None:
            continue
        for derivation in (content.extension, content.restriction):
            if derivation is not None:
                holders.append(derivation)
    return holders


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

    # ---------------------------------------------------------- ancestry
    def ancestors(self, type_tag: str) -> list[str]:
        """Base-type chain of a complex type, nearest first, builtins excluded."""
        result: list[str] = []
        seen = {type_tag}
        current = type_tag
        while True:
            node = self.complex_types.get(current)
            if node is None:
                break
            base_ref = _base_ref(node.obj)
            if base_ref is None:
                break
            base_tag = self.qref(base_ref, node.schema)
            if self.is_builtin(base_tag) or base_tag in seen:
                break
            if base_tag not in self.complex_types:
                if base_tag not in self.simple_types:
                    self._missing(base_tag, "base type")
                break
            seen.add(base_tag)
            result.append(base_tag)
            current = base_tag
        return result

    # -------------------------------------------------------- attributes
    def _make_attribute(self, attr: xsd.Attribute, schema: xsd.Schema) -> Optional[Attribute]:
        """Build an Attribute model; resolve refs; skip prohibited. None if skipped."""
        if attr.ref:
            tag = self.qref(attr.ref, schema)
            node = self.global_attributes.get(tag)
            if node is None:
                self._missing(tag, "attribute")
                return None
            return self._make_attribute(node.obj, node.schema)
        use = attr.use.value if attr.use is not None else "optional"
        if use == "prohibited":
            return None
        type_ref = attr.type
        if type_ref is None and attr.simple_type is not None and attr.simple_type.restriction:
            type_ref = attr.simple_type.restriction.base
        type_name = self.prefixed(self.qref(type_ref, schema)) if type_ref else "xs:string"
        prefix, _ = self.split(f"{{{schema.target_namespace or ''}}}{attr.name}")
        return Attribute(
            name=attr.name or "",
            prefix=prefix,
            type=type_name,
            use=use,
            default=attr.default,
            fixed=attr.fixed,
            description=_description(attr),
        )

    def _expand_attributes(self, holder, schema: xsd.Schema, seen_groups: set[str]) -> list[Attribute]:
        """Collect attributes on ``holder``, expanding attributeGroup refs recursively."""
        result: list[Attribute] = []
        for attr in getattr(holder, "attributes", []) or []:
            made = self._make_attribute(attr, schema)
            if made is not None:
                result.append(made)
        for group in getattr(holder, "attribute_groups", []) or []:
            ref = group.ref or group.name
            if not ref:
                continue
            tag = self.qref(ref, schema) if group.ref else f"{{{schema.target_namespace}}}{group.name}"
            if tag in seen_groups:
                continue
            seen_groups.add(tag)
            node = self.attribute_groups.get(tag)
            if node is None:
                self._missing(tag, "attribute group")
                continue
            result.extend(self._expand_attributes(node.obj, node.schema, seen_groups))
        return result

    def attributes_of(self, type_tag: str) -> list[Attribute]:
        """All attributes of a complex type, own + inherited, nearest wins, sorted by name."""
        merged: dict[str, Attribute] = {}
        for tag in [type_tag, *self.ancestors(type_tag)]:
            node = self.complex_types.get(tag)
            if node is None:
                continue
            for holder in _attribute_holders(node.obj):
                for attr in self._expand_attributes(holder, node.schema, set()):
                    merged.setdefault(attr.name, attr)  # nearest definition wins
        return sorted(merged.values(), key=lambda a: a.name)

