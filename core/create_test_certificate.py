#!/usr/bin/env python
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import MedicalCertificate, User, Child

# Создаем тестовую справку
try:
    parent = User.objects.get(username='Parent')
    child = parent.linked_child
    
    if child:
        cert = MedicalCertificate.objects.create(
            child=child,
            parent=parent,
            date_from='2025-09-01',
            date_to='2025-09-03',
            note='Ребенок болел ОРВИ',
            absence_reason='',
            status='pending'
        )
        print(f'✅ Создана тестовая справка ID: {cert.id}')
        print(f'   Ребенок: {child.full_name}')
        print(f'   Период: {cert.date_from} - {cert.date_to}')
        print(f'   Статус: {cert.status}')
    else:
        print('❌ У родителя нет привязанного ребенка')
        
except User.DoesNotExist:
    print('❌ Родитель Parenttest не найден')
except Exception as e:
    print(f'❌ Ошибка создания справки: {e}')
