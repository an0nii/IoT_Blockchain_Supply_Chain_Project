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
def get_warped_qr(img):
    # находим границы qr-кода на изображении

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    detector = cv2.QRCodeDetector()
    ok, points = detector.detect(gray)
    _, _, straight_qrcode = detector.detectAndDecode(gray)

    if not ok:
        print("QR-код не обнаружен.")
        return None, None

    # создаем выравненное изображение

    output_size = straight_qrcode.shape[0] * 15

    pts_src = points[0].astype(np.float32)

    dst_pts = np.array([[0, 0], [output_size-1, 0], [output_size-1, output_size-1], [0, output_size-1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(pts_src, dst_pts)

    warped = cv2.warpPerspective(gray, matrix, (output_size, output_size))

    return warped, straight_qrcode.shape[0]


def add_quiet_zone(img, border_modules=2):
    module_size = 1
    border = border_modules * module_size
    h, w = img.shape
    new_img = np.ones((h + 2*border, w + 2*border), dtype=np.uint8) * 255
    new_img[border:border+h, border:border+w] = img
    return new_img


def classify_sector(sector):
    y_max, x_max = sector.shape
    if np.mean(sector) > 0.85 * 255 and np.mean(sector[5:10, 5:10]) > 0.85 * 255:
        return 0
    elif np.mean(sector) < 0.15 * 255 and np.mean(sector[5:10, 5:10]) < 0.15 * 255:
        return 1
    elif np.mean(sector) < 0.5 * 255:
        return 2
    else:
        return 3


def clip_image(img):
    rows = np.any(img < 255, axis=1)
    cols = np.any(img < 255, axis=0)

    y_min, y_max = np.where(rows)[0][[0, -1]]
    x_min, x_max = np.where(cols)[0][[0, -1]]

    return img[y_min:y_max-2, x_min:x_max-4]


def draw_finder(matrix, x, y):

    pattern = np.array([
        [1,1,1,1,1,1,1],
        [1,0,0,0,0,0,1],
        [1,0,1,1,1,0,1],
        [1,0,1,1,1,0,1],
        [1,0,1,1,1,0,1],
        [1,0,0,0,0,0,1],
        [1,1,1,1,1,1,1],
    ], dtype=np.uint8)

    matrix[y:y+7, x:x+7] = pattern


def split_and_decode_dual_qr(img):

    cv2_imshow(img)

    straight_img, sector_size = get_warped_qr(img)

    # мы его бинаризируем по специальному алгоритму (числа для функции были подобраны для лучшего результата)

    binary = cv2.threshold(straight_img, 150, 255, cv2.ADAPTIVE_THRESH_MEAN_C)[1]
	
	# дебаг
    # cv2_imshow(binary)
	
    # а теперь мы делим наш qr-код на два

    qr1 = np.zeros((sector_size, sector_size), dtype=np.uint8)
    qr2 = np.zeros((sector_size, sector_size), dtype=np.uint8)

	# дебаг
	
    # errors = np.zeros((sector_size, sector_size), dtype=np.uint8)

    # real_qr1 = create_matrix_qr_code(real_key1, border=0)
    # real_qr2 = create_matrix_qr_code(real_key2, border=0)

    # cv2_imshow(real_qr1)
    # cv2_imshow(real_qr2)

    for y in range(sector_size):
        for x in range(sector_size):

            sector = binary[y * 15 + 2:(y+1) * 15 - 2, x * 15 + 2:(x+1) * 15 - 2]
            cls = classify_sector(sector)

			# дебаг
			
            # print(cls, y, x)
            # cv2_imshow(sector)

            # if real_qr1[y][x] == 0 and real_qr2[y][x] == 0:
            #     real_cls = 0
            # elif real_qr1[y][x] == 1 and real_qr2[y][x] == 0:
            #     real_cls = 1
            # elif real_qr1[y][x] == 1 and real_qr2[y][x] == 1:
            #     real_cls = 2
            # elif real_qr1[y][x] == 0 and real_qr2[y][x] == 1:
            #     real_cls = 3

            # if real_cls != cls and (x > 7 and y > 7) and x != 6 and y != 6:
            #     print(cls, real_cls, y, x, real_qr1[y, x], real_qr2[y, x])
            #     errors[y][x] = 1
            #     cv2_imshow(sector)

            if cls == 1:    # черный
                qr1[y][x] = 1
                if cls == 1 and (x == 6 or y == 6):
                    qr2[y][x] = 1

            if cls == 2:    # черный + рисунок
                qr1[y][x] = 1
                qr2[y][x] = 1

            if cls == 3:    # белый + рисунок
                qr2[y][x] = 1

    # дорисовываем служебную зону qr2

    draw_finder(qr2, 0, 0)
    draw_finder(qr2, qr2.shape[0]-7, 0)
    draw_finder(qr2, 0, qr2.shape[0]-7)

    # переводим матрицы в изображения
    img1 = (1 - qr1) * 255
    img2 = (1 - qr2) * 255

    img1 = add_quiet_zone(img1)
    img2 = add_quiet_zone(img2)

    detector = cv2.QRCodeDetector()
    key1, _, _ = detector.detectAndDecode(img1)
    detector = cv2.QRCodeDetector()
    key2, _, _ = detector.detectAndDecode(img2)

	# дебаг
	
    # img1 = cv2.resize(img1, (300,300), interpolation=cv2.INTER_NEAREST)
    # img2 = cv2.resize(img2, (300,300), interpolation=cv2.INTER_NEAREST)

    # print(f"QR1: {key1}")
    # cv2_imshow(img1)
    # print(f"QR2: {key2}")
    # cv2_imshow(img2)

    return key1, key2


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
