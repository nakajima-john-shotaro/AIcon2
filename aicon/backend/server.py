import os
import time
import json
import datetime # pylint: disable=unused-import
from typing import Any, Dict, Optional, Union
from uuid import uuid4
from multiprocessing import Process, Queue, synchronize, Manager, Lock
from queue import Empty
from pprint import pprint # pylint: disable=unused-import
from logging import StreamHandler, Logger, getLogger, INFO

from flask import Flask, Response, jsonify, render_template, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve

from translation import Translation
from constant import *


app: Flask = Flask(
    import_name=__name__, 
    template_folder=os.path.abspath('../frontend/templates'), 
    static_folder=os.path.abspath('../frontend/static')
)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
CORS(app)
api: Api = Api(app)

stream_handler: StreamHandler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(CustomFormatter())
logger: Logger = getLogger()
logger.addHandler(stream_handler)
logger.setLevel(INFO)

manager = Manager()
_client_data: Dict[str, Dict[str, Union[str, Queue]]] = manager.dict()


# debag
class DummyModel():
    def __init__(
        self,
        client_uuid: str,
        queue: Queue,
    ) -> None:
        self.client_uuid: str = client_uuid
        self.queue: Queue = queue

    def run(self):
        for i in range(10):
            data: Dict[str, str] = {
                "client_uuid": self.client_uuid,
                JSON_CURRENT_ITER: str(i),
                JSON_IMG_PATH: f"/home/aicon/img/{self.client_uuid}/{i}",
                JSON_GIF_PATH: f"/home/aicon/gif/{self.client_uuid}/{i}",
                JSON_COMPLETE: False
            }
            self.queue.put(data)
            time.sleep(2)
        
        data: Dict[str, str] = {
            "client_uuid": self.client_uuid,
            JSON_CURRENT_ITER: "10",
            JSON_IMG_PATH: f"/home/aicon/img/{self.client_uuid}/{i}",
            JSON_GIF_PATH: f"/home/aicon/gif/{self.client_uuid}/{i}",
            JSON_COMPLETE: True
        }
        self.queue.put(data)

        logger.info(f"[{self.client_uuid}]: Completed image generation")


class AIconCore:
    def __init__(
        self,
        model_name: str,
        client_uuid: str,
        args: Any,
        queue: Queue = Queue(),
    ) -> None:
        self.model_name: str = model_name
        self.client_uuid: str = client_uuid

        p: Process = Process(target=self.run, args=(queue, args, ), daemon=True)
        p.start()

    def run(self, queue: Queue, args: Any) -> None:
        logger.info(f"[{self.client_uuid}]: Start image generation with {self.model_name}")

        model = DummyModel(self.client_uuid, queue)
        if self.model_name == MODEL_NAME_BID_SLEEP:
            model.run()
        elif self.model_name == MODEL_NAME_DEEP_DAZE:
            model.run()
        elif self.model_name == MODEL_NAME_DALL_E:
            model.run()
        else:
            logger.fatal(f"[{self.client_uuid}]: Invalid model name `{self.model_name}` requested")
            abort(BadRequest, f"Invalid model name {self.model_name}")


