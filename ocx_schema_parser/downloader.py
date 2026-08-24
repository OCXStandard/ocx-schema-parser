#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
"""Download an XSD schema and all its referenced schemas into one folder."""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from loguru import logger
from xsdata.codegen import opener
from xsdata.utils.downloader import Downloader

from ocx_schema_parser.errors import OcxParserError


def is_valid_uri(uri: str) -> bool:
    """Return True if ``uri`` is a URI with a scheme (http, https, file, ...)."""
    try:
        parsed = urlparse(uri)
        if not parsed.scheme:
            return False
        if parsed.scheme == "file":
            return bool(parsed.path)
        return bool(parsed.netloc)
    except Exception:
        return False


class SchemaDownloader(Downloader):
    """Downloader specialisation: writes all referenced schemas into one folder.

    Args:
        output: The path to the schema download folder.
    """

    def __init__(self, output: Path):
        super().__init__(output)
        self.schema_folder = output

    def write_file(self, uri: str, location: Optional[str], content: str):
        """Write a downloaded schema into the single download folder."""
        name = Path(uri).name
        file_path = self.schema_folder / name
        file_path.write_text(content, encoding="utf-8")
        logger.debug(
            f"Writing schema {file_path.resolve()} to folder {self.schema_folder.resolve()}"
        )
        self.downloaded[uri] = file_path
        if location:
            self.downloaded[location] = file_path

    def wget(self, uri: str, location: Optional[str] = None):
        """Download ``uri`` (remote URI or local file path) with circular protection.

        Raises:
            OcxParserError: If the source cannot be fetched or parsed.
        """
        try:
            if uri in self.downloaded:
                return

            self.downloaded[uri] = None
            if location:
                self.downloaded[location] = None

            if is_valid_uri(uri):
                logger.info(f"Fetching {uri}")
                input_stream = opener.open(uri).read()  # nosec
            else:
                input_file = Path(uri).resolve()
                logger.info(f"Fetching local file {input_file}")
                with open(str(input_file), "rb") as file:
                    input_stream = file.read()

            if uri.endswith("wsdl"):
                self.parse_definitions(uri, input_stream)
            else:
                self.parse_schema(uri, input_stream)
                self.write_file(uri, location, input_stream.decode())

        except FileNotFoundError as exc:
            raise OcxParserError(f"The file at {uri} was not found.") from exc
        except OcxParserError:
            raise
        except Exception as exc:
            raise OcxParserError(f"Failed to download {uri}: {exc}") from exc
