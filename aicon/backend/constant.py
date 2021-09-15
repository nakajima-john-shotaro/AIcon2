"""constant.py"""

from logging import (
    StreamHandler, Logger, Formatter, 
    getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
)
from typing import List

RATE_LIMIT: str = "1000 per minute"
PORT: int = 5050

RECEIVED_DATA: str = "received_data"

JSON_MODEL_NAME: str = "model_name"
JSON_TEXT: str = "text"
JSON_CURRENT_ITER: str = "current_iter"
JSON_SIZE: str = "size"
JSON_HASH: str = "hash"
JSON_COMPLETE: str = "complete"
JSON_ABORT: str = "abort"
JSON_PRIORITY: str = "priority"
JSON_NUM_CLIENTS: str = "num_clients"
JSON_IMG_PATH: str = "img_path"
JSON_MP4_PATH: str = "mp4_path"

JSON_GAE: int = "gae"
JSON_SEED: int = "seed"
JSON_TOTAL_ITER: str = "total_iter"
JSON_BACKBONE: str = "backbone"

JSON_NUM_LAYER: int = "num_layer"
JSON_HIDDEN_SIZE: int = "hidden_size"
JSON_BATCH_SIZE: int = "batch_size"

JSON_CARROT: str = "carrot"
JSON_STICK: str = "stick"

MODEL_NAME_BIG_SLEEP: str = "BigSleep"
MODEL_NAME_DEEP_DAZE: str = "DeepDaze"
MODEL_NAME_DALL_E: str = "DALL-E"

ACCEPTABLE_BACK_BONE: List[str] = ["RN50", "RN101", "RN50x4", "ViT-B32"]

IF_HASH_INIT: str = "00000000-0000-0000-0000-000000000000"
IF_BASE_IMG_PATH: str = "../frontend/static/dst_img"
IF_BASE_MP4_PATH: str = "../frontend/static/dst_mp4"
IF_QUEUE_EMPTY_COUNTER: str = "queue_empty_counter"
IF_EMPTY_TOLERANCE: int = 100

CORE_COMPATIBLE_PYTORCH_VERSION: str = "1.7.1"
CORE_C2I_QUEUE: str = "c2i_queue"
CORE_I2C_QUEUE: str = "i2c_queue"

CHC_TIMEOUT: float = 7.0
CHC_EMPTY_TOLERANCE: int = 5
CHC_LAST_CONNECTION_TIME: str = "last_connection_time"

GC_TIMEOUT: int = 3600


class CustomFormatter(Formatter):

    gray = "\x1b[98;1m"
    blue = "\x1b[94;1m"
    green = "\x1b[92;1m"
    yellow = "\x1b[93;1m"
    red = "\x1b[91;1m"
    red_underlined = "\x1b[91;1;4m"
    reset = "\x1b[0m"

    format = "[%(levelname)-8s] [%(asctime)s]: %(message)s (%(filename)s:L%(lineno)d)"

    FORMATS = {
        DEBUG: blue + format + reset,
        INFO: gray + format + reset,
        WARNING: yellow + format + reset,
        ERROR: red + format + reset,
        CRITICAL: red_underlined + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = Formatter(log_fmt)

        return formatter.format(record)


def get_logger(name: str = "aicon", level: int = INFO):
    logger: Logger = getLogger(name)
    logger.propagate = False

    if not logger.hasHandlers():
        stream_handler: StreamHandler = StreamHandler()
        stream_handler.setLevel(level)
        stream_handler.setFormatter(CustomFormatter())

        logger.addHandler(stream_handler)
        logger.setLevel(level)

    return logger


class AIconBaseException(Exception):
    def __init__(self, arg="AIcon internal error") -> None:
        self.arg = arg


class AIconRuntimeError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconValueError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconTypeError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconOutOfMemoryError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconFileNotFoundError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconAbortedError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"
