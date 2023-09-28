"""The data_classes module contains the dataclasses holding schema attributes after parsing."""
#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
from dataclasses import dataclass, field, fields
from typing import Dict, List, Tuple


@dataclass
class BaseDataClass:
    """Base class for OCX dataclasses.

    Each subclass has to implement a field metadata with name `header` for each of its attributes, for example:

        ``name : str = field(metadata={'header': '<User friendly field name>'})``

    """

    def to_dict(self) -> Dict:
        """Output the data class as a dict with field names as keys."""
        my_fields = fields(self)
        return {
            my_fields[i].metadata["header"]: value
            for i, (key, value) in enumerate(self.__dict__.items())
        }


@dataclass
class SchemaChange(BaseDataClass):
    """Class for keeping track of OCX schema changes.

    Parameters:
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

    Parameters:
         name: The schema type name
         prefix: The schema type namespace prefix
         source_line: The line number in the schema file where the type is defined
         tag: The schema type tag

    """

    prefix: str = field(metadata={"header": "Prefix"})
    name: str = field(metadata={"header": "Name"})
    tag: str = field(metadata={"header": "Tag"})
    source_line: int = field(metadata={"header": "Source Line"})
    # annotation: str = field(default='', metadata={"header": "Description"})


@dataclass
class SchemaSummary(BaseDataClass):
    """Class for schema summary information.

    Parameters:
         schema_version: The schema version
         schema_types: Tuples of the number of schema types
         schema_namespaces: Tuples of namespace prefixes

    """

    schema_version: List[Tuple] = field(metadata={"header": "Schema Version"})
    schema_types: List[Tuple] = field(metadata={"header": "Schema Types"})
    schema_namespaces: List[Tuple] = field(metadata={"header": "Namespaces"})


@dataclass
class SchemaAttribute(BaseDataClass):
    """Schema attribute type class.

    Parameters:
        name: The name of the ``xs:attribute`` attribute
        type: the attribute type
        prefix: The namespace prefix
        restriction: attribute restriction if any
        description: The attribute annotation
    """

    name: str = field(metadata={"header": "Attribute"})
    prefix: str = field(default="", metadata={"header": "Namespace"})
    type: str = field(default="", metadata={"header": "Type"})
    restriction: str = field(default="", metadata={"header": "Restriction"})
    description: str = field(default="", metadata={"header": "Description"})


@dataclass
class OcxEnumerator:
    """Enumerator class.

    Parameters:
        name: The name of the ``xs:attribute`` enumerator
        values: Enumeration values
        descriptions: Enumeration descriptions
    """

    prefix: str = field(metadata={"header": "Attribute name"})
    name: str = field(metadata={"header": "Prefix"})
    tag: str = field(metadata={"header": "Tag"})
    values: List[str] = field(metadata={"header": "Value"}, default_factory=lambda: [])
    descriptions: List[str] = field(
        metadata={"header": "Description"}, default_factory=lambda: []
    )

    def to_dict(self) -> Dict:
        """Output the enumerator values and annotations."""
        return {"Value": self.values, "Description": self.descriptions}


@dataclass
class OcxSchemaAttribute(BaseDataClass):
    """Attribute class.

    Parameters:
        name: The name of the ``xs:attribute`` attribute
        prefix: The Attribute namespace prefix
        type: the attribute type
        use: If the attribute is mandatory or not
        default: The attribute value default if any
        fixed: The attribute fixed value if any
        description: The attribute annotation
    """

    name: str = field(metadata={"header": "Attribute"})
    prefix: str = field(metadata={"header": "Namespace"})
    type: str = field(metadata={"header": "Type"})
    use: str = field(metadata={"header": "Use"})
    default: str = field(default="", metadata={"header": "Default"})
    fixed: str = field(default="", metadata={"header": "Fixed"})
    description: str = field(default="", metadata={"header": "Description"})


@dataclass
class OcxSchemaChild(BaseDataClass):
    """Child element  class.

    Parameters:
        name: The name of the ``xs:element`` element
        prefix: The namespace prefix
        type: the element type
        use: If the element is mandatory or not
        cardinality: The cardinality of the child element
        is_choice: Whether the child is a choice element or not
        description: The child annotation
    """

    name: str = field(metadata={"header": "Child"})
    prefix: str = field(metadata={"header": "Namespace"})
    type: str = field(metadata={"header": "Type"})
    use: str = field(metadata={"header": "Use"})
    cardinality: str = field(metadata={"header": "Cardinality"})
    is_choice: bool = field(default=False, metadata={"header": "Choice"})
    description: str = field(default="", metadata={"header": "Description"})
