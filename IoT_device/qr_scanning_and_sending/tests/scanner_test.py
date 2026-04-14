import cv2

from IoT_Blockchain_Supply_Chain_Project.IoT_device.qr_scanning_and_sending.source.qr_code_scanner import split_and_decode_dual_qr


def video_test(video_path):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("Не удалось открыть видео")
        return

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Конец видео")
            break

        key1, key2 = split_and_decode_dual_qr(frame)

        if key1 or key2:
            print(f"Найден QR: {key1}, {key2}")

        cv2.imshow("Video", frame)

        # замедление (важно для видео)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    video_test('../source/IMG_0220.MOV')