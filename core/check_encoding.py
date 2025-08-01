#!/usr/bin/env python3
"""
Скрипт для диагностики проблем с кодировкой в проекте AtlantService
"""
import os
import sys
import django
from pathlib import Path

# Добавляем путь к проекту
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
import chardet
import locale


def check_system_encoding():
    """Проверка системной кодировки"""
    print("=== Проверка системной кодировки ===")
    print(f"System encoding: {sys.getdefaultencoding()}")
    print(f"File system encoding: {sys.getfilesystemencoding()}")
    print(f"Current locale: {locale.getlocale()}")
    
    # Проверка переменных окружения
    env_vars = ['LANG', 'LC_ALL', 'PYTHONIOENCODING']
    for var in env_vars:
        value = os.environ.get(var, 'Not set')
        print(f"{var}: {value}")
    print()


def check_database_encoding():
    """Проверка кодировки базы данных"""
    print("=== Проверка кодировки базы данных ===")
    try:
        with connection.cursor() as cursor:
            # PostgreSQL
            cursor.execute("SELECT current_setting('server_encoding');")
            server_encoding = cursor.fetchone()[0]
            print(f"Database server encoding: {server_encoding}")
            
            cursor.execute("SELECT current_setting('client_encoding');")
            client_encoding = cursor.fetchone()[0]
            print(f"Database client encoding: {client_encoding}")
            
            cursor.execute("SHOW LC_COLLATE;")
            lc_collate = cursor.fetchone()[0]
            print(f"Database LC_COLLATE: {lc_collate}")
            
            cursor.execute("SHOW LC_CTYPE;")
            lc_ctype = cursor.fetchone()[0]
            print(f"Database LC_CTYPE: {lc_ctype}")
            
    except Exception as e:
        print(f"Error checking database encoding: {e}")
    print()


def check_file_encodings():
    """Проверка кодировки файлов проекта"""
    print("=== Проверка кодировки файлов ===")
    
    files_to_check = [
        'fotball/models.py',
        'fotball/views.py',
        'fotball/utils.py',
        'fotball/middleware.py',
        'core/settings.py',
    ]
    
    for file_path in files_to_check:
        full_path = BASE_DIR / file_path
        if full_path.exists():
            try:
                with open(full_path, 'rb') as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    confidence = result.get('confidence', 0)
                    encoding = result.get('encoding', 'unknown')
                    
                    status = "✓" if encoding.lower() in ['utf-8', 'ascii'] and confidence > 0.8 else "⚠"
                    print(f"{status} {file_path}: {encoding} (confidence: {confidence:.2f})")
                    
            except Exception as e:
                print(f"✗ {file_path}: Error reading file - {e}")
        else:
            print(f"✗ {file_path}: File not found")
    print()


def test_unicode_operations():
    """Тестирование операций с Unicode"""
    print("=== Тестирование Unicode операций ===")
    
    test_strings = [
        "Привет мир!",
        "Тест с эмодзи: 🚀⚽",
        "Кириллица: абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
        "КИРИЛЛИЦА: АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
        "Mixed: Hello Привет 123 🌟",
    ]
    
    for test_str in test_strings:
        try:
            # Тест кодирования/декодирования
            encoded = test_str.encode('utf-8')
            decoded = encoded.decode('utf-8')
            
            if test_str == decoded:
                print(f"✓ {test_str[:30]}...")
            else:
                print(f"✗ {test_str[:30]}... (encoding mismatch)")
                
        except Exception as e:
            print(f"✗ {test_str[:30]}...: {e}")
    print()


def test_database_unicode():
    """Тестирование Unicode в базе данных"""
    print("=== Тестирование Unicode в базе данных ===")
    
    try:
        from fotball.models import User
        
        # Создание тестового пользователя с русскими символами
        test_username = "тест_пользователь_🚀"
        
        # Проверяем, существует ли уже такой пользователь
        existing_user = User.objects.filter(username=test_username).first()
        if existing_user:
            existing_user.delete()
        
        # Создаем нового пользователя
        user = User.objects.create(
            username=test_username,
            password="тест_пароль_123",
            role="admin"
        )
        
        # Читаем из базы
        retrieved_user = User.objects.get(id=user.id)
        
        if retrieved_user.username == test_username:
            print("✓ Database Unicode support working correctly")
        else:
            print(f"✗ Database Unicode issue: expected '{test_username}', got '{retrieved_user.username}'")
        
        # Удаляем тестового пользователя
        user.delete()
        
    except Exception as e:
        print(f"✗ Database Unicode test failed: {e}")
    print()


def check_django_settings():
    """Проверка настроек Django"""
    print("=== Проверка настроек Django ===")
    
    from django.conf import settings
    
    important_settings = [
        ('LANGUAGE_CODE', 'ru-ru'),
        ('TIME_ZONE', 'Europe/Moscow'),
        ('USE_I18N', True),
        ('USE_TZ', True),
        ('DEFAULT_CHARSET', 'utf-8'),
    ]
    
    for setting_name, expected in important_settings:
        actual = getattr(settings, setting_name, None)
        status = "✓" if actual == expected else "⚠"
        print(f"{status} {setting_name}: {actual} (expected: {expected})")
    
    # Проверка middleware
    middleware = getattr(settings, 'MIDDLEWARE', [])
    encoding_middleware = [
        'fotball.middleware.UnicodeErrorHandlingMiddleware',
        'fotball.middleware.EncodingFixMiddleware'
    ]
    
    for mw in encoding_middleware:
        status = "✓" if mw in middleware else "✗"
        print(f"{status} Middleware {mw}: {'Installed' if mw in middleware else 'Missing'}")
    
    print()


def main():
    """Основная функция диагностики"""
    print("AtlantService - Диагностика кодировки Unicode")
    print("=" * 50)
    
    try:
        check_system_encoding()
        check_database_encoding()
        check_file_encodings()
        test_unicode_operations()
        test_database_unicode()
        check_django_settings()
        
        print("=== Рекомендации ===")
        print("1. Убедитесь, что все файлы сохранены в UTF-8")
        print("2. Настройте переменные окружения: LANG=ru_RU.UTF-8, LC_ALL=ru_RU.UTF-8")
        print("3. Убедитесь, что PostgreSQL создан с кодировкой UTF-8")
        print("4. Используйте .env файл для безопасного хранения настроек")
        print("5. Установите зависимости: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"Ошибка при диагностике: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()