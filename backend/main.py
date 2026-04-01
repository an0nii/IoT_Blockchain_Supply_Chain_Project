from flask import Flask
from flask_cors import CORS

from db import init_db, devices_bp
from qr_gen import qr_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    init_db(app)
    app.register_blueprint(devices_bp, url_prefix="/api")
    app.register_blueprint(qr_bp, url_prefix="/api")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=3000, debug=True)