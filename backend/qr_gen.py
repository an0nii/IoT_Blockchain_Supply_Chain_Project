from flask import Blueprint, jsonify, request
import base64
import io
import zlib

import pyqrcode

qr_bp = Blueprint("qr", __name__)


@qr_bp.route("/generate_qr", methods=["POST"])
def generate_qr():
	try:
		data = request.json.get("data", "")
		if not data:
			return jsonify({"error": "No data provided"}), 400

		data_compress_zlib = zlib.compress(data.encode("utf-8"))
		qr_data = base64.b64encode(data_compress_zlib)

		qr = pyqrcode.create(qr_data)
		buffer = io.BytesIO()
		qr.png(buffer, scale=6)
		buffer.seek(0)

		img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
		data_url = f"data:image/png;base64,{img_base64}"

		return jsonify({"qrCode": data_url})
	except Exception as e:
		return jsonify({"error": str(e)}), 500
