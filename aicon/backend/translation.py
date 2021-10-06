"""translation.py"""

import os
os.environ['WDM_LOG_LEVEL'] = '0'
import time

from googletrans import Translator
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager


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
                try:
                    self.d_options.add_argument('--headless')
                    self.d_options.add_argument('--no-sandbox')

                    driver: webdriver.Chrome = webdriver.Chrome(
                        ChromeDriverManager(print_first_line=False).install(), 
                        options=self.d_options
                    )
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

                except (NoSuchElementException, TimeoutException):
                    raise RuntimeError(f"Failed to translate by DeepL. Consider to use google translator mode.")
    
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


def install_webdriver() -> None:
    options: Options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    _ = webdriver.Chrome(ChromeDriverManager(print_first_line=False).install(), options=options)
