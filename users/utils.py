import random

from rest_framework.authtoken.models import Token


def generate_ref_code():
    """
    Метод для генерации реферального кода пользователя
    """
    return ''.join([random.choice(list('123456789ABCDEFG')) for x in range(5)])


def generate_auth_code():
    """
    Метод для генерации кода активации пользователя
    """
    return ''.join([random.choice(list('123456789')) for x in range(5)])


def send_auth_code(user, auth_code):
    """
    Метод, имитирующий отправку кода авторизации
    """
    print(f'Ваш код авторизации: {auth_code}')


def create_auth_token(user):
    """
    Метод для создания токена авториазции пользователя
    """
    return Token.objects.get_or_create(user=user)[0]