class ConnectionHealthChecker:
    def __init__(
        self,
        lock: Union[synchronize.Lock, synchronize.RLock],
        interval: float = 5.,
    ) -> None:
        p: Process = Process(target=self.run, args=(lock, interval), daemon=True)
        p.start()

    def run(
        self, 
        lock: Union[synchronize.Lock, synchronize.RLock], 
        interval: float,
    ) -> None:

        while True:
            global _client_data
            print(bool(_client_data))
            if _client_data:
                print("うんちぶりぶりっ")
                for client_uuid, client_data in _client_data.items():
                    last_connection_time: float = client_data["last_connection_time"]

                    print(f"now: {time.time()} last_connection_time: {last_connection_time}")

                    logger.info(f"[{client_uuid}]: <<Connection Health Checker>> Checking connection health")

                    if time.time() - last_connection_time > CHC_TIMEOUT:
                        lock.acquire()
                        result = _client_data.pop(client_uuid, None)
                        lock.release()

                        if result is None:
                            return False
                        else:
                            logger.error(f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause the connection has timed out {CHC_TIMEOUT}s")
            
            time.sleep(interval)


class AIcon(Resource):
    def __init__(
        self,
        translator_name: str = "deepl",
    ) -> None:
        super().__init__()

        self.translator: Translation = Translation(translator_name)

        self.base_img_path: str = "../frontend/static/dst_img"
        self.base_gif_path: str = "../frontend/static/dst_gif"

    def _get_client_priority(self, client_uuid: str) -> int:
        global _client_data

        return list(_client_data.keys()).index(client_uuid) + 1

    def _set_path(self, client_uuid: str) -> None:
        global _client_data

        model_name: str = _client_data[client_uuid][JSON_MODEL_NAME]

        img_path: str = os.path.join(self.base_img_path, model_name, client_uuid)
        gif_path: str = os.path.join(self.base_gif_path, model_name, client_uuid)

        os.makedirs(img_path, exist_ok=True)
        os.makedirs(gif_path, exist_ok=True)

        _client_data[client_uuid][JSON_IMG_PATH] = img_path
        _client_data[client_uuid][JSON_GIF_PATH] = gif_path

    def _remove_client_data(self, client_uuid: str) -> bool:
        global _client_data

        result = _client_data.pop(client_uuid, None)

        if result is None:
            return False
        else:
            return True
        
    def post(self):
        global _client_data

        received_data: Dict[str, Any] = request.get_json(force=True)
        logger.info(f"Requested from {request.remote_addr} | {request.method} {str(request.url_rule)} {request.environ.get('SERVER_PROTOCOL')} {request.environ.get('HTTP_CONNECTION')}")

        client_uuid: str = received_data[JSON_HASH]

        if client_uuid == P_HASH_INIT:
            client_uuid: str = str(uuid4())

            logger.info(f"[{P_HASH_INIT}]: Connection requested from a non-registered client. UUID {client_uuid} is assined.")

            try:
                translated_text: str = self.translator.translate(received_data[JSON_TEXT])
                logger.info(f"[{client_uuid}]: Translated text `{received_data[JSON_TEXT]}` to `{translated_text}`")

                queue: Queue = Queue()

                _client_data[client_uuid] = {
                    JSON_MODEL_NAME: received_data[JSON_MODEL_NAME],
                    JSON_TEXT: translated_text,
                    JSON_TOTAL_ITER: received_data[JSON_TOTAL_ITER],
                    JSON_SIZE: received_data[JSON_SIZE],
                    JSON_ABORT: received_data[JSON_ABORT],
                    JSON_COMPLETE: False,
                    "queue": queue,
                    "last_connection_time": time.time()
                }

            except KeyError as error_state:
                logger.fatal(f"[{client_uuid}]: {error_state}")
                abort(BadRequest, error_state)

            self._set_path(client_uuid)

            client_priority: int = self._get_client_priority(client_uuid)

            if client_priority == 1:
                aicon_core: AIconCore = AIconCore(received_data[JSON_MODEL_NAME], client_uuid, translated_text, queue)

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_uuid,
                JSON_PRIORITY: client_priority,
                JSON_NUM_CLIENTS: len(_client_data),
                JSON_CURRENT_ITER: "0",
                JSON_COMPLETE: False,
                JSON_IMG_PATH: None,
                JSON_GIF_PATH: None,
            }

            return jsonify(res)

        if client_uuid in _client_data.keys():
            logger.info(f"[{client_uuid}]: Connection requested from a registered client")

            _client_data[client_uuid][JSON_ABORT] = received_data[JSON_ABORT]
            _client_data[client_uuid]["last_connection_time"] = time.time()

            client_priority = self._get_client_priority(client_uuid)

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_uuid,
                JSON_PRIORITY: client_priority,
                JSON_NUM_CLIENTS: len(_client_data),
                JSON_CURRENT_ITER: "0",
                JSON_COMPLETE: False,
                JSON_IMG_PATH: None,
                JSON_GIF_PATH: None,
            }
    
            if client_priority == 1:
                logger.info(f"[{client_uuid}]: This client is #{client_priority}.")

                client_data: Dict[str, Union[str, Queue]] = _client_data[client_uuid]

                try:
                    queued_data: Dict[str, str] = client_data["queue"].get(timeout=1.)

                    res[JSON_CURRENT_ITER] = queued_data[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = queued_data[JSON_IMG_PATH]
                    res[JSON_GIF_PATH] = queued_data[JSON_GIF_PATH]
                    res[JSON_COMPLETE] = queued_data[JSON_COMPLETE]
                except Empty:
                    logger.warning(f"[{client_uuid}]: Queue is empty")

                if queued_data[JSON_COMPLETE]:
                    self._remove_client_data(client_uuid)
                    logger.info(f"[{client_uuid}]: Removed clients data bacause the task is completed")
            else:
                logger.warning(f"[{client_uuid}]: {len(_client_data)} clients are queued. This client is #{client_priority}. Skipping the task.")
        else:
            logger.fatal(f"[{client_uuid}]: Invalid UUID")
            abort(Forbidden, f"Invalid UUID: {client_uuid}")

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
    logger.info("Seesion started")

    lock: Union[synchronize.Lock, synchronize.RLock] = Lock()

    chc: ConnectionHealthChecker = ConnectionHealthChecker(lock)

    aicon: AIcon = AIcon()
    api.add_resource(AIcon, '/service')

    serve(app, host='0.0.0.0', port=5050, threads=10)
