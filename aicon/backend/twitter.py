import os
from typing import Dict, Optional, Union

from tweepy import OAuthHandler, API, TweepError
from flask import Response, make_response, jsonify
from flask_restful import Resource
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

            raise AIconEnvVarNotFindError(f"Cannot find secret environment variable")
    
    return secrets


class Authorization(Resource):
    def post(self) -> Response:
        res: Dict[str, Union[str, int]] = {
            TWITTER_AUTHORIZATION_URL: None,
        }

        try:
            secrets: Dict[str, Optional[str]] = get_secrets()

            auth_handler: OAuthHandler = OAuthHandler(
                consumer_key=secrets[TWITTER_CONSUMER_KEY],
                consumer_secret=secrets[TWITTER_CONSUMER_SECRET]
            )

            res[TWITTER_AUTHORIZATION_URL] = auth_handler.get_authorization_url()
        
        except TweepError as e:
            logger.error(f"<<AIcon Twitter Control>> {e}")
        
        except AIconEnvVarNotFindError as e:
            logger.error(f"<<AIcon Twitter Control>> {e}")

        finally:
            return make_response(jsonify(res))
