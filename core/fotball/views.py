from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from rest_framework import serializers

from .models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()



class LoginApiView(APIView):
    """
    API endpoint для аутентификации пользователя

    Выполняется post запрос с данными в формате JSON
    - username (str)
    - password (str)

    Коды ответа:
        200 - OK(Успешная аутентификация)
        401 - Не верные учетные данные
        400 - Ошибка валидации данных
    """
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            print(username)
            print(password)
            try:
                user = User.objects.get(username=username)
                if check_password(password, user.password):
                    return Response({
                        'user_id': user.id,
                        'username': user.username,
                        'role': getattr(user, 'role', None)
                    })
                else:
                    return Response({'error': 'Неверный логин или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
            except User.DoesNotExist:
                return Response({'error': 'Неверный логин или пароль'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)