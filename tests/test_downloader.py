#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from pathlib import Path

from ocx_schema_parser import WORKING_DRAFT
from ocx_schema_parser.ocxdownloader.downloader import SchemaDownloader


def test_download(datadir: Path):
    downloader = SchemaDownloader(datadir)
    downloader.wget(WORKING_DRAFT)
    files = list(datadir.glob("*.xsd"))
    assert len(files) == 3
