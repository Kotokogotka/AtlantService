# API Документация - Система управления футбольными группами

## Обзор

Система состоит из Django бэкенда и React фронтенда. API построен на Django REST Framework с JWT аутентификацией.

## Структура проекта

```
AtlantService/
├── core/                    # Django бэкенд
│   ├── core/               # Основные настройки Django
│   ├── fotball/            # Основное приложение
│   │   ├── models.py       # Модели данных
│   │   ├── views.py        # API endpoints
│   │   ├── urls.py         # URL маршруты
│   │   └── management/     # Django команды
│   └── manage.py
└── front_football/         # React фронтенд
    ├── src/
    │   ├── components/     # React компоненты
    │   ├── utils/          # Утилиты (включая api.js)
    │   └── App.js
    └── package.json
```

## API Endpoints

### Аутентификация

#### POST /api/login/
**Описание:** Вход в систему
**Параметры:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Ответ:**
```json
{
  "success": true,
  "message": "Вы успешно вошли как Тренер",
  "token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "user": {
    "id": 1,
    "username": "trainer1",
    "role": "trainer",
    "role_display": "Тренер"
  }
}
```

#### POST /api/logout/
**Описание:** Выход из системы
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "message": "Вы успешно вышли из системы"
}
```

#### GET /api/user-info/
**Описание:** Получение информации о текущем пользователе
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "username": "trainer1",
    "role": "trainer"
  }
}
```

### API для тренера

#### GET /api/trainer/groups/
**Описание:** Получение всех групп тренера
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "trainer_info": {
    "full_name": "Иванов Иван Иванович",
    "phone": "+7 (999) 123-45-67",
    "work_space": "Детский сад №1, группы 1-3"
  },
  "groups": [
    {
      "id": 1,
      "name": "Солнышко",
      "age_level": "Младшая",
      "children_count": 4
    }
  ],
  "groups_count": 3
}
```

#### GET /api/trainer/group/{group_id}/
**Описание:** Получение детальной информации о группе
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "group": {
    "id": 1,
    "name": "Солнышко",
    "age_level": "Младшая",
    "children_count": 4
  },
  "children": [
    {
      "id": 1,
      "full_name": "Алексей Сидорова",
      "birth_date": "2018-05-15",
      "is_active": true,
      "parent_name": "Сидорова Мария Петровна"
    }
  ],
  "children_count": 4
}
```

## Файл api.js - Подробное описание

Файл `front_football/src/utils/api.js` содержит все функции для работы с API.

### Основные компоненты:

#### 1. Настройка axios
```javascript
const API_BASE_URL = 'http://localhost:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});
```

#### 2. Интерцепторы
- **Request Interceptor:** Автоматически добавляет JWT токен к каждому запросу
- **Response Interceptor:** Обрабатывает ошибки 401 (неавторизован) и перенаправляет на страницу входа

#### 3. API модули

##### authAPI
```javascript
export const authAPI = {
  login: async (username, password) => { /* ... */ },
  logout: async () => { /* ... */ },
  getUserInfo: async () => { /* ... */ }
};
```

**Функции:**
- `login(username, password)` - вход в систему, сохраняет токен в localStorage
- `logout()` - выход из системы, очищает localStorage
- `getUserInfo()` - получение информации о текущем пользователе

##### trainerAPI
```javascript
export const trainerAPI = {
  getGroups: async () => { /* ... */ },
  getGroupDetail: async (groupId) => { /* ... */ }
};
```

**Функции:**
- `getGroups()` - получение всех групп тренера
- `getGroupDetail(groupId)` - получение детальной информации о группе

##### apiUtils
```javascript
export const apiUtils = {
  isAuthenticated: () => { /* ... */ },
  getCurrentUser: () => { /* ... */ },
  getToken: () => { /* ... */ },
  clearAuth: () => { /* ... */ },
  handleError: (error) => { /* ... */ }
};
```

**Функции:**
- `isAuthenticated()` - проверка авторизации пользователя
- `getCurrentUser()` - получение текущего пользователя из localStorage
- `getToken()` - получение JWT токена
- `clearAuth()` - очистка данных авторизации
- `handleError(error)` - обработка ошибок API

## Использование в React компонентах

### Пример использования в TrainerDashboard:

