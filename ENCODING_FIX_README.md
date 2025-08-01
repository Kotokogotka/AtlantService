# Исправление ошибок кодировки Unicode

## Проблема
Ошибка `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 in position 61: invalid continuation byte` возникает при проблемах с кодировкой данных.

## Реализованные исправления

### 1. Обновленные настройки Django (`core/core/settings.py`)

#### Переменные окружения
Добавлена поддержка переменных окружения для безопасности:
```python
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
```

#### Улучшенные настройки базы данных
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'OPTIONS': {
            'charset': 'utf8',
            'client_encoding': 'UTF8',
            'default_transaction_isolation': 'read committed',
            'timezone': 'Europe/Moscow',
        },
    }
}
```

#### Настройки локализации
```python
LANGUAGE_CODE = 'ru-ru'
TIME_ZONE = 'Europe/Moscow'
os.environ.setdefault('LANG', 'ru_RU.UTF-8')
os.environ.setdefault('LC_ALL', 'ru_RU.UTF-8')
```

### 2. Утилиты для работы с кодировкой (`core/fotball/utils.py`)

Созданы функции для безопасной работы с кодировками:
- `safe_decode()` - безопасное декодирование с автоопределением кодировки
- `safe_encode()` - безопасное кодирование текста
- `read_file_safe()` - безопасное чтение файлов
- `normalize_text()` - нормализация Unicode текста
- `fix_mojibake()` - исправление неправильно декодированного текста

### 3. Middleware для обработки кодировки (`core/fotball/middleware.py`)

Созданы два middleware:
- `EncodingFixMiddleware` - исправляет кодировку в запросах/ответах
- `UnicodeErrorHandlingMiddleware` - глобальная обработка ошибок Unicode

### 4. Обновленные зависимости (`requirements.txt`)

Добавлена библиотека `chardet==5.2.0` для автоматического определения кодировки.

## Инструкции по применению

### Шаг 1: Создать файл .env
```bash
cp .env.example .env
```

Отредактировать `.env` файл с вашими настройками:
```env
SECRET_KEY=your-very-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
DB_NAME=fotball_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
LANG=ru_RU.UTF-8
LC_ALL=ru_RU.UTF-8
PYTHONIOENCODING=utf-8
```

### Шаг 2: Установить зависимости
```bash
pip install -r requirements.txt
```

### Шаг 3: Настроить PostgreSQL
Убедитесь, что PostgreSQL настроен для UTF-8:

```sql
-- Проверить кодировку базы данных
SELECT datname, datcollate, datctype FROM pg_database WHERE datname = 'fotball_db';

-- Создать базу с правильной кодировкой (если нужно)
CREATE DATABASE fotball_db 
WITH ENCODING 'UTF8' 
LC_COLLATE='ru_RU.UTF-8' 
LC_CTYPE='ru_RU.UTF-8' 
TEMPLATE=template0;
```

### Шаг 4: Настроить системную локаль
На Ubuntu/Debian:
```bash
# Установить русскую локаль
sudo apt-get install language-pack-ru

# Сгенерировать локаль
sudo locale-gen ru_RU.UTF-8

# Обновить локаль
sudo dpkg-reconfigure locales

# Экспортировать переменные окружения
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8
export PYTHONIOENCODING=utf-8
```

### Шаг 5: Запустить миграции
```bash
python manage.py makemigrations
python manage.py migrate
```

## Диагностика проблем

### Проверка кодировки файлов
```python
import chardet

def check_file_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        print(f"{file_path}: {result}")

# Проверить кодировку важных файлов
check_file_encoding('core/fotball/models.py')
check_file_encoding('core/fotball/views.py')
```

### Проверка подключения к базе данных
```python
from django.db import connection

def check_db_encoding():
    with connection.cursor() as cursor:
        cursor.execute("SHOW client_encoding;")
        encoding = cursor.fetchone()[0]
        print(f"Database client encoding: {encoding}")
        
        cursor.execute("SHOW server_encoding;")
        encoding = cursor.fetchone()[0]
        print(f"Database server encoding: {encoding}")
```

### Тестирование Unicode
```python
def test_unicode_handling():
    test_strings = [
        "Привет мир!",
        "Тест с эмодзи: 🚀⚽",
        "Special chars: ñáéíóú",
        "Кириллица: абвгдеёжз"
    ]
    
    for test_str in test_strings:
        try:
            # Тест кодирования/декодирования
            encoded = test_str.encode('utf-8')
            decoded = encoded.decode('utf-8')
            assert test_str == decoded
            print(f"✓ {test_str}")
        except Exception as e:
            print(f"✗ {test_str}: {e}")
```

## Частые проблемы и решения

### 1. Ошибка при подключении к PostgreSQL
**Проблема**: `UnicodeDecodeError` при подключении к базе
**Решение**: Проверить настройки PostgreSQL и убедиться, что база создана с кодировкой UTF-8

### 2. Ошибки в POST запросах
**Проблема**: Ошибки при обработке русского текста в JSON
**Решение**: Убедиться, что клиент отправляет данные в UTF-8 и добавлен заголовок `Content-Type: application/json; charset=utf-8`

### 3. Проблемы с миграциями
**Проблема**: Ошибки при создании таблиц с русскими комментариями
**Решение**: Убедиться, что PostgreSQL настроен правильно и использовать environment variables

### 4. Файлы с неправильной кодировкой
**Проблема**: Файлы проекта в неправильной кодировке
**Решение**: Конвертировать файлы в UTF-8:
```bash
# Проверить кодировку файла
file -bi filename.py

# Конвертировать в UTF-8
iconv -f windows-1251 -t utf-8 filename.py > filename_utf8.py
```

## Мониторинг

Добавить логирование для отслеживания проблем с кодировкой:

```python
import logging

# В settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'encoding_file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'encoding_errors.log',
        },
    },
    'loggers': {
        'fotball.middleware': {
            'handlers': ['encoding_file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}
```

## Поддержка

При возникновении проблем:
1. Проверить логи в `encoding_errors.log`
2. Использовать утилиты из `fotball/utils.py` для диагностики
3. Проверить настройки базы данных и системной локали