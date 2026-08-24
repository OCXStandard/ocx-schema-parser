"""Typed, immutable data model of a resolved OCX schema (Pydantic v2)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict


class FrozenModel(BaseModel):
    """Base model: immutable after construction."""

    model_config = ConfigDict(frozen=True)


class Cardinality(FrozenModel):
    """Occurrence bounds of an element. ``upper=None`` means unbounded."""

    lower: int
    upper: Optional[int]

    def __str__(self) -> str:
        upper = "\u221e" if self.upper is None else str(self.upper)
        return f"[{self.lower}, {upper}]"


class Attribute(FrozenModel):
    """A resolved XML attribute of a global element or complex type."""

    name: str
    prefix: str
    type: str
    use: Literal["required", "optional"] = "optional"
    default: Optional[str] = None
    fixed: Optional[str] = None
    description: str = ""


class ChildElement(FrozenModel):
    """A resolved child element (particle) of a global element or complex type."""

    name: str
    prefix: str
    type: str
    cardinality: Cardinality
    is_choice: bool = False
    from_substitution_group: Optional[str] = None  # prefixed head tag when expanded
    inherited_from: Optional[str] = None
    description: str = ""


class GlobalElement(FrozenModel):
    """A global element declaration with its fully flattened content model."""

    name: str
    prefix: str
    tag: str
    type: str
    abstract: bool = False
    cardinality: Cardinality
    description: str = ""
    parents: list[str] = []
    attributes: list[Attribute] = []
    children: list[ChildElement] = []
    substitution_group: Optional[str] = None


class ComplexType(FrozenModel):
    """A named complex type declared in the schema."""

    name: str
    prefix: str
    tag: str
    abstract: bool = False
    description: str = ""
    parents: list[str] = []
    attributes: list[Attribute] = []
    children: list[ChildElement] = []


class EnumValue(FrozenModel):
    """One enumeration facet value."""

    value: str
    description: str = ""


class EnumType(FrozenModel):
    """A simple type restricted to an enumeration."""

    name: str
    prefix: str
    tag: str
    description: str = ""
    values: list[EnumValue] = []


class SimpleType(FrozenModel):
    """A non-enumeration simple type with its restriction facets."""

    name: str
    prefix: str
    tag: str
    base: str
    description: str = ""
    restriction: dict[str, str] = {}


class SchemaChange(FrozenModel):
    """A SchemaChange appinfo record."""

    version: str
    author: str = ""
    date: str = ""
    description: str = ""


class OcxSchema(FrozenModel):
    """The fully resolved OCX schema."""

    schema_version: str
    target_namespace: str
    namespaces: dict[str, str]
    elements: list[GlobalElement] = []
    complex_types: list[ComplexType] = []
    enumerations: list[EnumType] = []
    simple_types: list[SimpleType] = []
    attribute_groups: dict[str, list[Attribute]] = {}
    substitution_groups: dict[str, list[str]] = {}
    schema_changes: list[SchemaChange] = []

    def get(self, name: str) -> Optional[GlobalElement]:
        """Look up a global element by ``name`` or ``prefix:name``."""
        _, _, local = name.rpartition(":")
        for element in self.elements:
            if element.name == local:
                return element
        return None
