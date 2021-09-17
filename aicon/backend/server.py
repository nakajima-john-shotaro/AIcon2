import datetime
import json
import multiprocessing
import os
import shutil
import time
from multiprocessing import Event, Process, Queue
from multiprocessing.synchronize import Event as Event_
from pathlib import Path
from pprint import pprint  # pylint: disable=unused-import
from queue import Empty, Full
from queue import Queue as Queue_
from threading import Lock, Thread
from typing import Any, Dict, List, Optional, Union
from urllib.parse import unquote
from uuid import uuid4

from flask import Flask, Response, abort, jsonify, render_template, request
from flask.helpers import make_response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_restful import Api, Resource
from tweepy import API, OAuthHandler, TweepError
from waitress import serve
from werkzeug.exceptions import (BadRequest, Forbidden, HTTPException,
                                 InternalServerError)

from constant import *
from models.big_sleep import big_sleep
from models.deep_daze import deep_daze
from translation import Translation, install_webdriver
from twitter import get_secrets

app: Flask = Flask(
    import_name=__name__, 
    template_folder=os.path.abspath('../frontend/templates'), 
    static_folder=os.path.abspath('../frontend/static')
)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
app.config['RATELIMIT_HEADERS_ENABLED'] = True
Limiter(app, key_func=get_remote_address, default_limits=[RATE_LIMIT])
CORS(app)
api: Api = Api(app)

logger: Logger = get_logger()

_client_data: Dict[str, Dict[str, Union[bool, int, float, str, Queue, Event_]]] = {}
_chc_queue: Queue_ = Queue_(maxsize=1)
_pm_queue: Queue_ = Queue_(maxsize=1)
_valid_response: Dict[str, Union[str, bool, int]] = {
    JSON_CURRENT_ITER: None,
    JSON_IMG_PATH: None,
    JSON_MP4_PATH: None,
    JSON_MODEL_STATUS: False,
}
_lock: Lock = Lock()
_twitter_database: Dict[str, str] = {}

_translator: Translation = Translation("deepl")


def _reset_valid_response() -> None:
        _valid_response[JSON_CURRENT_ITER] = None
        _valid_response[JSON_IMG_PATH] = None
        _valid_response[JSON_MP4_PATH] = None
        _valid_response[JSON_MODEL_STATUS] = False


def _remove_client_data(client_uuid: str) -> bool:
    global _client_data

    result = _client_data.pop(client_uuid, None)

    if result is None:
        return False
    else:
        return True


class GarbageCollector:
    def __init__(
        self,
        target_dirs: List[Path],
        interval: float = 60.,
    ) -> None:
        p: Thread = Thread(target=self.run, args=(interval, target_dirs, ), daemon=True)
        p.start()

    def run(self, interval: float, target_dirs: List[Path]) -> None:
        while True:
            for target_dir in target_dirs:
                if target_dir.exists():
                    dir_list: List[Path] = [p for p in target_dir.iterdir() if p.is_dir()]

                    for dir in dir_list:
                        mtime: float = dir.stat().st_mtime
                        now: float = time.time()

                        if now - mtime > GC_TIMEOUT:
                            logger.info(
                                f"[{dir.stem}]: <<Garbage Collector>> Removed outdated directory {dir}"
                            )
                            shutil.rmtree(dir)
            time.sleep(interval)


