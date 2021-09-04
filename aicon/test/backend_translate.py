from . import backend_import


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
        if self.translator == "google":
            lang = self.g_translator.detect(text).lang

            if not lang == "en":
                output_text = self.g_translator.translate(text, src=lang, dest="en").text
            else:
                output_text = text

            return output_text
        else:
            self.d_options.add_argument('--headless')
            self.d_options.add_argument('--no-sandbox')
            driver: webdriver.Chrome = webdriver.Chrome(chrome_options=self.d_options)
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
    translator_deepl = Translation("deepl")
    output: str = translator_deepl.translate("AIconはとてもパワフルで効率的な画像生成WEBアプリケーションです。")
    print(output)

    translator_google = Translation("google")
    output = translator_google.translate("AIconはとてもパワフルで効率的な画像生成WEBアプリケーションです。")
    print(output)