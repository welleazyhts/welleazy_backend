from rest_framework import serializers
from .models import State, City


class StateSerializer(serializers.ModelSerializer):
    country = serializers.SerializerMethodField()

    class Meta:
        model = State
        fields = ["id", "name", "country", "is_active", "created_at", "updated_at" , "created_by", "updated_by"]

    def get_country(self, obj):
        return "India"
    

class CitySerializer(serializers.ModelSerializer):
    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    state_name = serializers.CharField(source="state.name", read_only=True)
    country = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = [
            "id",
            "name",
            "state",
            "state_name",
            "country",
            "is_active",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        ]

    def get_country(self, obj):
        return "India"
