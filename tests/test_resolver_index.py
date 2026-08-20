"""Tests for the resolver index pass and reference resolution."""
from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver, _cardinality, _description

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:element name="Thing" type="t:Thing_T">
    <xs:annotation><xs:documentation>A thing.</xs:documentation></xs:annotation>
  </xs:element>
  <xs:complexType name="Thing_T">
    <xs:sequence>
      <xs:element name="Part" type="xs:string" minOccurs="0" maxOccurs="unbounded"/>
    </xs:sequence>
  </xs:complexType>
  <xs:simpleType name="guid">
    <xs:restriction base="xs:string"/>
  </xs:simpleType>
  <xs:attribute name="id" type="xs:ID"/>
  <xs:attributeGroup name="idGroup">
    <xs:attribute ref="t:id"/>
  </xs:attributeGroup>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_index_pass():
    r = make_resolver()
    assert "{urn:test}Thing" in r.elements
    assert "{urn:test}Thing_T" in r.complex_types
    assert "{urn:test}guid" in r.simple_types
    assert "{urn:test}id" in r.global_attributes
    assert "{urn:test}idGroup" in r.attribute_groups


def test_namespaces_and_prefixes():
    r = make_resolver()
    assert r.namespaces["t"] == "urn:test"
    assert r.prefixed("{urn:test}Thing") == "t:Thing"
    assert r.prefixed("{http://www.w3.org/2001/XMLSchema}string") == "xs:string"


def test_qref():
    r = make_resolver()
    schema = r.schemas[0]
    assert r.qref("t:Thing_T", schema) == "{urn:test}Thing_T"
    assert r.qref("xs:string", schema) == "{http://www.w3.org/2001/XMLSchema}string"


def test_unprefixed_qref_uses_default_namespace_before_target_namespace():
    fragment = """<?xml version="1.0"?>
<schema xmlns="http://www.w3.org/2001/XMLSchema"
        xmlns:xs="http://www.w3.org/2001/XMLSchema"
        xmlns:t="urn:test"
        targetNamespace="urn:test">
  <complexType name="Thing_T">
    <attribute name="name" type="string"/>
  </complexType>
</schema>
"""
    r = _Resolver([parse_fragment(fragment)])

    attrs = {a.name: a for a in r.attributes_of("{urn:test}Thing_T")}
    assert attrs["name"].type == "xs:string"


def test_is_builtin():
    r = make_resolver()
    assert r.is_builtin("{http://www.w3.org/2001/XMLSchema}string")
    assert not r.is_builtin("{urn:test}Thing_T")


def test_description_helper():
    r = make_resolver()
    node = r.elements["{urn:test}Thing"]
    assert _description(node.obj) == "A thing."


def test_cardinality_helper():
    r = make_resolver()
    ct = r.complex_types["{urn:test}Thing_T"].obj
    part = ct.sequence.elements[0]
    card = _cardinality(part)
    assert card.lower == 0
    assert card.upper is None  # unbounded


def test_index_full_ocx_schema(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    assert f"{{{tns}}}Vessel" in r.elements
    assert len(r.elements) > 300  # ocx + unitsml + xml global elements
    assert r.namespaces["ocx"] == tns
