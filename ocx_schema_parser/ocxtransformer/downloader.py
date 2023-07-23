#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE

from xsdata.utils.downloader import Downloader, logger
from ocx_schema_parser.utils.utilities import root_dir
from typing import Optional
from pathlib import Path


class SchemaDownloader(Downloader):
    """Downloader specialisation class.

    Arguments:
        output: The location of the download folder relative to current directory

    Args:
        schema_folder: The path to the schema download folder
    """
    def __init__(self, output: Path):
        super().__init__(output)
        self.schema_folder = output

    def write_file(self, uri: str, location: Optional[str], content: str):
        """
        Override super class method and output all schemas into one folder.

        Arguments:
            uri: the location of the schema to download. All referenced schemas will be collected.


        """
        # Get the uri file name
        name = Path(uri).name
        file_path = Path(root_dir()) / self.schema_folder / name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")

        logger.debug("Writing %s", file_path)
        self.downloaded[uri] = file_path

        if location:
            self.downloaded[location] = file_path
