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

# Создаем тестового тренера
python manage.py create_test_user

# Создаем тестового родителя
python manage.py create_test_parent

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

### Тренер:
- **Логин:** `trainer` | **Пароль:** `trainer123`

### Родитель:
- **Логин:** `parent` | **Пароль:** `parent123`

### Администратор:
- **Логин:** `admin` | **Пароль:** `admin123`

## Функциональность

### Для тренеров:
1. **Просмотр групп** - просмотр всех групп, которые ведет тренер
2. **Отметка посещаемости** - отметка детей на тренировках с выбором даты
3. **История посещаемости** - просмотр истории посещаемости по группам

### Для родителей:
1. **Информация о ребенке** - полная информация о ребенке и его группе
2. **Посещаемость** - просмотр посещаемости с фильтрацией по месяцам
3. **Статистика** - процент посещаемости, количество пропусков
4. **Комментарии тренера** - комментарии и рекомендации от тренера
5. **Следующая тренировка** - информация о предстоящих занятиях
6. **Справки и перерасчет** - загрузка медицинских справок и запросы на перерасчет
7. **Сумма к оплате** - расчет стоимости занятий с учетом пропусков

### Для администраторов:
1. **Уведомления о справках** - просмотр всех справок и запросов на перерасчет
2. **Подтверждение/отклонение справок** - управление статусом справок
3. **Просмотр деталей справок** - полная информация о справке и прикрепленных файлах

### Особенности:
- Показываются только активные дети (не в архиве)
- Отображается количество посещенных занятий в текущем месяце
- Показывается телефон родителя
- Интуитивный интерфейс с навигацией между функциями
- Адаптивный дизайн для мобильных устройств

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

### Общие:
- `POST /api/login/` - авторизация
- `POST /api/logout/` - выход из системы
- `GET /api/user-info/` - информация о пользователе

### Для тренеров:
- `GET /api/trainer/groups/` - группы тренера
- `GET /api/trainer/group/{id}/` - детали группы
- `GET /api/trainer/attendance/` - данные для посещаемости
- `POST /api/trainer/attendance/` - создание посещаемости
- `GET /api/trainer/attendance/group/{id}/` - дети группы для посещаемости
- `GET /api/trainer/attendance/history/{id}/` - история посещаемости

### Для родителей:
- `GET /api/parent/child-info/` - информация о ребенке
- `GET /api/parent/attendance/` - посещаемость ребенка
- `GET /api/parent/next-training/` - следующая тренировка
- `GET /api/parent/comments/` - комментарии тренера
- `GET /api/parent/medical-certificates/` - справки о болезни
- `POST /api/parent/medical-certificates/` - загрузка справки о болезни

### Для администратора:
- `GET /api/admin/medical-certificates/` - все справки о болезни
- `POST /api/admin/medical-certificates/{id}/approve/` - подтверждение справки
- `POST /api/admin/medical-certificates/{id}/reject/` - отклонение справки

## Технологии

- **Backend:** Django 5.2, Django REST Framework, PostgreSQL
- **Frontend:** React 18, CSS Modules, Axios
- **Authentication:** JWT (JSON Web Tokens)
- **Database:** PostgreSQL 