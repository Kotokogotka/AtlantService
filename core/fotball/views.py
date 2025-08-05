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
from datetime import date

from .models import User, GroupKidGarden, Attendance


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
            
            # Генерация JWT токена с правильным user_id
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Убеждаемся, что токен содержит правильный user_id
            access_token['user_id'] = user.id
            access_token['username'] = user.username
            access_token['role'] = user.role

            # Возвращаем успешный ответ и информацию о пользователе
            return Response({
                'success': True,
                'message': f'Вы успешно вошли как {user.get_role_display()}',
                'token': str(access_token),
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
        

class GroupKidgarenSerializer(serializers.ModelSerializer):
    """
    Сериализатор для групп детского сада
    """
    age_level = serializers.CharField(source='get_age_level_display')
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = GroupKidGarden
        fields = ['id', 'name', 'age_level', 'children_count']

    def get_children_count(self, obj):
        """
        Получаем количество активных детей в группе 
        """
        return obj.children_group.filter(is_active=True).count()
        

class TrainerGroupsApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Получение групп, связанные с тренером
        Возвращает список групп, которые ведет тренер
        """
        try:
            print(f"DEBUG: Request user: {request.user}")
            print(f"DEBUG: User type: {type(request.user)}")
            print(f"DEBUG: User authenticated: {request.user.is_authenticated}")
            
            user = request.user

            # Проверка, что пользователь является тренером 
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного тренера с пользователем
            if not user.linked_trainer:
                return Response({
                    'error': 'Тренер не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Получение всех групп, связанных с тренером
            groups = user.linked_trainer.groups.all()

            # Сериализация полученных данных
            serializer = GroupKidgarenSerializer(groups, many=True)

            return Response({
                'success': True,
                'trainer_info': {
                    'full_name': user.linked_trainer.full_name,
                    'phone': user.linked_trainer.phone,
                    'work_space': user.linked_trainer.work_space
                },
                'groups': serializer.data,
                'groups_count': groups.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении групп тренера: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroupDetailApiView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        """
        Получение детальной информации о группе

        Args:
            group_id (int): ID группы
        """

        try:
            user = request.user

            # Проверка, что пользователь является тренером
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение группы по ID
            try:
                group = GroupKidGarden.objects.get(id=group_id)
            except GroupKidGarden.DoesNotExist:
                return Response({
                    'error': 'Группа не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверка, что тренер ведет данную группу
            if not user.linked_trainer or group not in user.linked_trainer.groups.all():
                return Response({
                    'error': 'Нет доступа к данной группе'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение только активных детей в группе
            children = group.children_group.filter(is_active=True)

            # Получаем текущий месяц для подсчета посещаемости
            from datetime import datetime
            current_month = datetime.now().month
            current_year = datetime.now().year

            # Сериализация данных о группе
            group_serializer = GroupKidgarenSerializer(group)

            # Сериализация данных о детях
            children_data = []
            for child in children:
                # Подсчитываем количество посещенных занятий в текущем месяце
                attendance_count = Attendance.objects.filter(
                    child=child,
                    group=group,
                    status=True,  # Только присутствовавшие
                    date__year=current_year,
                    date__month=current_month
                ).count()
                
                children_data.append({
                    'id': child.id,
                    'full_name': child.full_name,
                    'birth_date': child.birth_date,
                    'is_active': child.is_active,
                    'parent_name': child.parent_name.full_name if child.parent_name else None,
                    'parent_phone': child.parent_name.phone if child.parent_name else None,
                    'attendance_count': attendance_count
                })
            
            return Response({
                'success': True,
                'group': group_serializer.data,
                'children': children_data,
                'children_count': children.count()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении информации о группе: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendanceSerializer(serializers.ModelSerializer):
    """Сериализатор для посещаемости"""
    child_name = serializers.CharField(source='child.full_name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'child', 'child_name', 'group', 'group_name', 'date', 'status', 'reason']
        read_only_fields = ['id']


class AttendanceCreateSerializer(serializers.Serializer):
    """Сериализатор для создания посещаемости"""
    group_id = serializers.IntegerField()
    date = serializers.DateField()
    attendance_data = serializers.ListField(
        child=serializers.DictField()
    )


class TrainerAttendanceApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение данных для отметки посещаемости
        Возвращает список садов и групп тренера
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является тренером
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного тренера
            if not user.linked_trainer:
                return Response({
                    'error': 'Тренер не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Получаем все группы тренера
            groups = user.linked_trainer.groups.all()
            
            # Группируем по садам
            kindergartens = {}
            for group in groups:
                kindergarten_number = group.kindergarten_number
                if kindergarten_number not in kindergartens:
                    kindergartens[kindergarten_number] = {
                        'number': kindergarten_number,
                        'groups': []
                    }
                
                kindergartens[kindergarten_number]['groups'].append({
                    'id': group.id,
                    'name': group.name,
                    'age_level': group.get_age_level_display(),
                    'children_count': group.children_group.filter(is_active=True).count()
                })
            
            return Response({
                'success': True,
                'kindergartens': list(kindergartens.values())
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении данных для посещаемости: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self, request):
        """
        Создание записей посещаемости
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является тренером
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            serializer = AttendanceCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'error': 'Ошибка валидации данных',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            group_id = serializer.validated_data['group_id']
            attendance_date = serializer.validated_data['date']
            attendance_data = serializer.validated_data['attendance_data']
            
            # Проверяем, что группа принадлежит тренеру
            try:
                group = GroupKidGarden.objects.get(id=group_id)
                if group not in user.linked_trainer.groups.all():
                    return Response({
                        'error': 'У вас нет доступа к этой группе'
                    }, status=status.HTTP_403_FORBIDDEN)
            except GroupKidGarden.DoesNotExist:
                return Response({
                    'error': 'Группа не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Удаляем существующие записи для этой группы и даты
            Attendance.objects.filter(group=group, date=attendance_date).delete()
            
            # Создаем новые записи
            created_records = []
            for item in attendance_data:
                child_id = item.get('child_id')
                status_value = item.get('status', False)
                reason = item.get('reason', '')
                
                try:
                    child = group.children_group.get(id=child_id)
                    attendance = Attendance.objects.create(
                        child=child,
                        group=group,
                        date=attendance_date,
                        status=status_value,
                        reason=reason if not status_value else ''
                    )
                    created_records.append(attendance)
                except Exception as e:
                    print(f"Ошибка при создании записи для ребенка {child_id}: {e}")
            
            return Response({
                'success': True,
                'message': f'Создано {len(created_records)} записей посещаемости',
                'created_count': len(created_records)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            print(f"Ошибка при создании посещаемости: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroupAttendanceApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, group_id):
        """
        Получение списка детей группы для отметки посещаемости
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является тренером
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем группу
            try:
                group = GroupKidGarden.objects.get(id=group_id)
            except GroupKidGarden.DoesNotExist:
                return Response({
                    'error': 'Группа не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, что тренер ведет эту группу
            if group not in user.linked_trainer.groups.all():
                return Response({
                    'error': 'У вас нет доступа к этой группе'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем детей в группе
            children = group.children_group.filter(is_active=True)
            
            # Получаем текущий месяц для подсчета посещаемости
            from datetime import datetime
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            children_data = []
            for child in children:
                # Подсчитываем количество посещенных занятий в текущем месяце
                attendance_count = Attendance.objects.filter(
                    child=child,
                    group=group,
                    status=True,
                    date__year=current_year,
                    date__month=current_month
                ).count()
                
                children_data.append({
                    'id': child.id,
                    'full_name': child.full_name,
                    'birth_date': child.birth_date,
                    'parent_name': child.parent_name.full_name if child.parent_name else 'Не указан',
                    'parent_phone': child.parent_name.phone if child.parent_name else None,
                    'attendance_count': attendance_count
                })
            
            return Response({
                'success': True,
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'kindergarten_number': group.kindergarten_number,
                    'age_level': group.get_age_level_display()
                },
                'children': children_data,
                'children_count': len(children_data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении детей группы: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AttendanceHistoryApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, group_id):
        """
        Получение истории посещаемости группы
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является тренером
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен, доступ только для тренера'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем группу
            try:
                group = GroupKidGarden.objects.get(id=group_id)
            except GroupKidGarden.DoesNotExist:
                return Response({
                    'error': 'Группа не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Проверяем, что тренер ведет эту группу
            if group not in user.linked_trainer.groups.all():
                return Response({
                    'error': 'У вас нет доступа к этой группе'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем параметры запроса
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            # Фильтруем записи посещаемости
            attendance_queryset = Attendance.objects.filter(group=group)
            
            if date_from:
                attendance_queryset = attendance_queryset.filter(date__gte=date_from)
            if date_to:
                attendance_queryset = attendance_queryset.filter(date__lte=date_to)
            
            # Группируем по датам
            attendance_by_date = {}
            for attendance in attendance_queryset.order_by('date', 'child__full_name'):
                date_str = attendance.date.isoformat()
                if date_str not in attendance_by_date:
                    attendance_by_date[date_str] = []
                
                attendance_by_date[date_str].append({
                    'child_id': attendance.child.id,
                    'child_name': attendance.child.full_name,
                    'status': attendance.status,
                    'reason': attendance.reason or ''
                })
            
            return Response({
                'success': True,
                'group': {
                    'id': group.id,
                    'name': group.name,
                    'kindergarten_number': group.kindergarten_number
                },
                'attendance_history': attendance_by_date
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении истории посещаемости: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)