import cv2
import numpy as np
import zlib
import base64
import logging

logger = logging.getLogger(__name__)


def _get_warped_qr(img):
    # img уже grayscale после preprocess_image
    gray = img if len(img.shape) == 2 else cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    detector = cv2.QRCodeDetector()
    ok, points = detector.detect(blurred)
    if not ok or points is None or len(points) == 0:
        return None, None, None

    _, _, straight_qrcode = detector.detectAndDecode(blurred)
    if straight_qrcode is None or straight_qrcode.size == 0 or straight_qrcode.shape[0] == 0:
        return None, None, None

    sector_size = straight_qrcode.shape[0]
    output_size = sector_size * 15

    pts_src = points[0].astype(np.float32)
    dst_pts = np.array(
        [[0, 0], [output_size - 1, 0], [output_size - 1, output_size - 1], [0, output_size - 1]],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(pts_src, dst_pts)
    warped = cv2.warpPerspective(gray, matrix, (output_size, output_size))

    return warped, sector_size, points[0].astype(int)


def _add_quiet_zone(img, border_modules=2):
    border = border_modules
    h, w = img.shape
    new_img = np.ones((h + 2 * border, w + 2 * border), dtype=np.uint8) * 255
    new_img[border:border + h, border:border + w] = img
    return new_img


def _classify_sector(sector):
    if sector.size == 0:
        return 0
    center = sector[5:10, 5:10] if sector.shape[0] >= 10 and sector.shape[1] >= 10 else sector
    if center.size == 0:
        center = sector
    whole_mean = np.mean(sector)
    small_mean = np.mean(center)
    if whole_mean > 0.85 * 255 and small_mean > 0.85 * 255:
        return 0
    elif whole_mean < 0.15 * 255 and small_mean < 0.15 * 255:
        return 1
    elif whole_mean < 0.5 * 255:
        return 2
    else:
        return 3


def _draw_finder(matrix, x, y):
    pattern = np.array([
        [1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 1, 1, 1, 0, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1],
    ], dtype=np.uint8)
    matrix[y:y + 7, x:x + 7] = pattern


def _decode_value(val):
    if not val:
        return None
    try:
        parts = zlib.decompress(base64.b64decode(val)).decode('utf-8').split('||')
        if len(parts) == 3:
            return parts
    except Exception:
        pass
    return [val] if val else None


def qr_scanner(img: np.ndarray):
    try:
        warped, sector_size, pts = _get_warped_qr(img)
        if warped is None:
            return None

        for i in range(4):
            cv2.line(img, tuple(pts[i]), tuple(pts[(i + 1) % 4]), (0, 0, 255), 3)

        _, binary = cv2.threshold(warped, float(warped.mean()), 255, cv2.THRESH_BINARY)

        qr1 = np.zeros((sector_size, sector_size), dtype=np.uint8)
        qr2 = np.zeros((sector_size, sector_size), dtype=np.uint8)

        for y in range(sector_size):
            for x in range(sector_size):
                sector = binary[y * 15 + 2:(y + 1) * 15 - 2, x * 15 + 2:(x + 1) * 15 - 2]
                cls = _classify_sector(sector)

                if cls == 1:
                    qr1[y][x] = 1
                    if x == 6 or y == 6:
                        qr2[y][x] = 1
                elif cls == 2:
                    qr1[y][x] = 1
                    qr2[y][x] = 1
                elif cls == 3:
                    qr2[y][x] = 1

        _draw_finder(qr2, 0, 0)
        _draw_finder(qr2, qr2.shape[0] - 7, 0)
        _draw_finder(qr2, 0, qr2.shape[0] - 7)

        img1 = cv2.resize(_add_quiet_zone((1 - qr1) * 255), (300, 300), interpolation=cv2.INTER_NEAREST)
        img2 = cv2.resize(_add_quiet_zone((1 - qr2) * 255), (300, 300), interpolation=cv2.INTER_NEAREST)

        det1 = cv2.QRCodeDetector()
        key1, _, _ = det1.detectAndDecode(img1)
        det2 = cv2.QRCodeDetector()
        key2, _, _ = det2.detectAndDecode(img2)

        val = _decode_value(key1) or _decode_value(key2)

        if val and len(val) >= 3:
            x0, y0 = pts[0][0], pts[0][1]
            for text, dy in [("Item id: " + val[0], 90), ("Sender: " + val[1], 60), ("Receiver: " + val[2], 30)]:
                cv2.putText(img, text, (x0, y0 - dy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 4)
                cv2.putText(img, text, (x0, y0 - dy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

        return val

    except Exception as e:
        logger.warning("qr_scanner error: %s", e)
        return None
