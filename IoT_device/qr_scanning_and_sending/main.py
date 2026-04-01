import logging
import os

os.environ["LIBCAMERA_LOG_LEVELS"] = "*:ERROR"
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"

import cv2
import numpy as np
from picamera2 import Picamera2

from source.blockchain_info_sender import GatewaySender
from source.qr_scanner import qr_scanner
from source.quality_enchancers import preprocess_image

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:3000")
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "")
DEVICE_ROLE = os.getenv("DEVICE_ROLE", "sender")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def read_frame(cam):
    cam_frame = cam.capture_array("main")
    frame = cv2.cvtColor(cam_frame, cv2.COLOR_YUV420p2RGB)
    frame = cv2.rotate(frame, cv2.ROTATE_180)
    return frame


def main():
    if not DEVICE_API_KEY:
        logger.error("DEVICE_API_KEY не задан")
        return

    sender = GatewaySender(GATEWAY_URL, DEVICE_API_KEY)

    cam = Picamera2()
    cfg = cam.create_video_configuration(main={"size": (960, 520), "format": "YUV420"})
    cam.configure(cfg)
    cam.start()
    cam.set_controls({"AwbEnable": True})

    logger.info("Устройство запущено. Роль: %s. Gateway: %s", DEVICE_ROLE, GATEWAY_URL)

    last_label_id = None

    try:
        while True:
            try:
                frame = read_frame(cam)
            except Exception as e:
                logger.warning("Не удалось прочитать кадр: %s", e)
                continue

            processed = preprocess_image(frame)
            values = qr_scanner(processed)
            try:
                cv2.imshow("IoT Scanner", processed)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except cv2.error:
                pass
            if not values:
                continue

            label_id = values[0]
            if label_id == last_label_id:
                continue

            last_label_id = label_id
            logger.info("Считан QR: labelId=%s", label_id)

            try:
                if DEVICE_ROLE == "sender":
                    result = sender.mark_as_sent(label_id)
                    logger.info("Метка отправлена: %s", result)
                elif DEVICE_ROLE == "receiver":
                    result = sender.mark_as_received(label_id)
                    logger.info("Метка получена: %s", result)
                else:
                    logger.error("Неизвестная роль устройства: %s", DEVICE_ROLE)
            except Exception as e:
                logger.error("Ошибка отправки на Gateway: %s", e)

    finally:
        cam.stop()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass


if __name__ == "__main__":
    main()
