from IoT_Blockchain_Supply_Chain_Project.IoT_device.qr_scanning_and_sending.source.qr_code_creator import create_dual_qr_code
from IoT_Blockchain_Supply_Chain_Project.IoT_device.qr_scanning_and_sending.source.qr_code_scanner import split_and_decode_dual_qr


def test_dual_qr_generation_and_decoding(key1, key2):
    img = create_dual_qr_code(key1, key2, test=True)
    decoded_key1, decoded_key2 = split_and_decode_dual_qr(img)

    assert decoded_key1 == key1, f"Key1 mismatch: {decoded_key1} != {key1}"
    assert decoded_key2 == key2, f"Key2 mismatch: {decoded_key2} != {key2}"

    print(f"Двойной QR-код с ключами {key1}, {key2} был успешно создан")


if __name__ == "__main__":
    key1, key2 = 'auwduikawdgawugdyawgd', 'hilvhiklahvilhaseihghsae'
    test_dual_qr_generation_and_decoding(key1, key2)

    key1, key2 = 'uhiouho78ityd78yowdy7atyodu8yawo8ydwdtaw7d', 'yd8oh8yh8d7yya2yd78y9a8y7ty8of78ogy09gui90'
    test_dual_qr_generation_and_decoding(key1, key2)

    key1, key2 = 'ljfhjkliafho89y4a78oyt4o83iuot348ty3784oyufiher7ufyeo8y3879478ofu3h48of', 'hiojheuilafhioaesfiluhgshjfjhseuifhshhjvjh89fee98fyu89u89pfeuasuhfihehfsaghef'
    test_dual_qr_generation_and_decoding(key1, key2)
