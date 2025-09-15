#!/usr/bin/env python
import os
import sys
import django
from django.core.files import File

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import MedicalCertificate, User, Child

# Создаем тестовую справку с файлом
try:
    parent = User.objects.get(username='Parenttest')
    child = parent.linked_child
    
    if child:
        # Создаем справку
        cert = MedicalCertificate.objects.create(
            child=child,
            parent=parent,
            date_from='2025-09-01',
            date_to='2025-09-03',
            note='Ребенок болел ОРВИ',
            absence_reason='',
            status='pending'
        )
        
        # Прикрепляем файл
        test_file_path = os.path.join(os.path.dirname(__file__), 'test_certificate.txt')
        if os.path.exists(test_file_path):
            with open(test_file_path, 'rb') as f:
                cert.certificate_file.save('test_certificate.txt', File(f), save=True)
        
        print(f'✅ Создана тестовая справка с файлом ID: {cert.id}')
        print(f'   Ребенок: {child.full_name}')
        print(f'   Период: {cert.date_from} - {cert.date_to}')
        print(f'   Статус: {cert.status}')
        print(f'   Файл: {cert.certificate_file.name if cert.certificate_file else "Нет файла"}')
        print(f'   URL файла: {cert.certificate_file.url if cert.certificate_file else "Нет URL"}')
    else:
        print('❌ У родителя нет привязанного ребенка')
        
except User.DoesNotExist:
    print('❌ Родитель Parenttest не найден')
except Exception as e:
    print(f'❌ Ошибка создания справки: {e}')
