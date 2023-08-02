#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from tabulate import tabulate
from loguru import logger
from pathlib import Path
from ocx_schema_parser.parser import OcxSchema
from ocx_schema_parser.ocxdownloader.downloader import SchemaDownloader
from ocx_schema_parser import WORKING_DRAFT, SCHEMA_FOLDER


def print_table(element: str= 'Header'):

    downloader = SchemaDownloader(SCHEMA_FOLDER)
    downloader.wget(WORKING_DRAFT)

    file_name = Path(SCHEMA_FOLDER) / Path(WORKING_DRAFT).name
    url = str(file_name.resolve())
    schema_folder = Path(SCHEMA_FOLDER)
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(folder)
    if result := schema_reader.process_schema(url):
        elements = schema_reader.get_ocx_elements()
        result = filter(lambda target: target.get_name() == element, elements)
        for item in result:
            if item.get_name() == element:
                result = item.children_to_dict()
                print (tabulate(item.attributes_to_dict(), headers="keys"))

def print_enum(target: str = 'prefix'):

    downloader = SchemaDownloader(SCHEMA_FOLDER)
    downloader.wget(WORKING_DRAFT)

    file_name = Path(SCHEMA_FOLDER) / Path(WORKING_DRAFT).name
    url = str(file_name.resolve())
    schema_folder = Path(SCHEMA_FOLDER)
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(folder)
    if result := schema_reader.process_schema(url):
        enums = schema_reader.get_schema_enumerators()
        for key in enums:
            enum = enums[key]
            if enum.name == target:
                print(tabulate(enum.to_dict(), headers='keys'))

def print_summary():

    downloader = SchemaDownloader(SCHEMA_FOLDER)
    downloader.wget(WORKING_DRAFT)

    file_name = Path(SCHEMA_FOLDER) / Path(WORKING_DRAFT).name
    url = str(file_name.resolve())
    schema_folder = Path(SCHEMA_FOLDER)
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(folder)
    if result := schema_reader.process_schema(url):
        print(tabulate(schema_reader.tbl_summary(), headers='keys'))


def print_attributes():

    downloader = SchemaDownloader(SCHEMA_FOLDER)
    downloader.wget(WORKING_DRAFT)

    file_name = Path(SCHEMA_FOLDER) / Path(WORKING_DRAFT).name
    url = str(file_name.resolve())
    schema_folder = Path(SCHEMA_FOLDER)
    folder = str(schema_folder.resolve())
    schema_reader = OcxSchema(folder)
    if result := schema_reader.process_schema(url):
        print(tabulate(schema_reader.tbl_summary(), headers='keys'))


if __name__ == "__main__":
    print_enum()
