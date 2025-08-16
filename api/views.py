import os
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework import viewsets, status
from django.core.files.storage import default_storage
from django.conf import settings
from django.shortcuts import get_object_or_404
from datetime import datetime
import logging
import sys

from api.serializers import KndSerializer
from knd.models import Knd, Users
from api.utils.one_qrcod_in_url_decode import decode_qr_code
from api.utils.parser_erknm_headless import parse_knm_data

from .utils.logging_config import logger

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


class KndViewSet(viewsets.ModelViewSet):
    """ViewSet для работы КНД."""

    queryset = Knd.objects.all()
    serializer_class = KndSerializer
    FIELD_MAPPING = {
        'Дата регистрации': 'reg_data',
        'Номер КНМ': 'number_knd',
        'Статус КНМ': 'status_knm',
        'Дата регистрации': 'reg_data',
        'Дата начала': 'start_data', 
        'Дата окончания': 'end_data', 
        'Адрес': 'adress'
    }

    @action(detail=False, methods=['post'], url_path='upload_qrcod', parser_classes=[MultiPartParser])
    def upload_qrcod(self, request):
        # Получаем файл из запроса
        file = request.FILES.get('file')  # 'file' — имя поля в FormData
        if not file:
            return Response(
                {"error": "Файл не предоставлен"},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Проверяем тип файла (только изображения)
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif']
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in allowed_extensions:
            return Response(
                {"error": "Недопустимый формат файла"},
                status=status.HTTP_400_BAD_REQUEST
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
                'inspector': self.request.user,
                'number_knd': result_knd.get('Номер КНМ'),
                'status_knm': result_knd.get('Статус КНМ'),
                'reg_data': parse_datetime(result_knd['Дата регистрации']),
                'start_data': parse_date(result_knd['Дата начала']),
                'end_data': parse_date(result_knd['Дата окончания']),
                'adress': parse_date(result_knd['Адрес'])
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
                {"error": f"{KndViewSet.__name__}: Ошибка обработки данных: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_knd(self):
        """Возвращает проверку по id из URL или 404 если пост не найден."""

        if getattr(self, 'swagger_fake_view', False):
            # Во время генерации схемы возвращаем None
            return None
        return get_object_or_404(Knd, pk=self.kwargs['pk'])
    

    def perform_update(self, serializer):
        """Создает комментарий к посту с текущим пользователем, как автора."""
        
        content = parse_knm_data(self.get_knd().url_knd)
        update_data = {}
        knm_status = content['Статус КНМ']
        db_status = getattr(self.get_knd(), self.FIELD_MAPPING['Статус КНМ'])
        if db_status != knm_status:
            update_data[self.FIELD_MAPPING['Статус КНМ']] = knm_status
            logger.debug(f"Поле {self.FIELD_MAPPING['Статус КНМ']} изменено с {db_status} на {knm_status}")

        if update_data:
            serializer.save(inspektor=self.request.user, **update_data)
        else:
            logger.debug("Изменений не обнаружено")