class ConnectionHealthChecker:
    def __init__(
        self,
        interval: float = 1.,
    ) -> None:
        p: Thread = Thread(target=self.run, args=(interval, ), daemon=True)
        p.start()

    def run(self, interval: float) -> None:
        _empty_counter: int = 0
    
        while True:
            try:
                _client_data: Dict[str, Dict[str, Union[bool, int, float, str, Queue, Event_]]] = _chc_queue.get_nowait()

                _empty_counter = 0

                if _client_data:
                    for client_uuid, client_data in list(_client_data.items()):
                        last_connection_time: float = client_data[CHC_LAST_CONNECTION_TIME]

                        if time.time() - last_connection_time > CHC_TIMEOUT:
                            client_data[CORE_I2C_EVENT].set()

                            _lock.acquire()
                            _remove_client_data(client_uuid)
                            _lock.release()

                            logger.error(
                                f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause the connection has timed out {CHC_TIMEOUT}s"
                            )
            except Empty:
                _empty_counter += 1

                if _empty_counter > CHC_EMPTY_TOLERANCE:
                    try:
                        for client_uuid, client_data in list(_client_data.items()):
                            client_data[CORE_I2C_EVENT].set()

                            _lock.acquire()
                            _remove_client_data(client_uuid)
                            _lock.release()

                            logger.error(
                                f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause there was no connection for a long time."
                            )
                    except UnboundLocalError:
                        pass

            time.sleep(interval)


class PriorityMonitor:
    def __init__(
        self,
        interval: float = .3,
    ) -> None:
        p: Thread = Thread(target=self.run, args=(interval, ), daemon=True)
        p.start()

    def run(self, interval: float) -> None:
        started_clients: List[str] = []

        while True:
            try:
                _client_data: dict = _pm_queue.get_nowait()
                if _client_data:
                    for client_uuid, client_data in _client_data.items():
                        if (client_data[JSON_PRIORITY] == 1) and (client_uuid not in started_clients):
                            AIconCore(client_data, client_uuid)
                            started_clients.append(client_uuid)
            except Empty:
                pass

            time.sleep(interval)


class AIconCore:
    def __init__(
        self,
        client_data: Dict[str, Union[str, Queue]],
        client_uuid: str,
    ) -> None:
        self.model_name: str = client_data[RECEIVED_DATA][JSON_MODEL_NAME]
        self.client_uuid: str = client_uuid

        p: Process = Process(target=self.run, args=(client_data, ), daemon=True)
        p.start()

    def run(self, client_data: Any) -> None:
        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Start image generation with {self.model_name}")

        if self.model_name == MODEL_NAME_BIG_SLEEP:
            try:
                big_sleep.Imagine(self.client_uuid, client_data)()
            except (AIconOutOfMemoryError, AIconAbortedError, AIconRuntimeError, KeyboardInterrupt) as e:
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> {e}")

        elif self.model_name == MODEL_NAME_DEEP_DAZE:
            try:
                deep_daze.Imagine(self.client_uuid, client_data)()
            except (AIconOutOfMemoryError, AIconAbortedError, AIconRuntimeError, KeyboardInterrupt) as e:
                logger.error(f"[{self.client_uuid}]: <<AIcon Core>> {e}")

        elif self.model_name == MODEL_NAME_DALL_E:
            raise NotImplementedError

        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Finished image generation")


