#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from ocx_schema_parser import config


def test_schema_url():
    assert (
        config.get("SchemaParserSettings", "schema_url")
        == "https://3docx.org/fileadmin/ocx_schema/V286/OCX_Schema.xsd"
    )


def test_name_exceptions(data_regression):
    result= config.get("SchemaParserSettings", "ocx_name_exceptions").split()
    data_regression.check(result)


def test_known_word_list():
    assert config.get("SchemaParserSettings", "known_word_list").split() == [
        "3D",
        "NURBS",
        "OCX",
        "XML",
        "authoring",
        "circumcircle",
        "consumables",
        "enumerated",
        "mm",
        "modulus",
        "multiplicities",
        "ordinate",
        "orthogonal",
        "scantling",
        "scantlings",
        "schema",
        "stiffeners",
    ]


def test_process_schema_types():
    assert config.get("SchemaParserSettings", "process_schema_types").split() == [
        "element",
        "attribute",
        "complexType",
        "simpleType",
        "attributeGroup",
    ]


def test_w3c_schema_builtin_types(data_regression):
    keys = config.get("SchemaParserSettings", "w3c_schema_builtin_keys").split()
    values = config.get("SchemaParserSettings", "w3c_schema_builtin_values").split()
    result = dict(zip(keys, values))
    data_regression.check(result)