```javascript
import { trainerAPI, apiUtils } from '../../utils/api';

function TrainerDashboard() {
  const [groups, setGroups] = useState([]);
  const [error, setError] = useState(null);

  const loadGroups = async () => {
    try {
      const response = await trainerAPI.getGroups();
      if (response.success) {
        setGroups(response.groups);
      }
    } catch (err) {
      const errorMessage = apiUtils.handleError(err);
      setError(errorMessage);
    }
  };

  // ...
}
```

## Модели данных

### User (Пользователь)
- `username` - логин
- `password` - пароль (захэшированный)
- `role` - роль (admin/trainer/parent)
- `linked_trainer` - связанный тренер
- `linked_child` - связанный ребенок

### Trainer (Тренер)
- `full_name` - ФИО
- `phone` - телефон
- `work_space` - место работы
- `groups` - группы (ManyToMany)

### GroupKidGarden (Группа)
- `name` - название группы
- `kindergarten_number` - номер детского сада
- `age_level` - возрастная группа (S/M/L)
- `trainer` - тренер группы

### Child (Ребенок)
- `full_name` - ФИО
- `birth_date` - дата рождения
- `parent_name` - родитель
- `group` - группа
- `is_active` - активен ли

## Создание тестовых данных

Для создания тестовых данных используйте команду:

```bash
cd core
python manage.py create_test_data
```

Это создаст:
- 2 тренеров с учетными записями
- 6 групп (по 3 на каждого тренера)
- 6 родителей
- 24 ребенка (по 4 в каждой группе)

## Запуск системы

### Бэкенд (Django):
```bash
cd core
python manage.py runserver
```

### Фронтенд (React):
```bash
cd front_football
npm start
```

## Тестовые учетные записи

После создания тестовых данных доступны:

1. **Тренер 1:**
   - Логин: `trainer1`
   - Пароль: `password123`

2. **Тренер 2:**
   - Логин: `trainer2`
   - Пароль: `password123`

### API для родителя

#### GET /api/parent/child-info/
**Описание:** Получение информации о ребенке родителя
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "child": {
    "id": 1,
    "full_name": "Иванов Алексей Сергеевич",
    "birth_date": "2018-05-15",
    "is_active": true,
    "group": {
      "id": 1,
      "name": "Старшая группа",
      "kindergarten_number": 15,
      "age_level": "Старшая"
    }
  }
}
```

#### GET /api/parent/attendance/
**Описание:** Получение посещаемости ребенка
**Заголовки:** `Authorization: Bearer <token>`
**Параметры запроса:**
- `month` (int, optional) - месяц (1-12), по умолчанию текущий месяц
- `year` (int, optional) - год, по умолчанию текущий год

**Ответ:**
```json
{
  "success": true,
  "child": {
    "id": 1,
    "full_name": "Иванов Алексей Сергеевич",
    "group_name": "Старшая группа"
  },
  "attendance_stats": {
    "total_training_days": 12,
    "attended_days": 10,
    "missed_days": 2,
    "attendance_percentage": 83.3
  },
  "attendance_records": [
    {
      "date": "2024-01-15",
      "status": true,
      "reason": null,
      "group_name": "Старшая группа"
    },
    {
      "date": "2024-01-17",
      "status": false,
      "reason": "Болел",
      "group_name": "Старшая группа"
    }
  ],
  "period": {
    "month": 1,
    "year": 2024
  }
}
```

#### GET /api/parent/next-training/
**Описание:** Получение информации о следующей тренировке
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "next_training": {
    "group": {
      "id": 1,
      "name": "Старшая группа",
      "kindergarten_number": 15,
      "age_level": "Старшая"
    },
    "message": "Расписание тренировок будет доступно в ближайшее время"
  }
}
```

#### GET /api/parent/comments/
**Описание:** Получение комментариев тренера о ребенке
**Заголовки:** `Authorization: Bearer <token>`
**Ответ:**
```json
{
  "success": true,
  "comments": [
    {
      "id": 1,
      "date": "2024-01-15",
      "trainer_name": "Иванов И.И.",
      "comment": "Ребенок хорошо занимается, показывает прогресс в координации движений.",
      "type": "positive"
    },
    {
      "id": 2,
      "date": "2024-01-10",
      "trainer_name": "Иванов И.И.",
      "comment": "Рекомендую больше внимания уделить растяжке.",
      "type": "recommendation"
    }
  ],
  "message": "Функция комментариев будет доступна после реализации в кабинете тренера"
}
```

## API для справок о болезни

