from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField

from users.utils import generate_ref_code, generate_auth_code


# Create your models here.
class CustomUserManager(BaseUserManager):
    """
        Переопределяем функциональность класса
    """

    use_in_migrations = True

    def create_user(self, phone_number):
        """
            Метод создания суперпользователя
        """
        if not phone_number:
            raise ValueError('Требуется ввод номера телефона')

        user, created = User.objects.get_or_create(phone_number=phone_number) # получаем или создаем пользователя если его нет в БД

        if user.referral_code is None:
            user.referral_code = generate_ref_code()
            user.save()
        code = AuthenticationCode.objects.create(user=user)
        code.save()

        return user

    def create_superuser(self, phone_number, **extra_fields):
        """
        Метод класса, который создает суперпользователя по номеру телефона и паролю.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(phone_number)
        user.is_staff = extra_fields['is_staff']
        user.is_superuser = extra_fields['is_superuser']
        user.save()

        return user


class User(AbstractUser):

    username = None
    password = None
    phone_number = PhoneNumberField(unique=True, verbose_name='Номер телефона')
    referral_code = models.CharField(max_length=5, null=True, default=None, verbose_name='Реферальный код')
    was_referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='referrals', verbose_name='Приглашенный пользователь')
    is_verified = models.BooleanField(default=False, verbose_name='Проверенный пользователь')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class AuthenticationCode(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    date_created = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    code = models.CharField(max_length=5, default=generate_auth_code, verbose_name='Код активации профиля')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Код активации'
        verbose_name_plural = 'Коды активации'
        ordering = ['-id'] # упорядочиваем по убыванию id
