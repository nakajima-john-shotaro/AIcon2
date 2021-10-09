"""constant.py"""

from logging import (
    StreamHandler, Logger, Formatter, 
    getLogger, DEBUG, INFO, WARNING, ERROR, CRITICAL
)
from typing import List
from shutil import get_terminal_size


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
JSON_IMG_PATH: str = "img_path"
JSON_MP4_PATH: str = "mp4_path"
JSON_MODEL_STATUS: str = "model_status"
JSON_TARGET_IMG: str = "target_img"
JSON_SOURCE_IMG: str = "source_img"
JSON_DIAGNOSTICS: str = "diagnostics"

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

ACCEPTABLE_MODEL: List[str] = [MODEL_NAME_BIG_SLEEP, MODEL_NAME_DEEP_DAZE, MODEL_NAME_DALL_E]

BACKBONE_NAME_RN50: str = "RN50"
BACKBONE_NAME_RN101: str = "RN101"
BACKBONE_NAME_RN50x4: str = "RN50x4"
BACKBONE_NAME_ViTB32: str = "ViT-B32"

PRETRAINED_BACKBONE_MODEL_PATH: str = "/home/user/.cache"

ACCEPTABLE_BACKBONE: List[str] = [BACKBONE_NAME_RN50, BACKBONE_NAME_RN101, BACKBONE_NAME_RN50x4, BACKBONE_NAME_ViTB32]

IF_HASH_INIT: str = "00000000-0000-0000-0000-000000000000"
IF_BASE_IMG_PATH: str = "../frontend/static/dst_img"
IF_BASE_MP4_PATH: str = "../frontend/static/dst_mp4"
IF_QUEUE_EMPTY_COUNTER: str = "queue_empty_counter"
IF_EMPTY_TOLERANCE: int = 100
IF_DIAGNOSTICS_OK: int = 0b0000
IF_DIAGNOSTICS_DEEPL: int = 0b0001
IF_DIAGNOSTICS_MEMORY: int = 0b0010
IF_DIAGNOSTICS_UNEXPECTED: int = 0b0100
IF_DIAGNOSTICS_RESERVED: int = 0b1000

CORE_COMPATIBLE_PYTORCH_VERSION: str = "1.7.1"
CORE_C2I_QUEUE: str = "c2i_queue"
CORE_C2I_BREAK_QUEUE: str = "c2i_brake_queue"
CORE_C2I_EVENT: str = "c2i_event"
CORE_C2I_ERROR_EVENT: str = "c2i_error_event"
CORE_I2C_EVENT: str = "i2c_event"

CHC_TIMEOUT: float = 7.0
CHC_EMPTY_TOLERANCE: int = 5
CHC_LAST_CONNECTION_TIME: str = "last_connection_time"

GC_TIMEOUT: int = 3600

TEST_DIAGNOSTICS: str = "pre_diagnostics"
TEST_FRONTEND_VERSION: str = "version"

TEST_DIAGNOSTICS_OK: int = 0b0000
TEST_DIAGNOSTICS_MINOR_VERSION_CONFLICT: int = 0b0001
TEST_DIAGNOSTICS_MAJOR_VERSION_CONFLICT: int = 0b0010
TEST_DIAGNOSTICS_GPU_AVAILABLE: int = 0b0100
TEST_DIAGNOSTICS_TENSOR_CORE_AVAILABLE: int = 0b1000

TWITTER_CONSUMER_KEY: str = "CONSUMER_KEY"
TWITTER_CONSUMER_SECRET: str = "CONSUMER_SECRET"
TWITTER_ACCESS_TOKEN: str = "ACCESS_TOKEN"
TWITTER_ACCESS_TOKEN_SECRET: str = "ACCESS_TOKEN_SECRET"
TWITTER_AUTHORIZATION_URL: str = "authorization_url"
TWITTER_ENV_VAR: str = "is_set_env_var"
TWITTER_OAUTH_TOKEN: str = "oauth_token" 
TWITTER_OAUTH_VERIFIER: str = "oauth_verifier"
TWITTER_OAUTH_TOKEN_SECRET: str = "oauth_token_secret"
TWITTER_IMG_PATH: str = JSON_IMG_PATH
TWITTER_TEXT: str = JSON_TEXT
TWITTER_MODE: str = "mode"
TWITTER_UUID: str = "uuid"

TWITTER_MODE_ICON: str = "icon"
TWITTER_MODE_TWEET: str = "tweet"


class CustomFormatter(Formatter):

    gray = "\x1b[98;1m"
    blue = "\x1b[94;1m"
    green = "\x1b[92;1m"
    yellow = "\x1b[93;1m"
    red = "\x1b[91;1m"
    red_underlined = "\x1b[91;1;4m"
    reset = "\x1b[0m"

    format = "[%(levelname)-8s] [%(asctime)s]: %(message)s"

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
        logger.setLevel(DEBUG)

    return logger


def truncate(string: str, length: int = get_terminal_size().columns - 41, ellipsis: str = "...") -> str:
    length: int = get_terminal_size().columns - 41

    return string[:length] + (ellipsis if string[length:] else '')


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


class AIconEnvVarNotFoundError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"


class AIconCookieNotFoundError(AIconBaseException):
    def __str__(self):
        return f"{self.arg}"
