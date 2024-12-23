from .models import Referral
from rest_framework import serializers
from django.contrib.auth.models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class VerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    verification_code = serializers.CharField(max_length=4)


class ReferralProfileSerializer(serializers.ModelSerializer):
    invited_users = serializers.StringRelatedField(many=True)

    class Meta:
        model = Referral
        fields = ['phone_number', 'is_verified', 'activated_invite_code', 'invite_code', 'invited_users']


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)

    def validate_phone_number(self, value):
        """Записываем номер в формате 10 или 7 цифр"""
        # Удаляем лишние символы
        phone = value.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        # Проверяем, что номер начинается с разрешенных символов и остальная часть состоит из цифр
        if phone.startswith("8") and len(phone) == 11 and phone[1:].isdigit():
            phone = phone[1:]  # Убираем первую цифру "8"
        elif phone.startswith("+7") and len(phone) == 12 and phone[2:].isdigit():
            phone = phone[2:]  # Убираем "+7"
        elif len(phone) == 10 and phone.isdigit():
            pass  # Номер уже в правильном формате
        elif len(phone) == 7 and phone.isdigit():
            pass  # Прямой номер без изменений
        else:
            raise serializers.ValidationError("Неверный формат номера телефона.")

        return phone


class ActivateInviteCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    invite_code = serializers.CharField(max_length=6)


class SuccessResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="Сообщение о статусе операции.")


class ErrorResponseSerializer(serializers.Serializer):
    detail = serializers.CharField(help_text="Описание ошибки.")

