import axios from 'axios';

// Базовый URL для API
const API_BASE_URL = 'http://localhost:8000';

// Создаем экземпляр axios с базовой конфигурацией
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Интерцептор для добавления токена авторизации к каждому запросу
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Интерцептор для обработки ответов
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Если токен истек или недействителен
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

/**
 * API функции для аутентификации
 */
export const authAPI = {
  /**
   * Вход в систему
   * @param {string} username - логин пользователя
   * @param {string} password - пароль пользователя
   * @returns {Promise} - ответ с токеном и информацией о пользователе
   */
  login: async (username, password) => {
    try {
      const response = await api.post('/api/login/', {
        username,
        password,
      });
      
      // Сохраняем токен и информацию о пользователе
      if (response.data.token) {
        localStorage.setItem('token', response.data.token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
      }
      
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Выход из системы
   * @returns {Promise} - результат выхода
   */
  logout: async () => {
    try {
      await api.post('/api/logout/');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      return { success: true };
    } catch (error) {
      // Даже если запрос не прошел, очищаем локальное хранилище
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение информации о текущем пользователе
   * @returns {Promise} - информация о пользователе
   */
  getUserInfo: async () => {
    try {
      const response = await api.get('/api/user-info/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

/**
 * API функции для тренера
 */
export const trainerAPI = {
  /**
   * Получение всех групп тренера
   * @returns {Promise} - список групп с информацией о тренере
   */
  getGroups: async () => {
    try {
      const response = await api.get('/api/trainer/groups/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение детальной информации о группе
   * @param {number} groupId - ID группы
   * @returns {Promise} - детальная информация о группе и детях
   */
  getGroupDetail: async (groupId) => {
    try {
      const response = await api.get(`/api/trainer/group/${groupId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение данных для отметки посещаемости (сады и группы)
   * @returns {Promise} - список садов с группами
   */
  getAttendanceData: async () => {
    try {
      const response = await api.get('/api/trainer/attendance/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение списка детей группы для отметки посещаемости
   * @param {number} groupId - ID группы
   * @returns {Promise} - список детей в группе
   */
  getGroupChildren: async (groupId) => {
    try {
      const response = await api.get(`/api/trainer/attendance/group/${groupId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Создание записей посещаемости
   * @param {Object} data - данные посещаемости
   * @param {number} data.group_id - ID группы
   * @param {string} data.date - дата в формате YYYY-MM-DD
   * @param {Array} data.attendance_data - массив записей посещаемости
   * @returns {Promise} - результат создания
   */
  createAttendance: async (data) => {
    try {
      const response = await api.post('/api/trainer/attendance/', data);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение истории посещаемости группы
   * @param {number} groupId - ID группы
   * @param {string} dateFrom - дата начала (опционально)
   * @param {string} dateTo - дата окончания (опционально)
   * @returns {Promise} - история посещаемости
   */
  getAttendanceHistory: async (groupId, dateFrom = null, dateTo = null) => {
    try {
      const params = new URLSearchParams();
      if (dateFrom) params.append('date_from', dateFrom);
      if (dateTo) params.append('date_to', dateTo);
      
      const response = await api.get(`/api/trainer/attendance/history/${groupId}/?${params}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

/**
 * API функции для администратора
 */
export const adminAPI = {
  // Здесь будут функции для администратора
  // Например: управление пользователями, группами, тренерами
};

/**
 * API функции для родителя
 */
export const parentAPI = {
  // Здесь будут функции для родителя
  // Например: просмотр информации о ребенке, посещаемости
};

/**
 * Утилитарные функции для работы с API
 */
export const apiUtils = {
  /**
   * Проверка, авторизован ли пользователь
   * @returns {boolean} - true если пользователь авторизован
   */
  isAuthenticated: () => {
    return !!localStorage.getItem('token');
  },

  /**
   * Получение текущего пользователя из localStorage
   * @returns {Object|null} - информация о пользователе или null
   */
  getCurrentUser: () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  },

  /**
   * Получение токена из localStorage
   * @returns {string|null} - токен или null
   */
  getToken: () => {
    return localStorage.getItem('token');
  },

  /**
   * Очистка всех данных авторизации
   */
  clearAuth: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },

  /**
   * Обработка ошибок API
   * @param {Error} error - ошибка от API
   * @returns {string} - понятное сообщение об ошибке
   */
  handleError: (error) => {
    if (error.response?.data?.error) {
      return error.response.data.error;
    }
    if (error.response?.data?.details) {
      // Если есть детали ошибки валидации
      const details = error.response.data.details;
      if (typeof details === 'object') {
        return Object.values(details).flat().join(', ');
      }
      return details;
    }
    if (error.message) {
      return error.message;
    }
    return 'Произошла неизвестная ошибка';
  },
};

// Экспортируем основной экземпляр axios для прямого использования
export default api; 