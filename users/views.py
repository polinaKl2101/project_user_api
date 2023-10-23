from django.shortcuts import render
from rest_framework import generics
from time import sleep
from rest_framework.response import Response
from rest_framework import status
from rest_framework import views
from rest_framework.permissions import AllowAny, IsAuthenticated
from users.models import User, AuthenticationCode
from users.serializers import LoginSerializer, VerifyAuthCodeSerializer, TokenSerializer, UserSerializer
from users.utils import send_auth_code, create_auth_token


# Create your views here.
class LoginAPIView(generics.CreateAPIView):

    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if serializer.is_valid():
            user = User.objects.get(pk=serializer.data['id'])
            confirm_token = AuthenticationCode.objects.filter(user=user).first()
            sleep(3)
            send_auth_code(user, confirm_token, **kwargs)

        data = {
            "user": serializer.data,
            "message": "На указанный номер отправлен токен авторизации",
        }

        return Response(data, status=status.HTTP_201_CREATED)


class VerificationTokenAPIView(views.APIView):
    """
    Функция используется для верификации токена аутентификации пользователя.
    Она принимает POST-запрос с данными пользователя, включая код аутентификации,
    и проверяет его на валидность. Если данные верны, функция создает новый токен
    аутентификации для пользователя и отправляет его в ответе.

    """

    serializer_class = VerifyAuthCodeSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs) -> Response:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        auth_token = create_auth_token(user)
        if auth_token:
            token_serializer = TokenSerializer(data={"token": auth_token.key, }, partial=True)
            if token_serializer.is_valid():
                return Response(token_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Ошибка'}, status=status.HTTP_400_BAD_REQUEST)


class UserAPIView(generics.RetrieveUpdateDestroyAPIView):

    """
    Функция используется для получения и обновления информации
    о пользователе. Она требует аутентификации пользователя, чтобы иметь доступ
    к этим действиям. Возвращает объект пользователя, который запрашивает действие.
    """
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user