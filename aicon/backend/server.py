import os
import time
import json
import multiprocessing
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from multiprocessing import Process, Queue
from threading import Thread, Lock
from queue import Empty, Full, Queue as Queue_
from pprint import pprint # pylint: disable=unused-import

from flask import Flask, Response, jsonify, render_template, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve

from translation import Translation, install_webdriver
from models.deep_daze import deep_daze
from constant import *


app: Flask = Flask(
    import_name=__name__, 
    template_folder=os.path.abspath('../frontend/templates'), 
    static_folder=os.path.abspath('../frontend/static')
)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
app.config['RATELIMIT_HEADERS_ENABLED'] = True
limiter = Limiter(app, key_func=get_remote_address, default_limits=[RATE_LIMIT])
CORS(app)
api: Api = Api(app)

logger: Logger = get_logger()

_client_data: Dict[str, Dict[str, Union[str, Queue]]] = {}
_client_data_queue_chc: Queue_ = Queue_(maxsize=1)
_client_data_queue_pm: Queue_ = Queue_(maxsize=1)
_valid_response: Dict[str, Union[str, bool, int]] = {
    JSON_CURRENT_ITER: None,
    JSON_IMG_PATH: None,
    JSON_MP4_PATH: None,
}
_lock: Lock = Lock()


class AIconCore:
    def __init__(
        self,
        client_data: Dict[str, Union[str, Queue]],
        client_uuid: str,
    ) -> None:
        self.model_name: str = client_data[JSON_MODEL_NAME]
        self.client_uuid: str = client_uuid

        p: Process = Process(target=self.run, args=(client_data, ), daemon=True)
        p.start()

    def run(self, client_data: Any) -> None:
        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Start image generation with {self.model_name}")

        if self.model_name == MODEL_NAME_BIG_SLEEP:
            raise NotImplementedError

        elif self.model_name == MODEL_NAME_DEEP_DAZE:
            try:
                deep_daze.Imagine(self.client_uuid, client_data)()
            except (AIconOutOfMemoryError, AIconAbortedError, AIconRuntimeError, KeyboardInterrupt) as e:
                print(e)
        elif self.model_name == MODEL_NAME_DALL_E:
            raise NotImplementedError

        logger.info(f"[{self.client_uuid}]: <<AIcon Core>> Finished image generation")


