#  Copyright (c) 2022. OCX Consortium https://3docx.org. See the LICENSE
from schema_parser.xelement import LxmlElement


class TestLxmlElement:
    def test_items(self):
        # ToDo: write test
        pass

    def test_get_root(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        root = LxmlElement.get_root(element)
        assert root is not None

    def test_get_source_line(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        line = LxmlElement.get_source_line(element)
        assert line == 14

    def test_get_parent(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_get_children(self, load_schema_from_file):
        element = load_schema_from_file.get_root()
        children = LxmlElement.get_children(element)
        assert len(children) == 4863

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
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        name = LxmlElement.unique_tag(vessel)
        assert name == "{http://www.w3.org/2001/XMLSchema}Vessel"

    def test_get_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        name = LxmlElement.get_name(vessel)
        assert name == "Vessel"

    def test_get_use(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        attribute = LxmlElement.find_attributes(root)[0]
        use = LxmlElement.get_use(attribute)
        assert use == "required"

    def test_get_reference(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_is_reference(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_is_mandatory(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_cardinality(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_is_choice(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_is_substitution_group(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        assert LxmlElement.is_substitution_group(vessel) is True

    def test_is_abstract(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        element = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Curve3D")[0]
        assert LxmlElement.is_abstract(element) is True

    def test_get_substitution_group(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        assert LxmlElement.get_substitution_group(vessel) == "ocx:Form"

    def test_get_element_text(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        text = LxmlElement.get_element_text(vessel)
        assert text == "Vessel asset subject to Classification."

    def test_get_namespace(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        namespace = LxmlElement.get_namespace(root)
        assert namespace == "http://www.w3.org/2001/XMLSchema"

    def test_iter(self, load_schema_from_file):
        # ToDo: write test
        pass

    def test_find_all_children_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        children = LxmlElement.find_all_children_with_name(root, "complexType")
        assert len(children) == 202

    def test_find_child_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        child = LxmlElement.find_child_with_name(vessel, "annotation")
        assert len(child) == 1

    def test_find_attributes(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        attributes = LxmlElement.find_attributes(root)
        assert len(attributes) == 153

    def test_find_attribute_groups(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        groups = LxmlElement.find_attribute_groups(root)
        assert len(groups) == 8

    def test_has_child_with_name(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        vessel = LxmlElement.find_all_children_with_attribute_value(root, "element", "name", "Vessel")[0]
        assert LxmlElement.has_child_with_name(vessel, "annotation") is True

    def test_find_all_children_with_attribute_value(self, load_schema_from_file):
        # If the schema version changes, the test should probably be updated
        root = load_schema_from_file.get_root()
        child = LxmlElement.find_all_children_with_attribute_value(root, "attribute", "name", "schemaVersion")[0]
        assert child.get("fixed") == "2.8.7"

    def test_find_all_children_with_name_and_attribute(self, load_schema_from_file):
        root = load_schema_from_file.get_root()
        children = LxmlElement.find_all_children_with_name_and_attribute(root, "element", "name")
        assert len(children) == 318

    def test_find_assertion(self, load_schema_from_file):
        # If the schema version changes, the test should probably be updated
        root = load_schema_from_file.get_root()
        child = LxmlElement.find_all_children_with_attribute_value(root, "complexType", "name", "EntityRefBase_T")[0]
        assert len(LxmlElement.find_assertion(child)) > 0

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
        # ToDo: write test
        pass
