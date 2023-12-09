#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

# Add sections and options programmatically
config["SchemaParserSettings"] = {
    "schema_url": "https://3docx.org/fileadmin/ocx_schema/V286/OCX_Schema.xsd",
    "working_draft": "https://3docx.org/fileadmin//ocx_schema//V300b0//OCX_Schema.xsd",
    "schema_folder": "schema_versions",
    "tmp_folder": "tmp",
    "w3c_schema_builtin_keys": """
        {http://www.w3.org/2001/XMLSchema}string
        {http://www.w3.org/2001/XMLSchema}ID
        {http://www.w3.org/2001/XMLSchema}IDREF
        {http://www.w3.org/2001/XMLSchema}boolean
        {http://www.w3.org/2001/XMLSchema}decimal
        {http://www.w3.org/2001/XMLSchema}float
        {http://www.w3.org/2001/XMLSchema}integer
        {http://www.w3.org/2001/XMLSchema}double
        {http://www.w3.org/2001/XMLSchema}duration
        {http://www.w3.org/2001/XMLSchema}dateTime
        {http://www.w3.org/2001/XMLSchema}gYearMonth
        {http://www.w3.org/2001/XMLSchema}gYear
        {http://www.w3.org/2001/XMLSchema}gMonthDay
        {http://www.w3.org/2001/XMLSchema}hexBinary
        {http://www.w3.org/2001/XMLSchema}base64Binary
        {http://www.w3.org/2001/XMLSchema}anyURI
        {http://www.w3.org/2001/XMLSchema}QName
        {http://www.w3.org/2001/XMLSchema}token
        {http://www.w3.org/2001/XMLSchema}NOTATION
        {http://www.w3.org/2001/XMLSchema}byte
        {http://www.w3.org/2001/XMLSchema}normalizedString""",
    "w3c_schema_builtin_values": """
        https://www.w3.org/TR/xmlschema-2/#string
        https://www.w3.org/TR/xmlschema-2/#ID
        https://www.w3.org/TR/xmlschema-2/#IDREF
        https://www.w3.org/TR/xmlschema-2/#boolean
        https://www.w3.org/TR/xmlschema-2/#decimal
        https://www.w3.org/TR/xmlschema-2/#float
        https://www.w3.org/TR/xmlschema-2/#integer
        https://www.w3.org/TR/xmlschema-2/#double
        https://www.w3.org/TR/xmlschema-2/#duration
        https://www.w3.org/TR/xmlschema-2/#dateTime
        https://www.w3.org/TR/xmlschema-2/#gYearMonth
        https://www.w3.org/TR/xmlschema-2/#gYear
        https://www.w3.org/TR/xmlschema-2/#gMonthDay
        https://www.w3.org/TR/xmlschema-2/#hexBinary
        https://www.w3.org/TR/xmlschema-2/#base64Binary
        https://www.w3.org/TR/xmlschema-2/#string
        https://www.w3.org/TR/xmlschema-2/#QName
        https://www.w3.org/TR/xmlschema-2/#token
        https://www.w3.org/TR/xmlschema-2/#NOTATION
        https://www.w3.org/TR/xmlschema-2/#byte
        https://www.w3.org/TR/xmlschema-2/#normalizedString""",
    "process_schema_types": "element    attribute    complexType    simpleType    attributeGroup",
    "known_word_list": """3D
        NURBS
        OCX
        XML
        authoring
        circumcircle
        consumables
        enumerated
        mm
        modulus
        multiplicities
        ordinate
        orthogonal
        scantling
        scantlings
        schema
        stiffeners""",
    # Schema naming conformance exceptions
    "ocx_name_exceptions": """AP_Pos FP_Pos GUIDRef U_NURBSproperties V_NURBSproperties application_version ocxXML
        originating_system
        time_stamp""",
}
