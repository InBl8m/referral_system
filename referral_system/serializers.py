from .models import User
from rest_framework import serializers


class VerificationCodeSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=15)
    verification_code = serializers.CharField(max_length=4)


class UserProfileSerializer(serializers.ModelSerializer):
    invited_users = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
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

