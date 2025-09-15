#!/usr/bin/env python
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import User

# Создаем администратора
try:
    admin_user = User.objects.create(
        username='admin', 
        password='admin123', 
        role='admin'
    )
    print(f'✅ Создан администратор: {admin_user.username}')
    print(f'   Пароль: admin123')
    print(f'   Роль: {admin_user.role}')
except Exception as e:
    if 'UNIQUE constraint failed' in str(e):
        print('⚠️  Администратор уже существует')
    else:
        print(f'❌ Ошибка создания администратора: {e}')
