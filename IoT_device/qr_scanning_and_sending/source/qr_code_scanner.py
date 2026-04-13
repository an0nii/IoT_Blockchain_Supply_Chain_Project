import numpy as np
import cv2
from pyzbar.pyzbar import decode


def get_warped_qr(img):
    # находим границы qr-кода на изображении

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    detector = cv2.QRCodeDetector()
    ok, points = detector.detect(gray)
    _, _, straight_qrcode = detector.detectAndDecode(gray)

    if not ok or straight_qrcode is None:
        return None, None

    # создаем выравненное изображение

    output_size = straight_qrcode.shape[0] * 15

    pts_src = points[0].astype(np.float32)

    dst_pts = np.array([[0, 0], [output_size-1, 0], [output_size-1, output_size-1], [0, output_size-1]], dtype=np.float32)
    matrix = cv2.getPerspectiveTransform(pts_src, dst_pts)

    warped = cv2.warpPerspective(img, matrix, (output_size, output_size))

    return warped, straight_qrcode.shape[0]


def add_quiet_zone(img, border_modules=4):
    module_size = 1
    border = border_modules * module_size
    h, w = img.shape
    new_img = np.ones((h + 2*border, w + 2*border), dtype=np.uint8) * 255
    new_img[border:border+h, border:border+w] = img
    return new_img


def classify_sector(sector):
    whole_mean = np.mean(sector)
    small_mean = np.mean(sector[5:10, 5:10])
    if whole_mean > 0.85 * 255 and small_mean > 0.85 * 255:
        return 0
    elif whole_mean < 0.15 * 255 and small_mean < 0.15 * 255:
        return 1
    elif whole_mean < 0.5 * 255:
        return 2
    else:
        return 3


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

    # cv2_imshow(img)

    straight_img, sector_size = get_warped_qr(img)
    if straight_img is None:
        return '', ''

    # мы его бинаризируем по специальному алгоритму
    binary = cv2.threshold(straight_img, straight_img.mean(), 255, cv2.ADAPTIVE_THRESH_MEAN_C)[1]
    # а теперь мы делим наш qr-код на два

    qr1 = np.zeros((sector_size, sector_size), dtype=np.uint8)
    qr2 = np.zeros((sector_size, sector_size), dtype=np.uint8)

    for y in range(sector_size):
        for x in range(sector_size):

            sector = binary[y * 15 + 2:(y+1) * 15 - 2, x * 15 + 2:(x+1) * 15 - 2]
            cls = classify_sector(sector)

            if cls == 1:    # черный
                qr1[y][x] = 1
                if cls == 1 and (x == 6 or y == 6): # служебный
                    qr2[y][x] = 1

            elif cls == 2:    # черный + крестик
                qr1[y][x] = 1
                qr2[y][x] = 1

            elif cls == 3:    # белый + крестик
                qr2[y][x] = 1

                              # иначе белый, тут ничего заполнять не надо

    # дорисовываем служебную зону qr2

    draw_finder(qr2, 0, 0)
    draw_finder(qr2, qr2.shape[0]-7, 0)
    draw_finder(qr2, 0, qr2.shape[0]-7)

    # переводим матрицы в изображения
    img1 = ((1 - qr1) * 255).astype(np.uint8)
    img2 = ((1 - qr2) * 255).astype(np.uint8)

    img1 = add_quiet_zone(img1)
    img2 = add_quiet_zone(img2)

    # img1 = cv2.resize(img1, (15 * sector_size, 15 * sector_size), interpolation=cv2.INTER_NEAREST)
    # img2 = cv2.resize(img2, (15 * sector_size, 15 * sector_size), interpolation=cv2.INTER_NEAREST)

    # cv2.imshow("QR Image", img1)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    #
    # cv2.imshow("QR Image", img2)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    detector = cv2.QRCodeDetector()
    key1, _, _ = detector.detectAndDecode(img1)
    detector = cv2.QRCodeDetector()
    key2, _, _ = detector.detectAndDecode(img2)

    return key1.strip(), key2.strip()