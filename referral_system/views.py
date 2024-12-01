from django.contrib.auth import authenticate, login, logout
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Referral
from .serializers import (PhoneNumberSerializer, VerificationCodeSerializer, ReferralProfileSerializer,
                          UserRegistrationSerializer)
from .tasks import send_verification_code_to_user


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user = authenticate(request, username=user.username, password=request.data['password'])
            if user is not None:
                login(request, user)
                return Response({"message": "User registered and logged in successfully."},
                                status=status.HTTP_201_CREATED)
            else:
                return Response({"error": "Authentication failed"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return Response({"message": "User logged in successfully."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


def login_page(request):
    if request.user.is_authenticated:
        return redirect('user_profile')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)  # Выход из системы
    return redirect('login_page')


@login_required
def user_profile(request):
    """
    Отображение профиля пользователя.
    Только для авторизованных пользователей.
    """
    user = request.user  # Получаем текущего авторизованного пользователя
    return render(request, 'user_profile.html', {'user': user})


@api_view(['POST'])
def send_verification_code(request):
    """
    1. Получаем номер телефона.
    2. Генерируем случайный 4-значный код.
    3. Сохраняем его в базе данных.
    4. Отправляем код (задержка 1-2 секунды).
    """

    # Валидация входных данных
    serializer = PhoneNumberSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']

        # Проверяем, существует ли пользователь с таким номером
        user, created = Referral.objects.get_or_create(phone_number=phone_number)

        if not created and user.is_verified:
            return Response({"detail": phone_number + " is already verified."}, status=status.HTTP_400_BAD_REQUEST)

        # Отправляем задачу в фоновом режиме
        send_verification_code_to_user.delay(phone_number)

        return Response({"message": "Verification code is being sent to " + phone_number}, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def verify_code(request):
    """
    1. Проверяем номер телефона и код.
    2. Если код правильный, меняем статус пользователя на верифицированный.
    """

    # Валидация входных данных
    serializer = VerificationCodeSerializer(data=request.data)
    if serializer.is_valid():
        phone_number = serializer.validated_data['phone_number']
        verification_code = serializer.validated_data['verification_code']

        # Находим пользователя по номеру телефона
        try:
            user = Referral.objects.get(phone_number=phone_number)
        except Referral.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Проверяем, совпадает ли код
        if user.verification_code == verification_code:
            # Обновляем статус верификации
            user.is_verified = True
            user.save()
            return Response({"message": "User verified successfully!"}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid verification code."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_last_verification_code(request):
    """
    Эндпоинт для получения последнего отправленного кода подтверждения по номеру телефона.
    """
    phone_number = request.query_params.get('phone_number')

    if not phone_number:
        return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Referral.objects.get(phone_number=phone_number)
        if user.verification_code:
            return Response({"verification_code": user.verification_code}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "No verification code found for this number"}, status=status.HTTP_404_NOT_FOUND)
    except Referral.DoesNotExist:
        return Response({"error": "User with this phone number does not exist"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_user_profile(request):
    """
    Получение профиля пользователя по номеру телефона.
    Возвращаем информацию о активированном инвайт-коде и пользователях, которые использовали его.
    """
    phone_number = request.query_params.get('phone_number')

    if not phone_number:
        return Response({"error": "Phone number is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Referral.objects.get(phone_number=phone_number)
    except Referral.DoesNotExist:
        return Response({"detail": f"User with phone number {phone_number} not found."},
                        status=status.HTTP_404_NOT_FOUND)

    # Сериализация данных пользователя
    serializer = ReferralProfileSerializer(user)
    data = serializer.data

    # Возвращаем список пользователей, которые использовали инвайт-код текущего пользователя
    invited_users = user.invited_users.all()
    invited_users_data = [u.phone_number for u in invited_users]  # Получаем только номера телефонов пользователей
    data['invited_users'] = invited_users_data

    return Response(data)


@api_view(['POST'])
def activate_invite_code(request):
    """
    Активация инвайт-кода. Пользователь может ввести чужой инвайт-код.
    Проверка на существование инвайт-кода и активация его для пользователя.
    """
    phone_number = request.data.get('phone_number')
    invite_code = request.data.get('invite_code')

    if not phone_number or not invite_code:
        return Response({"error": "Phone number and invite code are required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = Referral.objects.get(phone_number=phone_number)
    except Referral.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    # Проверка, активировал ли пользователь уже инвайт-код
    if user.activated_invite_code:
        return Response({"detail": "User has already activated an invite code.",
                         "activated_invite_code": user.activated_invite_code}, status=status.HTTP_400_BAD_REQUEST)

    # Активация инвайт-кода
    if user.activate_invite_code(invite_code):
        return Response({"message": "Invite code activated successfully!"}, status=status.HTTP_200_OK)
    else:
        return Response({"detail": "Invalid invite code."}, status=status.HTTP_400_BAD_REQUEST)
