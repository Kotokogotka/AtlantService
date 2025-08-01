from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
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