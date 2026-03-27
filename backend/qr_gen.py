from flask import Blueprint, jsonify, request
import base64
import hashlib
import os
from pathlib import Path
import zlib

import cv2
import ecdsa
import numpy as np
import qrcode

qr_bp = Blueprint("qr", __name__)


def generate_keypair() -> tuple[str, str]:
	signing_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
	verifying_key = signing_key.get_verifying_key()
	private_key_hex = signing_key.to_string().hex()
	public_key_hex = verifying_key.to_string().hex()
	return private_key_hex, public_key_hex


def save_keys_to_env(private_key_hex: str, public_key_hex: str, overwrite: bool) -> bool:
	env_path = Path(__file__).resolve().parent / ".env"
	if env_path.exists() and not overwrite:
		return False

	content = f"PRIVATE_KEY={private_key_hex}\nPUBLIC_KEY={public_key_hex}\n"
	env_path.write_text(content, encoding="utf-8")
	os.environ["PRIVATE_KEY"] = private_key_hex
	os.environ["PUBLIC_KEY"] = public_key_hex
	return True


def load_env_keys() -> None:
	env_path = Path(__file__).resolve().parent / ".env"
	if env_path.exists():
		for line in env_path.read_text(encoding="utf-8").splitlines():
			line = line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue
			key, value = line.split("=", 1)
			key = key.strip()
			value = value.strip()
			if key and value and key not in os.environ:
				os.environ[key] = value

	private_key_hex = os.environ.get("PRIVATE_KEY", "")
	public_key_hex = os.environ.get("PUBLIC_KEY", "")
	if not private_key_hex or not public_key_hex:
		private_key_hex, public_key_hex = generate_keypair()
		save_keys_to_env(private_key_hex, public_key_hex, overwrite=True)
		print("Generated new keypair and saved to backend/.env")


load_env_keys()


def sign_message(message: str, private_key_hex: str) -> str:
	if not message:
		raise ValueError("Message is required")
	if not private_key_hex:
		raise ValueError("Private key is required")

	try:
		private_key_bytes = bytes.fromhex(private_key_hex)
	except ValueError as exc:
		raise ValueError("Private key must be hex-encoded") from exc

	if len(private_key_bytes) != 32:
		raise ValueError("Private key must be 32 bytes (64 hex chars)")

	signing_key = ecdsa.SigningKey.from_string(
		private_key_bytes,
		curve=ecdsa.SECP256k1,
		hashfunc=hashlib.sha256,
	)
	message_hash = hashlib.sha256(message.encode("utf-8")).digest()
	signature_der = signing_key.sign_digest(
		message_hash,
		sigencode=ecdsa.util.sigencode_der,
	)

	return base64.b64encode(signature_der).decode("utf-8")


def create_matrix_qr_code(key: str, border: int = 3) -> np.ndarray:
	qr = qrcode.QRCode(
		version=4,
		error_correction=qrcode.constants.ERROR_CORRECT_H,
		border=border,
		mask_pattern=0,
	)
	qr.add_data(key)
	qr.make()
	return np.array(qr.get_matrix())


# Для тестирования и отладки, не является частью API
def decode_dual_qr_png(png_path: str, border: int = 3, scale: int = 25) -> tuple[str, str]:
	img = cv2.imread(png_path, cv2.IMREAD_GRAYSCALE)
	if img is None:
		raise ValueError("Failed to read PNG")

	height, width = img.shape[:2]
	if height != width:
		raise ValueError("QR image must be square")
	if height % scale != 0:
		raise ValueError("Image size must be divisible by scale")

	full_size = height // scale
	full_pixels = (img < 128).astype(np.uint8)
	modules = np.zeros((full_size, full_size), dtype=bool)

	for i in range(full_size):
		for j in range(full_size):
			block = full_pixels[i * scale:(i + 1) * scale, j * scale:(j + 1) * scale]
			modules[i, j] = block.mean() > 0.5

	inner_size = full_size - 2 * border
	inner1 = modules[border:full_size - border, border:full_size - border].copy()
	inner2 = np.zeros_like(inner1)

	for i in range(inner_size):
		for j in range(inner_size):
			bg = inner1[i, j]
			if is_service_module(i, j, inner_size):
				inner2[i, j] = inner1[i, j]
				continue

			block = full_pixels[
				(border + i) * scale:(border + i + 1) * scale,
				(border + j) * scale:(border + j + 1) * scale,
			]
			s = scale / 5
			center = block[int(1.5 * s):int(3.5 * s), int(1.5 * s):int(3.5 * s)]
			cross_is_dark = center.mean() > 0.5
			inner2[i, j] = bg != cross_is_dark

	full1 = np.zeros((full_size, full_size), dtype=bool)
	full2 = np.zeros((full_size, full_size), dtype=bool)
	full1[border:full_size - border, border:full_size - border] = inner1
	full2[border:full_size - border, border:full_size - border] = inner2
	full2[:border, :] = full1[:border, :]
	full2[-border:, :] = full1[-border:, :]
	full2[:, :border] = full1[:, :border]
	full2[:, -border:] = full1[:, -border:]

	layer1_img = (1 - full1.astype(np.uint8)) * 255
	layer2_img = (1 - full2.astype(np.uint8)) * 255

	decoder = cv2.QRCodeDetector()
	layer1_text, _, _ = decoder.detectAndDecode(layer1_img)
	layer2_text, _, _ = decoder.detectAndDecode(layer2_img)

	if not layer1_text:
		raise ValueError("Failed to decode layer 1")
	if not layer2_text:
		raise ValueError("Failed to decode layer 2")

	try:
		decoded_bytes = base64.b64decode(layer1_text)
		decoded_message = zlib.decompress(decoded_bytes).decode("utf-8")
	except Exception as exc:
		raise ValueError("Failed to decode layer 1 payload") from exc

	return decoded_message, layer2_text


