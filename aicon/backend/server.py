import os
import time
import json
import functools
from typing import Any, Dict, Optional, Union
from uuid import uuid4
from multiprocessing import Process, Queue
from queue import Empty
from pprint import pprint # pylint: disable=unused-import
from logging import StreamHandler, Logger, getLogger, DEBUG

import chromedriver_binary # pylint: disable=unused-import
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask, Response, jsonify, render_template, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve
from googletrans import Translator

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
stream_handler.setLevel(DEBUG)
stream_handler.setFormatter(CustomFormatter())
logger: Logger = getLogger()
logger.addHandler(stream_handler)
logger.setLevel(DEBUG)

_client_data: Dict[str, Dict[str, Union[str, Queue]]] = {}


class Translation(object):
    def __init__(
        self,
        translator: str = "google"
    ) -> None:
        super().__init__()

        if translator in ["google", "deepl"]:
            self.translator: str = translator
            self.g_translator: Translator = Translator()
            self.d_options: Options = Options()
        else:
            raise ValueError("Expected translator is `google` or `deepl` but got {translator}")

    def translate(self, text: str) -> str:
        lang = self.g_translator.detect(text).lang

        if not lang == "en":
            if self.translator == "google":
                output_text = self.g_translator.translate(text, src=lang, dest="en").text
            elif self.translator == "deepl":
                self.d_options.add_argument('--headless')
                self.d_options.add_argument('--no-sandbox')

                driver: webdriver.Chrome = webdriver.Chrome(options=self.d_options)
                driver.get("https://www.deepl.com/ja/translator")

                input_selector = driver.find_element_by_css_selector(".lmt__textarea.lmt__source_textarea.lmt__textarea_base_style")
                input_selector.send_keys(text)

                while True:
                    output_selector: str = ".lmt__textarea.lmt__target_textarea.lmt__textarea_base_style"
                    output_text: str = driver.find_element_by_css_selector(output_selector).get_property("value")
                    if output_text != "":
                        break
                    time.sleep(1)

                driver.close()
        else:
            output_text = text

        for i, char in enumerate(output_text):
            list(output_text)[i] = char.translate(str.maketrans({
                '\u3000': ' ',
                ' ': ' ',
                '　': ' ',
                '\t': '',
                '\r': '',
                '\x0c': '',
                '\x0b': '',
                '\xa0': '',
            }))
        output_text = "".join(output_text)

        return output_text


# debag
class DeepDaze():
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

        model = DeepDaze(self.client_uuid, queue)
        if self.model_name == MODEL_NAME_BID_SLEEP:
            model.run()
        elif self.model_name == MODEL_NAME_DEEP_DAZE:
            model.run()
        elif self.model_name == MODEL_NAME_DALL_E:
            model.run()
        else:
            logger.fatal(f"[{self.client_uuid}]: Invalid model name `{self.model_name}` requested")
            abort(BadRequest, f"Invalid model name {self.model_name}")


class AIcon(Resource):
    def __init__(
        self,
        translator: str = "deepl",
    ) -> None:
        super().__init__()

        self.translator: Translation = Translation(translator)

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
        logger.info(f"[N/A]: Requested from {request.remote_addr} | {request.method} {str(request.url_rule)} {request.environ.get('SERVER_PROTOCOL')} {request.environ.get('HTTP_CONNECTION')}")

        client_uuid: str = received_data[JSON_HASH]

        if client_uuid == P_HASH_INIT:
            client_uuid = str(uuid4())

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
                }

                aicon_core: AIconCore = AIconCore(received_data[JSON_MODEL_NAME], client_uuid, translated_text, queue)

            except KeyError as error_state:
                logger.fatal(f"[{client_uuid}]: {error_state}")
                abort(BadRequest, error_state)

            self._set_path(client_uuid)

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_uuid,
                JSON_PRIORITY: self._get_client_priority(client_uuid),
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

            client_priority: int = self._get_client_priority(client_uuid)
            if client_priority == 1:
                logger.info(f"[{client_uuid}]: The client is #{client_priority}. Starting AIcon-core.")

                client_data: Dict[str, Union[str, Queue]] = _client_data[client_uuid]

                res: Dict[str, Optional[Union[str, bool]]] = {
                    JSON_HASH: client_uuid,
                    JSON_PRIORITY: client_priority,
                    JSON_NUM_CLIENTS: len(_client_data),
                    JSON_CURRENT_ITER: "0",
                    JSON_COMPLETE: False,
                    JSON_IMG_PATH: None,
                    JSON_GIF_PATH: None,
                }

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
                    logger.info(f"[{client_uuid}]: Removed data from clients completed with the task")
            else:
                logger.warning(f"[{client_uuid}]: {len(_client_data)} clients are queued. The client is #{client_priority}. Skipping the task.")

                res: Dict[str, Optional[Union[str, bool]]] = {
                    JSON_HASH: client_uuid,
                    JSON_PRIORITY: client_priority,
                    JSON_NUM_CLIENTS: len(_client_data),
                    JSON_CURRENT_ITER: "0",
                    JSON_COMPLETE: False,
                    JSON_IMG_PATH: None,
                    JSON_GIF_PATH: None,
                }
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

    aicon: AIcon = AIcon()
    api.add_resource(AIcon, '/service')

    serve(app, host='0.0.0.0', port=5050, threads=10)
