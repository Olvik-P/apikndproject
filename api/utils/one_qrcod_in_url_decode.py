"""Преобразует файл изображения с QRCode в ссылку.

Для работы необходимо установить следующие зависимости:

- opencv-python==4.12.0.88
- pyzbar==0.1.9
"""
import cv2
import os
from pyzbar.pyzbar import decode


class DeletionError(Exception):
    """Исключение при ошибке удаления файла."""
    pass


def decode_qr_code(image_path):
    """
    Распознает QR-код на изображении и возвращает данные в виде словаря.
    Всегда удаляет файл после обработки, даже при ошибках.

    Args:
        image_path (str): Путь к изображению с QR-кодом.

    Returns:
        dict: Словарь с ключом 'url' и распознанным значением.

    Raises:
        FileNotFoundError: Если файл не найден.
        ValueError: Если QR-код не распознан или данные пусты.
        Exception: При других ошибках.
    """
    try:
        # Проверка существования файла
        img = cv2.imread(image_path)
        if img is None:
            raise FileNotFoundError(
                f"Файл не найден или поврежден: {image_path}")

        # Декодирование QR-кода
        decoded = decode(img)
        if not decoded:
            raise ValueError("QR-код не распознан на изображении")

        # Извлечение данных
        qr_data = decoded[0].data.decode('utf-8')
        if not qr_data:
            raise ValueError("Распознанные данные пусты")

        return {'url': qr_data}

    except Exception:
        raise
    finally:
        # Удаление файла в любом случае
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"Файл удален: {image_path}")
        except Exception as err:
            print(f"Ошибка при удалении файла {image_path}: {err}")


# Пример использования
if __name__ == "__main__":
    try:
        # С удалением файла (с обработкой ошибки удаления)
        result = decode_qr_code(
            'qrCode/66250926600018079904.png')
        print("Результат:", result)
    except DeletionError:
        print("Файл не удален, но данные распознаны.")
    except Exception:
        print("Программа завершена с ошибкой.")