class AIconInterface(Resource):
    def _translate(self, input_text: str, client_uuid: int) -> str:
        if input_text != "":
            logger.info(f"[{client_uuid}]: <<AIcon I/F >> Translating input text")
            output_text: str = _translator.translate(input_text)
            logger.info(f"[{client_uuid}]: <<AIcon I/F >> Translated input text `{input_text}` to `{output_text}`")

            input_text = output_text
        
        return input_text

    def _get_client_priority(self, client_data: Dict[str, Dict[str, Union[bool, int, float, str, Queue, Event_]]], client_uuid: str) -> int:
        return list(client_data.keys()).index(client_uuid) + 1

    def _set_path(self, client_uuid: str) -> None:
        global _client_data

        model_name: str = _client_data[client_uuid][RECEIVED_DATA][JSON_MODEL_NAME]

        img_path: str = os.path.join(IF_BASE_IMG_PATH, model_name, client_uuid)
        mp4_path: str = os.path.join(IF_BASE_MP4_PATH, model_name, client_uuid)

        os.makedirs(img_path, exist_ok=True)
        os.makedirs(mp4_path, exist_ok=True)

        _client_data[client_uuid][JSON_IMG_PATH] = img_path
        _client_data[client_uuid][JSON_MP4_PATH] = mp4_path

    def post(self):
        global _client_data

        received_data: Dict[str, Union[str, bool]] = request.get_json(force=True)

        client_uuid: str = received_data[JSON_HASH]

        res: Dict[str, Optional[Union[str, bool]]] = {
            JSON_HASH: None,
            JSON_PRIORITY: None,
            JSON_CURRENT_ITER: None,
            JSON_COMPLETE: False,
            JSON_IMG_PATH: None,
            JSON_MP4_PATH: None,
            JSON_MODEL_STATUS: False,
        }

        if client_uuid == IF_HASH_INIT:
            client_uuid = str(uuid4())

            logger.info(f"[{IF_HASH_INIT}]: <<AIcon I/F >> Connection requested from an anonymous client. UUID {client_uuid} is assined.")

            received_data[JSON_TEXT] = self._translate(received_data[JSON_TEXT], client_uuid)
            received_data[JSON_CARROT] = self._translate(received_data[JSON_CARROT], client_uuid)
            received_data[JSON_STICK] = self._translate(received_data[JSON_STICK], client_uuid)

            c2i_queue: Queue = Queue()
            c2i_brake_queue: Queue = Queue()
            c2i_event: Event_ = Event()
            i2c_event: Event_ = Event()

            _client_data[client_uuid] = {
                RECEIVED_DATA: received_data,
                JSON_COMPLETE: False,
                CORE_C2I_QUEUE: c2i_queue,
                CORE_C2I_BREAK_QUEUE: c2i_brake_queue,
                CORE_C2I_EVENT: c2i_event,
                CORE_I2C_EVENT: i2c_event,
                CHC_LAST_CONNECTION_TIME: time.time(),
                IF_QUEUE_EMPTY_COUNTER: 0,
            }

            client_priority: int = self._get_client_priority(_client_data, client_uuid)
            _client_data[client_uuid][JSON_PRIORITY] = client_priority

            try:
                _chc_queue.put_nowait(_client_data)
                _pm_queue.put_nowait(_client_data)
            except Full:
                pass

            self._set_path(client_uuid)

            res[JSON_HASH] = client_uuid
            res[JSON_PRIORITY] = client_priority

            return jsonify(res)

        if client_uuid in _client_data.keys():
            client_priority: int = self._get_client_priority(_client_data, client_uuid)

            res[JSON_HASH] = client_uuid
            res[JSON_PRIORITY] = client_priority

            _client_data[client_uuid][JSON_PRIORITY] = client_priority
            _client_data[client_uuid][CHC_LAST_CONNECTION_TIME] = time.time()

            try:
                _chc_queue.put_nowait(_client_data)
            except Full:
                pass

            if received_data[JSON_ABORT]:
                _client_data[client_uuid][CORE_I2C_EVENT].set()

                res[JSON_CURRENT_ITER] = _valid_response[JSON_CURRENT_ITER]
                res[JSON_COMPLETE] = True
                res[JSON_IMG_PATH] = _valid_response[JSON_IMG_PATH]
                res[JSON_MP4_PATH] = _valid_response[JSON_MP4_PATH]
                res[JSON_MODEL_STATUS] = True

                _reset_valid_response()

                try:
                    _pm_queue.put(_client_data, block=True, timeout=3.)
                except Full:
                    pass

                _lock.acquire()
                _remove_client_data(client_uuid)
                _lock.release()

                return jsonify(res)

            if client_priority == 1:
                try:
                    _pm_queue.put_nowait(_client_data)
                except Full:
                    pass

                try:
                    get_data: Dict[str, Union[str, bool, int]] = _client_data[client_uuid][CORE_C2I_QUEUE].get_nowait()

                    _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] = 0

                    res[JSON_CURRENT_ITER] = get_data[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = get_data[JSON_IMG_PATH]
                    res[JSON_MP4_PATH] = get_data[JSON_MP4_PATH]
                    res[JSON_COMPLETE] = get_data[JSON_COMPLETE]
                    res[JSON_MODEL_STATUS] = get_data[JSON_MODEL_STATUS]

                    if get_data[JSON_CURRENT_ITER] is not None:
                        _valid_response[JSON_CURRENT_ITER] = get_data[JSON_CURRENT_ITER]
                    if get_data[JSON_IMG_PATH] is not None:
                        _valid_response[JSON_IMG_PATH] = get_data[JSON_IMG_PATH]
                    if get_data[JSON_MP4_PATH] is not None:
                        _valid_response[JSON_MP4_PATH] = get_data[JSON_MP4_PATH]
                    if get_data[JSON_MODEL_STATUS]:
                        _valid_response[JSON_MODEL_STATUS] = get_data[JSON_MODEL_STATUS]

                    if _client_data[client_uuid][CORE_C2I_EVENT].is_set():
                        get_data = _client_data[client_uuid][CORE_C2I_BREAK_QUEUE].get_nowait()

                        res[JSON_CURRENT_ITER] = get_data[JSON_CURRENT_ITER]
                        res[JSON_IMG_PATH] = get_data[JSON_IMG_PATH]
                        res[JSON_MP4_PATH] = get_data[JSON_MP4_PATH]
                        res[JSON_COMPLETE] = True
                        res[JSON_MODEL_STATUS] = True

                        _lock.acquire()
                        _remove_client_data(client_uuid)
                        _lock.release()

                        logger.info(f"[{client_uuid}]: <<AIcon I/F >> The task is successfully completed. Removed the client data.")


                        _reset_valid_response()

                except Empty:
                    _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] += 1

                    res[JSON_CURRENT_ITER] = _valid_response[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = _valid_response[JSON_IMG_PATH]
                    res[JSON_MP4_PATH] = _valid_response[JSON_MP4_PATH]
                    res[JSON_MODEL_STATUS] = _valid_response[JSON_MODEL_STATUS]

                    if IF_EMPTY_TOLERANCE >= _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] > 3 * IF_EMPTY_TOLERANCE / 4:
                        logger.warning(f"[{client_uuid}]: <<AIcon I/F >> No data has been sent from AIcon Core for a long time. AIcon Core may have crashed.")

                    elif _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] > IF_EMPTY_TOLERANCE:
                        logger.error(f"[{client_uuid}]: <<AIcon I/F >> AIcon Core crashed. Sending an abort signal.")

                        _client_data[client_uuid][CORE_I2C_EVENT].set()

                        res[JSON_COMPLETE] = True

                        _lock.acquire()
                        _remove_client_data(client_uuid)
                        _lock.release()

                        _reset_valid_response()
        else:
            logger.fatal(f"[{client_uuid}]: <<AIcon I/F >> Invalid UUID")
            abort(403, f"Invalid UUID: {client_uuid}")

        return jsonify(res)

    
