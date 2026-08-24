"""Tests for the Pydantic schema model."""

import pytest
from pydantic import ValidationError

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import (
    Attribute,
    Cardinality,
    ChildElement,
    EnumType,
    EnumValue,
    GlobalElement,
    OcxSchema,
    SchemaChange,
    SimpleType,
)


def test_error_is_exception():
    assert issubclass(OcxParserError, Exception)


def test_cardinality_str():
    assert str(Cardinality(lower=1, upper=1)) == "[1, 1]"
    assert str(Cardinality(lower=0, upper=None)) == "[0, \u221e]"


def test_models_are_frozen():
    card = Cardinality(lower=1, upper=1)
    with pytest.raises(ValidationError):
        card.lower = 2


def test_attribute_defaults():
    attr = Attribute(name="id", prefix="ocx", type="xs:ID")
    assert attr.use == "optional"
    assert attr.default is None
    assert attr.fixed is None
    assert attr.description == ""


def test_child_element_defaults():
    child = ChildElement(
        name="Point3D",
        prefix="ocx",
        type="ocx:Point3D_T",
        cardinality=Cardinality(lower=1, upper=1),
    )
    assert child.is_choice is False
    assert child.from_substitution_group is None
    assert child.inherited_from is None


def test_ocx_schema_get_by_name():
    elem = GlobalElement(
        name="Vessel",
        prefix="ocx",
        tag="{urn:test}Vessel",
        type="ocx:Vessel_T",
        cardinality=Cardinality(lower=1, upper=1),
    )
    schema = OcxSchema(
        schema_version="3.0.0",
        target_namespace="urn:test",
        namespaces={"ocx": "urn:test"},
        elements=[elem],
    )
    assert schema.get("Vessel") is elem
    assert schema.get("ocx:Vessel") is elem
    assert schema.get("NoSuchElement") is None


def test_schema_serializes_to_json():
    schema = OcxSchema(
        schema_version="3.0.0", target_namespace="urn:test", namespaces={}
    )
    data = schema.model_dump_json()
    assert '"schema_version":"3.0.0"' in data


def test_enum_and_simple_type():
    enum = EnumType(
        name="functionType",
        prefix="ocx",
        tag="{urn:test}functionType",
        values=[EnumValue(value="cargo oil", description="")],
    )
    assert enum.values[0].value == "cargo oil"
    st = SimpleType(
        name="guid",
        prefix="ocx",
        tag="{urn:test}guid",
        base="xs:string",
        restriction={"pattern": r"\{.*\}"},
    )
    assert st.restriction["pattern"] == r"\{.*\}"


def test_schema_change():
    change = SchemaChange(
        version="3.0.0", author="OCX", date="2023-01-01", description="Initial"
    )
    assert change.version == "3.0.0"
