# Система управления футбольными группами

Система для управления группами детского футбола с ролями: администратор, тренер, родитель.

## Быстрый старт

### 1. Запуск бэкенда (Django)

```bash
cd core
python manage.py migrate
python manage.py create_test_data
python manage.py runserver
```

### 2. Запуск фронтенда (React)

```bash
cd front_football
npm install
npm start
```

### 3. Тестовые учетные записи

После создания тестовых данных доступны:

- **Тренер 1:** `trainer1` / `password123`
- **Тренер 2:** `trainer2` / `password123`

## Функциональность

### Для тренера:
- **Просмотр групп** - просмотр всех групп, которые ведет тренер
- **Отметка посещаемости** - отметка детей на тренировках с выбором даты
- **Детальная информация о детях** - дата рождения, родитель, телефон, количество посещений
- **Фильтрация активных детей** - показываются только дети, не находящиеся в архиве
- **Подсчет посещаемости** в текущем месяце

### Архитектура:
- **Бэкенд:** Django + Django REST Framework + JWT
- **Фронтенд:** React + Axios
- **База данных:** SQLite (для разработки)

## Структура проекта

```
AtlantService/
├── core/                    # Django бэкенд
│   ├── fotball/            # Основное приложение
│   │   ├── models.py       # Модели данных
│   │   ├── views.py        # API endpoints
│   │   └── urls.py         # URL маршруты
│   └── manage.py
├── front_football/         # React фронтенд
│   ├── src/
│   │   ├── components/     # React компоненты
│   │   ├── utils/          # API утилиты
│   │   └── App.js
│   └── package.json
└── API_DOCUMENTATION.md    # Подробная документация API
```

## API Endpoints

- `POST /api/login/` - Вход в систему
- `POST /api/logout/` - Выход из системы
- `GET /api/user-info/` - Информация о пользователе
- `GET /api/trainer/groups/` - Группы тренера
- `GET /api/trainer/group/{id}/` - Детали группы

## Подробная документация

См. файл `API_DOCUMENTATION.md` для полного описания API и функций системы.