### GET /api/parent/payment-calculation/
Получение расчета предварительной суммы к оплате за текущий месяц.

**Заголовки:**
- `Authorization: Bearer <token>`

**Ответ:**
```json
{
  "month": 9,
  "year": 2025,
  "total_trainings": 8,
  "attended_trainings": 2,
  "missed_trainings": 6,
  "excused_days": 4,
  "unexcused_missed": 2,
  "cost_per_lesson": 500.0,
  "amount_to_pay": 1000.0
}
```

**Поля ответа:**
- `month` - номер месяца
- `year` - год
- `total_trainings` - общее количество тренировок в месяце
- `attended_trainings` - количество посещенных тренировок
- `missed_trainings` - количество пропущенных тренировок
- `excused_days` - количество дней с уважительной причиной (одобренные справки)
- `unexcused_missed` - количество пропусков без уважительной причины
- `cost_per_lesson` - стоимость одного занятия
- `amount_to_pay` - сумма к доплате

### GET /api/parent/medical-certificates/
Получение списка справок о болезни ребенка родителя.

**Заголовки:**
- `Authorization: Bearer <token>`

**Ответ:**
```json
{
  "certificates": [
    {
      "id": 1,
      "date_from": "01.01.2025",
      "date_to": "05.01.2025",
      "note": "Дополнительная информация",
      "absence_reason": "ОРВИ, высокая температура",
      "uploaded_at": "06.01.2025 14:30",
      "status": "На рассмотрении",
      "status_code": "pending",
      "admin_comment": null,
      "cost_per_lesson": 500.0,
      "total_cost": 2500.0,
      "file_url": "/media/medical_certificates/2025/01/06/certificate.pdf",
      "file_name": "certificate.pdf"
    }
  ],
  "child_name": "Иванов Алексей Сергеевич"
}
```

### POST /api/parent/medical-certificates/
Загрузка справки о болезни или запрос на перерасчет.

**Заголовки:**
- `Authorization: Bearer <token>`
- `Content-Type: multipart/form-data`

**Параметры:**
- `date_from` (string, обязательный) - дата начала болезни/отсутствия (YYYY-MM-DD)
- `date_to` (string, обязательный) - дата окончания болезни/отсутствия (YYYY-MM-DD)
- `note` (string, необязательный) - примечание (для обычной справки)
- `absence_reason` (string, необязательный) - причина отсутствия для перерасчета (для запроса на перерасчет)
- `certificate_file` (file, необязательный) - файл справки (обязателен для обычной справки, необязателен для запроса на перерасчет)

**Ответ:**
```json
{
  "message": "Справка успешно загружена",
  "certificate_id": 1
}
```

### GET /api/admin/medical-certificates/
Получение всех справок для администратора.

**Заголовки:**
- `Authorization: Bearer <token>`

**Ответ:**
```json
{
  "certificates": [
    {
      "id": 1,
      "child_name": "Иванов Алексей Сергеевич",
      "parent_name": "parent",
      "date_from": "01.01.2025",
      "date_to": "05.01.2025",
      "note": "Дополнительная информация",
      "absence_reason": "ОРВИ, высокая температура",
      "uploaded_at": "06.01.2025 14:30",
      "status": "На рассмотрении",
      "status_code": "pending",
      "admin_comment": null,
      "cost_per_lesson": 500.0,
      "total_cost": 2500.0,
      "file_url": "/media/medical_certificates/2025/01/06/certificate.pdf",
      "file_name": "certificate.pdf"
    }
  ]
}
```

## Создание тестовых данных

### Для тренера:
```bash
cd core
python manage.py create_test_user
```

### Для родителя:
```bash
cd core
python manage.py create_test_parent
```

## Тестовые учетные записи

После создания тестовых данных доступны:

1. **Тренер:**
   - Логин: `trainer`
   - Пароль: `trainer123`

2. **Родитель:**
   - Логин: `parent`
   - Пароль: `parent123`

## Особенности реализации

1. **JWT аутентификация** - безопасная аутентификация без состояния
2. **Автоматическое управление токенами** - интерцепторы axios
3. **Обработка ошибок** - централизованная обработка ошибок API
4. **Responsive дизайн** - адаптивный интерфейс для мобильных устройств
5. **Модульная архитектура** - разделение API по функциональности
6. **Кабинет родителя** - полный функционал просмотра посещаемости и информации о ребенке
7. **Справки о болезни** - загрузка и просмотр медицинских справок родителями 