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


def _multiply_cardinality(left: Cardinality, right: Cardinality) -> Cardinality:
    """Multiply nested occurrence bounds; ``upper=None`` means unbounded."""
    if left.upper is None or right.upper is None:
        upper = None
    else:
        product = left.upper * right.upper
        upper = None if product >= UNBOUNDED else product
    return Cardinality(lower=left.lower * right.lower, upper=upper)


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


_FACET_FIELDS = (
    "min_exclusive",
    "min_inclusive",
    "max_exclusive",
    "max_inclusive",
    "total_digits",
    "fraction_digits",
    "length",
    "min_length",
    "max_length",
    "white_space",
)


def _facets(restriction: xsd.Restriction) -> dict[str, str]:
    """Extract non-enumeration facets of a restriction as a name->value dict."""
    result: dict[str, str] = {}
    for field in _FACET_FIELDS:
        facet = getattr(restriction, field, None)
        if facet is not None and facet.value is not None:
            result[field] = str(facet.value)
    if restriction.patterns:
        result["pattern"] = "|".join(p.value for p in restriction.patterns if p.value)
    return result


def _schema_changes_from(element) -> list[SchemaChange]:
    """Recursively collect SchemaChange records from an appinfo AnyElement tree."""
    result: list[SchemaChange] = []
    qname = getattr(element, "qname", None) or ""
    if qname.endswith("SchemaChange"):
        attrs = getattr(element, "attributes", {}) or {}
        description = ""
        for child in getattr(element, "children", []) or []:
            child_qname = getattr(child, "qname", None) or ""
            if child_qname.endswith("Description") and getattr(child, "text", None):
                description = child.text.strip()
        result.append(
            SchemaChange(
                version=attrs.get("version", ""),
                author=attrs.get("author", ""),
                date=attrs.get("date", ""),
                description=description,
            )
        )
    for child in getattr(element, "children", []) or []:
        result.extend(_schema_changes_from(child))
    return result


@dataclass
class _Node:
    """A schema component together with the schema that declares it."""

    obj: object
    schema: xsd.Schema
    tag: str


