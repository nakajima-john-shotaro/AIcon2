"""backend_translat.py"""

import time

import requests
import chromedriver_binary
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from googletrans import Translator


class Translation():
    def __init__(
        self,
        translator: str = "google"
    ) -> None:

        if translator in ["google", "deepl"]:
            self.translator: str = translator
            self.g_translator: Translator = Translator()
            self.d_options = Options()
        else:
            raise ValueError("Expected translator is `google` or `deepl` but got {translator}")

    def translate(self, text: str) -> str:
        if self.translator == "google":
            lang = self.g_translator.detect(text).lang

            if not lang == "en":
                output_text = self.g_translator.translate(text, src=lang, dest="en").text
            else:
                output_text = text
        else:
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
                if output_text != "" :
                    break
                time.sleep(1)

            driver.close()

        return output_text


if __name__ == "__main__":
    r = requests.get(r"https://ja.wikipedia.org/wiki/%E3%83%A1%E3%82%A4%E3%83%B3%E3%83%9A%E3%83%BC%E3%82%B8")
    soup = BeautifulSoup(r.text, "html.parser")
    div_tag = soup.find('div', class_='mainpage-content-text')
    p_tag = div_tag.find_all('p')[0]

    translator_deepl = Translation("deepl")
    output: str = translator_deepl.translate(p_tag.text)
    print(f"DeepL: {output}")

    translator_google = Translation("google")
    output = translator_google.translate(p_tag.text)
    print(f"Google: {output}")
