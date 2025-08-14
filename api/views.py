import os
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.core.files.storage import default_storage
from django.conf import settings
from datetime import datetime


from api.serializers import KndSerializer
from knd.models import Knd
from api.utils.one_qrcod_in_url_decode import decode_qr_code
from api.utils.parser_erknm_headless import parse_knm_data


# Функции для преобразования дат
def parse_datetime(dt_str):
    if dt_str == 'Не найдено' or not dt_str.strip():
        return None
    try:
        return datetime.strptime(dt_str, '%d.%m.%Y %H:%M')
    except ValueError:
        return None

def parse_date(date_str):
    if date_str == 'Не найдено' or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str, '%d.%m.%Y').date()
    except ValueError:
        return None


class SimpleFileUploadView(APIView):
    """Класс загрузки файла QR coda."""

    parser_classes = (MultiPartParser,)  # Для обработки multipart/form-data

    def post(self, request):
        # Получаем файл из запроса
        file = request.FILES.get('file')  # 'file' — имя поля в FormData
        if not file:
            return Response(
                {"error": "Файл не предоставлен"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Проверяем тип файла (например, только изображения)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return Response(
                {"error": "Недопустимый формат файла"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Проверка уникальности имени файла
        save_path = os.path.join('uploads', file.name)
        if default_storage.exists(save_path):
            return Response(
                {"error": "Такой файл КНД проверки уже есть."},
                status=status.HTTP_409_CONFLICT
            )
        # Сохраняем файл в папку `media/uploads/`
        save_path = os.path.join('uploads', file.name)
        file_path = default_storage.save(save_path, file)
        # Возвращаем URL до сохраненного файла
        file_url = os.path.join(settings.MEDIA_URL, file_path)
        try:
            result_url = decode_qr_code('.' + file_url)
            result_knd = parse_knm_data(result_url['url'])
            if result_knd.get('Статус КНМ') == 'Завершено':
                return Response(
                    {"error": "Проверка завершена. Введите другой QR Code"},
                    status=status.HTTP_409_CONFLICT
                )
            # Создание объекта Knd
            knd_data = {
                'url_knd': result_url['url'],
                'number_knd': result_knd.get('Номер КНМ'),
                'status_knm': result_knd.get('Статус КНМ'),
                'reg_data': parse_datetime(result_knd['Дата регистрации']),
                'start_data': parse_date(result_knd['Дата начала']),
                'end_data': parse_date(result_knd['Дата окончания'])
            }
            # Проверка на существование записи
            if Knd.objects.filter(number_knd=knd_data['number_knd']).exists():
                return Response(
                    {"error": "Запись с таким номером КНМ уже существует"},
                    status=status.HTTP_409_CONFLICT
                )
            # Создание и сохранение объекта
            knd_instance = Knd.objects.create(**knd_data)
            # Возврат данных через сериализатор
            serializer = KndSerializer(knd_instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"{SimpleFileUploadView.__name__}: Ошибка обработки данных: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class KndViewSet(viewsets.ModelViewSet):
    """ViewSet для работы КНД."""

    queryset = Knd.objects.all()
    serializer_class = KndSerializer
