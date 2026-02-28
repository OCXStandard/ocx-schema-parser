#  Copyright (c) 2022-2025. OCX Consortium https://3docx.org. See the LICENSE
from ocx_schema_parser.xparse import LxmlElement


class TestLxmlElement:
    def test_items(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        items = LxmlElement.items(vessel)
        assert isinstance(items, list)
        assert len(items) > 0
        keys = [k for k, v in items]
        assert "name" in keys

    def test_get_root(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        root = LxmlElement.get_root(element)
        assert root is not None

    def test_get_source_line(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        line = LxmlElement.get_source_line(element)
        assert line == 1

    def test_get_parent(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # Root element has no parent
        assert LxmlElement.get_parent(root) is None
        # A child element should have a parent
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.get_parent(vessel) is not None

    def test_get_children(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        children = LxmlElement.get_children(element)
        assert len(children) == 3655

    def test_get_xml_attrib(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        attrib = LxmlElement.get_xml_attrib(element)
        assert len(attrib) == 4

    def test_get_localname(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        name = LxmlElement.get_localname(element)
        assert name == "schema"

    def test_unique_tag(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        name = LxmlElement.unique_tag(vessel)
        assert name == "{http://www.w3.org/2001/XMLSchema}Vessel"

    def test_get_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        name = LxmlElement.get_name(vessel)
        assert name == "Vessel"

    def test_get_use(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        panel = LxmlElement.find_all_children_with_attribute_value(
            root, name="complexType", attrib_value="Panel_T", attrib_name="name"
        )
        if len(panel) > 0:
            panel = panel[0]
            attrib = LxmlElement.find_attributes(panel)
            if len(attrib) > 0:
                use = LxmlElement.get_use(attrib[0])
                assert use == "req."
            else:
                assert False
        else:
            assert False

    def test_get_reference(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        refs = LxmlElement.find_all_children_with_name_and_attribute(
            root, "element", "ref"
        )
        assert len(refs) > 0
        ref_value = LxmlElement.get_reference(refs[0])
        assert ref_value is not None
        assert isinstance(ref_value, str)
        assert len(ref_value) > 0

    def test_is_reference(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # An attribute with use="required" should be detected as a reference
        panel = LxmlElement.find_all_children_with_attribute_value(
            root, name="complexType", attrib_value="Panel_T", attrib_name="name"
        )
        assert len(panel) > 0
        attribs = LxmlElement.find_attributes(panel[0])
        required = [a for a in attribs if a.get("use") == "required"]
        assert len(required) > 0
        assert LxmlElement.is_reference(required[0]) is True
        # Root has no "use" attribute — not a reference
        assert LxmlElement.is_reference(root) is False

    def test_is_mandatory(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # Elements with minOccurs="0" are optional (not mandatory)
        optional_elems = LxmlElement.find_all_children_with_name_and_attribute(
            root, "element", "minOccurs"
        )
        assert len(optional_elems) > 0
        zero_min = [e for e in optional_elems if e.get("minOccurs") == "0"]
        assert len(zero_min) > 0
        assert LxmlElement.is_mandatory(zero_min[0]) is False
        # Vessel has no minOccurs → default lower bound is 1 → mandatory
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.is_mandatory(vessel) is True

    def test_cardinality(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # An element with maxOccurs="unbounded"
        unbounded = LxmlElement.find_all_children_with_name_and_attribute(
            root, "element", "maxOccurs"
        )
        assert len(unbounded) > 0
        unb_elem = [e for e in unbounded if e.get("maxOccurs") == "unbounded"][0]
        lower, upper = LxmlElement.cardinality(unb_elem)
        assert upper == "unbounded"
        # Vessel has no minOccurs/maxOccurs → default (1, 1)
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        lower, upper = LxmlElement.cardinality(vessel)
        assert lower == 1
        assert upper == 1

    def test_is_choice(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # Find elements directly inside an xs:choice
        choice_parents = LxmlElement.find_all_children_with_name(root, "choice")
        assert len(choice_parents) > 0
        choice_children = LxmlElement.find_all_children_with_name(
            choice_parents[0], "element"
        )
        assert len(choice_children) > 0
        assert LxmlElement.is_choice(choice_children[0]) is True
        # Vessel is not inside any choice
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.is_choice(vessel) is False

    def test_is_substitution_group(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.is_substitution_group(vessel) is True

    def test_is_abstract(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        element = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Curve3D"
        )[0]
        assert LxmlElement.is_abstract(element) is True

    def test_get_substitution_group(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.get_substitution_group(vessel) == "ocx:Form"

    def test_get_element_text(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        text = LxmlElement.get_element_text(vessel)
        assert text == "Vessel asset subject to Classification."

    def test_get_namespace(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        namespace = LxmlElement.get_namespace(root)
        assert namespace == "http://www.w3.org/2001/XMLSchema"

    def test_iter(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        # Iterate over all complexType elements
        complex_types = list(LxmlElement.iter(root, "{*}complexType"))
        assert len(complex_types) > 0
        for elem in complex_types:
            assert LxmlElement.get_localname(elem) == "complexType"
        # Without tag filter, all elements are returned (at least as many)
        all_elements = list(LxmlElement.iter(root))
        assert len(all_elements) >= len(complex_types)

    def test_find_all_children_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        children = LxmlElement.find_all_children_with_name(root, "complexType")
        assert len(children) == 214

    def test_find_child_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        child = LxmlElement.find_child_with_name(vessel, "annotation")
        assert len(child) == 1

    def test_find_attributes(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        attributes = LxmlElement.find_attributes(root)
        assert len(attributes) == 155

    def test_find_attribute_groups(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        groups = LxmlElement.find_attribute_groups(root)
        assert len(groups) == 10

    def test_has_child_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(
            root, "element", "name", "Vessel"
        )[0]
        assert LxmlElement.has_child_with_name(vessel, "annotation") is True

    def test_find_all_children_with_attribute_value(self, load_schema_from_file):
        # If the schema version changes, the test should probably be updated
        root = load_schema_from_file.get_root()
        child = LxmlElement.find_all_children_with_attribute_value(
            root, "attribute", "name", "schemaVersion"
        )[0]
        assert child.get("fixed") == "3.0.0"

    def test_find_all_children_with_name_and_attribute(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        children = LxmlElement.find_all_children_with_name_and_attribute(
            root, "element", "name"
        )
        assert len(children) == 307

    def test_find_assertion(self, load_schema_from_file):
        # If the schema version changes, the test should probably be updated
        root = load_schema_from_file.get_root()
        children = LxmlElement.find_all_children_with_attribute_value(
            root, "complexType", "name", "EntityRefBase_T"
        )
        assert len(children) == 0

    def test_namespace_prefix(self, load_schema_from_file):
        result = LxmlElement.namespace_prefix("ocx:Vessel")
        assert result == "ocx"

    def test_namespaces_decorate(self, load_schema_from_file):
        result = LxmlElement.namespaces_decorate("ocx")
        assert result == "{ocx}"

    def test_strip_namespace_prefix(self, load_schema_from_file):
        result = LxmlElement.strip_namespace_prefix("ocx:Vessel")
        assert result == "Vessel"

    def test_strip_namespace_tag(self, load_schema_from_file):
        # Strip a Clark-notation namespace tag
        assert (
            LxmlElement.strip_namespace_tag(
                "{http://www.w3.org/2001/XMLSchema}complexType"
            )
            == "complexType"
        )
        # A string without a namespace tag is returned unchanged
        assert LxmlElement.strip_namespace_tag("complexType") == "complexType"
        # Verify against an actual element tag from the parsed schema
        root = load_schema_from_file.get_root()
        complex_types = LxmlElement.find_all_children_with_name(root, "complexType")
        assert len(complex_types) > 0
        stripped = LxmlElement.strip_namespace_tag(complex_types[0].tag)
        assert stripped == "complexType"
