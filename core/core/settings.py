"""
Django settings for core project.

Секреты и настройки окружения берутся из переменных окружения и файла .env в корне проекта.
"""

import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Корень репозитория (родитель core/) — для билда фронта и .env
REPO_ROOT = BASE_DIR.parent
FRONTEND_BUILD_DIR = REPO_ROOT / 'front_football' / 'build'

# Загружаем .env из корня проекта (рядом с front_football и core)
load_dotenv(REPO_ROOT / '.env')


def env(key, default=None):
    """Читает переменную окружения (после load_dotenv)."""
    return os.environ.get(key, default)


def env_bool(key, default=False):
    val = env(key)
    if val is None:
        return default
    return str(val).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=None):
    val = env(key)
    if val is None or val.strip() == '':
        return default or []
    return [s.strip() for s in val.split(',') if s.strip()]


# Quick-start development settings - unsuitable for production
# SECURITY: на хостинге задайте SECRET_KEY в .env (длинная случайная строка)
SECRET_KEY = env('SECRET_KEY', 'django-insecure-dev-key-change-in-production')

# На хостинге установите DEBUG=0 или DEBUG=false
DEBUG = env_bool('DEBUG', True)

# На хостинге укажите через запятую: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS = env_list('ALLOWED_HOSTS', ['localhost', '127.0.0.1', ''])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'fotball.apps.FotballConfig',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'core.urls'

# CORS: на хостинге укажите через запятую, например CORS_ALLOWED_ORIGINS=https://yourdomain.com
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', True)
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS') or [
    "http://localhost:3000",
    "http://localhost:8000",
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'test': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    },
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'fotball.authentication.CustomJWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True, # При обновлении создается новый токен
    'BLACKLIST_AFTER_ROTATION': True, # Старые токены блокируются при истечении срока жизни
    'UPDATE_LAST_LOGIN': False, # Не обновляет время последнего входа
    'ALGORITHM': 'HS256', # Алгоритм шифрования
    'SIGNING_KEY': SECRET_KEY, # Ключ для шифрования
    'AUTH_HEADER_TYPES': ('Bearer',), # Типы заголовков авторизации
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}


AUTHENTICATION_BACKENDS = [
    'fotball.authentication.CustomUserBackend', # Кастомный бэкенд для работы с моделью User
    'django.contrib.auth.backends.ModelBackend', # Стандартный бэкенд для работы с моделью User
]

# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'ru'

LANGUAGES = [
    ('ru', 'Русский'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Media files (uploads). На хостинге можно задать MEDIA_ROOT в .env при необходимости
MEDIA_URL = env('MEDIA_URL', '/media/')
MEDIA_ROOT = Path(env('MEDIA_ROOT', str(BASE_DIR / 'media')))

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройки для тестов
import sys
if 'test' in sys.argv:
    DATABASES['default'] = DATABASES['test']
