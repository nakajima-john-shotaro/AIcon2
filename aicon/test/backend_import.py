"""backend_import.py"""

# pylint: disable=unused-import

import time
import json
import urllib
import requests

import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from flask import Flask, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
from googletrans import Translator
