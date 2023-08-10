#  Copyright (c) 2023. OCX Consortium https://3docx.org. See the LICENSE
# System imports
from typing import Optional
from pathlib import Path
# Third part imports
from xsdata.utils.downloader import Downloader
from loguru import logger
#Module imports
from ocx_schema_parser.utils.utilities import root_dir



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
        file_path = self.schema_folder / name
        file_path.write_text(content, encoding="utf-8")
        logger.debug(f'Writing schema {file_path.resolve()} to folder {self.schema_folder.resolve()}')
        # logger.debug(content)
        self.downloaded[uri] = file_path

        if location:
            self.downloaded[location] = file_path
