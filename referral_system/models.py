import string
import random
from django.db import models


class User(models.Model):
    phone_number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    verification_code = models.CharField(max_length=4, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    invite_code = models.CharField(max_length=6, null=True, blank=True)
    activated_invite_code = models.CharField(max_length=6, null=True, blank=True)
    invited_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                   related_name='invited_users')

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        if not self.invite_code:  # Генерируем инвайт-код только при первом сохранении пользователя
            self.invite_code = generate_invite_code()
        super().save(*args, **kwargs)

    def activate_invite_code(self, code):
        """
        Активация инвайт-кода.
        """
        # Проверка, существует ли пользователь с таким инвайт-кодом
        inviter = User.objects.filter(invite_code=code).first()
        if inviter is None:
            return False
        if self == inviter:
            return False
        # Если инвайт-код валиден и не совпадает с собственным кодом
        self.activated_invite_code = code
        self.save()
        inviter.invited_users.add(self)  # Добавляем пользователя в список приглашённых
        inviter.save()
        return True


def generate_invite_code():
    """Генерация случайного инвайт-кода"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(6))
