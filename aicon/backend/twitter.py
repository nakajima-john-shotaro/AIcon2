import os
from typing import Dict, Optional

from constant import *


logger: Logger = get_logger()


def get_secrets() -> Dict[str, Optional[str]]:
    secrets: Dict[str, Optional[str]] = {
        TWITTER_CONSUMER_KEY: os.environ.get(TWITTER_CONSUMER_KEY, default=None),
        TWITTER_CONSUMER_SECRET: os.environ.get(TWITTER_CONSUMER_SECRET, default=None),
        TWITTER_ACCESS_TOKEN: os.environ.get(TWITTER_ACCESS_TOKEN, default=None),
        TWITTER_ACCESS_TOKEN_SECRET: os.environ.get(TWITTER_ACCESS_TOKEN_SECRET, default=None),
    }

    for key, value in secrets.items():
        if value is None:
            logger.fatal(f"<<AIcon Twitter Control>> Cannot find secret environment variable {key}")

            raise AIconEnvVarNotFoundError(f"Cannot find secret environment variable")
    
    return secrets
