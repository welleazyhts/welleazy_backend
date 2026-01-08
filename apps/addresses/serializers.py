from rest_framework import serializers
from .models import Address, AddressType
from apps.dependants.models import RelationshipType, Dependant
from apps.location.models import State, City

class AddressTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressType
        fields = ["id", "name", "created_at", "updated_at"]


class AddressSerializer(serializers.ModelSerializer):
    address_type = serializers.PrimaryKeyRelatedField(queryset=AddressType.objects.all())

    state = serializers.PrimaryKeyRelatedField(queryset=State.objects.all())
    city = serializers.PrimaryKeyRelatedField(queryset=City.objects.all())

    state_name = serializers.CharField(source="state.name", read_only=True)
    city_name = serializers.CharField(source="city.name", read_only=True)

    relationship_name = serializers.SerializerMethodField()
    person_name = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = [
            "id",
            "person_name",
            "relationship_name",

            "address_type",
            "state", "state_name",
            "city", "city_name",

            "address_line1",
            "address_line2",
            "landmark",
            "pincode",

            "is_active",
            "is_default",
        ]

    def get_relationship_name(self, obj):
        if obj.dependant:
            return obj.dependant.relationship.name if obj.dependant.relationship else None
        elif obj.user:
            return "Self"
        return None

    def get_person_name(self, obj):
        if obj.dependant:
            return obj.dependant.name
        elif obj.user:
            return obj.user.name or obj.user.get_full_name() or obj.user.email
        return None

    def validate(self, attrs):

        return attrs

    def create(self, validated_data):
        dependant = self.context.get("dependant")
        user = self.context["request"].user

        # Assign user/dependant automatically
        if dependant:
            validated_data["dependant"] = dependant
        else:
            validated_data["user"] = user

        # If this address is default, unset previous defaults
        if validated_data.get("is_default"):
            Address.objects.filter(
                user=user if not dependant else None,
                dependant=dependant if dependant else None,
                address_type=validated_data.get("address_type"),
            ).update(is_default=False)

        return Address.objects.create(**validated_data)