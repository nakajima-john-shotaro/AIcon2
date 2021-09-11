import os
import time
import json
import datetime # pylint: disable=unused-import
import multiprocessing
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from multiprocessing import Process, Queue
from threading import Thread, Lock
from queue import Empty, Full, Queue as Queue_
from pprint import pprint # pylint: disable=unused-import
from logging import StreamHandler, Logger, getLogger, INFO

from flask import Flask, Response, jsonify, render_template, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve

from translation import Translation
from models.deep_daze.deep_daze import Imagine
from constant import *


app: Flask = Flask(
    import_name=__name__, 
    template_folder=os.path.abspath('../frontend/templates'), 
    static_folder=os.path.abspath('../frontend/static')
)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
app.config['RATELIMIT_HEADERS_ENABLED'] = True
limiter = Limiter(app, key_func=get_remote_address, default_limits=["100 per minute"])
CORS(app)
api: Api = Api(app)

stream_handler: StreamHandler = StreamHandler()
stream_handler.setLevel(INFO)
stream_handler.setFormatter(CustomFormatter())
logger: Logger = getLogger()
logger.addHandler(stream_handler)
logger.setLevel(INFO)

_client_data: Dict[str, Dict[str, Union[str, Queue]]] = {}
_client_data_queue_chc: Queue_ = Queue_(maxsize=1)
_client_data_queue_pm: Queue_ = Queue_(maxsize=1)
_lock: Lock = Lock()


