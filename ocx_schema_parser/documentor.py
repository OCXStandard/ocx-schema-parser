#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
"""Main module for creating the OCX schema documentation tables."""
from collections import Iterator

# System imports
from pathlib import Path

# Third party modules
from loguru import logger

# Module imports
from ocx_schema_parser.parser import OcxSchema

from ocx_schema_parser import TMP_FOLDER, WORKING_DRAFT
from ocx_schema_parser.ocxdownloader.downloader import SchemaDownloader


@staticmethod
def resolve_source(source: str, recursive: bool) -> Iterator[str]:
    """Resolve the source url.

    Args:
        source:
        recursive: True if
    """
    if "://" in source and not source.startswith("file://"):
        yield source
    else:
        path = Path(source).resolve()
        match = "**/*" if recursive else "*"
        if path.is_dir():
            for ext in ["wsdl", "xsd", "dtd", "xml", "json"]:
                yield from (x.as_uri() for x in path.glob(f"{match}.{ext}"))
        else:  # is file
            yield path.as_uri()


class Documentor:
    """OCX schema documentation class."""

    def __init__(self):
        self._parsr = OcxSchema()

    def _download_schema_from_url(self, url: str = WORKING_DRAFT) -> bool:
        """ "Download the schemas from an url before processing.

        Args:
            url: The location of the schema

        Returns:
            True if the was downloaded , false otherwise:
        """
        schema_folder = Path(TMP_FOLDER)
        schema_folder.mkdir(parents=True, exist_ok=True)
        # Delete any content if existing
        for file in schema_folder.glob("*.xsd"):
            Path(file).unlink()
        downloader = SchemaDownloader(TMP_FOLDER)
        downloader.wget(WORKING_DRAFT)
        files = list(schema_folder.glob("*.xsd"))
        logger.debug(f"Downloaded schema files: {files}")
        return len(files) > 0

    def generate_documentation_from_url(self, url: str = WORKING_DRAFT) -> bool:
        """Generate the schema documentation from the schema with 'url'.

        Args:
            url: The location of the schema

        Returns:
            True if success, False otherwise.
        """
