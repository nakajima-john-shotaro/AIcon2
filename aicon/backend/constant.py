"""constant.py"""

import logging

JSON_MODEL_NAME: str = "model_name"
JSON_TEXT: str = "text"
JSON_CURRENT_ITER: str = "current_iter"
JSON_TOTAL_ITER: str = "total_iter"
JSON_SIZE: str = "size"
JSON_HASH: str = "hash"
JSON_COMPLETE: str = "complete"
JSON_ABORT: str = "abort"
JSON_PRIORITY: str = "priority"
JSON_NUM_CLIENTS: str = "num_clients"
JSON_IMG_PATH: str = "img_path"
JSON_GIF_PATH: str = "git_path"

MODEL_NAME_BID_SLEEP: str = "BigSleep"
MODEL_NAME_DEEP_DAZE: str = "DeepDaze"
MODEL_NAME_DALL_E: str = "DALL-E"

P_HASH_INIT: str = "00000000-0000-0000-0000-000000000000"

CHC_TIMEOUT: float = 7.0
CHC_EMPTY_TOLERANCE: int = 5

MAIN_EMPTY_TOLERANCE: int = 10


class CustomFormatter(logging.Formatter):

    gray = "\x1b[38;1m"
    blue = "\x1b[34;1m"
    green = "\x1b[32;1m"
    yellow = "\x1b[33;1m"
    red = "\x1b[31;1m"
    red_underlined = "\x1b[31;1;4m"
    reset = "\x1b[0m"

    format = "[%(levelname)s] [%(asctime)s]: %(message)s (%(filename)s:L%(lineno)d)"

    FORMATS = {
        logging.DEBUG: blue + format + reset,
        logging.INFO: gray + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: red_underlined + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)

        return formatter.format(record)