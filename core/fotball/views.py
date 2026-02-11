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
from datetime import date, datetime, timedelta

from .models import User, GroupKidGarden, Attendance, Child, MedicalCertificate, TrainingSchedule, Trainer, TrainerComment, ScheduleChangeNotification, NotificationRead, ParentCommentRead, PaymentInvoice, PaymentReceipt, PaymentSettings, GlobalPaymentQR, TrainingCancellationNotification, Parent
from .payment_service import PaymentService


class RootView(APIView):
    """Корень сайта: краткая информация и ссылки (без авторизации)."""
    permission_classes = []  # доступ без токена
    authentication_classes = []

    def get(self, request):
        return Response({
            'message': 'API работает',
            'api_test': request.build_absolute_uri('/api/test/'),
            'admin': request.build_absolute_uri('/admin/'),
            'login': request.build_absolute_uri('/api/login/'),
        }, status=status.HTTP_200_OK)


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


def get_parent_children(user):
    """Возвращает список всех детей родителя (через Parent или linked_child)."""
    if not user or user.role != 'parent':
        return []
    if not user.linked_child:
        return []
    parent = getattr(user.linked_child, 'parent_name', None)
    if parent:
        children = list(parent.children.filter(is_active=True).order_by('full_name').select_related('group'))
        if user.linked_child not in children:
            children.insert(0, user.linked_child)
        return children
    return [user.linked_child]


class ParentChildInfoApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение информации о детях родителя (все дети, если их несколько).
        """
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Время последнего просмотра комментариев по каждому ребёнку (для индикатора непрочитанного)
            try:
                read_records = {
                    r['child_id']: r['last_read_at']
                    for r in ParentCommentRead.objects.filter(
                        user=user, child__in=children
                    ).values('child_id', 'last_read_at')
                }
            except Exception:
                read_records = {}
            children_data = []
            for child in children:
                group_info = None
                if child.group:
                    group_info = {
                        'id': child.group.id,
                        'name': child.group.name,
                        'kindergarten_number': child.group.kindergarten_number,
                        'age_level': child.group.get_age_level_display()
                    }
                last_read = read_records.get(child.id)
                if last_read is not None:
                    unread_comments_count = TrainerComment.objects.filter(
                        child=child, created_at__gt=last_read
                    ).count()
                else:
                    unread_comments_count = TrainerComment.objects.filter(child=child).count()
                children_data.append({
                    'id': child.id,
                    'full_name': child.full_name,
                    'birth_date': child.birth_date,
                    'is_active': child.is_active,
                    'group': group_info,
                    'unread_comments_count': unread_comments_count,
                })
            
            primary_id = user.linked_child_id if user.linked_child_id else (children_data[0]['id'] if children_data else None)
            return Response({
                'success': True,
                'children': children_data,
                'primary_child_id': primary_id,
                'child': children_data[0] if children_data else None
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении информации о детях: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentAttendanceApiView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Получение посещаемости ребенка родителя. Опционально ?child_id= — по выбранному ребенку.
        """
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    child = next((c for c in children if c.id == cid), None)
                    if not child:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    child = children[0]
            else:
                child = children[0]
            
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
        Получение информации о следующей тренировке. Опционально ?child_id= — по выбранному ребенку.
        """
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    child = next((c for c in children if c.id == cid), None)
                    if not child:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    child = children[0]
            else:
                child = children[0]
            
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
        Получение комментариев тренера о ребенке/детях. Опционально ?child_id= — по одному ребенку.
        """
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен, доступ только для родителя'
                }, status=status.HTTP_403_FORBIDDEN)
            
            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден в системе'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child_ids = [c.id for c in children]
            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    if cid not in child_ids:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                    child_ids = [cid]
                except (ValueError, TypeError):
                    pass
            
            comments = TrainerComment.objects.filter(child_id__in=child_ids).select_related('trainer', 'child').order_by('-created_at')
            
            comments_data = []
            for comment in comments:
                comments_data.append({
                    'id': comment.id,
                    'child_id': comment.child_id,
                    'child_name': comment.child.full_name,
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


class ParentCommentsMarkReadApiView(APIView):
    """Отметить комментарии по ребёнку как прочитанные (для сброса красной точки)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            if user.role != 'parent':
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
            children = get_parent_children(user)
            if not children:
                return Response({'error': 'Ребенок не найден'}, status=status.HTTP_404_NOT_FOUND)
            child_id = request.data.get('child_id')
            if child_id is None:
                return Response({'error': 'Укажите child_id'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                child_id = int(child_id)
            except (ValueError, TypeError):
                return Response({'error': 'Некорректный child_id'}, status=status.HTTP_400_BAD_REQUEST)
            child = next((c for c in children if c.id == child_id), None)
            if not child:
                return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
            now = timezone.now()
            ParentCommentRead.objects.update_or_create(
                user=user, child=child,
                defaults={'last_read_at': now}
            )
            return Response({'success': True, 'message': 'Комментарии отмечены как прочитанные'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка при отметке комментариев: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        """Рассчитать сумму к оплате за текущий месяц. Опционально ?child_id= — по выбранному ребенку."""
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    child = next((c for c in children if c.id == cid), None)
                    if not child:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    child = children[0]
            else:
                child = children[0]

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
        """Получить список справок. Опционально ?child_id= — по одному ребенку, иначе по всем детям родителя."""
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ запрещен'
                }, status=status.HTTP_403_FORBIDDEN)

            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child_ids = [c.id for c in children]
            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    if cid not in child_ids:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                    child_ids = [cid]
                except (ValueError, TypeError):
                    pass

            certificates = MedicalCertificate.objects.filter(
                child_id__in=child_ids
            ).select_related('child').order_by('-uploaded_at')

            certificates_data = []
            for cert in certificates:
                certificates_data.append({
                    'id': cert.id,
                    'child_id': cert.child_id,
                    'child_name': cert.child.full_name,
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

            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'Ребенок не найден'
                }, status=status.HTTP_404_NOT_FOUND)

            child_id_param = request.data.get('child_id')
            if child_id_param is not None:
                try:
                    cid = int(child_id_param)
                    child = next((c for c in children if c.id == cid), None)
                    if not child:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    child = children[0]
            else:
                child = children[0]

            # Валидация данных
            required_fields = ['date_from', 'date_to']
            for field in required_fields:
                if field not in request.data:
                    return Response({
                        'error': f'Поле {field} обязательно'
                    }, status=status.HTTP_400_BAD_REQUEST)

            date_from_str = request.data['date_from']
            date_to_str = request.data['date_to']
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                return Response({
                    'error': 'Некорректный формат даты. Используйте ГГГГ-ММ-ДД.'
                }, status=status.HTTP_400_BAD_REQUEST)

            if date_from > date_to:
                return Response({
                    'error': 'Дата окончания не может быть раньше даты начала болезни/отсутствия.'
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
                'date_from': date_from,
                'date_to': date_to,
                'note': request.data.get('note', ''),
                'absence_reason': request.data.get('absence_reason', '')
            }
            
            # Добавляем файл только если он загружен
            if 'certificate_file' in request.FILES:
                certificate_data['certificate_file'] = request.FILES['certificate_file']
            
            certificate = MedicalCertificate.objects.create(**certificate_data)

            return Response({
                'success': True,
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

            # Получаем все справки (parent_name — связь Child -> Parent для телефона)
            certificates = MedicalCertificate.objects.select_related(
                'child', 'child__parent_name', 'parent'
            ).order_by('-uploaded_at')

            certificates_data = []
            for cert in certificates:
                # Телефон родителя для связи (из модели Parent, привязанной к ребёнку)
                parent_phone = ''
                if cert.child.parent_name:
                    parent_phone = cert.child.parent_name.phone or ''

                # Проверка пересечения дат с другими справками/запросами по тому же ребёнку
                overlapping = MedicalCertificate.objects.filter(
                    child=cert.child
                ).exclude(
                    id=cert.id
                ).filter(
                    date_from__lte=cert.date_to,
                    date_to__gte=cert.date_from
                ).order_by('date_from')

                overlap_warning = overlapping.exists()
                overlap_message = ''
                if overlap_warning:
                    periods = [
                        f'{o.date_from.strftime("%d.%m.%Y")}–{o.date_to.strftime("%d.%m.%Y")}'
                        for o in overlapping[:5]
                    ]
                    overlap_message = (
                        'Даты пересекаются с другими справками/запросами по этому ребёнку (периоды: %s). '
                        'Уточните у родителя. Телефон для связи: %s.'
                    ) % (', '.join(periods), parent_phone or 'не указан')

                certificates_data.append({
                    'id': cert.id,
                    'child_name': cert.child.full_name,
                    'parent_name': cert.parent.username,
                    'parent_phone': parent_phone,
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
                    'file_name': cert.certificate_file.name.split('/')[-1] if cert.certificate_file else None,
                    'overlap_warning': overlap_warning,
                    'overlap_message': overlap_message,
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

    def delete(self, request, training_id):
        """Удалить тренировку"""
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

            # Сохраняем информацию о тренировке для уведомления
            training_info = {
                'group_name': training.group.name,
                'date': training.date.strftime('%d.%m.%Y'),
                'time': training.time.strftime('%H:%M'),
                'trainer_name': training.trainer.full_name
            }

            # Удаляем тренировку
            training.delete()

            # Создаем уведомление об удалении для тренера
            try:
                ScheduleChangeNotification.objects.create(
                    training=None,  # Тренировка уже удалена
                    notification_type='deleted',
                    message=f"Тренировка для группы {training_info['group_name']} на {training_info['date']} в {training_info['time']} была удалена администратором.",
                    created_by=user,
                    old_date=training.date,
                    old_time=training.time
                )
            except Exception as notification_error:
                print(f"Ошибка при создании уведомления об удалении: {notification_error}")

            # Создаем уведомление об отмене тренировки для тренера и родителей
            try:
                TrainingCancellationNotification.objects.create(
                    group=training.group,
                    cancelled_date=training.date,
                    cancelled_time=training.time,
                    reason="Тренировка отменена администратором",
                    created_by=user,
                    affects_payment=True
                )
            except Exception as cancellation_error:
                print(f"Ошибка при создании уведомления об отмене: {cancellation_error}")

            return Response({
                'message': 'Тренировка успешно удалена',
                'deleted_training': training_info
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Ошибка при удалении тренировки: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TrainingCancellationNotificationsApiView(APIView):
    """API для получения уведомлений об отмене тренировок"""
    
    def get(self, request):
        """Получить уведомления об отмене тренировок"""
        try:
            user = request.user
            
            if user.role == 'trainer':
                # Тренер видит уведомления для своих групп
                trainer = Trainer.objects.get(user=user)
                notifications = TrainingCancellationNotification.objects.filter(
                    group__trainer=trainer,
                    is_read_by_trainer=False
                ).order_by('-created_at')
                
                # Отмечаем как прочитанные
                notifications.update(is_read_by_trainer=True)
                
            elif user.role == 'parent':
                # Родитель видит уведомления для групп всех своих детей
                children = get_parent_children(user)
                group_ids = [c.group_id for c in children if c.group_id]
                notifications = TrainingCancellationNotification.objects.filter(
                    group_id__in=group_ids,
                    is_read_by_parents=False
                ).order_by('-created_at') if group_ids else []
                
                # Отмечаем как прочитанные
                notifications.update(is_read_by_parents=True)
                
            else:
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
            
            notifications_data = []
            for notification in notifications:
                notifications_data.append({
                    'id': notification.id,
                    'group_name': notification.group.name,
                    'cancelled_date': notification.cancelled_date.strftime('%d.%m.%Y'),
                    'cancelled_time': notification.cancelled_time.strftime('%H:%M'),
                    'reason': notification.reason,
                    'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
                    'affects_payment': notification.affects_payment
                })
            
            return Response({
                'notifications': notifications_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении уведомлений об отмене: {e}")
            return Response({
                'error': 'Ошибка при получении уведомлений'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAttendanceApiView(APIView):
    """API для получения данных о посещениях детей (для админа)"""
    
    def get(self, request):
        """Получить данные о посещениях детей"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем параметры фильтрации
            group_id = request.GET.get('group_id')
            child_id = request.GET.get('child_id')
            date_from = request.GET.get('date_from')
            date_to = request.GET.get('date_to')
            
            print(f"DEBUG: Фильтры посещаемости - group_id: {group_id}, child_id: {child_id}, date_from: {date_from}, date_to: {date_to}")
            
            # Базовый запрос для посещений
            attendances_query = Attendance.objects.select_related(
                'child', 'child__group'
            ).all()
            
            # Фильтрация по группе
            if group_id:
                attendances_query = attendances_query.filter(child__group_id=group_id)
            
            # Фильтрация по ребенку
            if child_id:
                attendances_query = attendances_query.filter(child_id=child_id)
            
            # Фильтрация по дате
            if date_from:
                attendances_query = attendances_query.filter(date__gte=date_from)
            if date_to:
                attendances_query = attendances_query.filter(date__lte=date_to)
            
            # Получаем посещения
            attendances = attendances_query.order_by('-date', 'child__full_name')
            
            # Группируем по детям
            children_data = {}
            for attendance in attendances:
                child = attendance.child
                if child.id not in children_data:
                    children_data[child.id] = {
                        'child_id': child.id,
                        'child_name': child.full_name,
                        'group_name': child.group.name,
                        'kindergarten_name': f"Детский сад №{child.group.kindergarten_number}",
                        'attendances': [],
                        'total_trainings': 0,
                        'attended_trainings': 0,
                        'missed_trainings': 0,
                        'confirmed_absences': 0,
                        'payment_amount': 0
                    }
                
                # Добавляем информацию о посещении
                attendance_info = {
                    'id': attendance.id,
                    'date': attendance.date.strftime('%d.%m.%Y'),
                    'time': '09:00',  # Время по умолчанию, так как в модели нет поля time
                    'attended': attendance.status,
                    'absence_reason': attendance.reason,
                    'attendance_id': attendance.id
                }
                children_data[child.id]['attendances'].append(attendance_info)
                children_data[child.id]['total_trainings'] += 1
                
                if attendance.status:
                    children_data[child.id]['attended_trainings'] += 1
                else:
                    children_data[child.id]['missed_trainings'] += 1
                    
                    # Проверяем, есть ли подтвержденная справка
                    if attendance.reason and MedicalCertificate.objects.filter(
                        child=child,
                        date_from__lte=attendance.date,
                        date_to__gte=attendance.date,
                        status='approved'
                    ).exists():
                        children_data[child.id]['confirmed_absences'] += 1
            
            # Рассчитываем оплату для каждого ребенка
            for child_id, child_data in children_data.items():
                # Получаем настройки оплаты для сада
                try:
                    # Извлекаем номер сада из названия
                    kindergarten_number = child_data['kindergarten_name'].replace('Детский сад №', '')
                    payment_settings = PaymentSettings.objects.filter(
                        kindergarten__kindergarten_number=kindergarten_number,
                        is_active=True
                    ).order_by('-updated_at').first()
                    
                    if payment_settings:
                        price_per_training = payment_settings.price_per_training
                    else:
                        price_per_training = 500.00  # Значение по умолчанию
                except Exception as e:
                    print(f"Ошибка при получении настроек оплаты: {e}")
                    price_per_training = 500.00  # Значение по умолчанию
                
                # Рассчитываем сумму к оплате
                billable_trainings = child_data['total_trainings'] - child_data['confirmed_absences']
                child_data['payment_amount'] = float(billable_trainings * price_per_training)
                child_data['price_per_training'] = float(price_per_training)
            
            return Response({
                'children': list(children_data.values())
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении данных о посещениях: {e}")
            return Response({
                'error': 'Ошибка при получении данных о посещениях'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminAttendanceTableApiView(APIView):
    """API для получения данных таблицы посещений (Excel формат)"""
    
    def get(self, request):
        """Получить данные для таблицы посещений за месяц"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем месяц в формате YYYY-MM
            month = request.GET.get('month')
            if not month:
                return Response({'error': 'Не указан месяц'}, status=status.HTTP_400_BAD_REQUEST)
            
            print(f"DEBUG: Загрузка таблицы посещений для месяца: {month}")
            
            # Парсим месяц
            try:
                year, month_num = month.split('-')
                year = int(year)
                month_num = int(month_num)
                
                # Проверка корректности месяца
                if month_num < 1 or month_num > 12:
                    return Response({'error': 'Некорректный номер месяца'}, status=status.HTTP_400_BAD_REQUEST)
                    
            except ValueError:
                return Response({'error': 'Неверный формат месяца'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем все группы
            groups = GroupKidGarden.objects.all()
            if not groups.exists():
                return Response({
                    'children': [],
                    'training_dates': []
                }, status=status.HTTP_200_OK)
            
            # Получаем все тренировки за месяц
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
            
            print(f"DEBUG: Период поиска: {start_date} - {end_date}")
            
            # Получаем расписание тренировок за месяц
            training_dates = []
            for group in groups:
                # Получаем расписание для группы
                group_schedule = TrainingSchedule.objects.filter(
                    group=group,
                    date__range=[start_date, end_date]
                ).order_by('date')
                
                for schedule in group_schedule:
                    if schedule.date not in training_dates:
                        training_dates.append(schedule.date)
            
            training_dates.sort()
            print(f"DEBUG: Найдено {len(training_dates)} дат тренировок: {training_dates}")
            
            # Получаем всех детей из всех групп
            children_data = {}
            total_children = 0
            for group in groups:
                children = Child.objects.filter(group=group).order_by('full_name')
                print(f"DEBUG: Группа {group.name} - {children.count()} детей")
                
                for child in children:
                    total_children += 1
                    # Получаем посещения ребенка за месяц
                    attendances = Attendance.objects.filter(
                        child=child,
                        date__range=[start_date, end_date]
                    ).order_by('date')
                    
                    # Формируем данные о посещениях
                    attendance_list = []
                    for attendance in attendances:
                        attendance_list.append({
                            'date': attendance.date.strftime('%Y-%m-%d'),
                            'attended': attendance.status,
                            'absence_reason': attendance.reason or ''
                        })
                    
                    children_data[child.id] = {
                        'child_id': child.id,
                        'child_name': child.full_name,
                        'birth_date': child.birth_date.strftime('%Y-%m-%d') if child.birth_date else None,
                        'group_name': group.name,
                        'group_number': group.kindergarten_number,
                        'attendances': attendance_list
                    }
            
            print(f"DEBUG: Всего детей: {total_children}, уникальных дат: {len(training_dates)}")
            
            return Response({
                'children': list(children_data.values()),
                'training_dates': [date.strftime('%Y-%m-%d') for date in training_dates]
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении таблицы посещений: {e}")
            return Response({
                'error': 'Ошибка при получении таблицы посещений'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminGroupChildrenApiView(APIView):
    """API для получения детей группы (для админа)"""
    
    def get(self, request):
        """Получить детей группы"""
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)
            
            group_id = request.GET.get('group_id')
            if not group_id:
                return Response({'error': 'Не указан ID группы'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Получаем детей группы
            children = Child.objects.filter(group_id=group_id).select_related('group')
            
            children_data = []
            for child in children:
                children_data.append({
                    'id': child.id,
                    'full_name': child.full_name,
                    'group_name': child.group.name,
                    'kindergarten_name': f"Детский сад №{child.group.kindergarten_number}"
                })
            
            return Response({
                'children': children_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении детей группы: {e}")
            return Response({
                'error': 'Ошибка при получении детей группы'
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
                # Родитель получает уведомления для групп всех своих детей (1 ребёнок или несколько)
                children = get_parent_children(user)
                if not children:
                    return Response({
                        'notifications': []
                    }, status=status.HTTP_200_OK)
                group_ids = [c.group_id for c in children if c.group_id]
                if not group_ids:
                    return Response({
                        'notifications': []
                    }, status=status.HTTP_200_OK)
                notifications = ScheduleChangeNotification.objects.filter(
                    training__group_id__in=group_ids
                ).order_by('-created_at')[:20]
                
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
                children = get_parent_children(user)
                if notification.training.group_id and any(c.group_id == notification.training.group_id for c in children):
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


class PaymentInvoicesApiView(APIView):
    """
    API для работы с счетами на оплату.
    
    GET: Получить счета для родителя
    """
    permission_classes = [IsAuthenticated]
    
    def format_month_ru(self, date_obj):
        """Форматирует дату в русском формате месяца и года."""
        months_ru = [
            'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
            'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
        ]
        return f"{months_ru[date_obj.month - 1]} {date_obj.year}"
    
    def get(self, request):
        try:
            user = request.user
            
            if user.role != 'parent':
                return Response({
                    'error': 'Доступ разрешен только родителям'
                }, status=status.HTTP_403_FORBIDDEN)
            
            children = get_parent_children(user)
            if not children:
                return Response({
                    'error': 'У пользователя нет привязанного ребенка'
                }, status=status.HTTP_404_NOT_FOUND)
            
            child_ids = [c.id for c in children]
            child_id_param = request.GET.get('child_id')
            if child_id_param:
                try:
                    cid = int(child_id_param)
                    if cid not in child_ids:
                        return Response({'error': 'Недопустимый child_id'}, status=status.HTTP_400_BAD_REQUEST)
                    child_ids = [cid]
                except (ValueError, TypeError):
                    pass
            
            invoices = PaymentInvoice.objects.filter(
                child_id__in=child_ids
            ).select_related('child').prefetch_related('receipts').order_by('-invoice_month')

            unpaid_statuses = ('pending', 'overdue')
            unpaid_invoices = [inv for inv in invoices if inv.status in unpaid_statuses]
            unpaid_months_count = len(unpaid_invoices)
            total_unpaid_amount = sum(float(inv.total_amount) for inv in unpaid_invoices)
            
            invoices_data = []
            for invoice in invoices:
                receipts = list(invoice.receipts.all())
                latest_receipt = receipts[0] if receipts else None
                rec_parsed = latest_receipt if latest_receipt else None
                inv_item = {
                    'id': invoice.id,
                    'child_id': invoice.child_id,
                    'child_name': invoice.child.full_name,
                    'invoice_month': invoice.invoice_month.strftime('%Y-%m-%d'),
                    'invoice_month_display': self.format_month_ru(invoice.invoice_month),
                    'total_trainings': invoice.total_trainings,
                    'confirmed_absences': invoice.confirmed_absences,
                    'billable_trainings': invoice.billable_trainings,
                    'price_per_training': float(invoice.price_per_training),
                    'total_amount': float(invoice.total_amount),
                    'status': invoice.status,
                    'status_display': invoice.get_status_display(),
                    'generated_at': invoice.generated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'due_date': invoice.due_date.strftime('%Y-%m-%d'),
                    'paid_at': invoice.paid_at.strftime('%Y-%m-%d %H:%M:%S') if invoice.paid_at else None,
                    'notes': invoice.notes,
                    'receipt_status': latest_receipt.status if latest_receipt else None,
                    'receipt_status_display': latest_receipt.get_status_display() if latest_receipt else None,
                }
                if rec_parsed and rec_parsed.parsed_amount is not None:
                    inv_item['receipt_parsed_amount'] = float(rec_parsed.parsed_amount)
                    inv_item['receipt_amount_match'] = rec_parsed.amount_match
                    inv_item['receipt_parsed_bank'] = rec_parsed.get_parsed_bank_display() if rec_parsed.parsed_bank else None
                invoices_data.append(inv_item)

            global_qr = GlobalPaymentQR.objects.first()
            global_qr_code_url = request.build_absolute_uri(global_qr.qr_code.url) if global_qr and global_qr.qr_code else None
            
            return Response({
                'invoices': invoices_data,
                'unpaid_months_count': unpaid_months_count,
                'total_unpaid_amount': round(total_unpaid_amount, 2),
                'global_qr_code_url': global_qr_code_url,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении счетов: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParentUploadPaymentReceiptApiView(APIView):
    """Родитель загружает чек по счёту для подтверждения оплаты."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            user = request.user
            if user.role != 'parent':
                return Response({'error': 'Доступ только для родителя'}, status=status.HTTP_403_FORBIDDEN)
            children = get_parent_children(user)
            if not children:
                return Response({'error': 'Ребенок не найден'}, status=status.HTTP_404_NOT_FOUND)
            invoice_id = request.data.get('invoice_id')
            if invoice_id is None:
                return Response({'error': 'Укажите invoice_id'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                invoice_id = int(invoice_id)
            except (ValueError, TypeError):
                return Response({'error': 'Некорректный invoice_id'}, status=status.HTTP_400_BAD_REQUEST)
            if 'receipt_file' not in request.FILES:
                return Response({'error': 'Прикрепите файл чека'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                invoice = PaymentInvoice.objects.get(id=invoice_id)
            except PaymentInvoice.DoesNotExist:
                return Response({'error': 'Счет не найден'}, status=status.HTTP_404_NOT_FOUND)
            if invoice.child_id not in [c.id for c in children]:
                return Response({'error': 'Нет доступа к этому счету'}, status=status.HTTP_403_FORBIDDEN)
            if invoice.status == 'paid':
                return Response({'error': 'Счет уже оплачен'}, status=status.HTTP_400_BAD_REQUEST)
            receipt = PaymentReceipt.objects.create(
                invoice=invoice,
                uploaded_by=user,
                receipt_file=request.FILES['receipt_file'],
                status='pending',
            )
            # Распознать данные с чека для проверки суммы
            try:
                from .receipt_parser import parse_receipt_file
                file_path = receipt.receipt_file.path
            except (ValueError, NotImplementedError):
                file_path = None
            if file_path:
                try:
                    parsed = parse_receipt_file(file_path, invoice.total_amount)
                    receipt.parsed_amount = parsed.get('parsed_amount')
                    receipt.parsed_date = parsed.get('parsed_date')
                    receipt.parsed_bank = parsed.get('parsed_bank')
                    receipt.amount_match = parsed.get('amount_match')
                    receipt.parsed_raw_preview = (parsed.get('raw_preview') or '')[:2000]
                    receipt.save(update_fields=['parsed_amount', 'parsed_date', 'parsed_bank', 'amount_match', 'parsed_raw_preview'])
                except Exception as e:
                    print(f"Ошибка парсинга чека: {e}")
            response_data = {
                'success': True,
                'message': 'Чек загружен и отправлен на проверку',
                'receipt_id': receipt.id,
                'status': receipt.status,
            }
            if receipt.parsed_amount is not None:
                response_data['parsed_amount'] = float(receipt.parsed_amount)
                response_data['invoice_amount'] = float(invoice.total_amount)
                response_data['amount_match'] = receipt.amount_match
                response_data['parsed_bank'] = receipt.get_parsed_bank_display() if receipt.parsed_bank else None
                response_data['parsed_date'] = receipt.parsed_date.strftime('%d.%m.%Y') if receipt.parsed_date else None
            return Response(response_data, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"Ошибка загрузки чека: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminPaymentReceiptsApiView(APIView):
    """Админ: список чеков на проверку, подтверждение и отклонение."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role != 'admin':
                return Response({'error': 'Доступ только для администратора'}, status=status.HTTP_403_FORBIDDEN)
            status_filter = request.GET.get('status', 'pending')
            receipts = PaymentReceipt.objects.filter(
                status=status_filter
            ).select_related('invoice', 'invoice__child', 'uploaded_by').order_by('-created_at')[:100]
            data = []
            for r in receipts:
                item = {
                    'id': r.id,
                    'invoice_id': r.invoice_id,
                    'child_name': r.invoice.child.full_name,
                    'invoice_month': r.invoice.invoice_month.strftime('%Y-%m'),
                    'total_amount': float(r.invoice.total_amount),
                    'uploaded_by': r.uploaded_by.username,
                    'created_at': r.created_at.strftime('%d.%m.%Y %H:%M'),
                    'status': r.status,
                    'receipt_url': request.build_absolute_uri(r.receipt_file.url) if r.receipt_file else None,
                    'admin_comment': r.admin_comment,
                }
                if r.parsed_amount is not None:
                    item['parsed_amount'] = float(r.parsed_amount)
                    item['amount_match'] = r.amount_match
                    item['parsed_bank'] = r.get_parsed_bank_display() if r.parsed_bank else None
                    item['parsed_date'] = r.parsed_date.strftime('%d.%m.%Y') if r.parsed_date else None
                    item['parsed_raw_preview'] = (r.parsed_raw_preview or '')[:500]
                data.append(item)
            return Response({'receipts': data}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка списка чеков: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """Подтвердить или отклонить чек. В теле: receipt_id, action: 'approve' | 'reject', admin_comment (опционально)."""
        try:
            if request.user.role != 'admin':
                return Response({'error': 'Доступ только для администратора'}, status=status.HTTP_403_FORBIDDEN)
            receipt_id = request.data.get('receipt_id')
            action = request.data.get('action')
            admin_comment = request.data.get('admin_comment', '')
            if not receipt_id or action not in ('approve', 'reject'):
                return Response({'error': 'Укажите receipt_id и action: approve или reject'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                receipt = PaymentReceipt.objects.select_related('invoice').get(id=receipt_id)
            except PaymentReceipt.DoesNotExist:
                return Response({'error': 'Чек не найден'}, status=status.HTTP_404_NOT_FOUND)
            if receipt.status != 'pending':
                return Response({'error': 'Чек уже обработан'}, status=status.HTTP_400_BAD_REQUEST)
            receipt.admin_comment = admin_comment
            receipt.reviewed_at = timezone.now()
            receipt.reviewed_by = request.user
            if action == 'approve':
                receipt.status = 'approved'
                receipt.save()
                invoice = receipt.invoice
                invoice.status = 'paid'
                invoice.paid_at = timezone.now()
                invoice.save(update_fields=['status', 'paid_at'])
                return Response({'success': True, 'message': 'Оплата подтверждена'}, status=status.HTTP_200_OK)
            else:
                receipt.status = 'rejected'
                receipt.save()
                return Response({'success': True, 'message': 'Чек отклонен'}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка обработки чека: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminOverdueInvoicesApiView(APIView):
    """
    API для администратора: список родителей с непогашенными счетами за несколько месяцев.
    GET: Родители (ребёнок + контакт), у которых 2 и более месяцев не оплачены счета.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if user.role != 'admin':
                return Response({'error': 'Доступ разрешен только администраторам'}, status=status.HTTP_403_FORBIDDEN)

            unpaid_statuses = ('pending', 'overdue')
            # Дети, у которых есть хотя бы один неоплаченный счёт
            children_with_unpaid = (
                PaymentInvoice.objects.filter(status__in=unpaid_statuses)
                .values_list('child_id', flat=True)
                .distinct()
            )
            result = []
            for child_id in children_with_unpaid:
                child = Child.objects.select_related('parent_name').get(id=child_id)
                unpaid = PaymentInvoice.objects.filter(
                    child=child, status__in=unpaid_statuses
                )
                count = unpaid.count()
                if count < 2:
                    continue
                total = sum(float(inv.total_amount) for inv in unpaid)
                parent_user = User.objects.filter(role='parent', linked_child=child).first()
                parent_phone = (child.parent_name.phone or '') if child.parent_name else ''
                result.append({
                    'child_id': child.id,
                    'child_name': child.full_name,
                    'parent_username': parent_user.username if parent_user else '',
                    'parent_phone': parent_phone,
                    'unpaid_months_count': count,
                    'total_unpaid_amount': round(total, 2),
                })
            return Response({'overdue_parents': result}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка при получении списка должников: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminInvoicesListApiView(APIView):
    """Список счетов для админа (для привязки QR)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role != 'admin':
                return Response({'error': 'Доступ только для администратора'}, status=status.HTTP_403_FORBIDDEN)
            status_filter = request.GET.get('status')  # pending, paid, overdue, пусто = все
            qs = PaymentInvoice.objects.select_related('child').order_by('-invoice_month', 'child__full_name')
            if status_filter:
                qs = qs.filter(status=status_filter)
            qs = qs[:200]
            months_ru = [
                'Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
                'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь'
            ]
            data = []
            for inv in qs:
                data.append({
                    'id': inv.id,
                    'child_name': inv.child.full_name,
                    'invoice_month': inv.invoice_month.strftime('%Y-%m'),
                    'invoice_month_display': f"{months_ru[inv.invoice_month.month - 1]} {inv.invoice_month.year}",
                    'total_amount': float(inv.total_amount),
                    'status': inv.status,
                    'status_display': inv.get_status_display(),
                    'has_qr': bool(inv.qr_code),
                    'qr_code_url': request.build_absolute_uri(inv.qr_code.url) if inv.qr_code else None,
                })
            return Response({'invoices': data}, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка списка счетов: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminInvoiceQRUploadApiView(APIView):
    """Загрузка QR-кода для счёта (админ)."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, invoice_id):
        try:
            if request.user.role != 'admin':
                return Response({'error': 'Доступ только для администратора'}, status=status.HTTP_403_FORBIDDEN)
            if 'qr_file' not in request.FILES and 'qr_code' not in request.FILES:
                return Response({'error': 'Прикрепите файл QR-кода (qr_file или qr_code)'}, status=status.HTTP_400_BAD_REQUEST)
            try:
                invoice = PaymentInvoice.objects.get(id=invoice_id)
            except PaymentInvoice.DoesNotExist:
                return Response({'error': 'Счет не найден'}, status=status.HTTP_404_NOT_FOUND)
            file_key = 'qr_file' if 'qr_file' in request.FILES else 'qr_code'
            invoice.qr_code = request.FILES[file_key]
            invoice.save(update_fields=['qr_code'])
            return Response({
                'success': True,
                'message': 'QR-код загружен',
                'qr_code_url': request.build_absolute_uri(invoice.qr_code.url),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка загрузки QR: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GlobalPaymentQRApiView(APIView):
    """Один общий QR для оплаты (для родителей и админа)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        global_qr = GlobalPaymentQR.objects.first()
        qr_code_url = None
        if global_qr and global_qr.qr_code:
            qr_code_url = request.build_absolute_uri(global_qr.qr_code.url)
        return Response({'qr_code_url': qr_code_url}, status=status.HTTP_200_OK)


class AdminGlobalPaymentQRUploadApiView(APIView):
    """Загрузка одного общего QR для оплаты (только админ)."""
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            if request.user.role != 'admin':
                return Response({'error': 'Доступ только для администратора'}, status=status.HTTP_403_FORBIDDEN)
            if 'qr_file' not in request.FILES and 'qr_code' not in request.FILES:
                return Response({'error': 'Прикрепите файл QR-кода (qr_file или qr_code)'}, status=status.HTTP_400_BAD_REQUEST)
            global_qr, _ = GlobalPaymentQR.objects.get_or_create(pk=1, defaults={})
            file_key = 'qr_file' if 'qr_file' in request.FILES else 'qr_code'
            global_qr.qr_code = request.FILES[file_key]
            global_qr.save(update_fields=['qr_code'])
            return Response({
                'success': True,
                'message': 'Общий QR-код загружен',
                'qr_code_url': request.build_absolute_uri(global_qr.qr_code.url),
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Ошибка загрузки общего QR: {e}")
            return Response({'error': 'Внутренняя ошибка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GenerateInvoiceApiView(APIView):
    """
    API для генерации счетов (только для админов).
    
    POST: Сгенерировать счета на следующий месяц
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ разрешен только администраторам'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Генерируем счета на следующий месяц
            target_month = PaymentService.get_next_month()
            created_invoices = PaymentService.generate_invoices_for_month(target_month)
            
            return Response({
                'message': f'Сгенерировано счетов: {len(created_invoices)}',
                'target_month': target_month.strftime('%B %Y'),
                'invoices_count': len(created_invoices)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при генерации счетов: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PaymentSettingsApiView(APIView):
    """
    API для работы с настройками оплаты (только для админов).
    
    GET: Получить настройки оплаты
    PUT: Обновить настройки оплаты
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ разрешен только администраторам'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Получаем все настройки оплаты
            settings = PaymentSettings.objects.all().select_related('kindergarten')
            
            settings_data = []
            for setting in settings:
                settings_data.append({
                    'id': setting.id,
                    'kindergarten': {
                        'id': setting.kindergarten.id,
                        'name': setting.kindergarten.name,
                        'kindergarten_number': setting.kindergarten.kindergarten_number
                    },
                    'price_per_training': float(setting.price_per_training),
                    'default_trainings_per_month': setting.default_trainings_per_month,
                    'invoice_generation_day': setting.invoice_generation_day,
                    'is_active': setting.is_active,
                    'created_at': setting.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'updated_at': setting.updated_at.strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return Response({
                'settings': settings_data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при получении настроек оплаты: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def put(self, request):
        try:
            user = request.user
            
            if user.role != 'admin':
                return Response({
                    'error': 'Доступ разрешен только администраторам'
                }, status=status.HTTP_403_FORBIDDEN)
            
            setting_id = request.data.get('id')
            if not setting_id:
                return Response({
                    'error': 'ID настройки обязателен'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                setting = PaymentSettings.objects.get(id=setting_id)
            except PaymentSettings.DoesNotExist:
                return Response({
                    'error': 'Настройка не найдена'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Обновляем поля
            if 'price_per_training' in request.data:
                setting.price_per_training = request.data['price_per_training']
            
            if 'default_trainings_per_month' in request.data:
                setting.default_trainings_per_month = request.data['default_trainings_per_month']
            
            if 'invoice_generation_day' in request.data:
                setting.invoice_generation_day = request.data['invoice_generation_day']
            
            if 'is_active' in request.data:
                setting.is_active = request.data['is_active']
            
            setting.save()
            
            return Response({
                'message': 'Настройки обновлены',
                'setting': {
                    'id': setting.id,
                    'price_per_training': float(setting.price_per_training),
                    'default_trainings_per_month': setting.default_trainings_per_month,
                    'invoice_generation_day': setting.invoice_generation_day,
                    'is_active': setting.is_active
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(f"Ошибка при обновлении настроек оплаты: {e}")
            return Response({
                'error': 'Внутренняя ошибка сервера'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)