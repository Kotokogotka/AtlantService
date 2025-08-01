# 🚨 Быстрое исправление ошибки UnicodeDecodeError

## Проблема
```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xc2 in position 61: invalid continuation byte
```

## ⚡ Быстрые шаги исправления

### 1. Создать .env файл
```bash
cp .env.example .env
```

Отредактировать `.env`:
```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
LANG=ru_RU.UTF-8
LC_ALL=ru_RU.UTF-8
PYTHONIOENCODING=utf-8
```

### 2. Установить зависимости
```bash
pip install chardet==5.2.0
# или
pip install -r requirements.txt
```

### 3. Настроить переменные окружения
```bash
export LANG=ru_RU.UTF-8
export LC_ALL=ru_RU.UTF-8
export PYTHONIOENCODING=utf-8
```

### 4. Перезапустить приложение
```bash
python manage.py runserver
```

### 5. Проверить исправление
```bash
python check_encoding.py
```

## 🔧 Если проблема остается

### PostgreSQL база данных
```sql
-- Проверить кодировку базы
SELECT datname, datcollate, datctype FROM pg_database WHERE datname = 'fotball_db';

-- Создать заново с правильной кодировкой
DROP DATABASE IF EXISTS fotball_db;
CREATE DATABASE fotball_db 
WITH ENCODING 'UTF8' 
LC_COLLATE='ru_RU.UTF-8' 
LC_CTYPE='ru_RU.UTF-8' 
TEMPLATE=template0;
```

### Системная локаль (Ubuntu/Debian)
```bash
sudo apt-get install language-pack-ru
sudo locale-gen ru_RU.UTF-8
sudo dpkg-reconfigure locales
```

## 📋 Что было исправлено

✅ Добавлены middleware для обработки Unicode ошибок  
✅ Настроены переменные окружения  
✅ Улучшены настройки PostgreSQL  
✅ Добавлены утилиты для безопасной работы с кодировками  
✅ Создан скрипт диагностики  
✅ Добавлено логирование ошибок кодировки  

## 🆘 Если ничего не помогает

1. Проверить логи: `logs/encoding_errors.log`
2. Запустить диагностику: `python check_encoding.py`
3. Проверить кодировку файлов проекта
4. Обратиться к полной инструкции в `ENCODING_FIX_README.md`