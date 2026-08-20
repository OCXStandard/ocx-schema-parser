"""Tests for type ancestry and attribute flattening."""
from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:attributeGroup name="idGroup">
    <xs:attribute name="id" type="xs:ID" use="required">
      <xs:annotation><xs:documentation>Unique id.</xs:documentation></xs:annotation>
    </xs:attribute>
    <xs:attribute name="secret" type="xs:string" use="prohibited"/>
  </xs:attributeGroup>
  <xs:complexType name="Base_T">
    <xs:attribute name="name" type="xs:string" default="unnamed"/>
    <xs:attributeGroup ref="t:idGroup"/>
  </xs:complexType>
  <xs:complexType name="Middle_T">
    <xs:complexContent>
      <xs:extension base="t:Base_T">
        <xs:attribute name="version" type="xs:string" fixed="3.0.0"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
  <xs:complexType name="Leaf_T">
    <xs:complexContent>
      <xs:extension base="t:Middle_T">
        <xs:attribute name="name" type="xs:token"/>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_ancestors_nearest_first():
    r = make_resolver()
    parents = r.ancestors("{urn:test}Leaf_T")
    assert parents == ["{urn:test}Middle_T", "{urn:test}Base_T"]


def test_ancestors_stop_at_builtin():
    r = make_resolver()
    assert r.ancestors("{urn:test}Base_T") == []


def test_attributes_flattened_and_sorted():
    r = make_resolver()
    attrs = r.attributes_of("{urn:test}Leaf_T")
    names = [a.name for a in attrs]
    assert names == sorted(names)
    assert set(names) == {"id", "name", "version"}  # prohibited 'secret' skipped


def test_nearest_definition_wins():
    r = make_resolver()
    attrs = {a.name: a for a in r.attributes_of("{urn:test}Leaf_T")}
    assert attrs["name"].type == "xs:token"  # Leaf_T overrides Base_T


def test_attribute_details():
    r = make_resolver()
    attrs = {a.name: a for a in r.attributes_of("{urn:test}Leaf_T")}
    assert attrs["id"].use == "required"
    assert attrs["id"].description == "Unique id."
    assert attrs["version"].fixed == "3.0.0"
    base_attrs = {a.name: a for a in r.attributes_of("{urn:test}Base_T")}
    assert base_attrs["name"].default == "unnamed"


def test_full_schema_vessel_type(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    parents = r.ancestors(f"{{{tns}}}ocxXML_T")
    assert any(p.endswith("}DocumentBase_T") for p in parents)
