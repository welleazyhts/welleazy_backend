from rest_framework import serializers
from .models import Test


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'name', 'code', 'description', 'price', 'active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

