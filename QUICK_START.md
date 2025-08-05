# Быстрый старт системы AtlantService

## Запуск системы

### 1. Запуск бэкенда (Django)

```bash
# Переходим в папку core
cd core

# Активируем виртуальное окружение (если еще не активировано)
# Windows:
myenv\Scripts\activate
# Linux/Mac:
# source myenv/bin/activate

# Создаем тестовые данные
python manage.py create_test_data

# Запускаем сервер
python manage.py runserver
```

### 2. Запуск фронтенда (React)

```bash
# В новом терминале переходим в папку front_football
cd front_football

# Устанавливаем зависимости (если еще не установлены)
npm install

# Запускаем React приложение
npm start
```

## Тестовые учетные данные

### Тренеры:
- **Логин:** `trainer1` | **Пароль:** `password123`
- **Логин:** `trainer2` | **Пароль:** `password123`

### Администратор:
- **Логин:** `admin` | **Пароль:** `admin123`

### Родители:
- **Логин:** `parent1` | **Пароль:** `password123`
- **Логин:** `parent2` | **Пароль:** `password123`

## Функциональность

### Для тренеров:
1. **Просмотр групп** - просмотр всех групп, которые ведет тренер
2. **Отметка посещаемости** - отметка детей на тренировках с выбором даты

### Особенности:
- Показываются только активные дети (не в архиве)
- Отображается количество посещенных занятий в текущем месяце
- Показывается телефон родителя
- Интуитивный интерфейс с навигацией между функциями

## Структура проекта

```
AtlantService/
├── core/                 # Django бэкенд
│   ├── fotball/         # Основное приложение
│   │   ├── models.py    # Модели данных
│   │   ├── views.py     # API endpoints
│   │   └── urls.py      # URL маршруты
│   └── manage.py        # Django management
├── front_football/       # React фронтенд
│   ├── src/
│   │   ├── components/  # React компоненты
│   │   └── utils/       # API утилиты
│   └── package.json
└── requirements.txt     # Python зависимости
```

## API Endpoints

- `POST /api/login/` - авторизация
- `GET /api/trainer/groups/` - группы тренера
- `GET /api/trainer/group/{id}/` - детали группы
- `GET /api/trainer/attendance/` - данные для посещаемости
- `POST /api/trainer/attendance/` - создание посещаемости
- `GET /api/trainer/attendance/group/{id}/` - дети группы для посещаемости

## Технологии

- **Backend:** Django 5.2, Django REST Framework, PostgreSQL
- **Frontend:** React 18, CSS Modules, Axios
- **Authentication:** JWT (JSON Web Tokens)
- **Database:** PostgreSQL 