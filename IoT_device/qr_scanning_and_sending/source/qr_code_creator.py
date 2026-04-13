import numpy as np
import qrcode
import cv2


def create_matrix_qr_code(key, border=3):
    qr = qrcode.QRCode(version=4, error_correction=qrcode.constants.ERROR_CORRECT_H, border=border)
    qr.add_data(key)
    qr.make()
    return np.array(qr.get_matrix())


# возвращает, принадлежит ли (x, y) служебной области

def is_service_module(x, y, size):
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


# рисует паттерны нужного размера

def draw_cross(module, color):
    s = module.shape[0] / 5
    module[int(1.5 * s):int(3.5 * s), int(1.5 * s):int(3.5 * s)] = color
    return module

def create_dual_qr_code(key1, key2, border=3, scale=15, save_path=None, test=False):

    # создаём матрицы qr-кодов и выравниваем их, если они получились разных размеров

    matrix1 = create_matrix_qr_code(key1, border)
    matrix2 = create_matrix_qr_code(key2, border)

    while matrix1.shape != matrix2.shape:
        if matrix1.shape[0] < matrix2.shape[0]:
            key1 += ' '
        else:
            key2 += ' '
        matrix1 = create_matrix_qr_code(key1, border)
        matrix2 = create_matrix_qr_code(key2, border)

    # убираем задник, он нам не понадобится

    full_size = matrix1.shape[0]
    inner_size = full_size - 2 * border

    inner1 = matrix1[border:full_size-border, border:full_size-border]
    inner2 = matrix2[border:full_size-border, border:full_size-border]

    # создаем двойной qr-код

    result = np.zeros((inner_size * scale, inner_size * scale), dtype=bool)

    for i in range(inner_size):
        for j in range(inner_size):
            bg = inner1[i, j]
            module = np.full((scale, scale), bg, dtype=bool)

            if not is_service_module(i, j, inner_size):
                if inner2[i, j]:
                    color = not bg
                    draw_cross(module, color)

            result[i*scale:(i+1)*scale, j*scale:(j+1)*scale] = module

    # добавляем задник и сохраняем его

    full_pixels = np.zeros((full_size * scale, full_size * scale), dtype=bool)
    full_pixels[border*scale : (border+inner_size)*scale, border*scale : (border+inner_size)*scale] = result

    img = (1 - full_pixels.astype(np.uint8)) * 255
    if save_path is not None:
        cv2.imwrite(save_path, img)

    if test:
        cv2.imshow("QR Image", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return img