@dataclass
class _ExpandedAttributes:
    """Expanded attributes plus prohibited names that shadow ancestors."""

    attributes: list[Attribute]
    prohibited: set[str]


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
                        store[f"{{{tns}}}{item.name}"] = _Node(
                            item, schema, f"{{{tns}}}{item.name}"
                        )

            add(self.elements, schema.elements)
            add(self.complex_types, schema.complex_types)
            add(self.simple_types, schema.simple_types)
            add(self.global_attributes, schema.attributes)
            add(self.attribute_groups, schema.attribute_groups)
            add(self.groups, schema.groups)

        for schema in self.schemas:
            for element in schema.elements:
                if element.substitution_group and element.name:
                    head = self.qref(element.substitution_group, schema)
                    tag = f"{{{schema.target_namespace or ''}}}{element.name}"
                    self.substitution_groups.setdefault(head, []).append(tag)
        for head in self.substitution_groups:
            self.substitution_groups[head].sort()

    # -------------------------------------------------------- references
    def qref(self, ref: str, schema: xsd.Schema) -> str:
        """Resolve a ``prefix:Name`` reference to a ``{uri}Name`` tag."""
        prefix, _, local = ref.rpartition(":")
        ns_map = schema.ns_map or {}
        if prefix and prefix in ns_map:
            return f"{{{ns_map[prefix]}}}{local}"
        if not prefix and None in ns_map:
            return f"{{{ns_map[None]}}}{local}"
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
    def _make_attribute(
        self, attr: xsd.Attribute, schema: xsd.Schema
    ) -> Optional[Attribute]:
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
        inline = attr.simple_type
        restriction = inline.restriction if inline is not None else None
        if type_ref is None and restriction is not None:
            if restriction.enumerations:
                # Inline enum: point at the synthesized EnumType instead of the base.
                type_name = self.prefixed(
                    f"{{{schema.target_namespace or ''}}}{attr.name}"
                )
            else:
                base = restriction.base
                type_name = (
                    self.prefixed(self.qref(base, schema)) if base else "xs:string"
                )
        else:
            type_name = (
                self.prefixed(self.qref(type_ref, schema)) if type_ref else "xs:string"
            )
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

    def _prohibited_attribute_name(
        self, attr: xsd.Attribute, schema: xsd.Schema
    ) -> Optional[str]:
        """Return the local attribute name if this declaration prohibits it."""
        use = attr.use.value if attr.use is not None else "optional"
        if use != "prohibited":
            return None
        if attr.name:
            return attr.name
        if attr.ref:
            _, local = self.split(self.qref(attr.ref, schema))
            return local
        return None

    def _expand_attributes(
        self, holder, schema: xsd.Schema, seen_groups: set[str]
    ) -> _ExpandedAttributes:
        """Collect attributes on ``holder``, expanding attributeGroup refs recursively."""
        result: list[Attribute] = []
        prohibited: set[str] = set()
        for attr in getattr(holder, "attributes", []) or []:
            prohibited_name = self._prohibited_attribute_name(attr, schema)
            if prohibited_name is not None:
                prohibited.add(prohibited_name)
                continue
            made = self._make_attribute(attr, schema)
            if made is not None:
                result.append(made)
        for group in getattr(holder, "attribute_groups", []) or []:
            ref = group.ref or group.name
            if not ref:
                continue
            tag = (
                self.qref(ref, schema)
                if group.ref
                else f"{{{schema.target_namespace}}}{group.name}"
            )
            if tag in seen_groups:
                continue
            seen_groups.add(tag)
            node = self.attribute_groups.get(tag)
            if node is None:
                self._missing(tag, "attribute group")
                continue
            expanded = self._expand_attributes(node.obj, node.schema, seen_groups)
            result.extend(expanded.attributes)
            prohibited.update(expanded.prohibited)
        return _ExpandedAttributes(result, prohibited)

    def attributes_of(self, type_tag: str) -> list[Attribute]:
        """All attributes of a complex type, own + inherited, nearest wins, sorted by name."""
        merged: dict[str, Attribute] = {}
        prohibited: set[str] = set()
        for tag in [type_tag, *self.ancestors(type_tag)]:
            node = self.complex_types.get(tag)
            if node is None:
                continue
            for holder in _attribute_holders(node.obj):
                expanded = self._expand_attributes(holder, node.schema, set())
                for name in expanded.prohibited:
                    if name not in merged:
                        prohibited.add(name)
                for attr in expanded.attributes:
                    if attr.name not in merged and attr.name not in prohibited:
                        merged[attr.name] = attr  # nearest definition wins
        return sorted(merged.values(), key=lambda a: a.name)

    # ---------------------------------------------------------- children
    def _make_children(
        self,
        element: xsd.Element,
        schema: xsd.Schema,
        is_choice: bool,
        occurrence_factor: Cardinality,
    ) -> list[ChildElement]:
        """Build ChildElement(s) for one particle; expands abstract substitution heads."""
        card = _multiply_cardinality(occurrence_factor, _cardinality(element))
        if element.ref:
            tag = self.qref(element.ref, schema)
            node = self.elements.get(tag)
            if node is None:
                self._missing(tag, "element")
                return []
            target: xsd.Element = node.obj
            members = self.substitution_groups.get(tag, [])
            if target.abstract and members:
                head_prefixed = self.prefixed(tag)
                result = []
                for member_tag in members:
                    member = self.elements.get(member_tag)
                    if member is None:
                        continue
                    prefix, local = self.split(member_tag)
                    type_ref = member.obj.type
                    type_name = (
                        self.prefixed(self.qref(type_ref, member.schema))
                        if type_ref
                        else local
                    )
                    result.append(
                        ChildElement(
                            name=local,
                            prefix=prefix,
                            type=type_name,
                            cardinality=card,
                            is_choice=is_choice,
                            from_substitution_group=head_prefixed,
                            description=_description(member.obj),
                        )
                    )
                return result
            prefix, local = self.split(tag)
            type_name = (
                self.prefixed(self.qref(target.type, node.schema))
                if target.type
                else local
            )
            return [
                ChildElement(
                    name=local,
                    prefix=prefix,
                    type=type_name,
                    cardinality=card,
                    is_choice=is_choice,
                    description=_description(target),
                )
            ]
        # local (inline) element declaration
        prefix, _ = self.split(f"{{{schema.target_namespace or ''}}}{element.name}")
        type_name = (
            self.prefixed(self.qref(element.type, schema))
            if element.type
            else (element.name or "")
        )
        return [
            ChildElement(
                name=element.name or "",
                prefix=prefix,
                type=type_name,
                cardinality=card,
                is_choice=is_choice,
                description=_description(element),
            )
        ]

    def _collect_particles(
        self,
        container,
        schema: xsd.Schema,
        is_choice: bool,
        seen_groups: set[str],
        occurrence_factor: Optional[Cardinality] = None,
    ) -> list[ChildElement]:
        """Recursively walk a sequence/choice/all container collecting children."""
        if container is None:
            return []
        effective_occurs = _multiply_cardinality(
            occurrence_factor or Cardinality(lower=1, upper=1),
            _cardinality(container),
        )
        result: list[ChildElement] = []
        for element in getattr(container, "elements", []) or []:
            result.extend(
                self._make_children(element, schema, is_choice, effective_occurs)
            )
        for group in getattr(container, "groups", []) or []:
            result.extend(
                self._collect_group(
                    group, schema, is_choice, seen_groups, effective_occurs
                )
            )
        for choice in getattr(container, "choices", []) or []:
            result.extend(
                self._collect_particles(
                    choice, schema, True, seen_groups, effective_occurs
                )
            )
        for sequence in getattr(container, "sequences", []) or []:
            result.extend(
                self._collect_particles(
                    sequence, schema, is_choice, seen_groups, effective_occurs
                )
            )
        return result

    def _collect_group(
        self,
        group: xsd.Group,
        schema: xsd.Schema,
        is_choice: bool,
        seen_groups: set[str],
        occurrence_factor: Optional[Cardinality] = None,
    ) -> list[ChildElement]:
        """Resolve a named model group (possibly a ref) and collect its particles."""
        effective_occurs = _multiply_cardinality(
            occurrence_factor or Cardinality(lower=1, upper=1),
            _cardinality(group),
        )
        if group.ref:
            tag = self.qref(group.ref, schema)
            if tag in seen_groups:
                return []
            seen_groups.add(tag)
            node = self.groups.get(tag)
            if node is None:
                self._missing(tag, "group")
                return []
            return self._collect_group(
                node.obj, node.schema, is_choice, seen_groups, effective_occurs
            )
        result: list[ChildElement] = []
        result.extend(
            self._collect_particles(
                group.sequence, schema, is_choice, seen_groups, effective_occurs
            )
        )
        result.extend(
            self._collect_particles(
                group.choice, schema, True, seen_groups, effective_occurs
            )
        )
        result.extend(
            self._collect_particles(
                group.all, schema, is_choice, seen_groups, effective_occurs
            )
        )
        return result

    def _own_children(
        self, ct: xsd.ComplexType, schema: xsd.Schema
    ) -> list[ChildElement]:
        """Children declared directly on a complex type (incl. its derivation content)."""
        result: list[ChildElement] = []
        containers = [(ct.sequence, False), (ct.all, False), (ct.choice, True)]
        if ct.group is not None:
            result.extend(self._collect_group(ct.group, schema, False, set()))
        for content in (ct.complex_content, ct.simple_content):
            if content is None:
                continue
            for derivation in (content.extension, content.restriction):
                if derivation is None:
                    continue
                containers.extend(
                    [
                        (getattr(derivation, "sequence", None), False),
                        (getattr(derivation, "all", None), False),
                        (getattr(derivation, "choice", None), True),
                    ]
                )
                group = getattr(derivation, "group", None)
                if group is not None:
                    result.extend(self._collect_group(group, schema, False, set()))
        for container, is_choice in containers:
            result.extend(self._collect_particles(container, schema, is_choice, set()))
        return result

    def children_of(self, type_tag: str) -> list[ChildElement]:
        """All children of a complex type: own first (declaration order), then inherited."""
        merged: dict[str, ChildElement] = {}
        result: list[ChildElement] = []
        for tag in [type_tag, *self.ancestors(type_tag)]:
            node = self.complex_types.get(tag)
            if node is None:
                continue
            inherited_from = self.prefixed(tag) if tag != type_tag else None
            for child in self._own_children(node.obj, node.schema):
                if child.name in merged:
                    continue  # nearest definition wins
                if inherited_from is not None:
                    child = child.model_copy(update={"inherited_from": inherited_from})
                merged[child.name] = child
                result.append(child)
        return result

    # ----------------------------------------------------------- assembly
    def _main_schema(self) -> xsd.Schema:
        """The schema declaring the fixed ``schemaVersion`` attribute; else the first.

        Checks top-level attributes first, then complex types within each schema.
        Priority: top-level match > complex-type match (within same schema) > first schema.
        """
        # First pass: check top-level schemaVersion attributes
        for schema in self.schemas:
            for attr in schema.attributes:
                if attr.name == "schemaVersion" and attr.fixed:
                    return schema

        # Second pass: check complex type attributes (only from their declaring schema)
        for schema in self.schemas:
            for tag, node in self.complex_types.items():
                if node.schema is not schema:
                    continue
                for attr in self.attributes_of(tag):
                    if attr.name == "schemaVersion" and attr.fixed:
                        return schema

        return self.schemas[0]

    def _schema_version(self) -> str:
        """The fixed ``schemaVersion`` attribute from the main schema.

        Checks top-level attributes first, then complex types within the main schema.
        """
        main_schema = self._main_schema()

        # First check top-level attributes of main schema
        for attr in main_schema.attributes:
            if attr.name == "schemaVersion" and attr.fixed:
                return attr.fixed

        # Then check complex type attributes from main schema
        for tag, node in self.complex_types.items():
            if node.schema is not main_schema:
                continue
            for attr in self.attributes_of(tag):
                if attr.name == "schemaVersion" and attr.fixed:
                    return attr.fixed

        return ""

    def _type_tag_of(self, node: _Node) -> Optional[str]:
        """Tag of the (named or inline) complex type of a global element."""
        element: xsd.Element = node.obj
        if element.type:
            return self.qref(element.type, node.schema)
        return None

    def _build_element(self, node: _Node) -> GlobalElement:
        element: xsd.Element = node.obj
        prefix, local = self.split(node.tag)
        type_tag = self._type_tag_of(node)
        if type_tag is not None:
            type_name = self.prefixed(type_tag)
            parents = [self.prefixed(t) for t in self.ancestors(type_tag)]
            attributes = self.attributes_of(type_tag)
            children = self.children_of(type_tag)
        elif element.complex_type is not None:
            # inline anonymous complex type: resolve its own content + base ancestry
            ct = element.complex_type
            type_name = local
            base_ref = _base_ref(ct)
            base_tag = self.qref(base_ref, node.schema) if base_ref else None
            parents = (
                [
                    self.prefixed(base_tag),
                    *(self.prefixed(t) for t in self.ancestors(base_tag)),
                ]
                if base_tag and not self.is_builtin(base_tag)
                else []
            )
            own_attrs: dict[str, Attribute] = {}
            prohibited_attrs: set[str] = set()
            for holder in _attribute_holders(ct):
                expanded = self._expand_attributes(holder, node.schema, set())
                for name in expanded.prohibited:
                    if name not in own_attrs:
                        prohibited_attrs.add(name)
                for attr in expanded.attributes:
                    if attr.name not in own_attrs and attr.name not in prohibited_attrs:
                        own_attrs[attr.name] = attr
            inherited = (
                {
                    a.name: a
                    for a in self.attributes_of(base_tag)
                    if a.name not in prohibited_attrs
                }
                if base_tag and base_tag in self.complex_types
                else {}
            )
            attributes = sorted(
                {**inherited, **own_attrs}.values(), key=lambda a: a.name
            )
            children = self._own_children(ct, node.schema)
            if base_tag and base_tag in self.complex_types:
                own_names = {c.name for c in children}
                for child in self.children_of(base_tag):
                    if child.name not in own_names:
                        children.append(
                            child.model_copy(
                                update={"inherited_from": self.prefixed(base_tag)}
                            )
                        )
        else:
            type_name = (
                self.prefixed(self.qref(element.type, node.schema))
                if element.type
                else local
            )
            parents, attributes, children = [], [], []
        substitution = (
            self.prefixed(self.qref(element.substitution_group, node.schema))
            if element.substitution_group
            else None
        )
        return GlobalElement(
            name=local,
            prefix=prefix,
            tag=node.tag,
            type=type_name,
            abstract=bool(element.abstract),
            cardinality=Cardinality(lower=1, upper=1),
            description=_description(element),
            parents=parents,
            attributes=attributes,
            children=children,
            substitution_group=substitution,
        )

    def _build_complex_types(self) -> list[ComplexType]:
        """All named complex types declared in the schemas."""
        result = []
        for tag, node in self.complex_types.items():
            prefix, local = self.split(tag)
            result.append(
                ComplexType(
                    name=local,
                    prefix=prefix,
                    tag=tag,
                    abstract=bool(node.obj.abstract),
                    description=_description(node.obj),
                    parents=[self.prefixed(t) for t in self.ancestors(tag)],
                    attributes=self.attributes_of(tag),
                    children=self.children_of(tag),
                )
            )
        return sorted(result, key=lambda ct: ct.name)

    def _build_simple_types(self) -> tuple[list[EnumType], list[SimpleType]]:
        """Named simple types plus enums inlined on global attributes."""
        enums: list[EnumType] = []
        simple: list[SimpleType] = []
        for tag, node in self.simple_types.items():
            st: xsd.SimpleType = node.obj
            prefix, local = self.split(tag)
            restriction = st.restriction
            if restriction is None:
                continue
            if restriction.enumerations:
                values = sorted(
                    (
                        EnumValue(value=e.value or "", description=_description(e))
                        for e in restriction.enumerations
                    ),
                    key=lambda v: v.value,
                )
                enums.append(
                    EnumType(
                        name=local,
                        prefix=prefix,
                        tag=tag,
                        description=_description(st),
                        values=values,
                    )
                )
            else:
                base = (
                    self.prefixed(self.qref(restriction.base, node.schema))
                    if restriction.base
                    else "xs:string"
                )
                simple.append(
                    SimpleType(
                        name=local,
                        prefix=prefix,
                        tag=tag,
                        base=base,
                        description=_description(st),
                        restriction=_facets(restriction),
                    )
                )
        enums.extend(self._build_attribute_enums({e.tag for e in enums}))
        return (
            sorted(enums, key=lambda e: e.name),
            sorted(simple, key=lambda s: s.name),
        )

    def _inline_enum_attributes(self) -> list[tuple[str, xsd.Attribute]]:
        """(tag, attribute) pairs for attributes carrying an inline enumeration."""

        def candidates():
            for node in self.global_attributes.values():
                yield node.obj, node.schema
            for node in self.attribute_groups.values():
                for attr in node.obj.attributes:
                    yield attr, node.schema
            for node in self.complex_types.values():
                for holder in _attribute_holders(node.obj):
                    for attr in getattr(holder, "attributes", []) or []:
                        yield attr, node.schema

        result = []
        for attr, schema in candidates():
            inline = attr.simple_type
            restriction = inline.restriction if inline is not None else None
            if attr.name and restriction is not None and restriction.enumerations:
                tag = f"{{{schema.target_namespace or ''}}}{attr.name}"
                result.append((tag, attr))
        return result

    def _build_attribute_enums(self, taken: set[str]) -> list[EnumType]:
        """Enums declared as anonymous simple types on attributes.

        Covers global attributes plus local attributes declared inside
        attribute groups and complex types.
        """
        result: list[EnumType] = []
        for tag, attribute in self._inline_enum_attributes():
            if tag in taken:
                continue
            taken.add(tag)
            inline = attribute.simple_type
            restriction = inline.restriction
            prefix, local = self.split(tag)
            values = sorted(
                (
                    EnumValue(value=e.value or "", description=_description(e))
                    for e in restriction.enumerations
                ),
                key=lambda v: v.value,
            )
            description = _description(attribute) or _description(inline)
            result.append(
                EnumType(
                    name=local,
                    prefix=prefix,
                    tag=tag,
                    description=description,
                    values=values,
                )
            )
        return result

    def _build_attribute_groups(self) -> dict[str, list[Attribute]]:
        result = {}
        for tag, node in self.attribute_groups.items():
            _, local = self.split(tag)
            expanded = self._expand_attributes(node.obj, node.schema, {tag})
            result[local] = sorted(
                {a.name: a for a in expanded.attributes}.values(),
                key=lambda a: a.name,
            )
        return dict(sorted(result.items()))

    def _build_schema_changes(self) -> list[SchemaChange]:
        result: list[SchemaChange] = []
        for schema in self.schemas:
            for annotation in schema.annotations:
                for appinfo in annotation.app_infos:
                    for item in appinfo.content:
                        result.extend(_schema_changes_from(item))
        return result

    def build(self) -> OcxSchema:
        elements = sorted(
            (self._build_element(node) for node in self.elements.values()),
            key=lambda e: e.name,
        )
        enums, simple = self._build_simple_types()
        return OcxSchema(
            schema_version=self._schema_version(),
            target_namespace=self._main_schema().target_namespace or "",
            namespaces=dict(sorted(self.namespaces.items())),
            elements=elements,
            complex_types=self._build_complex_types(),
            enumerations=enums,
            simple_types=simple,
            attribute_groups=self._build_attribute_groups(),
            substitution_groups={
                self.prefixed(head): [self.prefixed(m) for m in members]
                for head, members in sorted(self.substitution_groups.items())
            },
            schema_changes=self._build_schema_changes(),
        )


def resolve(schemas: list[xsd.Schema]) -> OcxSchema:
    """Resolve parsed schemas into the immutable OcxSchema model.

    Raises:
        OcxParserError: If ``schemas`` is empty.
    """
    if not schemas:
        raise OcxParserError("No schemas to resolve.")
    return _Resolver(schemas).build()
