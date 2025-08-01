from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import User


class TestView(APIView):
    def get(self, request):
        return Response({'message': 'API работает!'}, status=status.HTTP_200_OK)
    
    def post(self, request):
        print("DEBUG: Тестовый POST запрос получен!")
        print(f"DEBUG: Данные: {request.data}")
        return Response({'message': 'POST работает!', 'data': request.data}, status=status.HTTP_200_OK)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150,
                                     error_messages={
                                         'blank': 'Логин не может быть пустым',
                                         'max_length': 'Логин не может быть длиннее 150 символов'
                                     })

    password = serializers.CharField(min_length=6,
                                     error_messages={
                                         'blank': 'Пароль не может быть пустым',
                                         'min_length': 'Пароль должен быть длиннее 6 символов'
                                     })

    def validate_username(self, value):
        """Валидация логина"""
        if not value.strip():
            raise serializers.ValidationError('Логин не может состоять только из пробелов')
        return value.strip()

    def validate_password(self, value):
        if not value.strip():
            raise serializers.ValidationError('Пароль не может состоять только из пробелов')
        return value.strip()



class LoginApiView(APIView):
    permission_classes = []  # Убираем требование аутентификации для входа
    """
    API endpoint для аутентификации пользователя

    Выполняется post запрос с данными в формате JSON
    - username (str): Логин пользователя (обязательно)
    - password (str): Пароль пользователя (обязательно, минимум 6 символов)

    Коды ответа:
        200 - OK (Успешная аутентификация)
        401 - Неверные учетные данные
        400 - Ошибка валидации данных
    """
    
    def post(self, request):
        print("DEBUG: ===== НАЧАЛО МЕТОДА POST =====")
        print(f"DEBUG: Данные запроса: {request.data}")
        print(f"DEBUG: Метод запроса: {request.method}")
        print(f"DEBUG: URL: {request.path}")
        
        serializer = LoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Ошибка валидации данных',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(username=username)
            print(f"DEBUG: Найден пользователь {username}")
            print(f"DEBUG: Пароль в БД: {user.password[:20]}...")
            print(f"DEBUG: Проверяем пароль: {password}")
            
            if not check_password(password, user.password):
                print(f"DEBUG: Пароль не совпадает!")
                return Response({
                    'error': 'Неверный логин или пароль'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Генерация JWT токена
            refresh = RefreshToken.for_user(user)

            # Возвращаем успешный ответ и информацию о пользователе
            return Response({
                'success': True,
                'message': f'Вы успешно вошли как {user.get_role_display()}',
                'token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'role': user.role,
                    'role_display': user.get_role_display()
                },
                'login_time': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            print(f"DEBUG: Пользователь {username} не найден в базе данных!")
            return Response({
                'error': 'Неверный логин или пароль'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        except Exception as e:
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserInfoApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            serializer = UserInfoSerializer(user)

            return Response({
                'success': True,
                'user': serializer.data,
                'role_display': user.get_role_display(),
                'login_time': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role']
        read_only_fields = ['id', 'username', 'role']


class LogOutApiView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # В тестовой реализации просто возвращаем 200 ОК
            # В продакшене нужно добавлять токены в черныцй список
            return Response({
                'success': True,
                'message': 'Вы успешно вышли из системы'
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                'error': 'Внутренняя ошибка сервера'
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)