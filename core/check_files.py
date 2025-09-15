#!/usr/bin/env python
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from fotball.models import MedicalCertificate

# Проверяем существующие справки
try:
    certificates = MedicalCertificate.objects.all()
    print(f'Найдено справок: {certificates.count()}')
    
    for cert in certificates:
        print(f'\nСправка ID: {cert.id}')
        print(f'  Ребенок: {cert.child.full_name}')
        print(f'  Статус: {cert.status}')
        if cert.certificate_file:
            print(f'  Файл: {cert.certificate_file.name}')
            print(f'  URL: {cert.certificate_file.url}')
            print(f'  Путь: {cert.certificate_file.path}')
            print(f'  Существует: {os.path.exists(cert.certificate_file.path)}')
        else:
            print('  Файл: Нет файла')
            
except Exception as e:
    print(f'Ошибка: {e}')
