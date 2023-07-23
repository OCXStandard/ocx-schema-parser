#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from pathlib import Path

from ocx_schema_parser.ocxtransformer.downloader import SchemaDownloader
from ocx_schema_parser import WORKING_DRAFT


def test_download(datadir: Path):
    downloader = SchemaDownloader(datadir)
    downloader.wget(WORKING_DRAFT)
    files = [file for file in datadir.glob('*')]
    assert len(files) == 3
