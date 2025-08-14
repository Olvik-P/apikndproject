from django.contrib.auth import get_user_model
from django.db import models

Users = get_user_model()

class Knd(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    inspector = models.ForeignKey(
        Users, 
        related_name='knd_inspector', 
        on_delete=models.CASCADE, 
        null=True, 
        verbose_name='Инспектор'
    )
    url_knd = models.URLField(
        'Ссылка на проверку',
        blank=True,
        null=True,
        default=None,
        unique=True,
        help_text='Ссылка на проверку в формате https://proverki.gov.ru/...'
    )
    number_knd = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True,
        verbose_name="Номер КНД"
    )
    status_knm = models.CharField(
        'Статус КНМ', max_length=20, blank=True, default='')
    reg_data = models.DateTimeField(
        'Дата регистрации КНМ', blank=True, null=True)
    start_data = models.DateField('Начало КНМ', blank=True, null=True)
    end_data = models.DateField('Окончание КНМ', blank=True, null=True)
    adress = models.TextField('Адрес', blank=True, null=True)
    departure_time = models.DateTimeField(
        'Время выезда',
        blank=True,
        null=True,
        help_text='Формат: DD.MM.YYYY HH:MM'
    )

    class Meta:
        ordering = ['created', 'number_knd']