@app.errorhandler(BadRequest)
@app.errorhandler(Forbidden)
@app.errorhandler(InternalServerError)
def handle_exception(e: HTTPException):
    """Return JSON instead of HTML for HTTP errors."""

    response: Response = e.get_response()
    response.data = json.dumps({
        "code": e.code,
        "name": e.name,
        "description": e.description,
    })
    response.content_type = "application/json"

    return response

@app.route('/')
def index() -> Response:
    return render_template("aicon.html", title="AIcon", name="AIcon")


@app.route('/twitter/callback')
def callback() -> Response:
    oauth_token = request.args.get(TWITTER_OAUTH_TOKEN)
    oauth_verifier = request.args.get(TWITTER_OAUTH_VERIFIER)

    if oauth_token is None:
        logger.error(f"<<AIcon Twitter Control>> Could not get `oauth_token`")
    
    if oauth_verifier is None:
        logger.error(f"<<AIcon Twitter Control>> Could not get `oauth_verifier`")

    client_uuid: str = request.cookies.get(TWITTER_UUID)

    if client_uuid is None:
        logger.error(f"<<AIcon Twitter Control>> Could not get `client_uuid` from cookie")
        raise AIconCookieNotFoundError("Could not get `client_uuid` from cookie")

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

        api: API = API(auth_handler=auth_handler)

        if _twitter_database[client_uuid][TWITTER_MODE] == TWITTER_MODE_ICON:
            img_path = unquote(_twitter_database[client_uuid][TWITTER_IMG_PATH])
            api.update_profile_image(img_path)

        elif _twitter_database[client_uuid][TWITTER_MODE] == TWITTER_MODE_TWEET:
            img_path = unquote(_twitter_database[client_uuid][TWITTER_IMG_PATH])
            api.update_with_media(status="AIconでアイコンを作ったよ！！\n\n#技育展\n#AIcon", filename=img_path)

        else:
            raise AIconRuntimeError("うううううううううううううんんんんんんんんんんんんちちちちちちちちいいいいいいいいいいいいいいいいいいいいいいぃぃぃぃぃぃぃぃぃ")

    except AIconEnvVarNotFoundError as e:
        logger.error(f"<<AIcon Twitter Control>> {e}")

    return render_template("twitter-send.html", title="Twitter-Send", name="Twitter-Send")


