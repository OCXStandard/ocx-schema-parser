#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from collections import defaultdict
from pathlib import Path

from tabulate import tabulate

from ocx_schema_parser import SCHEMA_FOLDER, WORKING_DRAFT
from ocx_schema_parser.transformer import Transformer


def ocx_look_up(transformer, type: str = "ocx:Vessel"):
    if transformer.is_transformed():
        ocx = transformer.get_ocx_element_from_type(type)
        print(f"Found element: {ocx.get_name()} with prefix {ocx.get_prefix()}")
        print(f"Children: {ocx.children_to_dict()}")


def element_table(transformer, element: str = "ocx:Vessel"):
    if transformer.is_transformed():
        ocx = transformer.get_ocx_element_from_type(element)
        if ocx:
            print(f"Table of {element}:")
            print(tabulate(ocx.children_to_dict(), headers="keys"))
            print(tabulate(ocx.attributes_to_dict(), headers="keys"))


def enum_values(transformer, target: str = "functionType"):
    if transformer.is_transformed():
        enums = transformer.get_enumerators()
        for key in enums:
            enum = enums[key]
            if enum.name == target:
                print(tabulate(enum.to_dict(), headers="keys"))


def enum_types(transformer):
    tbl = defaultdict(list)
    if transformer.is_transformed():
        enums = transformer.get_enumerators()
        for name, enum in enums.items():
            tbl["Name"].append(name)
            tbl["prefix"].append(enum.prefix)
            tbl["Tag"].append(enum.tag)
        print(tabulate(tbl, headers="keys"))


def summary(transformer):
    if transformer.is_transformed():
        for ns, tbl in transformer.parser.tbl_summary().items():
            print(f"Content of namespace {ns}:\n")
            print(tabulate(tbl, headers="keys"), "\n")


def simple_type(transformer, target="all"):
    if transformer.is_transformed():
        if target == "all":
            for type in transformer.get_simple_types():
                print(type.to_dict())
        else:
            for type in transformer.get_simple_types():
                if type.name == target:
                    print(type.to_dict())


def elements(transformer, target="Vessel"):
    if transformer.is_transformed():
        for ocx in transformer.get_ocx_elements():
            print(f"{ocx.get_prefix()}:{ocx.get_name()}")


def attribute(transformer, target="GUIDRef"):
    if transformer.is_transformed():
        for type in transformer.get_global_attributes():
            if type.name == target:
                print(type)


def substitution_groups(transformer):
    if transformer.is_transformed():
        groups = transformer.parser.get_substitution_groups()
        print(groups)


if __name__ == "__main__":
    transformer = Transformer()
    # transformer.transform_schema_from_folder(Path(SCHEMA_FOLDER))
    transformer.transform_schema_from_url(WORKING_DRAFT, Path(SCHEMA_FOLDER))
    # substitution_groups(transformer)
    ocx_look_up(transformer, "ocx:UnboundedGeometry")
