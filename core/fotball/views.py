from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date

from .models import User, GroupKidGarden, Attendance, Child, MedicalCertificate, TrainingSchedule, Trainer, TrainerComment, ScheduleChangeNotification, NotificationRead


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


class ParentChildInfoApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение информации о ребенке родителя
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является родителем
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного ребенка
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child = user.linked_child
            
            # Получение информации о группе
            group_info = None
            if child.group:
                group_info = {
                    'id': child.group.id,
                    'name': child.group.name,
                    'kindergarten_number': child.group.kindergarten_number,
                    'age_level': child.group.get_age_level_display()
                }
            
            return Response({
                'success': True,
                'child': {
                    'id': child.id,
                    'full_name': child.full_name,
                    'birth_date': child.birth_date,
                    'is_active': child.is_active,
                    'group': group_info
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении информации о ребенке: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentAttendanceApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение посещаемости ребенка родителя
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является родителем
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного ребенка
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child = user.linked_child
            
            # Получение параметров запроса
            month = request.GET.get('month')
            year = request.GET.get('year')
            
            # Если месяц и год не указаны, используем текущий месяц
            from datetime import datetime
            if not month:
                month = datetime.now().month
            if not year:
                year = datetime.now().year
            
            # Получение записей посещаемости за указанный месяц
            attendance_records = Attendance.objects.filter(
                child=child,
                date__year=year,
                date__month=month
            ).order_by('date')
            
            # Подсчет статистики
            total_training_days = attendance_records.count()
            attended_days = attendance_records.filter(status=True).count()
            missed_days = total_training_days - attended_days
            
            # Формирование данных о посещаемости
            attendance_data = []
            for record in attendance_records:
                attendance_data.append({
                    'date': record.date.isoformat(),
                    'status': record.status,
                    'reason': record.reason if not record.status else None,
                    'group_name': record.group.name if record.group else None
                })
            
            return Response({
                'success': True,
                'child': {
                    'id': child.id,
                    'full_name': child.full_name,
                    'group_name': child.group.name if child.group else None
                },
                'attendance_stats': {
                    'total_training_days': total_training_days,
                    'attended_days': attended_days,
                    'missed_days': missed_days,
                    'attendance_percentage': round((attended_days / total_training_days * 100) if total_training_days > 0 else 0, 1)
                },
                'attendance_records': attendance_data,
                'period': {
                    'month': int(month),
                    'year': int(year)
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении посещаемости: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentNextTrainingApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение информации о следующей тренировке
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является родителем
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного ребенка
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child = user.linked_child
            
            # Получение информации о группе
            if not child.group:
                return Response({
                    'success': True,
                    'next_training': None,
                    'message': 'Ребенок не привязан к группе'
                }, status=status.HTTP_200_OK)
            
            # Здесь можно добавить логику для определения следующей тренировки
            # Пока что возвращаем информацию о группе
            group_info = {
                'id': child.group.id,
                'name': child.group.name,
                'kindergarten_number': child.group.kindergarten_number,
                'age_level': child.group.get_age_level_display()
            }
            
            # TODO: Добавить логику определения расписания тренировок
            # Пока что возвращаем базовую информацию
            return Response({
                'success': True,
                'next_training': {
                    'group': group_info,
                    'message': 'Расписание тренировок будет доступно в ближайшее время'
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении информации о следующей тренировке: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentCommentsApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение комментариев тренера о ребенке
        """
        try:
            user = request.user
            
            # Проверка, что пользователь является родителем
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получение связанного ребенка
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child = user.linked_child
            
            # Получаем комментарии тренеров о ребенке
            comments = TrainerComment.objects.filter(child=child).select_related('trainer').order_by('-created_at')
            
            comments_data = []
            for comment in comments:
                comments_data.append({
                    'id': comment.id,
                    'date': comment.created_at.strftime('%d.%m.%Y'),
                    'trainer_name': comment.trainer.full_name,
                    'text': comment.comment_text,
                    'created_at': comment.created_at.isoformat()
                })
            
            return Response({
                'success': True,
                'comments': comments_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении комментариев: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainerCommentsApiView(APIView):
    """
    API для управления комментариями тренера.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить комментарии тренера для детей его групп"""
        try:
            user = request.user
            
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            if not user.linked_trainer:
                return Response({
                    'error': 'Тренер не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            # Получаем всех детей из групп тренера
            trainer_groups = user.linked_trainer.groups.all()
            children = Child.objects.filter(group__in=trainer_groups, is_active=True)
            
            # Получаем комментарии для этих детей
            comments = TrainerComment.objects.filter(
                trainer=user.linked_trainer,
                child__in=children
            ).select_related('child').order_by('-created_at')

            comments_data = []
            for comment in comments:
                comments_data.append({
                    'id': comment.id,
                    'child': {
                        'id': comment.child.id,
                        'name': comment.child.full_name,
                        'group': comment.child.group.name if comment.child.group else None
                    },
                    'comment_text': comment.comment_text,
                    'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
                })

            # Также возвращаем список детей для формы
            children_list = []
            for child in children:
                children_list.append({
                    'id': child.id,
                    'name': child.full_name,
                    'group': child.group.name if child.group else None
                })

            return Response({
                'comments': comments_data,
                'children': children_list
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при получении комментариев тренера: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Создать новый комментарий"""
        try:
            user = request.user
            
            if user.role != 'trainer':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            if not user.linked_trainer:
                return Response({
                    'error': 'Тренер не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            # Валидация данных
            child_id = request.data.get('child_id')
            comment_text = request.data.get('comment_text', '').strip()

            if not child_id:
                return Response({
                    'error': 'Не указан ребенок'
                }, status=status.HTTP_400_BAD_REQUEST)

            if not comment_text:
                return Response({
                    'error': 'Комментарий не может быть пустым'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем, что ребенок в группах тренера
            try:
                child = Child.objects.get(id=child_id)
            except Child.DoesNotExist:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            trainer_groups = user.linked_trainer.groups.all()
            if child.group not in trainer_groups:
                return Response({
                    'error': 'У вас нет доступа к этому ребенку'
                }, status=status.HTTP_403_FORBIDDEN)

            # Создаем комментарий
            comment = TrainerComment.objects.create(
                trainer=user.linked_trainer,
                child=child,
                comment_text=comment_text
            )

            return Response({
                'message': 'Комментарий успешно добавлен',
                'comment': {
                    'id': comment.id,
                    'child_name': comment.child.full_name,
                    'comment_text': comment.comment_text,
                    'created_at': comment.created_at.strftime('%d.%m.%Y %H:%M')
                }
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Ошибка при создании комментария: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentPaymentCalculationApiView(APIView):
    """
    API для расчета предварительной суммы к оплате.
    Рассчитывает сумму на основе пропущенных занятий без уважительной причины.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Рассчитать сумму к оплате за текущий месяц"""
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем ребенка родителя
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child = user.linked_child

            # Получаем текущий месяц и год
            now = timezone.now()
            current_month = now.month
            current_year = now.year

            # Получаем все посещения за текущий месяц
            attendances = Attendance.objects.filter(
                child=child,
                date__month=current_month,
                date__year=current_year
            )

            # Подсчитываем посещения и пропуски
            total_trainings = attendances.count()
            attended_trainings = attendances.filter(status=True).count()
            missed_trainings = total_trainings - attended_trainings

            # Получаем справки, которые были одобрены (статус 'approved')
            approved_certificates = MedicalCertificate.objects.filter(
                child=child,
                status='approved',
                date_from__month=current_month,
                date_from__year=current_year
            )

            # Подсчитываем количество пропущенных тренировок с уважительной причиной
            # Для этого проверяем каждую пропущенную тренировку на наличие одобренной справки
            excused_missed = 0
            missed_attendances = attendances.filter(status=False)
            
            for missed_attendance in missed_attendances:
                # Проверяем, есть ли одобренная справка, покрывающая эту дату
                for cert in approved_certificates:
                    if cert.date_from and cert.date_to:
                        if cert.date_from <= missed_attendance.date <= cert.date_to:
                            excused_missed += 1
                            break  # Нашли справку для этого пропуска, переходим к следующему

            # Рассчитываем количество пропусков без уважительной причины
            unexcused_missed = missed_trainings - excused_missed

            # Стоимость одного занятия (берем из первой справки или используем дефолтную)
            cost_per_lesson = 500.00
            if approved_certificates.exists():
                cost_per_lesson = float(approved_certificates.first().cost_per_lesson)

            # Рассчитываем сумму к оплате
            # Если есть пропуски без уважительной причины, то считаем полную стоимость всех тренировок
            # Если все пропуски с уважительной причиной, то платим только за посещенные тренировки
            if unexcused_missed > 0:
                amount_to_pay = total_trainings * cost_per_lesson
            else:
                amount_to_pay = attended_trainings * cost_per_lesson

            # Отладочная информация
            print(f"DEBUG Payment Calculation:")
            print(f"  Total trainings: {total_trainings}")
            print(f"  Attended: {attended_trainings}")
            print(f"  Missed: {missed_trainings}")
            print(f"  Excused missed: {excused_missed}")
            print(f"  Unexcused missed: {unexcused_missed}")
            print(f"  Cost per lesson: {cost_per_lesson}")
            print(f"  Logic: {'Full payment (unexcused missed > 0)' if unexcused_missed > 0 else 'Payment for attended only (all missed excused)'}")
            print(f"  Amount to pay: {amount_to_pay}")

            return Response({
                'month': current_month,
                'year': current_year,
                'total_trainings': total_trainings,
                'attended_trainings': attended_trainings,
                'missed_trainings': missed_trainings,
                'excused_missed': excused_missed,
                'unexcused_missed': unexcused_missed,
                'cost_per_lesson': cost_per_lesson,
                'amount_to_pay': amount_to_pay
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при расчете суммы к оплате: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentMedicalCertificatesApiView(APIView):
    """
    API для работы со справками о болезни ребенка.
    Позволяет родителю загружать и просматривать справки.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        """Получить список справок для ребенка родителя"""
        try:
            user = request.user
            print(f"DEBUG: User role: {user.role}")
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем ребенка родителя
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child = user.linked_child

            # Получаем справки
            certificates = MedicalCertificate.objects.filter(
                child=child
            ).order_by('-uploaded_at')

            certificates_data = []
            for cert in certificates:
                certificates_data.append({
                    'id': cert.id,
                    'date_from': cert.date_from.strftime('%d.%m.%Y'),
                    'date_to': cert.date_to.strftime('%d.%m.%Y'),
                    'note': cert.note,
                    'absence_reason': cert.absence_reason,
                    'uploaded_at': cert.uploaded_at.strftime('%d.%m.%Y %H:%M'),
                    'status': cert.get_status_display(),
                    'status_code': cert.status,
                    'admin_comment': cert.admin_comment,
                    'cost_per_lesson': float(cert.cost_per_lesson),
                    'total_cost': float(cert.total_cost),
                    'file_url': request.build_absolute_uri(cert.certificate_file.url) if cert.certificate_file else None,
                    'file_name': cert.certificate_file.name.split('/')[-1] if cert.certificate_file else None
                })

            return Response({
                'certificates': certificates_data,
                'child_name': child.full_name
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при получении справок: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Загрузить новую справку о болезни"""
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем ребенка родителя
            if not user.linked_child:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child = user.linked_child

            # Валидация данных
            required_fields = ['date_from', 'date_to']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'error': f'Поле {field} обязательно'
                    }, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем наличие файла только если это не запрос на перерасчет
            if 'absence_reason' not in request.data and 'certificate_file' not in request.FILES:
                return Response({
                    'error': 'Файл справки обязателен'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Создаем справку
            certificate_data = {
                'child': child,
                'parent': user,
                'date_from': request.data['date_from'],
                'date_to': request.data['date_to'],
                'note': request.data.get('note', ''),
                'absence_reason': request.data.get('absence_reason', '')
            }
            
            # Добавляем файл только если он загружен
            if 'certificate_file' in request.FILES:
                certificate_data['certificate_file'] = request.FILES['certificate_file']
            
            certificate = MedicalCertificate.objects.create(**certificate_data)

            return Response({
                'message': 'Справка успешно загружена',
                'certificate_id': certificate.id
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Ошибка при загрузке справки: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminMedicalCertificatesApiView(APIView):
    """
    API для администратора для просмотра всех справок.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить все справки для администратора"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем все справки
            certificates = MedicalCertificate.objects.select_related(
                'child', 'parent'
            ).order_by('-uploaded_at')

            certificates_data = []
            for cert in certificates:
                certificates_data.append({
                    'id': cert.id,
                    'child_name': cert.child.full_name,
                    'parent_name': cert.parent.username,
                    'date_from': cert.date_from.strftime('%d.%m.%Y'),
                    'date_to': cert.date_to.strftime('%d.%m.%Y'),
                    'note': cert.note,
                    'absence_reason': cert.absence_reason,
                    'uploaded_at': cert.uploaded_at.strftime('%d.%m.%Y %H:%M'),
                    'status': cert.get_status_display(),
                    'status_code': cert.status,
                    'admin_comment': cert.admin_comment,
                    'cost_per_lesson': float(cert.cost_per_lesson),
                    'total_cost': float(cert.total_cost),
                    'file_url': request.build_absolute_uri(cert.certificate_file.url) if cert.certificate_file else None,
                    'file_name': cert.certificate_file.name.split('/')[-1] if cert.certificate_file else None
                })

            return Response(certificates_data, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при получении справок для админа: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminApproveMedicalCertificateApiView(APIView):
    """
    API для администратора для подтверждения справки.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, certificate_id):
        """Подтвердить справку"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем справку
            try:
                certificate = MedicalCertificate.objects.get(id=certificate_id)
            except MedicalCertificate.DoesNotExist:
                return Response({
                    'error': 'Справка не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Обновляем статус
            certificate.status = 'approved'
            certificate.save()

            print(f"Справка {certificate_id} подтверждена администратором {user.username}")

            return Response({
                'message': 'Справка успешно подтверждена',
                'certificate_id': certificate_id,
                'status': 'approved'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при подтверждении справки: {e}")
            return Response({
                'error': 'Ошибка при подтверждении справки'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminRejectMedicalCertificateApiView(APIView):
    """
    API для администратора для отклонения справки.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, certificate_id):
        """Отклонить справку"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем справку
            try:
                certificate = MedicalCertificate.objects.get(id=certificate_id)
            except MedicalCertificate.DoesNotExist:
                return Response({
                    'error': 'Справка не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Обновляем статус
            certificate.status = 'rejected'
            certificate.save()

            print(f"Справка {certificate_id} отклонена администратором {user.username}")

            return Response({
                'message': 'Справка отклонена',
                'certificate_id': certificate_id,
                'status': 'rejected'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при отклонении справки: {e}")
            return Response({
                'error': 'Ошибка при отклонении справки'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminScheduleApiView(APIView):
    """
    API для управления расписанием тренировок (администратор).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить список всех групп для составления расписания"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем все группы, сгруппированные по садам
            groups = GroupKidGarden.objects.all()
            
            # Группируем по детским садам
            kindergartens = {}
            for group in groups:
                kindergarten_number = group.kindergarten_number
                if kindergarten_number not in kindergartens:
                    kindergartens[kindergarten_number] = {
                        'number': kindergarten_number,
                        'groups': []
                    }
                
                # Получаем тренера один раз
                primary_trainer = group.get_primary_trainer()
                
                kindergartens[kindergarten_number]['groups'].append({
                    'id': group.id,
                    'name': group.name,
                    'age_level': group.get_age_level_display(),
                    'trainer': {
                        'id': primary_trainer.id if primary_trainer else None,
                        'name': primary_trainer.full_name if primary_trainer else 'Не назначен'
                    },
                    'children_count': group.children_group.filter(is_active=True).count()
                })

            return Response({
                'kindergartens': list(kindergartens.values())
            }, status=status.HTTP_200_OK)

        except Exception as e:
            import traceback
            print(f"Ошибка при получении групп для расписания: {e}")
            print(f"Traceback: {traceback.format_exc()}")
            return Response({
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Создать тренировки в расписании (одну или несколько)"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Проверяем тип создания: одиночная тренировка или массовое создание
            if 'bulk_create' in request.data and request.data['bulk_create']:
                return self._bulk_create_trainings(request, user)
            else:
                return self._create_single_training(request, user)

        except Exception as e:
            print(f"Ошибка при создании тренировки: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _create_single_training(self, request, user):
        """Создать одну тренировку"""
        # Валидация данных
        required_fields = ['group_id', 'date', 'time']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'error': f'Поле {field} обязательно'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем группу
        try:
            group = GroupKidGarden.objects.get(id=request.data['group_id'])
        except GroupKidGarden.DoesNotExist:
            return Response({
                'error': 'Группа не найдена'
            }, status=status.HTTP_404_NOT_FOUND)

        # Получаем тренера группы
        trainer = group.get_primary_trainer()
        if not trainer:
            return Response({
                'error': 'У группы не назначен тренер'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Преобразуем строки в объекты даты и времени
        from datetime import datetime
        try:
            date_obj = datetime.strptime(request.data['date'], '%Y-%m-%d').date()
            time_obj = datetime.strptime(request.data['time'], '%H:%M').time()
        except ValueError as e:
            return Response({
                'error': f'Неверный формат даты или времени: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Создаем тренировку
        training = TrainingSchedule.objects.create(
            group=group,
            date=date_obj,
            time=time_obj,
            duration_minutes=request.data.get('duration_minutes', 40),
            location=request.data.get('location', ''),
            trainer=trainer,
            notes=request.data.get('notes', ''),
            created_by=user
        )

        return Response({
            'message': 'Тренировка успешно создана',
            'training_id': training.id,
            'training': {
                'id': training.id,
                'group_name': training.group.name,
                'date': training.date.strftime('%d.%m.%Y'),
                'time': training.time.strftime('%H:%M'),
                'trainer_name': training.trainer.full_name,
                'status': training.get_status_display()
            }
        }, status=status.HTTP_201_CREATED)

    def _bulk_create_trainings(self, request, user):
        """Массовое создание тренировок"""
        from datetime import datetime, timedelta
        
        # Валидация данных для массового создания
        required_fields = ['group_id', 'start_date', 'end_date', 'weekdays', 'time']
        for field in required_fields:
            if field not in request.data:
                return Response({
                    'error': f'Поле {field} обязательно'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Получаем группу
        try:
            group = GroupKidGarden.objects.get(id=request.data['group_id'])
        except GroupKidGarden.DoesNotExist:
            return Response({
                'error': 'Группа не найдена'
            }, status=status.HTTP_404_NOT_FOUND)

        trainer = group.get_primary_trainer()
        if not trainer:
            return Response({
                'error': 'У группы не назначен тренер'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Парсим даты и время
        try:
            start_date = datetime.strptime(request.data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.data['end_date'], '%Y-%m-%d').date()
            time_obj = datetime.strptime(request.data['time'], '%H:%M').time()
        except ValueError as e:
            return Response({
                'error': f'Неверный формат даты или времени: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        weekdays = request.data['weekdays']  # Список дней недели [0=понедельник, 1=вторник, ...]
        
        # Создаем тренировки для выбранных дней недели
        created_trainings = []
        current_date = start_date
        
        while current_date <= end_date:
            # Проверяем, является ли текущий день одним из выбранных дней недели
            if current_date.weekday() in weekdays:
                # Проверяем, нет ли уже тренировки в это время
                existing = TrainingSchedule.objects.filter(
                    group=group,
                    date=current_date,
                    time=time_obj
                ).exists()
                
                if not existing:
                    training = TrainingSchedule.objects.create(
                        group=group,
                        date=current_date,
                        time=time_obj,
                        duration_minutes=request.data.get('duration_minutes', 40),
                        location=request.data.get('location', ''),
                        trainer=trainer,
                        notes=request.data.get('notes', ''),
                        created_by=user
                    )
                    created_trainings.append(training)
            
            current_date += timedelta(days=1)

        return Response({
            'message': f'Создано {len(created_trainings)} тренировок',
            'created_count': len(created_trainings),
            'trainings': [{
                'id': t.id,
                'date': t.date.strftime('%d.%m.%Y'),
                'time': t.time.strftime('%H:%M')
            } for t in created_trainings]
        }, status=status.HTTP_201_CREATED)

    def put(self, request, training_id):
        """Обновить существующую тренировку"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем тренировку
            try:
                training = TrainingSchedule.objects.get(id=training_id)
            except TrainingSchedule.DoesNotExist:
                return Response({
                    'error': 'Тренировка не найдена'
                }, status=status.HTTP_404_NOT_FOUND)

            # Преобразуем строки в объекты даты и времени
            from datetime import datetime
            old_date = training.date
            old_time = training.time
            
            try:
                if 'date' in request.data:
                    new_date = datetime.strptime(request.data['date'], '%Y-%m-%d').date()
                    training.date = new_date
                if 'time' in request.data:
                    new_time = datetime.strptime(request.data['time'], '%H:%M').time()
                    training.time = new_time
            except ValueError as e:
                return Response({
                    'error': f'Неверный формат даты или времени: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Обновляем другие поля
            if 'duration_minutes' in request.data:
                training.duration_minutes = request.data['duration_minutes']
            if 'location' in request.data:
                training.location = request.data['location']
            if 'notes' in request.data:
                training.notes = request.data['notes']

            training.save()

            # Проверяем, изменились ли дата или время
            date_changed = old_date != training.date
            time_changed = old_time != training.time

            # Создаем уведомление об изменении, если дата или время изменились
            if date_changed or time_changed:
                # Определяем тип уведомления
                if date_changed and time_changed:
                    notification_type = 'both_changed'
                    message = f"Тренировка группы {training.group.name} перенесена с {old_date.strftime('%d.%m.%Y')} {old_time.strftime('%H:%M')} на {training.date.strftime('%d.%m.%Y')} {training.time.strftime('%H:%M')}"
                elif date_changed:
                    notification_type = 'date_changed'
                    message = f"Дата тренировки группы {training.group.name} изменена с {old_date.strftime('%d.%m.%Y')} на {training.date.strftime('%d.%m.%Y')} (время: {training.time.strftime('%H:%M')})"
                else:  # time_changed
                    notification_type = 'time_changed'
                    message = f"Время тренировки группы {training.group.name} изменено с {old_time.strftime('%H:%M')} на {training.time.strftime('%H:%M')} (дата: {training.date.strftime('%d.%m.%Y')})"

                # Создаем уведомление
                ScheduleChangeNotification.objects.create(
                    training=training,
                    notification_type=notification_type,
                    old_date=old_date if date_changed else None,
                    new_date=training.date if date_changed else None,
                    old_time=old_time if time_changed else None,
                    new_time=training.time if time_changed else None,
                    message=message,
                    created_by=user
                )

                print(f"Создано уведомление об изменении тренировки: {message}")

            return Response({
                'message': 'Тренировка успешно обновлена',
                'training_id': training.id,
                'changes': {
                    'date_changed': date_changed,
                    'time_changed': time_changed,
                    'old_date': old_date.strftime('%d.%m.%Y') if date_changed else None,
                    'old_time': old_time.strftime('%H:%M') if time_changed else None,
                    'new_date': training.date.strftime('%d.%m.%Y') if date_changed else None,
                    'new_time': training.time.strftime('%H:%M') if time_changed else None
                },
                'training': {
                    'id': training.id,
                    'group_name': training.group.name,
                    'date': training.date.strftime('%d.%m.%Y'),
                    'time': training.time.strftime('%H:%M'),
                    'trainer_name': training.trainer.full_name,
                    'status': training.get_status_display()
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при обновлении тренировки: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleApiView(APIView):
    """
    API для получения расписания тренировок (для всех ролей).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить расписание тренировок"""
        try:
            user = request.user
            
            # Фильтруем тренировки в зависимости от роли
            if user.role == 'trainer':
                # Тренер видит только свои тренировки
                if not user.linked_trainer:
                    print(f"DEBUG: Тренер не найден для пользователя {user.username}")
                    return Response({
                        'error': 'Тренер не найден'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                trainings = TrainingSchedule.objects.filter(
                    trainer=user.linked_trainer,
                    status='scheduled'
                ).order_by('date', 'time')
                
            elif user.role == 'parent':
                # Родитель видит тренировки группы своего ребенка
                if not user.linked_child or not user.linked_child.group:
                    return Response({
                        'error': 'Ребенок или группа не найдены'
                    }, status=status.HTTP_404_NOT_FOUND)
                
                trainings = TrainingSchedule.objects.filter(
                    group=user.linked_child.group,
                    status='scheduled'
                ).order_by('date', 'time')
                
            elif user.role == 'admin':
                # Администратор видит все тренировки
                trainings = TrainingSchedule.objects.all().order_by('date', 'time')
            else:
                return Response({
                    'error': 'Неизвестная роль пользователя'
                }, status=status.HTTP_403_FORBIDDEN)

            # Формируем данные для ответа
            trainings_data = []
            for training in trainings:
                trainings_data.append({
                    'id': training.id,
                    'group': {
                        'id': training.group.id,
                        'name': training.group.name,
                        'kindergarten_number': training.group.kindergarten_number,
                        'age_level': training.group.get_age_level_display(),
                        'garden': {
                            'name': f"Детский сад №{training.group.kindergarten_number}",
                            'number': training.group.kindergarten_number
                        }
                    },
                    'date': training.date.strftime('%d.%m.%Y'),
                    'time': training.time.strftime('%H:%M'),
                    'duration_minutes': training.duration_minutes,
                    'location': training.location,
                    'trainer': {
                        'id': training.trainer.id,
                        'name': training.trainer.full_name
                    },
                    'status': training.get_status_display(),
                    'status_code': training.status,
                    'notes': training.notes,
                    'created_at': training.created_at.strftime('%d.%m.%Y %H:%M')
                })

            return Response({
                'schedule': trainings_data,
                'trainings': trainings_data,
                'count': len(trainings_data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при получении расписания: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ScheduleNotificationsApiView(APIView):
    """
    API для получения уведомлений об изменениях расписания.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Получить уведомления для пользователя"""
        try:
            user = request.user
            
            if user.role == 'parent':
                # Родитель получает уведомления для группы своего ребенка
                if not user.linked_child or not user.linked_child.group:
                    return Response({
                        'notifications': []
                    }, status=status.HTTP_200_OK)
                
                notifications = ScheduleChangeNotification.objects.filter(
                    training__group=user.linked_child.group
                ).order_by('-created_at')[:10]  # Последние 10 уведомлений
                
            elif user.role == 'trainer':
                # Тренер получает уведомления для своих групп
                if not user.linked_trainer:
                    return Response({
                        'notifications': []
                    }, status=status.HTTP_200_OK)
                
                trainer_groups = user.linked_trainer.groups.all()
                notifications = ScheduleChangeNotification.objects.filter(
                    training__group__in=trainer_groups
                ).order_by('-created_at')[:10]  # Последние 10 уведомлений
                
            else:
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            # Получаем ID прочитанных уведомлений для текущего пользователя
            read_notification_ids = set(
                NotificationRead.objects.filter(
                    user=user,
                    notification__in=notifications
                ).values_list('notification_id', flat=True)
            )

            # Формируем данные для ответа
            notifications_data = []
            for notification in notifications:
                is_read = notification.id in read_notification_ids
                notifications_data.append({
                    'id': notification.id,
                    'type': notification.get_notification_type_display(),
                    'type_code': notification.notification_type,
                    'message': notification.message,
                    'training': {
                        'id': notification.training.id,
                        'group_name': notification.training.group.name,
                        'date': notification.training.date.strftime('%d.%m.%Y'),
                        'time': notification.training.time.strftime('%H:%M')
                    },
                    'changes': {
                        'old_date': notification.old_date.strftime('%d.%m.%Y') if notification.old_date else None,
                        'new_date': notification.new_date.strftime('%d.%m.%Y') if notification.new_date else None,
                        'old_time': notification.old_time.strftime('%H:%M') if notification.old_time else None,
                        'new_time': notification.new_time.strftime('%H:%M') if notification.new_time else None
                    },
                    'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
                    'is_read': is_read
                })

            return Response({
                'notifications': notifications_data,
                'count': len(notifications_data)
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при получении уведомлений о расписании: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MarkNotificationReadApiView(APIView):
    """API для отметки уведомления как прочитанного"""
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            user = request.user
            if user.role not in ['parent', 'trainer']:
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)

            # Проверяем существование уведомления
            try:
                notification = ScheduleChangeNotification.objects.get(id=notification_id)
            except ScheduleChangeNotification.DoesNotExist:
                return Response({'error': 'Уведомление не найдено'}, status=status.HTTP_404_NOT_FOUND)

            # Проверяем, имеет ли пользователь доступ к этому уведомлению
            has_access = False
            if user.role == 'parent':
                if user.linked_child and user.linked_child.group == notification.training.group:
                    has_access = True
            elif user.role == 'trainer':
                if user.linked_trainer and notification.training.group in user.linked_trainer.groups.all():
                    has_access = True

            if not has_access:
                return Response({'error': 'Доступ к уведомлению запрещен'}, status=status.HTTP_403_FORBIDDEN)

            # Создаем или получаем запись о прочтении
            notification_read, created = NotificationRead.objects.get_or_create(
                user=user,
                notification=notification
            )

            return Response({
                'message': 'Уведомление отмечено как прочитанное' if created else 'Уведомление уже было прочитано',
                'notification_id': notification_id,
                'is_new': created
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при отметке уведомления как прочитанного: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)