class ConnectionHealthChecker:
    def __init__(
        self,
        interval: float = 1.,
    ) -> None:
        p: Thread = Thread(target=self.run, args=(interval, ), daemon=True)
        p.start()

    def run(
        self,
        interval: float,
    ) -> None:
        empty_counter: int = 0
        while True:
            try:
                _client_data: dict = _client_data_queue_chc.get_nowait()
                if _client_data:
                    for client_uuid, client_data in list(_client_data.items()):
                        last_connection_time: float = client_data[CHC_LAST_CONNECTION_TIME]

                        logger.debug(f"[{client_uuid}]: <<Connection Health Checker>> Checking connection health")

                        if time.time() - last_connection_time > CHC_TIMEOUT:
                            _lock.acquire()
                            result = _client_data.pop(client_uuid, None)
                            _lock.release()

                            if result is None:
                                pass
                            else:
                                logger.error(f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause the connection has timed out {CHC_TIMEOUT}s")
                        else:
                            logger.debug(f"[{client_uuid}]: <<Connection Health Checker>> No problem was found")
                empty_counter = 0

            except Empty:
                empty_counter += 1
                
                if empty_counter > CHC_EMPTY_TOLERANCE:
                    try:
                        for client_uuid, client_data in list(_client_data.items()):
                            _lock.acquire()
                            result = _client_data.pop(client_uuid, None)
                            _lock.release()

                            if result is None:
                                pass
                            else:
                                logger.error(f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause there was no connection for a long time.")
                    except UnboundLocalError:
                        pass             

            time.sleep(interval)


class PriorityMonitor:
    def __init__(
        self,
        interval: float = 2.,
    ) -> None:
        p: Thread = Thread(target=self.run, args=(interval, ), daemon=True)
        p.start()

    def run(
        self,
        interval: float,
    ) -> None:
        started_clients: List[str] = []
        while True:
            try:
                _client_data: dict = _client_data_queue_pm.get_nowait()
                if _client_data:
                    for client_uuid, client_data in _client_data.items():
                        if client_data[JSON_PRIORITY] == 1:
                            if client_uuid not in started_clients:
                                _: AIconCore = AIconCore(client_data, client_uuid)
                                started_clients.append(client_uuid)
            except Empty:
                pass

            time.sleep(interval)


class AIconInterface(Resource):
    def __init__(
        self,
        translator_name: str = "deepl",
    ) -> None:
        super().__init__()

        self.translator: Translation = Translation(translator_name)

        self.base_img_path: str = "../frontend/static/dst_img"
        self.base_mp4_path: str = "../frontend/static/dst_mp4"

    def _get_client_priority(self, client_uuid: str) -> int:
        global _client_data

        return list(_client_data.keys()).index(client_uuid) + 1

    def _set_path(self, client_uuid: str) -> None:
        global _client_data

        model_name: str = _client_data[client_uuid][JSON_MODEL_NAME]

        img_path: str = os.path.join(self.base_img_path, model_name, client_uuid)
        mp4_path: str = os.path.join(self.base_mp4_path, model_name, client_uuid)

        os.makedirs(img_path, exist_ok=True)
        os.makedirs(mp4_path, exist_ok=True)

        _client_data[client_uuid][JSON_IMG_PATH] = img_path
        _client_data[client_uuid][JSON_MP4_PATH] = mp4_path

    def _remove_client_data(self, client_uuid: str) -> bool:
        global _client_data

        result = _client_data.pop(client_uuid, None)

        if result is None:
            return False
        else:
            return True
        
    def post(self):
        global _client_data

        received_data: Dict[str, Union[str, bool]] = request.get_json(force=True)
        logger.debug(f"<<AIcon I/F >> Requested from {request.remote_addr} | {request.method} {str(request.url_rule)} {request.environ.get('SERVER_PROTOCOL')} {request.environ.get('HTTP_CONNECTION')}")

        client_uuid: str = received_data[JSON_HASH]

        if client_uuid == IF_HASH_INIT:
            client_uuid = str(uuid4())

            logger.info(f"[{IF_HASH_INIT}]: <<AIcon I/F >> Connection requested from an anonymous client. UUID {client_uuid} is assined.")

            try:
                logger.info(f"[{client_uuid}]: <<AIcon I/F >> Translating input text")
                translated_text: str = self.translator.translate(received_data[JSON_TEXT])
                logger.info(f"[{client_uuid}]: <<AIcon I/F >> Translated text `{received_data[JSON_TEXT]}` to `{translated_text}`")

                c2i_queue: Queue = Queue()
                i2c_queue: Queue = Queue(maxsize=1)

                if received_data[JSON_MODEL_NAME] not in [MODEL_NAME_BIG_SLEEP, MODEL_NAME_DEEP_DAZE, MODEL_NAME_DALL_E]:
                    logger.fatal(f"[{client_uuid}]: <<AIcon I/F >> Invalid model name `{received_data[JSON_MODEL_NAME]}` requested")
                    abort(400, f"Invalid model name {received_data[JSON_MODEL_NAME]}")

                _client_data[client_uuid] = {
                    JSON_MODEL_NAME: received_data[JSON_MODEL_NAME],
                    JSON_TEXT: translated_text,
                    JSON_TOTAL_ITER: received_data[JSON_TOTAL_ITER],
                    JSON_SIZE: received_data[JSON_SIZE],
                    JSON_COMPLETE: False,
                    CORE_C2I_QUEUE: c2i_queue,
                    CORE_I2C_QUEUE: i2c_queue,
                    CHC_LAST_CONNECTION_TIME: time.time(),
                    IF_QUEUE_EMPTY_COUNTER: 0,
                }

                client_priority: int = self._get_client_priority(client_uuid)
                _client_data[client_uuid][JSON_PRIORITY] = client_priority

                try:
                    _client_data_queue_chc.put_nowait(_client_data)
                    _client_data_queue_pm.put_nowait(_client_data)
                except Full:
                    pass

            except KeyError as error_state:
                logger.fatal(f"[{client_uuid}]: <<AIcon I/F >> {error_state}")
                abort(400, error_state)

            self._set_path(client_uuid)

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_uuid,
                JSON_PRIORITY: client_priority,
                JSON_NUM_CLIENTS: len(_client_data),
                JSON_CURRENT_ITER: None,
                JSON_COMPLETE: False,
                JSON_IMG_PATH: None,
                JSON_MP4_PATH: None,
            }

            return jsonify(res)

        if client_uuid in _client_data.keys():
            client_priority = self._get_client_priority(client_uuid)

            logger.info(f"[{client_uuid}]: <<AIcon I/F >> Connection requested from a registered client. Queued Clients: {len(_client_data)} Priority: #{client_priority}")

            put_data: Dict[str, bool] = {
                JSON_ABORT: received_data[JSON_ABORT],
            }

            def _put_data(put_data: Dict[str, bool]) -> None:
                try:
                    _client_data[client_uuid][CORE_I2C_QUEUE].put_nowait(put_data)
                except Full:
                    try:
                        _ = _client_data[client_uuid][CORE_I2C_QUEUE].get_nowait()
                    except Empty:
                        _put_data(put_data)

            _put_data(put_data)

            _client_data[client_uuid][JSON_PRIORITY] = client_priority
            _client_data[client_uuid][CHC_LAST_CONNECTION_TIME] = time.time()

            try:
                _client_data_queue_chc.put_nowait(_client_data)
            except Full:
                pass

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_uuid,
                JSON_PRIORITY: client_priority,
                JSON_NUM_CLIENTS: len(_client_data),
                JSON_CURRENT_ITER: None,
                JSON_COMPLETE: False,
                JSON_IMG_PATH: None,
                JSON_MP4_PATH: None,
            }
    
            if client_priority == 1:
                try:
                    _client_data_queue_pm.put_nowait(_client_data)
                except Full:
                    pass

                client_data: Dict[str, Union[str, Queue]] = _client_data[client_uuid]

                try:
                    get_data: Dict[str, Union[str, bool, int]] = client_data[CORE_C2I_QUEUE].get_nowait()

                    _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] = 0

                    res[JSON_CURRENT_ITER] = get_data[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = get_data[JSON_IMG_PATH]
                    res[JSON_MP4_PATH] = get_data[JSON_MP4_PATH]
                    res[JSON_COMPLETE] = get_data[JSON_COMPLETE]

                    if get_data[JSON_CURRENT_ITER] is not None:
                        _valid_response[JSON_CURRENT_ITER] = get_data[JSON_CURRENT_ITER]
                    if get_data[JSON_IMG_PATH] is not None:
                        _valid_response[JSON_IMG_PATH] = get_data[JSON_IMG_PATH]
                    if get_data[JSON_MP4_PATH] is not None:
                        _valid_response[JSON_MP4_PATH] = get_data[JSON_MP4_PATH]

                    if get_data[JSON_COMPLETE]:
                        if self._remove_client_data(client_uuid):
                            logger.info(f"[{client_uuid}]: <<AIcon I/F >> The task is successfully completed. Removed the client data.")
                        else:
                            logger.warn(f"[{client_uuid}]: <<AIcon I/F >> The task is successfully completed. But failed to remove the client data.")

                except Empty:
                    _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] += 1

                    if IF_EMPTY_TOLERANCE >= _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] > 3 * IF_EMPTY_TOLERANCE / 4:
                        logger.warning(f"[{client_uuid}]: <<AIcon I/F >> No data has been sent from AIcon Core for a long time. AIcon Core may have crashed.")

                    elif _client_data[client_uuid][IF_QUEUE_EMPTY_COUNTER] > IF_EMPTY_TOLERANCE:
                        logger.error(f"[{client_uuid}]: <<AIcon I/F >> AIcon Core crashed. Sending an abort signal.")

                        put_data: Dict[str, bool] = {
                            JSON_ABORT: True,
                        }
                        _client_data[client_uuid][CORE_I2C_QUEUE].put_nowait(put_data)
                        res[JSON_COMPLETE] = True

                    res[JSON_CURRENT_ITER] = _valid_response[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = _valid_response[JSON_IMG_PATH]
                    res[JSON_MP4_PATH] = _valid_response[JSON_MP4_PATH]
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


    @app.route("/")
    def index():
        return render_template("aicon.html", title="AIcon", name="AIcon")


if __name__ == "__main__":
    logger.info("<<AIcon>> Seesion started")

    install_webdriver()

    multiprocessing.set_start_method("spawn")

    PriorityMonitor()
    ConnectionHealthChecker()

    AIconInterface()
    api.add_resource(AIconInterface, '/service')

    serve(app, host='0.0.0.0', port=5050, threads=30)
