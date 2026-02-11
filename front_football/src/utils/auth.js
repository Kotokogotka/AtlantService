import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL !== undefined
  ? process.env.REACT_APP_API_URL
  : (process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '');

export const checkAuthStatus = async () => {
  const token = localStorage.getItem('token');
  if (!token) return null;

  try {
    const response = await axios.get(`${API_BASE_URL}/api/user-info/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.data.success) {
      return {
        ...response.data.user,
        loginTime: new Date().toLocaleString('ru-RU')
      };
    }
  } catch (err) {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
  }
  
  return null;
};

export const login = async (username, password) => {
  console.log('DEBUG: Отправляем запрос на вход:', { username, password });
  console.log('DEBUG: URL запроса:', `${API_BASE_URL}/api/login/`);
  
  const response = await axios.post(`${API_BASE_URL}/api/login/`, {
    username: username.trim(),
    password: password
  });

  console.log('DEBUG: Ответ от сервера:', response.data);

  if (response.data.success) {
    console.log('DEBUG: Успешный вход, сохраняем токены');
    localStorage.setItem('token', response.data.token);
    localStorage.setItem('refresh_token', response.data.refresh_token);
    
    const userInfo = {
      ...response.data.user,
      loginTime: new Date().toLocaleString('ru-RU')
    };
    
    console.log('DEBUG: Возвращаем информацию о пользователе:', userInfo);
    return userInfo;
  }
  
  throw new Error(response.data.error || 'Ошибка входа');
};

export const logout = async () => {
  const token = localStorage.getItem('token');
  if (token) {
    try {
      await axios.post(`${API_BASE_URL}/api/logout/`, {}, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
    } catch (err) {
      // Игнорируем ошибки при выходе
    }
  }
  
  localStorage.removeItem('token');
  localStorage.removeItem('refresh_token');
};