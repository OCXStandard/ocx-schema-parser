"""Load OCX schemas from a local file, folder, or remote URL into xsdata Schema objects."""
from __future__ import annotations

import shutil
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

from loguru import logger
from xsdata.codegen.parsers.schema import SchemaParser
from xsdata.models import xsd

from ocx_schema_parser.downloader import SchemaDownloader
from ocx_schema_parser.errors import OcxParserError


def _is_url(source: str) -> bool:
    return urlparse(source).scheme in ("http", "https")


def _parse_file(path: Path) -> xsd.Schema:
    try:
        tree = ET.parse(str(path))
        root = tree.getroot()
        if root.tag != "{http://www.w3.org/2001/XMLSchema}schema":
            raise OcxParserError(f"Failed to parse {path}: root element is not an XSD schema")
        parser = SchemaParser(location=path.resolve().as_uri())
        return parser.parse(str(path), xsd.Schema)
    except OcxParserError:
        raise
    except Exception as exc:
        raise OcxParserError(f"Failed to parse {path}: {exc}") from exc


def _schema_files(folder: Path) -> list[Path]:
    files = sorted(folder.glob("*.xsd"))
    if not files:
        raise OcxParserError(f"No XSD files found in {folder}")
    return files


def load(
    source: Union[str, Path],
    download_folder: Optional[Path] = None,
) -> list[xsd.Schema]:
    """Load ``source`` and return one parsed ``xsd.Schema`` per XSD file.

    Args:
        source: A local ``.xsd`` file, a folder of ``.xsd`` files, or an http(s) URL.
        download_folder: Where remote schemas are downloaded. Defaults to a
            temporary folder. The folder is cleared before downloading.

    Raises:
        OcxParserError: If the source is missing, empty, or fails to parse.
    """
    if isinstance(source, str) and _is_url(source):
        folder = download_folder or Path(tempfile.mkdtemp(prefix="ocx_schema_"))
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        logger.info(f"Downloading {source} to {folder}")
        downloader = SchemaDownloader(folder)
        downloader.wget(source)
        return [_parse_file(f) for f in _schema_files(folder)]

    path = Path(source)
    if not path.exists():
        raise OcxParserError(f"The source {path} does not exist")
    if path.is_dir():
        return [_parse_file(f) for f in _schema_files(path)]
    return [_parse_file(path)]
