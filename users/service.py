from django.utils import timezone
from django.conf import settings

from users.models import AuthenticationCode


def check_auth_code_lifetime(value):

    """
    Метод для проверки срока действия кода авторизации
    """
    try:
        auth_code = AuthenticationCode.objects.filter(code=value, is_active=True).first()
        expire_time = (timezone.now() - auth_code.created_at).total_seconds()
        if expire_time <= settings.CODE_EXPIRE_TIME: # проверяем чтобы код авторизации действовал не более 10 минут
            return True
        else:
            auth_code.is_active = False
            auth_code.save()
            return False

    except AuthenticationCode.DoesNotExist: # если у пользователя нет кода авторизации
        return False