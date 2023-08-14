#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from tabulate import tabulate
from pathlib import Path
from ocx_schema_parser import WORKING_DRAFT, TMP_FOLDER, SCHEMA_FOLDER
from ocx_schema_parser.transformer import Transformer



def ocx_look_up(transformer, type: str= 'ocx:Vessel'):

    if transformer.is_transformed():
        ocx = transformer.get_ocx_element_from_type(type)
        print(f'Found element: {ocx.get_name()} with prefix {ocx.get_prefix()}')


def element_table(transformer, element: str= 'ocx:Vessel'):

    if transformer.is_transformed():
        elements = transformer.get_ocx_elements()
        ocx = transformer.get_ocx_element_from_type(element)
        if ocx:
            print(f'Table of {element}:')
            print (tabulate(ocx.children_to_dict(), headers="keys"))
            print (tabulate(ocx.attributes_to_dict(), headers="keys"))

def enum(transformer, target: str = 'functionType'):

    if transformer.is_transformed():
        enums = transformer.get_enumerators()
        for key in enums:
            enum = enums[key]
            if enum.name == target:
                print(tabulate(enum.to_dict(), headers='keys'))

def summary(transformer):


    if transformer.is_transformed():
        print(transformer.parser.tbl_summary())




def simple_type(transformer, target = 'all'):

    if transformer.is_transformed():
        if target == 'all':
            for type in transformer.get_simple_types():
                print(type.to_dict())
        else:
            for type in transformer.get_simple_types():
                if type.name == target:
                    print(type.to_dict())


def elements(transformer, target = 'Vessel'):

   if transformer.is_transformed():
        for ocx in transformer.get_ocx_elements():
            print(f'{ocx.get_prefix()}:{ocx.get_name()}')

def attribute(transformer, target = 'GUIDRef'):

    if transformer.is_transformed():
        for type in transformer.get_global_attributes():
            if type.name == target:
                print(type)



if __name__ == "__main__":
    transformer = Transformer()
    # transformer.transform_schema_from_folder(SCHEMA_FOLDER)
    transformer.transform_schema_from_url(WORKING_DRAFT, Path(TMP_FOLDER))
    ocx_look_up(transformer, 'ocx:Vessel')
