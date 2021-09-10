"""translation.py"""

import time

import chromedriver_binary # pylint: disable=unused-import
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from googletrans import Translator


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