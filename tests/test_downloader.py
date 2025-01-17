#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE

from pathlib import Path
import shutil
from ocx_schema_parser import WORKING_DRAFT
from ocx_schema_parser.ocxdownloader.downloader import SchemaDownloader

temp = Path("./temp")


def test_download_from_url():
    if not temp.exists():
        temp.mkdir(parents=True)
    downloader = SchemaDownloader(temp)
    downloader.wget(WORKING_DRAFT)
    files = list(temp.glob("*.xsd"))
    assert len(files) == 3
    # Clean up
    if temp.exists():
        shutil.rmtree(temp)


def test_download_from_file(shared_datadir: Path):
    if not temp.exists():
        temp.mkdir(parents=True)
    downloader = SchemaDownloader(temp)
    ocx_schema = shared_datadir / "OCX_Schema.xsd"
    downloader.wget(str(ocx_schema.resolve()))
    files = list(temp.glob("*.xsd"))
    assert len(files) == 3
    # Clean up
    if temp.exists():
        shutil.rmtree(temp)
