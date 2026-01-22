import axios from 'axios';

// Базовый URL для API
// Локальный Django API
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

  /**
   * Получение комментариев тренера и списка детей
   * @returns {Promise} - комментарии и список детей
   */
  getComments: async () => {
    try {
      const response = await api.get('/api/trainer/comments/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Создание нового комментария
   * @param {Object} commentData - данные комментария
   * @param {number} commentData.child_id - ID ребенка
   * @param {string} commentData.comment_text - текст комментария
   * @returns {Promise} - результат создания
   */
  createComment: async (commentData) => {
    try {
      const response = await api.post('/api/trainer/comments/', commentData);
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
  /**
   * Получение всех справок о болезни
   * @returns {Promise} - список всех справок
   */
  getMedicalCertificates: async () => {
    try {
      const response = await api.get('/api/admin/medical-certificates/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Подтверждение справки о болезни
   * @param {number} certificateId - ID справки
   * @returns {Promise} - результат операции
   */
  approveMedicalCertificate: async (certificateId) => {
    try {
      const response = await api.post(`/api/admin/medical-certificates/${certificateId}/approve/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Отклонение справки о болезни
   * @param {number} certificateId - ID справки
   * @returns {Promise} - результат операции
   */
  rejectMedicalCertificate: async (certificateId) => {
    try {
      const response = await api.post(`/api/admin/medical-certificates/${certificateId}/reject/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение групп для составления расписания
   * @returns {Promise} - список садов и групп
   */
  getGroupsForSchedule: async () => {
    try {
      const response = await api.get('/api/admin/schedule/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Создание новой тренировки (одиночной или массовое создание)
   * @param {Object} trainingData - данные о тренировке
   * @returns {Promise} - результат создания
   */
  createTraining: async (trainingData) => {
    try {
      const response = await api.post('/api/admin/schedule/', trainingData);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Массовое создание тренировок
   * @param {Object} bulkData - данные для массового создания
   * @returns {Promise} - результат создания
   */
  createBulkTrainings: async (bulkData) => {
    try {
      const response = await api.post('/api/admin/schedule/', {
        ...bulkData,
        bulk_create: true
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Обновление существующей тренировки
   * @param {number} trainingId - ID тренировки
   * @param {Object} trainingData - обновленные данные
   * @returns {Promise} - результат обновления
   */
  updateTraining: async (trainingId, trainingData) => {
    try {
      const response = await api.put(`/api/admin/schedule/${trainingId}/`, trainingData);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Удаление тренировки
   * @param {number} trainingId - ID тренировки
   * @returns {Promise} - результат удаления
   */
  deleteTraining: async (trainingId) => {
    try {
      const response = await api.delete(`/api/admin/schedule/${trainingId}/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  // Получить данные о посещениях детей
  getAttendanceData: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      if (filters.groupId) params.append('group_id', filters.groupId);
      if (filters.childId) params.append('child_id', filters.childId);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      
      const response = await api.get(`/api/admin/attendance/?${params.toString()}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  // Получить данные для таблицы посещений
  getAttendanceTableData: async (month) => {
    try {
      const response = await api.get(`/api/admin/attendance-table/?month=${month}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  // Получить детей группы
  getGroupChildren: async (groupId) => {
    try {
      const response = await api.get(`/api/admin/group-children/?group_id=${groupId}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

/**
 * API функции для родителя
 */
export const parentAPI = {
  /**
   * Получение информации о ребенке родителя
   * @returns {Promise} - информация о ребенке
   */
  getChildInfo: async () => {
    try {
      const response = await api.get('/api/parent/child-info/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение посещаемости ребенка
   * @param {number} month - месяц (1-12)
   * @param {number} year - год
   * @returns {Promise} - данные о посещаемости
   */
  getAttendance: async (month = null, year = null) => {
    try {
      const params = new URLSearchParams();
      if (month) params.append('month', month);
      if (year) params.append('year', year);
      
      const response = await api.get(`/api/parent/attendance/?${params}`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение информации о следующей тренировке
   * @returns {Promise} - информация о следующей тренировке
   */
  getNextTraining: async () => {
    try {
      const response = await api.get('/api/parent/next-training/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение комментариев тренера о ребенке
   * @returns {Promise} - комментарии тренера
   */
  getComments: async () => {
    try {
      const response = await api.get('/api/parent/comments/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение справок о болезни ребенка
   * @returns {Promise} - список справок
   */
  getMedicalCertificates: async () => {
    try {
      const response = await api.get('/api/parent/medical-certificates/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Загрузка справки о болезни
   * @param {FormData} formData - данные формы с файлом
   * @returns {Promise} - результат загрузки
   */
  uploadMedicalCertificate: async (formData) => {
    try {
      const response = await api.post('/api/parent/medical-certificates/', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение расчета суммы к оплате
   * @returns {Promise} - данные о сумме к оплате
   */
  getPaymentCalculation: async () => {
    try {
      const response = await api.get('/api/parent/payment-calculation/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
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

/**
 * Универсальная функция для выполнения API запросов
 * @param {string} url - URL endpoint
 * @param {string} method - HTTP метод
 * @param {Object} data - данные для отправки (опционально)
 * @returns {Promise} - ответ от API
 */
export const apiRequest = async (url, method = 'GET', data = null) => {
  try {
    const config = {
      method: method.toLowerCase(),
      url: url,
    };
    
    if (data) {
      if (method.toLowerCase() === 'get') {
        config.params = data;
      } else {
        config.data = data;
      }
    }
    
    const response = await api(config);
    return response.data;
  } catch (error) {
    throw error.response?.data || { error: 'Ошибка сети' };
  }
};

/**
 * API функции для расписания (для всех ролей)
 */
export const scheduleAPI = {
  /**
   * Получение расписания тренировок
   * @returns {Promise} - список тренировок
   */
  getSchedule: async () => {
    try {
      const response = await api.get('/api/schedule/');
      // API возвращает {trainings: [...], count: N}, но нам нужен массив
      return response.data.trainings || [];
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получение уведомлений об изменениях расписания
   * @returns {Promise} - список уведомлений
   */
  getNotifications: async () => {
    try {
      const response = await api.get('/api/schedule/notifications/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Отметить уведомление как прочитанное
   * @param {number} notificationId - ID уведомления
   * @returns {Promise} - результат операции
   */
  markNotificationAsRead: async (notificationId) => {
    try {
      const response = await api.post(`/api/schedule/notifications/${notificationId}/read/`);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

/**
 * API функции для работы с оплатой
 */
export const paymentAPI = {
  /**
   * Получить счета на оплату для родителя
   * @returns {Promise} - список счетов
   */
  getInvoices: async () => {
    try {
      const response = await api.get('/api/parent/invoices/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Сгенерировать счета на следующий месяц (только для админов)
   * @returns {Promise} - результат генерации
   */
  generateInvoices: async () => {
    try {
      const response = await api.post('/api/admin/generate-invoices/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Получить настройки оплаты (только для админов)
   * @returns {Promise} - настройки оплаты
   */
  getPaymentSettings: async () => {
    try {
      const response = await api.get('/api/admin/payment-settings/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },

  /**
   * Обновить настройки оплаты (только для админов)
   * @param {Object} settings - настройки для обновления
   * @returns {Promise} - результат обновления
   */
  updatePaymentSettings: async (settings) => {
    try {
      const response = await api.put('/api/admin/payment-settings/', settings);
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

// API для уведомлений об отмене тренировок
export const cancellationNotificationsAPI = {
  /**
   * Получить уведомления об отмене тренировок
   * @returns {Promise} - список уведомлений
   */
  getNotifications: async () => {
    try {
      const response = await api.get('/api/training-cancellation-notifications/');
      return response.data;
    } catch (error) {
      throw error.response?.data || { error: 'Ошибка сети' };
    }
  },
};

// Экспортируем основной экземпляр axios для прямого использования
export default api; 