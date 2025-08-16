from rest_framework import serializers
from knd.models import Knd


class KndSerializer(serializers.ModelSerializer):
    inspector = serializers.StringRelatedField(
        read_only=True,
    )

    class Meta:
        model = Knd
        fields = [
            'id',
            'created',
            'inspector',
            'url_knd',
            'number_knd',
            'status_knm',
            'reg_data',
            'start_data',
            'end_data',
            'departure_time',
            'adress'
        ]
