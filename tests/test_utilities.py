""" Tests for the cross module utility functions."""
#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from collections import defaultdict
from pathlib import Path

from schema_parser import config_file
from utils import utilities

TEST_DICT = {'Bob': 'male', 'Jenny': 'female', 'Axel': 'boy', 'Eva': 'girl', 'Theodora': 'hen'}

DEFAULTDICT = defaultdict(list)
DEFAULTDICT['col1'].append(range(6))
DEFAULTDICT['col2'].append((range(5, 10)))


@staticmethod
def test_root_dir():
    root = Path(utilities.root_dir()).name
    assert root == 'src'


@staticmethod
def test_current_dir():
    file = Path(utilities.root_dir()) / 'utils/utilities.py'
    dir = Path(utilities.current_dir(file)).name
    assert dir == 'utils'


@staticmethod
def test_load_yaml_config(data_regression):
    config = utilities.load_yaml_config(config_file)
    data_regression.check(config)


@staticmethod
def test_number_table_rows(data_regression):
    numbered_dict = utilities.number_table_rows(TEST_DICT)
    index = [0, 1, 2, 3]
    assert index == numbered_dict['#']
