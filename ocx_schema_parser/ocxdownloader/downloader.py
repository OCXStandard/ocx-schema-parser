#  Copyright (c) 2023-2025. OCX Consortium https://3docx.org. See the LICENSE
from pathlib import Path
from typing import Optional
from loguru import logger
from urllib.parse import urlparse

# Third part imports
from xsdata.utils.downloader import Downloader
from xsdata.codegen import opener


# Module imports


def is_valid_uri(uri: str) -> bool:
    try:
        parsed = urlparse(uri)
        # A valid URI must have a scheme
        if not parsed.scheme:
            return False

        # Special case for 'file:' scheme (netloc may be empty)
        if parsed.scheme == "file":
            return bool(parsed.path)

        # For other schemes, both scheme and netloc must be present
        return bool(parsed.netloc)
    except Exception:
        return False


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
        logger.debug(
            f"Writing schema {file_path.resolve()} to folder {self.schema_folder.resolve()}"
        )
        # logger.debug(content)
        self.downloaded[uri] = file_path

        if location:
            self.downloaded[location] = file_path

    def wget(self, uri: str, location: Optional[str] = None):
        """Download handler for any uri input with circular protection.
        Override super class method to handle a local file.

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

        except FileNotFoundError:
            print(f"The file at {uri} was not found.")

        except Exception as e:
            print(f"An error occurred: {e}")
