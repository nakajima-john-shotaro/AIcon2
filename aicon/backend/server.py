import os
import time
import json
from typing import Any, Dict, List, Optional, Union
import urllib
import requests
from uuid import uuid4 
from queue import Queue
from pprint import pprint

import chromedriver_binary # pylint: disable=unused-import
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask, Response, jsonify, make_response, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve
from googletrans import Translator

from constant import *


app: Flask = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config["JSON_SORT_KEYS"] = False
CORS(app)
api = Api(app)
parser = reqparse.RequestParser()

_client_data: Dict[str, Dict[str, str]] = {}


class Translation(object):
    def __init__(
        self,
        translator: str = "google"
    ) -> None:
        super().__init__()

        if translator in ["google", "deepl"]:
            self.translator: str = translator
            self.g_translator: Translator = Translator()
            self.d_options = Options()
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

                time.sleep(3)

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

        print(output_text)

        return output_text


class AIcon(Resource):
    def __init__(
        self,
        translator: str = "deepl",
    ) -> None:
        super().__init__()

        self.translator: Translation = Translation(translator)

        self.base_img_path: str = "../frontend/static/dst_img"
        self.base_gif_path: str = "../frontend/static/dst_gif"

    def _get_client_priority(self, client_hash: str) -> int:
        global _client_data

        return list(_client_data.keys()).index(client_hash)

    def _set_path(self, client_hash: str) -> None:
        global _client_data

        model_name: str = _client_data[client_hash][JSON_MODEL_NAME]

        img_path: str = os.path.join(self.base_img_path, model_name, client_hash)
        gif_path: str = os.path.join(self.base_gif_path, model_name, client_hash)

        os.makedirs(img_path, exist_ok=True)
        os.makedirs(gif_path, exist_ok=True)

        _client_data[client_hash][JSON_IMG_PATH] = img_path
        _client_data[client_hash][JSON_GIF_PATH] = gif_path
        
    def post(self):
        global _client_data

        received_data: Dict[str, Any] = request.get_json(force=True)
        pprint(received_data)

        client_hash: str = received_data[JSON_HASH]

        if client_hash == P_HASH_INIT:
            client_hash = str(uuid4())

            try:
                _client_data[client_hash] = {
                    JSON_MODEL_NAME: received_data[JSON_MODEL_NAME],
                    JSON_TEXT: self.translator.translate(received_data[JSON_TEXT]),
                    JSON_TOTAL_ITER: received_data[JSON_TOTAL_ITER],
                    JSON_SIZE: received_data[JSON_SIZE],
                    JSON_ABORT: received_data[JSON_ABORT],
                    JSON_COMPLETE: False,
                }
                pprint(_client_data)
            except KeyError as error_state:
                abort(400, error_state)

            self._set_path(client_hash)

            res: Dict[str, Optional[Union[str, bool]]] = {
                JSON_HASH: client_hash,
                JSON_PRIORITY: self._get_client_priority(client_hash),
                JSON_NUM_CLIENTS: len(_client_data),
                JSON_CURRENT_ITER: "0",
                JSON_COMPLETE: False,
                JSON_IMG_PATH: None,
                JSON_GIF_PATH: None,
            }

            return jsonify(res)

        if client_hash in _client_data.keys():
            _client_data[client_hash][JSON_ABORT] = received_data[JSON_ABORT]

            client_priority: int = self._get_client_priority(client_hash)
            if client_priority == 0:
                client_data: Dict[str, str] = _client_data[client_hash]

                # Do something here

                res: Dict[str, Optional[Union[str, bool]]] = {
                    JSON_HASH: client_hash,
                    JSON_PRIORITY: client_priority,
                    JSON_NUM_CLIENTS: len(_client_data),
                    JSON_CURRENT_ITER: "0",
                    JSON_COMPLETE: False,
                    JSON_IMG_PATH: None,
                    JSON_GIF_PATH: None,
                }
            else:
                res: Dict[str, Optional[Union[str, bool]]] = {
                    JSON_HASH: client_hash,
                    JSON_PRIORITY: client_priority,
                    JSON_NUM_CLIENTS: len(_client_data),
                    JSON_CURRENT_ITER: "0",
                    JSON_COMPLETE: False,
                    JSON_IMG_PATH: None,
                    JSON_GIF_PATH: None,
                }
        else:
            abort(Forbidden, f"Invalid Hash: {client_hash}")

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


if __name__ == "__main__":
    aicon: AIcon = AIcon()
    api.add_resource(AIcon, '/')

    serve(app, host='0.0.0.0', port=8081, threads=1)
