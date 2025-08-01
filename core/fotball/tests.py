from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password
import json

from rest_framework.test import APIClient, APITestCase
from rest_framework import status

from .models import User, Trainer, TrainingRate, Attendance, GroupKidGarden, Child
from .views import LoginApiView


class LoginApiViewTest(TestCase):
    """
    Тесты для LoginApiView

    Тестируем различные сценарии аутентификации пользователей:
    - Успешная аутентификация
    - Неверные учетные данные
    - Ошибки валидации
    """

    def setUp(self):
        """
        Настройка тестовых данных перед каждым тестом
        """
        self.client = APIClient()
        self.login_url = reverse('api-login')

        # Создание пользователей с разными ролями
        self.admin_user = User.objects.create(
            username='admin_test',
            password=make_password('admin123'),
            role='admin'
        )

        self.trainer_user = User.objects.create(
            username='trainer_test',
            password=make_password('trainer123'),
            role='trainer'
        )

        self.parent_user = User.objects.create(
            username='parent_test',
            password=make_password('parent123'),
            role='parent'
        )

    def tearDown(self):
        """
        Очистка тестовых данных после каждого теста
        Приведение БД в исходное состояние
        """
        # Удаление всех созданных пользователей
        User.objects.all().delete()

        # Удаление всех созданных тренеров
        Trainer.objects.all().delete()

        # Удаление всех созданных групп
        GroupKidGarden.objects.all().delete()

        # Удаление всех созданных детей
        Child.objects.all().delete()

        # Проверка, что БД очищена
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(Trainer.objects.count(), 0)
        self.assertEqual(GroupKidGarden.objects.count(), 0)
        self.assertEqual(Child.objects.count(), 0)


    def test_successful_login_admin(self):
        """
        Тест 1: Успешная аутентификация администратора
        """

        data = {
            'username': 'admin_test',
            'password': 'admin123'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user_id', response.data)
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'], 'admin_test')
        self.assertEqual(response.data['role'], 'admin')
        

    def test_successful_login_trainer(self):
        """
        Тест 2: Успешная аутентификация тренера
        """
        data = {
            'username': 'trainer_test',
            'password': 'trainer123'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'trainer_test')
        self.assertEqual(response.data['role'], 'trainer')

    
    def test_successful_login_parent(self):
        """
        Тест 3: Успешная аутентификация родителя
        """
        data = {
            'username': 'parent_test',
            'password': 'parent123'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'parent_test')
        self.assertEqual(response.data['role'], 'parent')


    def test_invalid_username(self):
        """
        Тест 4: Неверное имя пользователя
        """
        data = {
            'username': 'invalid_user',
            'password': 'anypassword'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Неверный логин или пароль')

    
    def test_invalid_password(self):
        """
        Тест 5: Неверный пароль
        """

        data = {
            'username': 'admin_test',
            'password': 'invalid_password'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'Неверный логин или пароль')

    
    def test_missing_username(self):
        """
        Тест 6: Отсутствие username
        """

        data = {
            'password': 'any_password'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)


    def test_missing_password(self):
        """
        Тест 7: Отсутствие password
        """

        data = {
            'username': 'admin_test'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)


    def test_empty_data(self):
        """
        Тест 8: Отсутствие данных
        """

        data = {
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    
    def test_response_structure(self):
        """
        Тест 9: Проверка структуры ответа JSON
        """
        
        data = {
            'username': 'admin_test',
            'password': 'admin123'
        }

        response = self.client.post(self.login_url, data, format='json')

        # Проверка всех полей
        expected_fields = ['user_id', 'username', 'role']
        for field in expected_fields:
            self.assertIn(field, response.data)

        
        # Проверка типа данных
        self.assertIsInstance(response.data['user_id'], int)
        self.assertIsInstance(response.data['username'], str)
        self.assertIsInstance(response.data['role'], str)

        # Проверка, что user_id соответсвует ID пользователя из БД
        user = User.objects.get(username='admin_test')
        self.assertEqual(response.data['user_id'], user.id)


    def test_user_with_linked_trainer(self):
        """
        Тест 10: Пользователь с привязанным тренером
        """

        # Создание тестового тренера
        trainer = Trainer.objects.create(
            full_name='Test trainer',
            phone='+79992345465',
            work_space="Детский сад 8"
        ) 


        # Создание пользователя с привязанным тренером
        user_with_linked_trainer = User.objects.create(
            username='user_with_trainer',
            password=make_password('password123'),
            role='parent',
            linked_trainer=trainer
        )

        # Проверяем что пользователь создан в БД с привязкой к тренеру
        user = User.objects.get(username='user_with_trainer')
        self.assertEqual(user.linked_trainer, trainer)

        # Тест аутентификации
        
        data = {
            'username': 'user_with_trainer',
            'password': 'password123'
        }

        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user_with_trainer')
        self.assertEqual(response.data['role'], 'parent')


    def test_user_linked_child(self):
        """
        Тест 11: Создание пользователя(родителя) имеющий ппривязку к ребенку
        """

        # Создание тренера
        trainer = Trainer.objects.create(
            full_name = "Test Trainer",
            phone = '+79992341234',
            work_space = 'Детский сад 8, группа 8'
        )

        # Создание группы в детском саду
        group = GroupKidGarden.objects.create(
            name='группа 8',
            kindergarten_number='Детский сад 8',
            age_level='M',
            trainer=trainer
        )

        # Создаем ребенка
        child = Child.objects.create(
            full_name="Тестовый ребенок",
            birth_date='2020-01-01',
            parent_name='тестовый родитель',
            phone_number='+79882345678',
            group=group,
            is_active=True
        )

        # Создаем пользователя с привязанным ребенком
        user_with_child = User.objects.create(
            username='user_with_child',
            password=make_password('password123'),
            role='parent',
            linked_child=child
        )
        
        # Проверяем, что пользователь создан с привязкой к ребенку
        user_from_db = User.objects.get(username='user_with_child')
        self.assertEqual(user_from_db.linked_child, child)
            
        # Тестируем аутентификацию
        data = {
            'username': 'user_with_child',
            'password': 'password123'
        }
            
        response = self.client.post(self.login_url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'user_with_child')
        self.assertEqual(response.data['role'], 'parent')