def is_service_module(x: int, y: int, size: int) -> bool:
	finder_size = 8
	if x < finder_size and y < finder_size:
		return True
	if x > size - finder_size - 1 and y < finder_size:
		return True
	if x < finder_size and y > size - finder_size - 1:
		return True
	if x == 6 or y == 6:
		return True
	return False


def draw_cross(module: np.ndarray, color: bool) -> np.ndarray:
	s = module.shape[0] / 5
	module[int(1.5 * s):int(3.5 * s), int(1.5 * s):int(3.5 * s)] = color
	return module


def create_dual_qr_code(
	key1: str,
	key2: str,
	border: int = 3,
	scale: int = 25,
) -> tuple[str, str, np.ndarray]:
	matrix1 = create_matrix_qr_code(key1, border)
	matrix2 = create_matrix_qr_code(key2, border)

	while matrix1.shape != matrix2.shape:
		if matrix1.shape[0] < matrix2.shape[0]:
			key1 += " "
		else:
			key2 += " "
		matrix1 = create_matrix_qr_code(key1, border)
		matrix2 = create_matrix_qr_code(key2, border)

	full_size = matrix1.shape[0]
	inner_size = full_size - 2 * border

	inner1 = matrix1[border:full_size - border, border:full_size - border]
	inner2 = matrix2[border:full_size - border, border:full_size - border]

	result = np.zeros((inner_size * scale, inner_size * scale), dtype=bool)

	for i in range(inner_size):
		for j in range(inner_size):
			bg = inner1[i, j]
			module = np.full((scale, scale), bg, dtype=bool)

			if not is_service_module(i, j, inner_size):
				if inner2[i, j]:
					color = not bg
					draw_cross(module, color)

			result[i * scale:(i + 1) * scale, j * scale:(j + 1) * scale] = module

	full_pixels = np.zeros((full_size * scale, full_size * scale), dtype=bool)
	full_pixels[
		border * scale:(border + inner_size) * scale,
		border * scale:(border + inner_size) * scale,
	] = result

	return key1, key2, full_pixels


@qr_bp.route("/generate_qr", methods=["POST"])
def generate_qr():
	try:
		payload = request.json or {}
		data = payload.get("data", "")
		private_key_hex = payload.get("privateKey", "") or os.environ.get("PRIVATE_KEY", "")
		if not data:
			return jsonify({"error": "No data provided"}), 400
		if not private_key_hex:
			return jsonify({"error": "No private key provided"}), 400

		data_compress_zlib = zlib.compress(data.encode("utf-8"))
		message = base64.b64encode(data_compress_zlib).decode("utf-8")
		signature = sign_message(message, private_key_hex)

		_, _, full_pixels = create_dual_qr_code(message, signature)
		img = (1 - full_pixels.astype(np.uint8)) * 255
		ok, encoded = cv2.imencode(".png", img)
		if not ok:
			return jsonify({"error": "Failed to encode QR image"}), 500

		img_base64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
		data_url = f"data:image/png;base64,{img_base64}"

		return jsonify({"qrCode": data_url, "signature": signature})
	except Exception as e:
		return jsonify({"error": str(e)}), 500


@qr_bp.route("/generate_keys", methods=["POST"])
def generate_keys():
	try:
		payload = request.json or {}
		overwrite = bool(payload.get("overwrite", False))
		private_key_hex, public_key_hex = generate_keypair()
		saved = save_keys_to_env(private_key_hex, public_key_hex, overwrite)
		return jsonify({
			"privateKey": private_key_hex,
			"publicKey": public_key_hex,
			"saved": saved,
			"path": ".env",
		})
	except Exception as e:
		return jsonify({"error": str(e)}), 500
