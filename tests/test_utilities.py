"""Tests for the cross module utility functions."""

#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
from collections import defaultdict
from pathlib import Path


from ocx_schema_parser.utils import utilities

TEST_DICT = {
    "Bob": "male",
    "Jenny": "female",
    "Axel": "boy",
    "Eva": "girl",
    "Theodora": "hen",
}

DEFAULTDICT = defaultdict(list)
DEFAULTDICT["col1"].append(range(6))
DEFAULTDICT["col2"].append((range(5, 10)))


def test_current_dir():
    file = Path(utilities.root_dir()) / "utils/utilities.py"
    dir = Path(utilities.current_dir(file)).name
    assert dir == "utils"


def test_number_table_rows(data_regression):
    numbered_dict = utilities.number_table_rows(TEST_DICT)
    index = [0, 1, 2, 3]
    assert index == numbered_dict["#"]


def test_camel_case_split():
    camel_case = "pythonGeekForGeeks"
    words = utilities.camel_case_split(camel_case)
    assert words == ["Geek", "For", "Geeks"]


def test_dromedary_case_split():
    camel_case = "pythonGeekForGeeks"
    words = utilities.dromedary_case_split(camel_case)
    assert words == ["python", "Geek", "For", "Geeks"]
