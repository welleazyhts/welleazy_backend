from rest_framework import serializers
from .models import Dependant, RelationshipType, DependantOTP, ProfileSwitch
import hashlib


class RelationshipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelationshipType
        fields = ["id", "name", "created_at", "updated_at"]


class DependantSerializer(serializers.ModelSerializer):
    relationship = serializers.PrimaryKeyRelatedField(queryset=RelationshipType.objects.all())

    class Meta:
        model = Dependant
        fields = [
            "id",
            "member_id",
            "name",
            "gender",
            "dob",
            "relationship",
            "mobile_number",
            "email",
            "occupation",
            "marital_status",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["member_id", "created_at", "updated_at"]

    def create(self, validated_data):
        user = self.context["request"].user
        dependant = Dependant.objects.create_dependant(user=user, **validated_data)
        return dependant


class SwitchProfileRequestSerializer(serializers.Serializer):
    #Serializer for requesting to switch to a dependant's profile.
    dependant_id = serializers.IntegerField()

    def validate_dependant_id(self, value):
        #Validate that the dependant exists and belongs to the requesting user.
        user = self.context['request'].user
        
        try:
            dependant = Dependant.objects.get(id=value, user=user)
        except Dependant.DoesNotExist:
            raise serializers.ValidationError("Dependant not found or does not belong to you.")
        
        # Check if dependant has a mobile number
        if not dependant.mobile_number:
            raise serializers.ValidationError(
                "This dependant does not have a mobile number registered. "
                "Please add a mobile number before switching profiles."
            )
        
        return value

    def create(self, validated_data):
        #Create OTP for the dependant.
        user = self.context['request'].user
        dependant = Dependant.objects.get(id=validated_data['dependant_id'])
        
        # Create OTP
        otp_plain = DependantOTP.create_otp(dependant, user)
        
        # Mask mobile number for display
        mobile = dependant.mobile_number
        masked_mobile = mobile[:2] + '*' * (len(mobile) - 4) + mobile[-2:] if len(mobile) > 4 else mobile
        
        return {
            'dependant_id': dependant.id,
            'dependant_name': dependant.name,
            'mobile_number': masked_mobile,
            'otp': otp_plain,  # Return OTP for testing (remove in production)
            'message': f'OTP sent to {masked_mobile}'
        }


class VerifySwitchOTPSerializer(serializers.Serializer):
    #Serializer for verifying OTP and switching to dependant profile.
    dependant_id = serializers.IntegerField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        #Validate OTP and dependant.
        user = self.context['request'].user
        dependant_id = data.get('dependant_id')
        otp_plain = data.get('otp')
        
        # Check dependant exists and belongs to user
        try:
            dependant = Dependant.objects.get(id=dependant_id, user=user)
        except Dependant.DoesNotExist:
            raise serializers.ValidationError({
                "dependant_id": "Dependant not found or does not belong to you."
            })
        
        # Hash the provided OTP
        otp_hash = hashlib.sha256(otp_plain.encode()).hexdigest()
        
        # Find matching OTP
        try:
            otp_obj = DependantOTP.objects.filter(
                dependant=dependant,
                user=user,
                otp_hash=otp_hash,
                is_used=False
            ).latest('created_at')
        except DependantOTP.DoesNotExist:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        
        # Check if OTP is still valid
        if not otp_obj.is_valid():
            raise serializers.ValidationError({"otp": "OTP has expired."})
        
        data['dependant'] = dependant
        data['otp_obj'] = otp_obj
        return data

    def create(self, validated_data):
        # Create or activate profile switch.
        user = self.context['request'].user
        dependant = validated_data['dependant']
        otp_obj = validated_data['otp_obj']
        
        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()
        
        # Create or reactivate profile switch
        profile_switch, created = ProfileSwitch.objects.get_or_create(
            user=user,
            dependant=dependant,
            defaults={'is_active': True}
        )
        
        if not created:
            profile_switch.activate()
        
        return {
            'message': f'Successfully switched to {dependant.name}\'s profile',
            'dependant_id': dependant.id,
            'dependant_name': dependant.name,
            'switched_at': profile_switch.switched_at
        }


class ActiveProfileSerializer(serializers.Serializer):
    #Serializer for getting the current active profile.
    
    def to_representation(self, instance):
        #Return the active profile information.
        user = instance
        active_switch = ProfileSwitch.get_active_switch(user)
        
        if active_switch:
            # User is switched to a dependant
            return {
                'profile_type': 'dependant',
                'user_id': user.id,
                'user_email': user.email,
                'user_name': user.name,
                'active_dependant': {
                    'id': active_switch.dependant.id,
                    'name': active_switch.dependant.name,
                    'member_id': active_switch.dependant.member_id,
                    'relationship': active_switch.dependant.relationship.name if active_switch.dependant.relationship else None,
                    'mobile_number': active_switch.dependant.mobile_number,
                },
                'switched_at': active_switch.switched_at
            }
        else:
            # User is on their own profile
            return {
                'profile_type': 'self',
                'user_id': user.id,
                'user_email': user.email,
                'user_name': user.name,
                'member_id': user.member_id,
                'active_dependant': None
            }
