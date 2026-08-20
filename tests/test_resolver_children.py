"""Tests for child element collection and substitution group expansion."""
from conftest import parse_fragment

from ocx_schema_parser.resolver import _Resolver

FRAGMENT = """<?xml version="1.0"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           xmlns:t="urn:test" targetNamespace="urn:test">
  <xs:element name="Shape" type="t:Shape_T" abstract="true"/>
  <xs:element name="Circle" type="t:Shape_T" substitutionGroup="t:Shape"/>
  <xs:element name="Square" type="t:Shape_T" substitutionGroup="t:Shape"/>
  <xs:element name="Label" type="xs:string"/>
  <xs:complexType name="Shape_T"/>
  <xs:group name="extras">
    <xs:sequence>
      <xs:element name="Note" type="xs:string" minOccurs="0"/>
    </xs:sequence>
  </xs:group>
  <xs:complexType name="Base_T">
    <xs:sequence>
      <xs:element ref="t:Label"/>
    </xs:sequence>
  </xs:complexType>
  <xs:complexType name="Drawing_T">
    <xs:complexContent>
      <xs:extension base="t:Base_T">
        <xs:sequence>
          <xs:element ref="t:Shape" maxOccurs="unbounded"/>
          <xs:choice>
            <xs:element name="Title" type="xs:string"/>
            <xs:element name="Caption" type="xs:string"/>
          </xs:choice>
          <xs:group ref="t:extras"/>
        </xs:sequence>
      </xs:extension>
    </xs:complexContent>
  </xs:complexType>
</xs:schema>
"""


def make_resolver():
    return _Resolver([parse_fragment(FRAGMENT)])


def test_substitution_group_index():
    r = make_resolver()
    assert r.substitution_groups["{urn:test}Shape"] == [
        "{urn:test}Circle",
        "{urn:test}Square",
    ]


def test_children_traversal_order_and_inheritance():
    r = make_resolver()
    children = r.children_of("{urn:test}Drawing_T")
    names = [c.name for c in children]
    # own children first (traversal order: elements, then groups, then choices),
    # inherited children afterwards
    assert names == ["Circle", "Square", "Note", "Title", "Caption", "Label"]
    by_name = {c.name: c for c in children}
    assert by_name["Label"].inherited_from == "t:Base_T"
    assert by_name["Circle"].inherited_from is None


def test_abstract_head_replaced_by_members():
    r = make_resolver()
    by_name = {c.name: c for c in r.children_of("{urn:test}Drawing_T")}
    assert "Shape" not in by_name  # abstract head not emitted
    assert by_name["Circle"].from_substitution_group == "t:Shape"
    assert by_name["Circle"].cardinality.upper is None  # inherits ref cardinality
    assert by_name["Note"].from_substitution_group is None


def test_choice_flag():
    r = make_resolver()
    by_name = {c.name: c for c in r.children_of("{urn:test}Drawing_T")}
    assert by_name["Title"].is_choice is True
    assert by_name["Caption"].is_choice is True
    assert by_name["Note"].is_choice is False


def test_full_schema_vessel_children(ocx_schemas):
    r = _Resolver(ocx_schemas)
    tns = "https://3docx.org/fileadmin//ocx_schema//V300//OCX_Schema.xsd"
    children = r.children_of(f"{{{tns}}}Vessel_T")
    assert len(children) > 0
