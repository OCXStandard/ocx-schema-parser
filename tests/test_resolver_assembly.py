"""Tests for enum/simple-type extraction, schema changes, and resolve()."""

import pytest
from conftest import parse_fragment

from ocx_schema_parser.errors import OcxParserError
from ocx_schema_parser.model import OcxSchema
from ocx_schema_parser.resolver import resolve

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:annotation>
    <xs:appinfo>
      <SchemaChange version="1.1.0" author="OCX" date="2023-01-01">
        <Description>Added Thing.</Description>
      </SchemaChange>
    </xs:appinfo>
  </xs:annotation>
  <xs:element name="Thing" type="t:Thing_T"/>
  <xs:complexType name="Thing_T">
    <xs:attribute ref="t:schemaVersion" use="required"/>
  </xs:complexType>
  <xs:complexType name="Orphan_T">
    <xs:annotation><xs:documentation>No global element uses me.</xs:documentation></xs:annotation>
  </xs:complexType>
  <xs:attribute name="schemaVersion" type="xs:string" fixed="9.9.9"/>
  <xs:attribute name="liquidCargoType">
    <xs:annotation><xs:documentation>Inline enum on a global attribute.</xs:documentation></xs:annotation>
    <xs:simpleType>
      <xs:restriction base="xs:string">
        <xs:enumeration value="crude oil"/>
        <xs:enumeration value="diesel oil"/>
      </xs:restriction>
    </xs:simpleType>
  </xs:attribute>
  <xs:simpleType name="functionType">
    <xs:restriction base="xs:string">
      <xs:enumeration value="cargo oil"/>
      <xs:enumeration value="ballast"/>
    </xs:restriction>
  </xs:simpleType>
  <xs:simpleType name="guid">
    <xs:restriction base="xs:string">
      <xs:pattern value="[0-9a-f]+"/>
      <xs:minLength value="8"/>
    </xs:restriction>
  </xs:simpleType>
</xs:schema>
"""


@pytest.fixture(scope="module")
def model() -> OcxSchema:
    return resolve([parse_fragment(FRAGMENT)])


def test_resolve_empty_raises():
    with pytest.raises(OcxParserError):
        resolve([])


def test_schema_version_from_fixed_attribute(model):
    assert model.schema_version == "9.9.9"


def test_target_namespace(model):
    assert model.target_namespace == "urn:test"


def test_enumerations(model):
    enums = {e.name: e for e in model.enumerations}
    assert [v.value for v in enums["functionType"].values] == ["ballast", "cargo oil"]


def test_enumeration_inline_on_global_attribute(model):
    enums = {e.name: e for e in model.enumerations}
    enum = enums["liquidCargoType"]
    assert [v.value for v in enum.values] == ["crude oil", "diesel oil"]
    assert enum.description == "Inline enum on a global attribute."


def test_simple_type_facets(model):
    st = {s.name: s for s in model.simple_types}["guid"]
    assert st.base == "xs:string"
    assert st.restriction["pattern"] == "[0-9a-f]+"
    assert st.restriction["min_length"] == "8"


def test_schema_changes(model):
    change = model.schema_changes[0]
    assert change.version == "1.1.0"
    assert change.author == "OCX"
    assert change.description == "Added Thing."


def test_all_named_complex_types_documented(model):
    names = [ct.name for ct in model.complex_types]
    assert "Orphan_T" in names
    assert "Thing_T" in names  # included even though global element Thing uses it


def test_global_element(model):
    thing = model.get("t:Thing")
    assert thing is not None
    assert thing.type == "t:Thing_T"
    assert thing.cardinality.lower == 1 and thing.cardinality.upper == 1
    attrs = {a.name: a for a in thing.attributes}
    assert attrs["schemaVersion"].fixed == "9.9.9"


def test_resolve_full_ocx_schema(ocx_model):
    assert ocx_model.schema_version == "3.0.0"
    assert (
        ocx_model.target_namespace
        == "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    )
    assert ocx_model.get("ocx:Vessel") is not None
    assert len(ocx_model.elements) > 300
    assert len(ocx_model.enumerations) > 0
    assert len(ocx_model.substitution_groups) > 0
    names = [e.name for e in ocx_model.elements]
    assert names == sorted(names)
