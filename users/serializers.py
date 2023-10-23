from rest_framework import serializers
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework.exceptions import ValidationError

from users.models import User, AuthenticationCode
from users.service import check_auth_code_lifetime
from users.utils import generate_ref_code


class LoginSerializer(serializers.ModelSerializer):

    phone_number = PhoneNumberField(required=True) # проверяем корректность номер телефона

    class Meta:
        model = User
        fields = ['id', 'phone_number']
        read_only_fields = ['id'] # оставляем поле только для чтения

        def create(self, validated_data):
            """
            Метод чтобы создать/получить экземпляр пользоателя
            Затем метод генерирует код активации для пользователя
            """

            value, _ = User.objects.get_or_create(**validated_data) # берем значение которое будет возвращено,
            # _ чтобы не использователь второе значение которое также может быть возвращено

            if value.referral_code is None: # проверка наличия реферального кода
                value.referral_code = generate_ref_code()
                value.save()

            code = AuthenticationCode.objects.create(user=value) # создаем экзмепляр класса AuthenticationCode и сохраняем его
            code.save()

            return value


class UserViewSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['phone_number']


class UserSerializer(serializers.ModelSerializer):

    no_ref_code = serializers.CharField(write_only=True)
    yes_ref_code = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'first_name', 'last_name', 'referral_code', 'no_ref_code', 'yes_ref_code']

    def get_yes_ref_code(self, obj: User):
        queryset = User.objects.filter(was_referred_by=obj)
        return [UserViewSerializer(i).data for i in queryset]

    def update(self, request, *args, **kwargs):
        self.partial = True # обновляем частично экзепляр
        self.is_valid(raise_exception=True) # проверяем корректность данных
        return super().update(request, *args, **kwargs) # обновляем объект в БД

    def is_valid(self, *, raise_exception=True):
        """Эта функция проверяет, был ли указан код реферала при создании объекта.
        Если код был указан и объект еще не имеет реферала, то функция пытается найти пользователя с таким кодом
        и присвоить его как реферала объекту. Если пользователь не найден или происходит ошибка при обработке кода,
        то генерируется исключение. Функция возвращает результат вызова метода is_valid() у родительского класса с
        переданными аргументами."""

        was_referred_by = self.initial_data.get('no_ref_code', None)

        if was_referred_by and not self.instance.was_referred_by:

            try:
                user_with_ref = User.objects.get(referral_code=was_referred_by)
                self.instance.was_referred_by = user_with_ref
                self.instance.save()
            except User.DoesNotExist:
                raise serializers.ValidationError('Введен неверный код.')
            except:
                raise serializers.ValidationError('Произошла ошибка при обработке промо-кода.')

        return super().is_valid(raise_exception=raise_exception)


class AuthenticationCodeSerializer(serializers.CharField):

    def validate(self, value):
        super().validate(value)
        if not check_auth_code_lifetime(value):
            raise serializers.ValidationError('Код недействителен')
        return value


class VerifyAuthCodeSerializer(serializers.Serializer):

    phone_number = PhoneNumberField(required=False, max_length=11)
    code = AuthenticationCodeSerializer(min_length=5, max_length=5, validators=[check_auth_code_lifetime])


    def validate(self, attrs):
        """
        Эта функция используется для проверки данных, переданных в сериализатор. В данном случае,
        функция проверяет наличие пользователя с заданным номером телефона и проверочным кодом,
        а также проверяет, что пользователь активен. Если данные проходят проверку, то они возвращаются
        в виде словаря attrs. Если же данные не проходят проверку, то функция генерирует исключение
        serializers.ValidationError с соответствующим сообщением об ошибке.
        """
        code = attrs['code']
        phone_number = attrs['phone_number']
        try:
            user = User.objects.get(phone_number=phone_number)
            AuthenticationCode.objects.filter(user=user, code=code, is_active=True).first()
            attrs['user'] = user
            user.is_verified = True
            user.save()

            if not user.is_active:
               raise serializers.ValidationError('Пользователь отключен.')

        except AuthenticationCode.DoesNotExist:
            raise serializers.ValidationError('Ошибка токена авторизации')
        except User.DoesNotExist:
            raise serializers.ValidationError('Пользователь не сущетвует')
        except ValidationError:
            raise serializers.ValidationError('Введены некорректные данные')
        else:
                return attrs


class TokenSerializer(serializers.Serializer):

    token = serializers.CharField(source='key')
    key = serializers.CharField(write_only=True)