# debag
import cv2
import numpy
class DummyModel():
    def __init__(
        self,
        client_uuid: str,
    ) -> None:
        self.client_uuid: str = client_uuid

    def run(self, client_data: Dict[str, Union[str, Queue]]):
        queue: Queue = client_data["queue"]
        total_iteration: int = int(client_data[JSON_TOTAL_ITER])
        for i in range(total_iteration):
            img: numpy.ndarray = numpy.zeros((client_data[JSON_SIZE], client_data[JSON_SIZE]))
            cv2.putText(img, f"{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{i:06d}.png", (0, 128), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.imwrite(f"../frontend/static/dst_img/{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{i:06d}.png", img)
            data: Dict[str, str] = {
                "client_uuid": self.client_uuid,
                JSON_CURRENT_ITER: str(i),
                JSON_IMG_PATH: f"../static/dst_img/{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{i:06d}.png",
                JSON_GIF_PATH: f"../static/dst_gif/{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{i:06d}.png",
                JSON_COMPLETE: False
            }
            queue.put(data)
            time.sleep(2)
        
        data: Dict[str, str] = {
            "client_uuid": self.client_uuid,
            JSON_CURRENT_ITER: str(total_iteration),
            JSON_IMG_PATH: f"../static/dst_img/{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{total_iteration-1:06d}.png",
            JSON_GIF_PATH: f"../static/dst_gif/{client_data[JSON_MODEL_NAME]}/{self.client_uuid}/{total_iteration-1:06d}.png",
            JSON_COMPLETE: True
        }
        queue.put(data)

        logger.info(f"[{self.client_uuid}]: Completed image generation")


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
        logger.info(f"[{self.client_uuid}]: Start image generation with {self.model_name}")

        model = DummyModel(self.client_uuid)
        imagine = Imagine(
            text=client_data[JSON_TEXT],
            img=None,
            lr=1e-5,
            num_layers=16,
            batch_size=1,
            gradient_accumulate_every=4,
            epochs=10,
            iterations=1000,
            image_width=int(client_data[JSON_SIZE]),
            save_every=1,
            save_progress=True,
            seed=42,
            open_folder=False,
            save_date_time=False,
            start_image_path=None,
            start_image_train_iters=50,
            theta_initial=None,
            theta_hidden=None,
            start_image_lr=3e-4,
            lower_bound_cutout=0.1,
            upper_bound_cutout=1.0,
            saturate_bound=False,
            create_story=False,
            story_start_words=5,
            story_words_per_epoch=5,
            story_separator=None,
            averaging_weight=0.3,
            gauss_sampling=False,
            gauss_mean=0.6,
            gauss_std=0.2,
            do_cutout=True,
            center_bias=False,
            center_focus=2,
            jit=False,
            hidden_size=256,
            model_name="ViT-B/32",
            optimizer="AdamP",
            save_gif=False,
            save_video=False,
        )
        if self.model_name == MODEL_NAME_BID_SLEEP:
            imagine()
        elif self.model_name == MODEL_NAME_DEEP_DAZE:
            imagine()
        elif self.model_name == MODEL_NAME_DALL_E:
            imagine()
        else:
            logger.fatal(f"[{self.client_uuid}]: Invalid model name `{self.model_name}` requested")
            abort(400, f"Invalid model name {self.model_name}")


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
                        last_connection_time: float = client_data["last_connection_time"]

                        logger.info(f"[{client_uuid}]: <<Connection Health Checker>> Checking connection health")

                        if time.time() - last_connection_time > CHC_TIMEOUT:
                            _lock.acquire()
                            result = _client_data.pop(client_uuid, None)
                            _lock.release()

                            if result is None:
                                pass
                            else:
                                logger.error(f"[{client_uuid}]: <<Connection Health Checker>> Removed clients data bacause the connection has timed out {CHC_TIMEOUT}s")
                        else:
                            logger.info(f"[{client_uuid}]: <<Connection Health Checker>> No problem was found")
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


class AIcon(Resource):
    def __init__(
        self,
        translator_name: str = "deepl",
    ) -> None:
        super(AIcon, self).__init__()

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
                    "last_connection_time": time.time(),
                    "_queue_empty_counter": 0,
                }

                client_priority: int = self._get_client_priority(client_uuid)
                _client_data[client_uuid][JSON_PRIORITY] = client_priority

                try:
                    _client_data_queue_chc.put_nowait(_client_data)
                    _client_data_queue_pm.put_nowait(_client_data)
                except Full:
                    pass

            except KeyError as error_state:
                logger.fatal(f"[{client_uuid}]: {error_state}")
                abort(400, error_state)

            self._set_path(client_uuid)

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

            client_priority = self._get_client_priority(client_uuid)

            _client_data[client_uuid][JSON_ABORT] = received_data[JSON_ABORT]
            _client_data[client_uuid][JSON_PRIORITY] = client_priority
            _client_data[client_uuid]["last_connection_time"] = time.time()

            try:
                _client_data_queue_chc.put_nowait(_client_data)
            except Full:
                pass

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

                try:
                    _client_data_queue_pm.put_nowait(_client_data)
                except Full:
                    pass

                client_data: Dict[str, Union[str, Queue]] = _client_data[client_uuid]

                try:
                    queued_data: Dict[str, str] = client_data["queue"].get(timeout=1.)

                    _client_data[client_uuid]["_queue_empty_counter"] = 0

                    res[JSON_CURRENT_ITER] = queued_data[JSON_CURRENT_ITER]
                    res[JSON_IMG_PATH] = queued_data[JSON_IMG_PATH]
                    res[JSON_GIF_PATH] = queued_data[JSON_GIF_PATH]
                    res[JSON_COMPLETE] = queued_data[JSON_COMPLETE]

                    if queued_data[JSON_COMPLETE]:
                        if self._remove_client_data(client_uuid):
                            logger.info(f"[{client_uuid}]: The task is successfully completed. Removed the client data.")
                        else:
                            logger.warn(f"[{client_uuid}]: The task is successfully completed. But failed to remove the client data.")
                except Empty:
                    _client_data[client_uuid]["_queue_empty_counter"] += 1
                    logger.warning(f"[{client_uuid}]: Queue is empty")

                    if _client_data[client_uuid]["_queue_empty_counter"] > MAIN_EMPTY_TOLERANCE:
                        logger.error(f"[{client_uuid}]: No data has been sent for a long time, AIcon Core may have crashed")
                        abort(500, "Server crashed")
            else:
                logger.warning(f"[{client_uuid}]: {len(_client_data)} clients are queued. This client is #{client_priority}. Skipping the task.")
        else:
            logger.fatal(f"[{client_uuid}]: Invalid UUID")
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
    logger.info("Seesion started")

    multiprocessing.set_start_method("spawn")

    PriorityMonitor()
    ConnectionHealthChecker()

    AIcon()
    api.add_resource(AIcon, '/service')

    serve(app, host='0.0.0.0', port=5050, threads=30)
