"""backend_import.py"""

# pylint: disable=unused-import

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from googletrans import Translator
from flask import Flask, Response, jsonify, render_template, abort, request
from flask_cors import CORS
from flask_restful import Api, Resource
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.exceptions import HTTPException, BadRequest, Forbidden, InternalServerError
from waitress import serve