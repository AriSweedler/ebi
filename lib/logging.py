import logging
import os
from pathlib import Path


def setup_logging():
    # Create a formatter to define the log message format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Find where to log
    data_root = os.getenv("XDG_DATA_HOME")
    logdir = Path(data_root) / "ebi"
    logdir.mkdir(exist_ok=True)

    # Create a file handler to log messages to a file
    file_handler = logging.FileHandler(logdir / "ebi.log")
    file_handler.setLevel(
        logging.DEBUG
    )  # Set the file handler level to DEBUG to capture all messages
    file_handler.setFormatter(formatter)

    # Create a stream handler to log info messages and above to stdout
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)  # Set the stream handler level to INFO
    stream_handler.setFormatter(formatter)

    # Get the root logger and set its level to INFO
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)
