from logging import debug
from flask import render_template, Flask
from flask_cors import CORS
from waitress import serve


app = Flask(__name__)

CORS(app)


@app.route("/")
def index():
    # return "Hello World!"
    return render_template("aicon.html", title="AIcon", name="AIcon")


if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8083)
