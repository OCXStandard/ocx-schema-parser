"""The data_classes module contains the dataclasses holding schema attributes after parsing."""
#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
from typing import Dict
from typing import List
from typing import Tuple


@dataclass
class BaseDataClass:
    """Base class for OCX dataclasses.

    Each subclass has to implement a field metadata with name `header` for each of its attributes, for example:

        ``name : str = field(metadata={'header': '<User friendly field name>'})``

    """

    def to_dict(self) -> Dict:
        """Output the data class as a dict with field names as keys."""
        my_fields = fields(self)
        table = {}
        i = 0
        for key, value in self.__dict__.items():
            table[my_fields[i].metadata["header"]] = value
            i += 1
        return table


@dataclass
class SchemaChange(BaseDataClass):
    """Class for keeping track of OCX schema changes.

    Args:
         version: The schema version the change applies to
         author: The author of the schem change
         date: The date of the schema change
         description: A description of the change

    """

    version: str = field(metadata={"header": "Version"})
    author: str = field(metadata={"header": "Author"})
    date: str = field(metadata={"header": "Date"})
    description: str = field(default="", metadata={"header": "Description"})


@dataclass
class SchemaType(BaseDataClass):
    """Class for xsd schema type information.

    Args:
         name: The schema type name
         prefix: The schema type namespace prefix
         source_line: The line number in the schema file where the type is defined
         tag: The schema type tag

    """

    prefix: str = field(metadata={"header": "Prefix"})
    name: str = field(metadata={"header": "Name"})
    tag: str = field(metadata={"header": "Tag"})
    source_line: int = field(metadata={"header": "Source Line"})


@dataclass
class SchemaSummary:
    """Class for schema summary information.

    Args:
         schema_version: The schema version
         schema_types: Tuples of the number of schema types
         schema_namespaces: Tuples of namespace prefixes

    """

    schema_version: List[Tuple] = field(metadata={"header": "Schema Version"})
    schema_types: List[Tuple] = field(metadata={"header": "Schema Types"})
    schema_namespaces: List[Tuple] = field(metadata={"header": "Namespaces"})


@dataclass
class SchemaEnumerator(BaseDataClass):
    """Enumerator class.

    Args:
        name: The name of the ``xs:attribute`` enumerator
        values: Enumeration values
        descriptions: Enumeration descriptions
    """

    name: str = field(metadata={"header": "Attribute name"})
    values: List[str] = field(metadata={"header": "Value"}, default_factory=lambda: [])
    descriptions: List[str] = field(metadata={"header": "Source Line"}, default_factory=lambda: [])
