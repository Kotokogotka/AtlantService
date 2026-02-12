from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import User

"""
Кастомный бэкенд для работы с моделью User
Определяет методы authenticate и get_user для аутентификации пользователей
и получения пользователя по идентификатору
Используется для аутентификации пользователей в Django
и для работы с моделью User
Выполняет проверку пароля и возвращает пользователя при успешной аутентификации
Или None при ошибке или отсутствии пользователя.
"""


class CustomUserBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None
    
        try: 
            user = User.objects.get(username=username)
            if check_password(password, user.password):
                return user
        except User.DoesNotExist:
            return None
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


class CustomJWTAuthentication(JWTAuthentication):
    """
    Кастомная JWT аутентификация для работы с моделью User
    """
    
    def get_user(self, validated_token):
        """Получаем пользователя из токена."""
        user_id = validated_token.get('user_id')
        if user_id is None:
            return None
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None