@app.route("/twitter/auth", methods=["POST"])
def auth() -> Response:
    received_data: Dict[str, str] = request.get_json(force=True)

    print(f"\n\nimg_path: {received_data[TWITTER_IMG_PATH]}")
    print(f"\n\nmode: {received_data[TWITTER_MODE]}")
    print(f"\n\cookies: {request.cookies}")

    client_uuid: str = request.cookies.get(TWITTER_UUID, None)
    
    secrets: Dict[str, Optional[str]] = get_secrets()

    auth_handler: OAuthHandler = OAuthHandler(
        consumer_key=secrets[TWITTER_CONSUMER_KEY],
        consumer_secret=secrets[TWITTER_CONSUMER_SECRET]
    )

    res: Dict[str, Union[str, int]] = {
        TWITTER_AUTHORIZATION_URL: None,
    }
    res[TWITTER_AUTHORIZATION_URL] = auth_handler.get_authorization_url()

    response = make_response(jsonify(res))

    if client_uuid not in _twitter_database.keys():
        client_uuid: str = str(uuid4())
        max_age: int = 60 * 60 * 24
        expires: int = int(datetime.datetime.now().timestamp()) + max_age

        try:
            response.set_cookie(TWITTER_UUID, value=client_uuid, max_age=max_age, expires=expires)

            _twitter_database[client_uuid] = {
                TWITTER_IMG_PATH: received_data[TWITTER_IMG_PATH],
                TWITTER_MODE: received_data[TWITTER_MODE],
            }
        
        except TweepError as e:
            logger.error(f"<<AIcon Twitter Control>> {e}")
        
        except AIconEnvVarNotFoundError as e:
            logger.error(f"<<AIcon Twitter Control>> {e}")

        finally:
            return make_response(jsonify(res))
    else:
        return make_response(jsonify(res))


if __name__ == "__main__":
    logger.info("<<AIcon>> Seesion started")

    logger.info("<<AIcon>> Installing web driver. This may take some time.")
    install_webdriver()

    multiprocessing.set_start_method("spawn")

    GarbageCollector(target_dirs=[
        Path(IF_BASE_IMG_PATH)/Path(MODEL_NAME_BIG_SLEEP),
        Path(IF_BASE_IMG_PATH)/Path(MODEL_NAME_DEEP_DAZE),
        Path(IF_BASE_IMG_PATH)/Path(MODEL_NAME_DALL_E),
        Path(IF_BASE_MP4_PATH)/Path(MODEL_NAME_BIG_SLEEP),
        Path(IF_BASE_MP4_PATH)/Path(MODEL_NAME_DEEP_DAZE),
        Path(IF_BASE_MP4_PATH)/Path(MODEL_NAME_DALL_E),
    ])
    PriorityMonitor()
    ConnectionHealthChecker()

    AIconInterface()
    api.add_resource(AIconInterface, '/service')

    logger.info(f"<<AIcon>> Running on http://localhost:{PORT}/")

    serve(app, host='0.0.0.0', port=PORT, threads=30)
