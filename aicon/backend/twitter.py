import os
from urllib.parse import unquote
from typing import Dict, Optional, Union

from tweepy import OAuthHandler, API, TweepError
from flask import Response, make_response, jsonify, render_template, request
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
    

class Callback(Resource):
    def get(self) -> Response:
        oauth_token = request.args.get(TWITTER_OAUTH_TOKEN)
        oauth_verifier = request.args.get(TWITTER_OAUTH_VERIFIER)

        if oauth_token is None:
            logger.error(f"<<AIcon Twitter Control>> Cannot get `oauth_token`")
        
        if  oauth_verifier is None:
            logger.error(f"<<AIcon Twitter Control>> Cannot get `oauth_verifier`")

        return render_template("twitter-callback.html", oauth_token=oauth_token, oauth_verifier=oauth_verifier)


class Executor(Resource):
    def get(self) -> Response:
        oauth_token = request.args.get(TWITTER_OAUTH_TOKEN)
        oauth_verifier = request.args.get(TWITTER_OAUTH_VERIFIER)

        try:
            secrets: Dict[str, Optional[str]] = get_secrets()

            auth_handler: OAuthHandler = OAuthHandler(
                consumer_key=secrets[TWITTER_CONSUMER_KEY],
                consumer_secret=secrets[TWITTER_CONSUMER_SECRET]
            )

            auth_handler.request_token = {
                TWITTER_OAUTH_TOKEN: oauth_token,
                TWITTER_OAUTH_TOKEN_SECRET: oauth_verifier
            }

            auth_handler.get_access_token(oauth_verifier)

            img_path: str = request.cookies.get(TWITTER_IMG_PATH)
            mode: str = request.cookies.get(TWITTER_MODE)

            api: API = API(auth_handler=auth_handler)

            if mode == TWITTER_MODE_ICON:
                img_path = unquote(img_path)
                api.update_profile_image(img_path)

            elif mode == TWITTER_MODE_TWEET:
                img_path = unquote(img_path)
                api.update_with_media(status="AIconでアイコンを作ったよ！！\n\n#技育展\n#AIcon", filename=img_path)

            return render_template("twitter-send.html", title="Twitter-Send", name="Twitter-Send")


        except AIconEnvVarNotFindError as e:
            logger.error(f"<<AIcon Twitter Control>> {e}")
