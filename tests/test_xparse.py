#  Copyright (c) 2022-2025. OCX Consortium https://3docx.org. See the LICENSE


class TestLxmlParser:
    def test_get_root(self, load_schema_from_file):
        get_root = load_schema_from_file.get_root()
        assert get_root is not None

    def test_doc_encoding(self, load_schema_from_file):
        doc_encoding = load_schema_from_file.doc_encoding()
        assert doc_encoding == "UTF-8"

    def test_doc_root_name(self, load_schema_from_file):
        doc_root_name = load_schema_from_file.doc_root_name()
        assert doc_root_name == "schema"

    def test_doc_xml_version(self, load_schema_from_file):
        doc_xml_version = load_schema_from_file.doc_xml_version()
        assert doc_xml_version == "1.0"

    def test_get_namespaces(self, data_regression, load_schema_from_file):
        namespaces = load_schema_from_file.get_namespaces()
        data_regression.check(namespaces)

    def test_get_target_namespace(self, data_regression, load_schema_from_file):
        target_namespace = {"namespace": load_schema_from_file.get_target_namespace()}
        data_regression.check(target_namespace)

    def test_get_referenced_files(self, data_regression, load_schema_from_file):
        referenced_files = load_schema_from_file.get_referenced_files()
        data_regression.check(referenced_files)
