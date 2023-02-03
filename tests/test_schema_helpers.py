#  Copyright (c) 2022. OCX Consortium https://3docx.org. See the LICENSE

from schema_parser.helpers import SchemaHelper


class TestSchemaHelpers:
    def test_get_schema_version(self, data_regression, load_schema_from_file):
        """Test retrieving the OCX schema version

        Args:
            data_regression: pytest regression test framework
            load_schema_from_file: Shared test data provided by @pytest.fixture in ``conftest.py``
        """
        root = load_schema_from_file.get_root()
        version = SchemaHelper.get_schema_version(root)
        assert version == "2.8.7"

    def test_find_schema_changes(self, data_regression, load_schema_from_file):
        """Test retrieving the OCX schema changes

        Args:
            data_regression: pytest regression test framework
            load_schema_from_file: Shared test data provided by @pytest.fixture in ``conftest.py``
        """
        root = load_schema_from_file.get_root()
        data = SchemaHelper.schema_changes_data_grid(root)
        data_regression.check(data)
