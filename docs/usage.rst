=====
Usage
=====

To use ``schema_parser`` in a Python script:


>>> import schema_parser
>>> from schema_parser.parser import OcxSchema
>>> import logging
>>> logger = logging.getLogger()
>>> parser = OcxSchema(logger)
>>> parser.process_schema("https://3docx.org/fileadmin//ocx_schema//V286//OCX_Schema.xsd")
True
>>> import json
>>> print(json.dumps(parser.tbl_summary().__dict__,indent=2))
{
  "schema_version": [
    [
      "Schema Version",
      "2.8.6"
    ]
  ],
  "schema_types": [
    [
      "element",
      334
    ],
    [
      "attribute",
      120
    ],
    [
      "complexType",
      189
    ],
    [
      "simpleType",
      7
    ],
    [
      "attributeGroup",
      11
    ]
  ],
  "schema_namespaces": [
    [
      "xml",
      "http://www.w3.org/XML/1998/namespace"
    ],
    [
      "xs",
      "http://www.w3.org/2001/XMLSchema"
    ],
    [
      "vc",
      "http://www.w3.org/2007/XMLSchema-versioning"
    ],
    [
      "xlink",
      "http://www.w3.org/1999/xlink"
    ],
    [
      "ocx",
      "http://data.dnvgl.com/Schemas/ocxXMLSchema"
    ],
    [
      "unitsml",
      "urn:oasis:names:tc:unitsml:schema:xsd:UnitsMLSchema_lite-0.9.18"
    ],
    [
      null,
      "urn:oasis:names:tc:unitsml:schema:xsd:UnitsMLSchema_lite-0.9.18"
    ],
    [
      "xsd",
      "http://www.w3.org/2001/XMLSchema"
    ]
  ]
}
