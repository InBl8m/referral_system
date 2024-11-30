from .models import User
from rest_framework import serializers


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)


class VerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    verification_code = serializers.CharField(max_length=4)


class UserProfileSerializer(serializers.ModelSerializer):
    invited_users = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ['phone_number', 'is_verified', 'activated_invite_code', 'invite_code', 'invited_users']
