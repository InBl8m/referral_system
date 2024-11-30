from celery import shared_task
import random
import time
from .models import User


@shared_task
def send_verification_code_to_user(phone_number):
    """
    Задача для отправки кода подтверждения пользователю.
    """
    print('Task started')
    time.sleep(2)
    verification_code = str(random.randint(1000, 9999))
    user, created = User.objects.get_or_create(phone_number=phone_number)

    if not created and user.is_verified:
        return "User is already verified."

    user.verification_code = verification_code
    user.is_verified = False
    user.save()
    return f"Verification code {verification_code} sent to {phone_number}"
